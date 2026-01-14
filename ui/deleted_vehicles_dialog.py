# ui/deleted_vehicles_dialog.py
"""
Deleted Vehicles Dialog - Giao diện quản lý xe đã xóa (soft delete).

Cung cấp:
- Xem danh sách xe đã xóa mềm
- Khôi phục xe đã xóa
- Xóa vĩnh viễn (hard delete)
- Xem lịch sử xe đã xóa vĩnh viễn
"""

import customtkinter as ctk
from tkinter import messagebox
from tkinter import ttk
import logging
from datetime import datetime
from typing import Optional, List, Callable
from translations import get_translation

logger = logging.getLogger(__name__)


class DeletedVehiclesDialog(ctk.CTkToplevel):
    """
    Dialog quản lý xe đã xóa.
    
    Features:
    - Tab 1: Xe đã xóa mềm (có thể khôi phục)
    - Tab 2: Xe đã xóa vĩnh viễn (chỉ xem)
    - Tìm kiếm và lọc
    - Khôi phục / Xóa vĩnh viễn
    """
    
    def __init__(
        self, 
        parent, 
        vehicle_manager,
        on_restore_callback: Optional[Callable] = None
    ):
        """
        Khởi tạo DeletedVehiclesDialog.
        
        Args:
            parent: Widget cha (main window)
            vehicle_manager: VehicleManager instance
            on_restore_callback: Callback được gọi sau khi restore thành công
        """
        super().__init__(parent)
        self.transient(parent)
        self.parent = parent
        self.vehicle_manager = vehicle_manager
        self.on_restore_callback = on_restore_callback
        # Ngôn ngữ hiện tại
        self.lang = getattr(parent, 'current_lang', None).get() if hasattr(parent, 'current_lang') else 'vi'
        # Window config
        self.title(get_translation("dialog_deleted_vehicles_title", self.lang))
        self.geometry("1100x650")
        self.minsize(900, 550)
        
        # Data
        self.deleted_vehicles: List[dict] = []
        self.archived_vehicles: List[dict] = []
        self.selected_deleted: Optional[dict] = None
        self.selected_archived: Optional[dict] = None
        
        # Pagination
        self.page_size = 50
        self.current_page_deleted = 0
        self.current_page_archived = 0
        self.total_deleted = 0
        self.total_archived = 0
        
        # Search/filter
        self.search_term = ""
        self.owner_filter = ""
        
        # Font settings (from parent if available)
        try:
            self.font_normal = parent.font_normal
            self.font_bold = parent.font_bold
        except AttributeError:
            self.font_normal = ctk.CTkFont(size=13)
            self.font_bold = ctk.CTkFont(size=13, weight="bold")
        
        self._setup_ui()
        self._load_deleted_vehicles()
        self._load_archived_vehicles()
        
        # Modal
        self.grab_set()
        self.focus_force()
    
    def _setup_ui(self):
        """Thiết lập giao diện."""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        # Tabview
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.pack(fill="both", expand=True)
        # Tab 1: Soft deleted (recoverable)
        self.tab_deleted = self.tabview.add(get_translation("tab_deleted_vehicles", self.lang))
        self._setup_deleted_tab()
        # Tab 2: Hard deleted (permanent archive)
        self.tab_archived = self.tabview.add(get_translation("tab_archived_vehicles", self.lang))
        self._setup_archived_tab()
        # Bottom buttons
        bottom_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_frame.pack(fill="x", pady=(10, 0))
        ctk.CTkButton(
            bottom_frame,
            text=get_translation("btn_close", self.lang),
            command=self.destroy,
            font=self.font_normal,
            width=100
        ).pack(side="right")
    
    def _setup_deleted_tab(self):
        """Setup tab xe đã xóa mềm."""
        # Search frame
        search_frame = ctk.CTkFrame(self.tab_deleted, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            search_frame, 
            text="🔍 " + get_translation("lbl_search", self.lang) + ":",
            font=self.font_normal
        ).pack(side="left", padx=(0, 5))
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text=get_translation("search_deleted_placeholder", self.lang),
            width=250,
            font=self.font_normal
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<Return>", lambda e: self._search_deleted())
        
        ctk.CTkButton(
            search_frame,
            text=get_translation("btn_find", self.lang),
            command=self._search_deleted,
            font=self.font_normal,
            width=80
        ).pack(side="left", padx=(0, 20))
        
        # Stats label
        self.stats_label = ctk.CTkLabel(
            search_frame,
            text=get_translation("loading", self.lang),
            font=self.font_normal
        )
        self.stats_label.pack(side="left")
        
        # Treeview frame
        tree_frame = ctk.CTkFrame(self.tab_deleted, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True)
        
        # Columns
        columns = ("vin", "owner", "vehicle_type", "date_in", "deleted_at", "deleted_by", "reason")
        
        self.deleted_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # Define headings
        self.deleted_tree.heading("vin", text=get_translation("col_vin", self.lang))
        self.deleted_tree.heading("owner", text=get_translation("col_owner", self.lang))
        self.deleted_tree.heading("vehicle_type", text=get_translation("col_vehicle_type", self.lang))
        self.deleted_tree.heading("date_in", text=get_translation("col_date_in", self.lang))
        self.deleted_tree.heading("deleted_at", text=get_translation("col_date_deleted", self.lang))
        self.deleted_tree.heading("deleted_by", text=get_translation("col_deleted_by", self.lang))
        self.deleted_tree.heading("reason", text=get_translation("col_delete_reason", self.lang))
        
        # Column widths
        self.deleted_tree.column("vin", width=160, minwidth=120)
        self.deleted_tree.column("owner", width=150, minwidth=100)
        self.deleted_tree.column("vehicle_type", width=100, minwidth=80)
        self.deleted_tree.column("date_in", width=100, minwidth=80)
        self.deleted_tree.column("deleted_at", width=140, minwidth=100)
        self.deleted_tree.column("deleted_by", width=100, minwidth=80)
        self.deleted_tree.column("reason", width=200, minwidth=100)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.deleted_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.deleted_tree.xview)
        self.deleted_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        self.deleted_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Selection binding
        self.deleted_tree.bind("<<TreeviewSelect>>", self._on_deleted_select)
        
        # Action buttons frame
        action_frame = ctk.CTkFrame(self.tab_deleted, fg_color="transparent")
        action_frame.pack(fill="x", pady=(10, 0))
        
        self.restore_btn = ctk.CTkButton(
            action_frame,
            text="♻️ " + get_translation("btn_restore_selected", self.lang),
            command=self._restore_selected,
            font=self.font_bold,
            fg_color="#28a745",
            hover_color="#218838",
            state="disabled",
            width=200
        )
        self.restore_btn.pack(side="left", padx=(0, 10))
        
        self.hard_delete_btn = ctk.CTkButton(
            action_frame,
            text="🗑️ " + get_translation("btn_delete_permanently", self.lang),
            command=self._hard_delete_selected,
            font=self.font_bold,
            fg_color="#dc3545",
            hover_color="#c82333",
            state="disabled",
            width=150
        )
        self.hard_delete_btn.pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            action_frame,
            text="🔄 " + get_translation("btn_refresh", self.lang),
            command=self._refresh_deleted,
            font=self.font_normal,
            width=100
        ).pack(side="left")
        
        # Pagination frame
        page_frame = ctk.CTkFrame(self.tab_deleted, fg_color="transparent")
        page_frame.pack(fill="x", pady=(5, 0))
        
        self.prev_btn_deleted = ctk.CTkButton(
            page_frame,
            text="◀ " + get_translation("btn_prev_page", self.lang),
            command=self._prev_page_deleted,
            font=self.font_normal,
            width=100,
            state="disabled"
        )
        self.prev_btn_deleted.pack(side="left")
        
        self.page_label_deleted = ctk.CTkLabel(
            page_frame,
            text=get_translation("pagination_label", self.lang).format(current=1, total=1),
            font=self.font_normal
        )
        self.page_label_deleted.pack(side="left", padx=20)
        
        self.next_btn_deleted = ctk.CTkButton(
            page_frame,
            text=get_translation("btn_next_page", self.lang) + " ▶",
            command=self._next_page_deleted,
            font=self.font_normal,
            width=100,
            state="disabled"
        )
        self.next_btn_deleted.pack(side="left")
    
    def _setup_archived_tab(self):
        """Setup tab xe đã xóa vĩnh viễn."""
        # Info label
        info_frame = ctk.CTkFrame(self.tab_archived, fg_color="transparent")
        info_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            info_frame,
            text="📋 " + get_translation("tab_archived_vehicles", self.lang) + " (" + get_translation("btn_delete_permanently", self.lang) + ")",
            font=self.font_normal,
            text_color="gray"
        ).pack(side="left")
        
        self.archived_stats_label = ctk.CTkLabel(
            info_frame,
            text="",
            font=self.font_normal
        )
        self.archived_stats_label.pack(side="right")
        
        # Treeview frame
        tree_frame = ctk.CTkFrame(self.tab_archived, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True)
        
        # Columns for archived
        columns = ("vin", "owner", "vehicle_type", "deleted_at", "deleted_by", "reason")
        
        self.archived_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # Define headings
        self.archived_tree.heading("vin", text=get_translation("col_vin", self.lang))
        self.archived_tree.heading("owner", text=get_translation("col_owner", self.lang))
        self.archived_tree.heading("vehicle_type", text=get_translation("col_vehicle_type", self.lang))
        self.archived_tree.heading("deleted_at", text=get_translation("col_date_deleted", self.lang))
        self.archived_tree.heading("deleted_by", text=get_translation("col_deleted_by", self.lang))
        self.archived_tree.heading("reason", text=get_translation("col_delete_reason", self.lang))
        
        # Column widths
        self.archived_tree.column("vin", width=160, minwidth=120)
        self.archived_tree.column("owner", width=180, minwidth=120)
        self.archived_tree.column("vehicle_type", width=120, minwidth=80)
        self.archived_tree.column("deleted_at", width=160, minwidth=120)
        self.archived_tree.column("deleted_by", width=120, minwidth=80)
        self.archived_tree.column("reason", width=250, minwidth=150)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.archived_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.archived_tree.xview)
        self.archived_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        self.archived_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bottom controls
        bottom_frame = ctk.CTkFrame(self.tab_archived, fg_color="transparent")
        bottom_frame.pack(fill="x", pady=(10, 0))
        # Refresh button
        ctk.CTkButton(
            bottom_frame,
            text="🔄 " + get_translation("btn_refresh", self.lang),
            command=self._refresh_archived,
            font=self.font_normal,
            width=100
        ).pack(side="left")
        # Clear all button
        ctk.CTkButton(
            bottom_frame,
            text="🧹 " + get_translation("btn_clear_all_archived", self.lang),
            command=self._clear_all_archived,
            font=self.font_normal,
            fg_color="#dc3545",
            hover_color="#c82333",
            width=180
        ).pack(side="left", padx=(10, 0))
        # Pagination
        self.prev_btn_archived = ctk.CTkButton(
            bottom_frame,
            text="◀ " + get_translation("btn_prev_page", self.lang),
            command=self._prev_page_archived,
            font=self.font_normal,
            width=100,
            state="disabled"
        )
        self.prev_btn_archived.pack(side="left", padx=(20, 0))
        self.page_label_archived = ctk.CTkLabel(
            bottom_frame,
            text=get_translation("pagination_label", self.lang).format(current=1, total=1),
            font=self.font_normal
        )
        self.page_label_archived.pack(side="left", padx=20)
        self.next_btn_archived = ctk.CTkButton(
            bottom_frame,
            text=get_translation("btn_next_page", self.lang) + " ▶",
            command=self._next_page_archived,
            font=self.font_normal,
            width=100,
            state="disabled"
        )
        self.next_btn_archived.pack(side="left")

    def _clear_all_archived(self):
        """Clear all permanently deleted vehicle logs."""
        if self.total_archived == 0:
            messagebox.showinfo(get_translation("info_title", self.lang), get_translation("no_archived_to_clear", self.lang), parent=self)
            return
        confirm = messagebox.askyesno(
            get_translation("confirm_clear_all_archived_title", self.lang),
            get_translation("confirm_clear_all_archived_msg", self.lang).format(total=self.total_archived),
            parent=self
        )
        if not confirm:
            return
        try:
            self.vehicle_manager.clear_archived_deleted_vehicles()
            messagebox.showinfo(
                get_translation("success_title", self.lang),
                get_translation("clear_all_archived_success", self.lang),
                parent=self
            )
            self._refresh_archived()
        except Exception as e:
            logger.error(f"Error clearing archived vehicles: {e}")
            messagebox.showerror(
                get_translation("error_title", self.lang),
                get_translation("clear_all_archived_error", self.lang).format(e=e),
                parent=self
            )
    
    # ========== Data Loading ==========
    
    def _load_deleted_vehicles(self):
        """Load danh sách xe đã xóa mềm."""
        try:
            offset = self.current_page_deleted * self.page_size
            
            self.deleted_vehicles = self.vehicle_manager.list_deleted_vehicles(
                limit=self.page_size,
                offset=offset,
                search_term=self.search_term if self.search_term else None,
                owner_filter=self.owner_filter if self.owner_filter else None
            )
            
            self.total_deleted = self.vehicle_manager.count_deleted_vehicles(
                search_term=self.search_term if self.search_term else None,
                owner_filter=self.owner_filter if self.owner_filter else None
            )
            
            self._populate_deleted_tree()
            self._update_deleted_stats()
            self._update_deleted_pagination()
            
        except Exception as e:
            logger.error(f"Error loading deleted vehicles: {e}")
            messagebox.showerror("Lỗi", f"Không thể tải danh sách xe đã xóa:\n{e}", parent=self)
    
    def _load_archived_vehicles(self):
        """Load danh sách xe đã xóa vĩnh viễn."""
        try:
            offset = self.current_page_archived * self.page_size
            
            self.archived_vehicles = self.vehicle_manager.get_archived_deleted_vehicles(
                limit=self.page_size,
                offset=offset
            )
            
            # Count total (simple approach - count from result)
            all_archived = self.vehicle_manager.get_archived_deleted_vehicles(limit=10000)
            self.total_archived = len(all_archived)
            
            self._populate_archived_tree()
            self._update_archived_stats()
            self._update_archived_pagination()
            
        except Exception as e:
            logger.error(f"Error loading archived vehicles: {e}")
            messagebox.showerror("Lỗi", f"Không thể tải danh sách lưu trữ:\n{e}", parent=self)
    
    def _populate_deleted_tree(self):
        """Populate treeview với dữ liệu xe đã xóa."""
        # Clear existing
        for item in self.deleted_tree.get_children():
            self.deleted_tree.delete(item)
        
        for vehicle in self.deleted_vehicles:
            # Format dates
            date_in = self._format_date(vehicle.get("date_in"))
            deleted_at = self._format_datetime(vehicle.get("deleted_at"))
            
            self.deleted_tree.insert("", "end", values=(
                vehicle.get("vin", ""),
                vehicle.get("owner", ""),
                vehicle.get("vehicle_type", ""),
                date_in,
                deleted_at,
                vehicle.get("deleted_by", ""),
                vehicle.get("delete_reason", "") or ""
            ))
    
    def _populate_archived_tree(self):
        """Populate treeview với dữ liệu xe đã xóa vĩnh viễn."""
        # Clear existing
        for item in self.archived_tree.get_children():
            self.archived_tree.delete(item)
        
        for vehicle in self.archived_vehicles:
            deleted_at = self._format_datetime(vehicle.get("deleted_at"))
            
            self.archived_tree.insert("", "end", values=(
                vehicle.get("vin", ""),
                vehicle.get("owner", ""),
                vehicle.get("vehicle_type", ""),
                deleted_at,
                vehicle.get("deleted_by", ""),
                vehicle.get("delete_reason", "") or ""
            ))
    
    def _format_date(self, date_str: str) -> str:
        """Format date string."""
        if not date_str:
            return ""
        try:
            if "T" in str(date_str):
                dt = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
                return dt.strftime("%d/%m/%Y")
            return str(date_str)[:10]
        except:
            return str(date_str)[:10] if date_str else ""
    
    def _format_datetime(self, dt_str: str) -> str:
        """Format datetime string."""
        if not dt_str:
            return ""
        try:
            if "T" in str(dt_str):
                dt = datetime.fromisoformat(str(dt_str).replace("Z", "+00:00"))
                return dt.strftime("%d/%m/%Y %H:%M")
            return str(dt_str)[:16]
        except:
            return str(dt_str)[:16] if dt_str else ""
    
    # ========== UI Updates ==========
    
    def _update_deleted_stats(self):
        """Update stats label cho tab deleted."""
        self.stats_label.configure(
            text=get_translation("deleted_stats_label", self.lang).format(total=self.total_deleted)
        )
    
    def _update_archived_stats(self):
        """Update stats label cho tab archived."""
        self.archived_stats_label.configure(
            text=get_translation("archived_stats_label", self.lang).format(total=self.total_archived)
        )
    
    def _update_deleted_pagination(self):
        """Update pagination controls cho tab deleted."""
        total_pages = max(1, (self.total_deleted + self.page_size - 1) // self.page_size)
        current = self.current_page_deleted + 1
        
        self.page_label_deleted.configure(text=get_translation("pagination_label", self.lang).format(current=current, total=total_pages))
        
        # Enable/disable buttons
        self.prev_btn_deleted.configure(
            state="normal" if self.current_page_deleted > 0 else "disabled"
        )
        self.next_btn_deleted.configure(
            state="normal" if current < total_pages else "disabled"
        )
    
    def _update_archived_pagination(self):
        """Update pagination controls cho tab archived."""
        total_pages = max(1, (self.total_archived + self.page_size - 1) // self.page_size)
        current = self.current_page_archived + 1
        
        self.page_label_archived.configure(text=get_translation("pagination_label", self.lang).format(current=current, total=total_pages))
        
        # Enable/disable buttons
        self.prev_btn_archived.configure(
            state="normal" if self.current_page_archived > 0 else "disabled"
        )
        self.next_btn_archived.configure(
            state="normal" if current < total_pages else "disabled"
        )
    
    # ========== Event Handlers ==========
    
    def _on_deleted_select(self, event):
        """Handle selection in deleted tree."""
        selection = self.deleted_tree.selection()
        if selection:
            item = self.deleted_tree.item(selection[0])
            values = item["values"]
            if values:
                vin = values[0]
                # Find the vehicle data
                self.selected_deleted = next(
                    (v for v in self.deleted_vehicles if v.get("vin") == vin),
                    None
                )
                self.restore_btn.configure(state="normal")
                self.hard_delete_btn.configure(state="normal")
        else:
            self.selected_deleted = None
            self.restore_btn.configure(state="disabled")
            self.hard_delete_btn.configure(state="disabled")
    
    def _search_deleted(self):
        """Search deleted vehicles."""
        self.search_term = self.search_entry.get().strip()
        self.current_page_deleted = 0
        self._load_deleted_vehicles()
    
    def _refresh_deleted(self):
        """Refresh deleted vehicles list."""
        self.search_term = ""
        self.search_entry.delete(0, "end")
        self.current_page_deleted = 0
        self._load_deleted_vehicles()
    
    def _refresh_archived(self):
        """Refresh archived vehicles list."""
        self.current_page_archived = 0
        self._load_archived_vehicles()
    
    def _prev_page_deleted(self):
        """Go to previous page (deleted)."""
        if self.current_page_deleted > 0:
            self.current_page_deleted -= 1
            self._load_deleted_vehicles()
    
    def _next_page_deleted(self):
        """Go to next page (deleted)."""
        total_pages = (self.total_deleted + self.page_size - 1) // self.page_size
        if self.current_page_deleted + 1 < total_pages:
            self.current_page_deleted += 1
            self._load_deleted_vehicles()
    
    def _prev_page_archived(self):
        """Go to previous page (archived)."""
        if self.current_page_archived > 0:
            self.current_page_archived -= 1
            self._load_archived_vehicles()
    
    def _next_page_archived(self):
        """Go to next page (archived)."""
        total_pages = (self.total_archived + self.page_size - 1) // self.page_size
        if self.current_page_archived + 1 < total_pages:
            self.current_page_archived += 1
            self._load_archived_vehicles()
    
    # ========== Actions ==========
    
    def _restore_selected(self):
        """Restore selected deleted vehicle."""
        if not self.selected_deleted:
            messagebox.showwarning(get_translation("warning_title", self.lang), get_translation("select_vehicle_restore_warning", self.lang), parent=self)
            return
        
        vin = self.selected_deleted.get("vin")
        owner = self.selected_deleted.get("owner", "")
        
        # Confirm
        confirm = messagebox.askyesno(
            get_translation("confirm_restore_title", self.lang),
            get_translation("confirm_restore_msg", self.lang).format(vin=vin, owner=owner),
            parent=self
        )
        
        if not confirm:
            return
        
        try:
            # Get current user (from parent if available)
            restored_by = "user"
            if hasattr(self.parent, 'current_user'):
                restored_by = self.parent.current_user or "user"
            
            result = self.vehicle_manager.restore_deleted_vehicle(
                vin=vin,
                restored_by=restored_by
            )
            
            if result["success"]:
                messagebox.showinfo(
                    get_translation("success_title", self.lang),
                    get_translation("restore_success_msg", self.lang).format(vin=vin),
                    parent=self
                )
                
                # Refresh list
                self._load_deleted_vehicles()
                
                # Clear selection
                self.selected_deleted = None
                self.restore_btn.configure(state="disabled")
                self.hard_delete_btn.configure(state="disabled")
                
                # Callback to refresh main window
                if self.on_restore_callback:
                    self.on_restore_callback()
            else:
                messagebox.showerror(
                    get_translation("error_title", self.lang),
                    get_translation("restore_error_msg", self.lang).format(msg=result.get('message', 'Unknown error')),
                    parent=self
                )
                
        except Exception as e:
            logger.error(f"Error restoring vehicle {vin}: {e}")
            messagebox.showerror(get_translation("error_title", self.lang), get_translation("restore_exception_msg", self.lang).format(e=e), parent=self)
    
    def _hard_delete_selected(self):
        """Permanently delete selected vehicle."""
        if not self.selected_deleted:
            messagebox.showwarning(get_translation("warning_title", self.lang), get_translation("select_vehicle_hard_delete_warning", self.lang), parent=self)
            return
        
        vin = self.selected_deleted.get("vin")
        owner = self.selected_deleted.get("owner", "")
        
        # Ask for reason
        reason_dialog = HardDeleteReasonDialog(self, vin, owner)
        
        if not reason_dialog.result:
            return
        
        reason = reason_dialog.result
        
        try:
            # Get current user
            deleted_by = "user"
            if hasattr(self.parent, 'current_user'):
                deleted_by = self.parent.current_user or "user"
            
            result = self.vehicle_manager.hard_delete_vehicle(
                vin=vin,
                deleted_by=deleted_by,
                delete_reason=reason
            )
            
            if result["success"]:
                messagebox.showinfo(
                    "Thành công",
                    f"Đã xóa vĩnh viễn xe {vin}.\n"
                    f"Dữ liệu đã được lưu vào bảng lưu trữ.",
                    parent=self
                )
                
                # Refresh both lists
                self._load_deleted_vehicles()
                self._load_archived_vehicles()
                
                # Clear selection
                self.selected_deleted = None
                self.restore_btn.configure(state="disabled")
                self.hard_delete_btn.configure(state="disabled")
                
            else:
                messagebox.showerror(
                    "Lỗi",
                    f"Không thể xóa vĩnh viễn xe:\n{result.get('message', 'Unknown error')}",
                    parent=self
                )
                
        except Exception as e:
            logger.error(f"Error hard deleting vehicle {vin}: {e}")
            messagebox.showerror("Lỗi", f"Lỗi khi xóa vĩnh viễn xe:\n{e}", parent=self)


class HardDeleteReasonDialog(ctk.CTkToplevel):
    """Dialog để nhập lý do xóa vĩnh viễn."""
    
    def __init__(self, parent, vin: str, owner: str):
        super().__init__(parent)
        self.transient(parent)
        # Language
        self.lang = getattr(parent, 'lang', 'vi') if hasattr(parent, 'lang') else 'vi'
        self.title(get_translation("hard_delete_dialog_title", self.lang))
        self.geometry("540x320")
        self.resizable(False, False)
        self.result = None
        # Warning frame
        warning_frame = ctk.CTkFrame(self, fg_color="#fff3cd")
        warning_frame.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(
            warning_frame,
            text=get_translation("hard_delete_warning", self.lang),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#856404"
        ).pack(pady=10)
        # Info
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(
            info_frame,
            text=f"VIN: {vin}",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w")
        ctk.CTkLabel(
            info_frame,
            text=get_translation("label_owner", self.lang) + f" {owner}",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w")
        # Reason input
        ctk.CTkLabel(
            self,
            text=get_translation("hard_delete_reason_label", self.lang),
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w", padx=20, pady=(10, 5))
        self.reason_entry = ctk.CTkEntry(
            self,
            placeholder_text=get_translation("hard_delete_reason_placeholder", self.lang),
            width=500,
            font=ctk.CTkFont(size=13)
        )
        self.reason_entry.pack(padx=20)
        self.reason_entry.focus()
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        ctk.CTkButton(
            btn_frame,
            text=get_translation("btn_cancel", self.lang),
            command=self._cancel,
            width=120
        ).pack(side="left")
        ctk.CTkButton(
            btn_frame,
            text=get_translation("btn_delete_permanently", self.lang),
            command=self._confirm,
            fg_color="#dc3545",
            hover_color="#c82333",
            width=180
        ).pack(side="right")
        # Bind Enter
        self.reason_entry.bind("<Return>", lambda e: self._confirm())
        self.grab_set()
        self.wait_window()
    
    def _confirm(self):
        """Confirm deletion."""
        reason = self.reason_entry.get().strip()
        if not reason:
            messagebox.showwarning(
                get_translation("warning_title", self.lang),
                get_translation("hard_delete_reason_required", self.lang),
                parent=self
            )
            return
        # Final confirmation
        if messagebox.askyesno(
            get_translation("hard_delete_final_confirm_title", self.lang),
            get_translation("hard_delete_final_confirm_msg", self.lang),
            parent=self
        ):
            self.result = reason
            self.destroy()
    
    def _cancel(self):
        """Cancel deletion."""
        self.result = None
        self.destroy()
