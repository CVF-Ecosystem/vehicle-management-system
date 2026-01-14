# ui/backup_dialog.py
"""
Backup and Restore Dialog - Giao diện quản lý sao lưu và phục hồi dữ liệu.

Cung cấp:
- Tạo backup thủ công
- Xem danh sách backups
- Phục hồi từ backup
- Xem chi tiết backup
- Xóa backup cũ
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
from tkinter import ttk
import logging
from datetime import datetime
from typing import Optional, List, Callable
from pathlib import Path

from core.backup_service import BackupService, BackupType, BackupMetadata
from database.audit_repository import log_backup, log_restore, AuditAction

logger = logging.getLogger(__name__)


def format_file_size(size_bytes: int) -> str:
    """Format file size thành chuỗi đọc được."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def format_datetime(dt: datetime) -> str:
    """Format datetime thành chuỗi đọc được."""
    return dt.strftime("%d/%m/%Y %H:%M:%S")


from translations import get_translation

class BackupDialog(ctk.CTkToplevel):
    """
    Dialog quản lý backup và restore.
    
    Features:
    - Tạo backup mới (manual)
    - Danh sách các backups hiện có
    - Chi tiết backup (size, ngày tạo, records count)
    - Restore từ backup đã chọn
    - Xóa backup
    """
    
    def __init__(
        self,
        parent,
        backup_service: BackupService,
        on_restore_callback: Optional[Callable] = None,
        lang: str = 'vi',
        get_t: Callable = None
    ):
        """
        Khởi tạo BackupDialog.
        
        Args:
            parent: Widget cha (main window)
            backup_service: BackupService instance
            on_restore_callback: Callback được gọi sau khi restore thành công
        """
        super().__init__(parent)
        
        self.transient(parent)
        self.parent = parent
        self.backup_service = backup_service
        self.on_restore_callback = on_restore_callback
        self.lang = lang
        self._t = get_t if get_t else (lambda key: get_translation(key, self.lang))
        
        # Window config
        self.title(self._t("dialog_backup_title"))
        self.geometry("900x600")
        self.minsize(800, 500)
        
        # Data
        self.backups: List[BackupMetadata] = []
        self.selected_backup: Optional[BackupMetadata] = None
        
        # Font settings (from parent if available)
        try:
            self.font_normal = parent.font_normal
            self.font_bold = parent.font_bold
        except AttributeError:
            self.font_normal = ctk.CTkFont(size=13)
            self.font_bold = ctk.CTkFont(size=13, weight="bold")
        
        self._setup_ui()
        self._load_backups()
        
        # Modal
        self.grab_set()
        self.focus_force()
    
    def _setup_ui(self):
        """Thiết lập giao diện."""
        # Main layout
        self.grid_columnconfigure(0, weight=2)  # List panel
        self.grid_columnconfigure(1, weight=1)  # Detail panel
        self.grid_rowconfigure(0, weight=1)
        
        # === LEFT PANEL: Backup List ===
        left_frame = ctk.CTkFrame(self)
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_rowconfigure(1, weight=1)
        
        # Header
        header_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            header_frame,
            text="📦 " + self._t("backup_list_header"),
            font=self.font_bold
        ).grid(row=0, column=0, sticky="w")
        
        # Filter buttons
        filter_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        filter_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="e")
        
        self.filter_var = ctk.StringVar(value="all")
        
        ctk.CTkRadioButton(
            filter_frame, text=self._t("filter_all"), variable=self.filter_var,
            value="all", command=self._on_filter_changed
        ).pack(side="left", padx=5)
        ctk.CTkRadioButton(
            filter_frame, text=self._t("filter_manual"), variable=self.filter_var,
            value="manual", command=self._on_filter_changed
        ).pack(side="left", padx=5)
        ctk.CTkRadioButton(
            filter_frame, text=self._t("filter_auto"), variable=self.filter_var,
            value="auto", command=self._on_filter_changed
        ).pack(side="left", padx=5)
        
        # Backup List (Treeview)
        list_frame = ctk.CTkFrame(left_frame)
        list_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        # Treeview for backup list
        columns = ("type", "created", "size", "records")
        self.backup_tree = ttk.Treeview(
            list_frame, 
            columns=columns, 
            show="headings",
            selectmode="browse"
        )
        
        # Configure columns
        self.backup_tree.heading("type", text=self._t("col_type"))
        self.backup_tree.heading("created", text=self._t("col_created"))
        self.backup_tree.heading("size", text=self._t("col_size"))
        self.backup_tree.heading("records", text=self._t("col_records"))
        
        self.backup_tree.column("type", width=80, anchor="center")
        self.backup_tree.column("created", width=150, anchor="center")
        self.backup_tree.column("size", width=80, anchor="center")
        self.backup_tree.column("records", width=60, anchor="center")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.backup_tree.yview)
        self.backup_tree.configure(yscrollcommand=scrollbar.set)
        
        self.backup_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Bind selection
        self.backup_tree.bind("<<TreeviewSelect>>", self._on_backup_selected)
        self.backup_tree.bind("<Double-1>", self._on_backup_double_click)
        
        # Action buttons
        btn_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        btn_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        self.btn_create = ctk.CTkButton(
            btn_frame,
            text="➕ " + self._t("btn_create_backup"),
            command=self._create_backup,
            font=self.font_normal,
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        self.btn_create.grid(row=0, column=0, padx=5, sticky="ew")
        
        self.btn_restore = ctk.CTkButton(
            btn_frame,
            text="♻️ " + self._t("btn_restore"),
            command=self._restore_backup,
            font=self.font_normal,
            fg_color="#4CAF50",
            hover_color="#388E3C",
            state="disabled"
        )
        self.btn_restore.grid(row=0, column=1, padx=5, sticky="ew")
        
        self.btn_delete = ctk.CTkButton(
            btn_frame,
            text="🗑️ " + self._t("btn_delete"),
            command=self._delete_backup,
            font=self.font_normal,
            fg_color="#D32F2F",
            hover_color="#B71C1C",
            state="disabled"
        )
        self.btn_delete.grid(row=0, column=2, padx=5, sticky="ew")
        
        # === RIGHT PANEL: Detail ===
        right_frame = ctk.CTkFrame(self)
        right_frame.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")
        right_frame.grid_columnconfigure(0, weight=1)
        
        # Detail header
        ctk.CTkLabel(
            right_frame,
            text="📋 " + self._t("backup_detail_header"),
            font=self.font_bold
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Detail content
        self.detail_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        self.detail_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.detail_frame.grid_columnconfigure(1, weight=1)
        
        # Labels for detail info
        self.detail_labels = {}
        detail_fields = [
            ("filename", self._t("detail_filename")),
            ("type", self._t("detail_type")),
            ("created", self._t("detail_created")),
            ("size", self._t("detail_size")),
            ("checksum", self._t("detail_checksum")),
            ("vehicles", self._t("detail_vehicles")),
            ("drivers", self._t("detail_drivers")),
            ("locations", self._t("detail_locations")),
            ("verified", self._t("detail_verified")),
        ]
        
        for i, (key, label) in enumerate(detail_fields):
            ctk.CTkLabel(
                self.detail_frame, 
                text=label,
                font=self.font_normal
            ).grid(row=i, column=0, padx=5, pady=3, sticky="w")
            
            value_label = ctk.CTkLabel(
                self.detail_frame, 
                text="-",
                font=self.font_normal
            )
            value_label.grid(row=i, column=1, padx=5, pady=3, sticky="w")
            self.detail_labels[key] = value_label
        
        # Verify button
        self.btn_verify = ctk.CTkButton(
            right_frame,
            text="✅ " + self._t("btn_verify"),
            command=self._verify_backup,
            font=self.font_normal,
            state="disabled"
        )
        self.btn_verify.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        
        # Export backup button
        self.btn_export = ctk.CTkButton(
            right_frame,
            text="📤 " + self._t("btn_export"),
            command=self._export_backup,
            font=self.font_normal,
            state="disabled"
        )
        self.btn_export.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        
        # Stats section
        stats_frame = ctk.CTkFrame(right_frame)
        stats_frame.grid(row=4, column=0, padx=10, pady=10, sticky="ew")
        stats_frame.grid_columnconfigure((0, 1), weight=1)
        
        ctk.CTkLabel(
            stats_frame,
            text="📊 " + self._t("stats_header"),
            font=self.font_bold
        ).grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        self.stats_labels = {}
        stats_fields = [
            ("total_backups", self._t("stats_total_backups")),
            ("manual_count", self._t("stats_manual_count")),
            ("auto_count", self._t("stats_auto_count")),
            ("total_size", self._t("stats_total_size")),
        ]
        
        for i, (key, label) in enumerate(stats_fields):
            ctk.CTkLabel(
                stats_frame, 
                text=label,
                font=self.font_normal
            ).grid(row=i+1, column=0, padx=5, pady=2, sticky="w")
            
            value_label = ctk.CTkLabel(
                stats_frame, 
                text="-",
                font=self.font_normal
            )
            value_label.grid(row=i+1, column=1, padx=5, pady=2, sticky="e")
            self.stats_labels[key] = value_label
    
    def _load_backups(self):
        """Load danh sách backups."""
        try:
            # Get filter
            filter_type = self.filter_var.get()
            
            if filter_type == "manual":
                self.backups = self.backup_service.list_backups(BackupType.MANUAL)
            elif filter_type == "auto":
                self.backups = self.backup_service.list_backups(BackupType.AUTO)
            else:
                self.backups = self.backup_service.list_backups()
            
            # Clear tree
            for item in self.backup_tree.get_children():
                self.backup_tree.delete(item)
            
            # Populate tree
            for backup in self.backups:
                type_text = self._t("type_manual") if backup.backup_type == BackupType.MANUAL else self._t("type_auto")
                records_count = backup.records_summary.get("vehicles", 0) if backup.records_summary else 0
                self.backup_tree.insert("", "end", iid=backup.backup_id, values=(
                    type_text,
                    format_datetime(backup.created_at),
                    format_file_size(backup.size_bytes),
                    records_count
                ))
            
            # Update stats
            self._update_stats()
            
        except Exception as e:
            logger.error(f"Error loading backups: {e}")
            messagebox.showerror(self._t("error_title"), self._t("error_load_backup").format(error=e), parent=self)
    
    def _update_stats(self):
        """Cập nhật thống kê."""
        try:
            stats = self.backup_service.get_backup_stats()
            
            self.stats_labels["total_backups"].configure(text=str(stats["total_backups"]))
            self.stats_labels["manual_count"].configure(text=str(stats["manual_count"]))
            self.stats_labels["auto_count"].configure(text=str(stats["auto_count"]))
            self.stats_labels["total_size"].configure(text=format_file_size(stats["total_size"]))
            
        except Exception as e:
            logger.error(f"Error updating stats: {e}")
    
    def _on_filter_changed(self):
        """Xử lý thay đổi filter."""
        self._load_backups()
        self._clear_detail()
    
    def _on_backup_selected(self, event):
        """Xử lý khi chọn backup trong list."""
        selection = self.backup_tree.selection()
        if not selection:
            self.selected_backup = None
            self._clear_detail()
            return
        
        backup_id = selection[0]
        self.selected_backup = next(
            (b for b in self.backups if b.backup_id == backup_id), None
        )
        
        if self.selected_backup:
            self._show_detail()
            self.btn_restore.configure(state="normal")
            self.btn_delete.configure(state="normal")
            self.btn_verify.configure(state="normal")
            self.btn_export.configure(state="normal")
    
    def _on_backup_double_click(self, event):
        """Xử lý double click - hiện verify."""
        if self.selected_backup:
            self._verify_backup()
    
    def _show_detail(self):
        """Hiển thị chi tiết backup được chọn."""
        if not self.selected_backup:
            return
        
        b = self.selected_backup
        
        self.detail_labels["filename"].configure(text=b.filename)
        type_text = self._t("type_manual") if b.backup_type == BackupType.MANUAL else self._t("type_auto")
        self.detail_labels["type"].configure(text=type_text)
        self.detail_labels["created"].configure(text=format_datetime(b.created_at))
        self.detail_labels["size"].configure(text=format_file_size(b.size_bytes))
        self.detail_labels["checksum"].configure(text=b.checksum[:16] + "..." if b.checksum else "-")
        
        if b.records_summary:
            self.detail_labels["vehicles"].configure(text=str(b.records_summary.get("vehicles", 0)))
            self.detail_labels["drivers"].configure(text=str(b.records_summary.get("drivers", 0)))
            self.detail_labels["locations"].configure(text=str(b.records_summary.get("locations", 0)))
        else:
            self.detail_labels["vehicles"].configure(text="-")
            self.detail_labels["drivers"].configure(text="-")
            self.detail_labels["locations"].configure(text="-")
        
        self.detail_labels["verified"].configure(text=self._t("not_verified"), text_color="gray")
    
    def _clear_detail(self):
        """Xóa chi tiết."""
        for label in self.detail_labels.values():
            label.configure(text="-")
        
        self.btn_restore.configure(state="disabled")
        self.btn_delete.configure(state="disabled")
        self.btn_verify.configure(state="disabled")
        self.btn_export.configure(state="disabled")
    
    def _create_backup(self):
        """Tạo backup mới."""
        try:
            # Confirm
            if not messagebox.askyesno(
                "Xác nhận",
                "Bạn có muốn tạo bản sao lưu mới không?",
                parent=self
            ):
                return
            
            # Create backup
            self.btn_create.configure(state="disabled", text=self._t("creating_backup"))
            self.update()
            
            metadata = self.backup_service.create_backup(
                backup_type=BackupType.MANUAL,
                description="Manual backup from UI"
            )
            
            # Log audit
            log_backup(
                backup_id=metadata.backup_id,
                backup_type="manual",
                filepath=metadata.filepath,
            )
            
            # Success
            messagebox.showinfo(
                self._t("success_title"),
                self._t("success_create_backup").format(filename=metadata.filename, size=format_file_size(metadata.size_bytes)),
                parent=self
            )
            
            # Reload list
            self._load_backups()
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            messagebox.showerror(self._t("error_title"), self._t("error_create_backup").format(error=e), parent=self)
        finally:
            self.btn_create.configure(state="normal", text="➕ " + self._t("btn_create_backup"))
    
    def _restore_backup(self):
        """Phục hồi từ backup."""
        if not self.selected_backup:
            return
        
        try:
            # Warning
            result = messagebox.askyesnocancel(
                self._t("warning_title"),
                self._t("confirm_restore_backup").format(
                    filename=self.selected_backup.filename,
                    created=format_datetime(self.selected_backup.created_at)
                ),
                parent=self
            )
            
            if result is None or result is False:
                return
            
            # Restore
            self.btn_restore.configure(state="disabled", text=self._t("restoring_backup"))
            self.update()
            
            pre_restore_backup = self.backup_service.restore_backup(
                self.selected_backup.backup_id,
                create_pre_restore_backup=True
            )
            
            # Log audit
            log_restore(
                backup_id=self.selected_backup.backup_id,
                filepath=self.selected_backup.filepath,
            )
            
            # Success
            pre_restore_info = ""
            if pre_restore_backup:
                pre_restore_info = f"\n\nBản sao lưu trước phục hồi: {pre_restore_backup.filename}"
            
            messagebox.showinfo(
                self._t("success_title"),
                self._t("success_restore_backup").format(pre_restore_info=pre_restore_info),
                parent=self
            )
            
            # Callback
            if self.on_restore_callback:
                self.on_restore_callback()
            
            # Reload
            self._load_backups()
            
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            messagebox.showerror(self._t("error_title"), self._t("error_restore_backup").format(error=e), parent=self)
        finally:
            self.btn_restore.configure(state="normal", text="♻️ " + self._t("btn_restore"))
    
    def _delete_backup(self):
        """Xóa backup."""
        if not self.selected_backup:
            return
        
        try:
            # Confirm
            if not messagebox.askyesno(
                self._t("confirm_delete_title"),
                self._t("confirm_delete_backup").format(
                    filename=self.selected_backup.filename,
                    created=format_datetime(self.selected_backup.created_at)
                ),
                parent=self
            ):
                return
            
            # Delete
            self.backup_service.delete_backup(self.selected_backup.backup_id)
            
            messagebox.showinfo(self._t("success_title"), self._t("success_delete_backup"), parent=self)
            
            self._load_backups()
            self._clear_detail()
            
        except Exception as e:
            logger.error(f"Error deleting backup: {e}")
            messagebox.showerror(self._t("error_title"), self._t("error_delete_backup").format(error=e), parent=self)
    
    def _verify_backup(self):
        """Kiểm tra tính toàn vẹn của backup."""
        if not self.selected_backup:
            return
        
        try:
            self.btn_verify.configure(state="disabled", text=self._t("verifying_backup"))
            self.update()
            
            result = self.backup_service.verify_backup(self.selected_backup.backup_id)
            
            if result["is_valid"]:
                self.detail_labels["verified"].configure(
                    text=self._t("valid_backup"),
                    text_color="green"
                )
                messagebox.showinfo(
                    self._t("verify_result_title"),
                    self._t("verify_success"),
                    parent=self
                )
            else:
                self.detail_labels["verified"].configure(
                    text=self._t("invalid_backup"),
                    text_color="red"
                )
                errors = "\n".join(f"• {e}" for e in result.get("errors", []))
                messagebox.showwarning(
                    self._t("verify_result_title"),
                    self._t("verify_failed").format(errors=errors),
                    parent=self
                )
                
        except Exception as e:
            logger.error(f"Error verifying backup: {e}")
            self.detail_labels["verified"].configure(
                text=self._t("verify_error"),
                text_color="red"
            )
            messagebox.showerror(self._t("error_title"), self._t("verify_error_msg").format(error=e), parent=self)
        finally:
            self.btn_verify.configure(state="normal", text="✅ " + self._t("btn_verify"))
    
    def _export_backup(self):
        """Xuất backup ra thư mục khác."""
        if not self.selected_backup:
            return
        
        try:
            # Ask for destination
            dest_dir = filedialog.askdirectory(
                title=self._t("select_export_dir"),
                parent=self
            )
            
            if not dest_dir:
                return
            
            # Copy file
            import shutil
            src_path = Path(self.selected_backup.filepath)
            dest_path = Path(dest_dir) / src_path.name
            
            if dest_path.exists():
                if not messagebox.askyesno(
                    self._t("file_exists_title"),
                    self._t("file_exists_msg").format(filename=dest_path.name),
                    parent=self
                ):
                    return
            
            shutil.copy2(src_path, dest_path)
            
            messagebox.showinfo(
                self._t("success_title"),
                self._t("success_export_backup").format(path=dest_path),
                parent=self
            )
            
        except Exception as e:
            logger.error(f"Error exporting backup: {e}")
            messagebox.showerror(self._t("error_title"), self._t("error_export_backup").format(error=e), parent=self)


def show_backup_dialog(parent, backup_service: BackupService, on_restore_callback=None):
    """
    Hiển thị backup dialog.
    
    Args:
        parent: Widget cha
        backup_service: BackupService instance
        on_restore_callback: Callback sau restore
    
    Returns:
        BackupDialog instance
    """
    return BackupDialog(parent, backup_service, on_restore_callback)
