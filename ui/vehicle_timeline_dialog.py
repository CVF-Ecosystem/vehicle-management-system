# ui/vehicle_timeline_dialog.py
"""
Vehicle Timeline Dialog - Phase 3.1
Dialog hiển thị lịch sử hoạt động của xe (timeline).
"""
import customtkinter as ctk
from tkinter import ttk
from datetime import datetime
import json
import logging

from config import PAD_GENERAL, PAD_SMALL
from database.audit_repository import get_audit_repository

# Module-level fonts (to avoid dependency on app instance)
FONT_NORMAL = ("Segoe UI", 13)
FONT_BOLD = ("Segoe UI", 13, "bold")
FONT_SMALL = ("Segoe UI", 11)

# Translation keys for this dialog
TRANSLATIONS = {
    "dlg_timeline_title": {"vi": "Lịch sử xe - {vin}", "en": "Vehicle Timeline - {vin}"},
    "timeline_no_history": {"vi": "Không có lịch sử hoạt động", "en": "No activity history"},
    "timeline_action_ADD": {"vi": "Nhập bãi", "en": "Inbound"},
    "timeline_action_UPDATE": {"vi": "Cập nhật", "en": "Update"},
    "timeline_action_DELETE": {"vi": "Xóa mềm", "en": "Soft Delete"},
    "timeline_action_RESTORE": {"vi": "Khôi phục", "en": "Restore"},
    "timeline_action_HARD_DELETE": {"vi": "Xóa vĩnh viễn", "en": "Hard Delete"},
    "timeline_action_DISPATCH_ADD": {"vi": "Thêm vào phiếu xuất", "en": "Added to Dispatch"},
    "timeline_action_DISPATCH_COMPLETE": {"vi": "Xuất bãi (phiếu)", "en": "Dispatched (Slip)"},
    "timeline_action_EXPORT": {"vi": "Export dữ liệu", "en": "Data Export"},
    "timeline_action_IMPORT": {"vi": "Import dữ liệu", "en": "Data Import"},
    "timeline_action_OUT": {"vi": "Xuất bãi (lẻ)", "en": "Dispatched (Single)"},
    "timeline_action_LOCATION_CHANGE": {"vi": "Đổi vị trí", "en": "Location Change"},
    "timeline_action_unknown": {"vi": "Hoạt động khác", "en": "Other Activity"},
    "timeline_col_time": {"vi": "Thời gian", "en": "Time"},
    "timeline_col_action": {"vi": "Hoạt động", "en": "Activity"},
    "timeline_col_user": {"vi": "Người thực hiện", "en": "User"},
    "timeline_col_details": {"vi": "Chi tiết", "en": "Details"},
    "btn_close": {"vi": "Đóng", "en": "Close"},
    "btn_refresh": {"vi": "Làm mới", "en": "Refresh"},
    "timeline_loading": {"vi": "Đang tải...", "en": "Loading..."},
}

def get_text(key, lang, **kwargs):
    """Get translated text with optional formatting."""
    entry = TRANSLATIONS.get(key, {})
    text = entry.get(lang, entry.get("vi", key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return text


class VehicleTimelineDialog(ctk.CTkToplevel):
    """Dialog hiển thị lịch sử hoạt động của một xe."""
    
    def __init__(self, parent, vin, vehicle_manager, lang="vi"):
        super().__init__(parent)
        self.vin = vin
        self.vehicle_manager = vehicle_manager
        self.lang = lang
        
        self.title(get_text("dlg_timeline_title", lang, vin=vin))
        self.geometry("900x500")
        self.minsize(700, 400)
        
        # Center on parent
        self.transient(parent)
        self.grab_set()
        
        self._setup_ui()
        self._load_timeline()
        
        # Wait for dialog to close
        self.wait_window()
    
    def _setup_ui(self):
        """Setup UI components."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header frame
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=PAD_GENERAL, pady=(PAD_GENERAL, PAD_SMALL), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame, 
            text=f"📋 {get_text('dlg_timeline_title', self.lang, vin=self.vin)}", 
            font=FONT_BOLD
        )
        title_label.grid(row=0, column=0, sticky="w")
        
        self.btn_refresh = ctk.CTkButton(
            header_frame,
            text=get_text("btn_refresh", self.lang),
            font=FONT_SMALL,
            width=80,
            command=self._load_timeline
        )
        self.btn_refresh.grid(row=0, column=1, padx=PAD_SMALL)
        
        # Timeline treeview
        tree_frame = ctk.CTkFrame(self)
        tree_frame.grid(row=1, column=0, padx=PAD_GENERAL, pady=PAD_SMALL, sticky="nsew")
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)
        
        cols = ("time", "action", "user", "details")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        # Configure columns
        self.tree.column("time", width=150, anchor="center")
        self.tree.column("action", width=150, anchor="center")
        self.tree.column("user", width=120, anchor="center")
        self.tree.column("details", width=400)
        
        self.tree.heading("time", text=get_text("timeline_col_time", self.lang))
        self.tree.heading("action", text=get_text("timeline_col_action", self.lang))
        self.tree.heading("user", text=get_text("timeline_col_user", self.lang))
        self.tree.heading("details", text=get_text("timeline_col_details", self.lang))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Style treeview
        style = ttk.Style()
        style.configure("Treeview", rowheight=30, font=FONT_NORMAL)
        style.configure("Treeview.Heading", font=FONT_BOLD)
        
        # Tag colors for different actions
        self.tree.tag_configure("add", background="#E8F5E9")  # Green for inbound
        self.tree.tag_configure("out", background="#FFEBEE")  # Red for outbound
        self.tree.tag_configure("update", background="#FFF8E1")  # Yellow for update
        self.tree.tag_configure("delete", background="#FFCDD2")  # Darker red for delete
        self.tree.tag_configure("restore", background="#C8E6C9")  # Light green for restore
        
        # Button frame
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, padx=PAD_GENERAL, pady=PAD_GENERAL, sticky="e")
        
        self.btn_close = ctk.CTkButton(
            btn_frame,
            text=get_text("btn_close", self.lang),
            font=FONT_NORMAL,
            width=100,
            command=self.destroy
        )
        self.btn_close.pack(side="right")
        
        # Status label
        self.status_label = ctk.CTkLabel(
            btn_frame,
            text="",
            font=FONT_SMALL,
            text_color="gray"
        )
        self.status_label.pack(side="left", padx=PAD_GENERAL)
    
    def _get_action_display(self, action_str):
        """Get translated display name for action."""
        action_map = {
            "ADD": ("timeline_action_ADD", "add"),
            "UPDATE": ("timeline_action_UPDATE", "update"),
            "DELETE": ("timeline_action_DELETE", "delete"),
            "RESTORE": ("timeline_action_RESTORE", "restore"),
            "HARD_DELETE": ("timeline_action_HARD_DELETE", "delete"),
            "DISPATCH_ADD": ("timeline_action_DISPATCH_ADD", "update"),
            "DISPATCH_COMPLETE": ("timeline_action_DISPATCH_COMPLETE", "out"),
            "EXPORT": ("timeline_action_EXPORT", "update"),
            "IMPORT": ("timeline_action_IMPORT", "add"),
            "OUT": ("timeline_action_OUT", "out"),
            "LOCATION_CHANGE": ("timeline_action_LOCATION_CHANGE", "update"),
        }
        
        key, tag = action_map.get(action_str, ("timeline_action_unknown", ""))
        return get_text(key, self.lang), tag
    
    def _format_details(self, details_dict):
        """Format details dict to readable string."""
        if not details_dict:
            return ""
        
        # Simplify common fields for display
        parts = []
        if "owner" in details_dict:
            parts.append(f"Chủ hàng: {details_dict['owner']}")
        if "vehicle_type" in details_dict:
            parts.append(f"Loại xe: {details_dict['vehicle_type']}")
        if "location" in details_dict:
            parts.append(f"Vị trí: {details_dict['location']}")
        if "old_location" in details_dict and "new_location" in details_dict:
            parts.append(f"{details_dict['old_location']} → {details_dict['new_location']}")
        if "transport_vehicle" in details_dict:
            parts.append(f"Xe VC: {details_dict['transport_vehicle']}")
        if "driver_name" in details_dict:
            parts.append(f"Tài xế: {details_dict['driver_name']}")
        if "dispatch_id" in details_dict:
            parts.append(f"Phiếu #{details_dict['dispatch_id']}")
        if "reason" in details_dict:
            parts.append(f"Lý do: {details_dict['reason']}")
        if "delete_reason" in details_dict:
            parts.append(f"Lý do: {details_dict['delete_reason']}")
        
        if parts:
            return " | ".join(parts)
        
        # Fallback: show raw JSON (truncated)
        try:
            raw = json.dumps(details_dict, ensure_ascii=False)
            if len(raw) > 100:
                raw = raw[:97] + "..."
            return raw
        except Exception:
            return str(details_dict)[:100]
    
    def _load_timeline(self):
        """Load timeline data from audit logs."""
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.status_label.configure(text=get_text("timeline_loading", self.lang))
        self.update_idletasks()
        
        try:
            audit_repo = get_audit_repository()
            entries = audit_repo.get_for_record("vehicles", self.vin, limit=200)
            
            if not entries:
                self.status_label.configure(text=get_text("timeline_no_history", self.lang))
                return
            
            # Sort by timestamp descending (newest first)
            entries.sort(key=lambda e: e.timestamp, reverse=True)
            
            for entry in entries:
                # Format timestamp
                time_str = entry.timestamp.strftime("%d/%m/%Y %H:%M:%S") if entry.timestamp else ""
                
                # Get action display
                action_str = entry.action.value if hasattr(entry.action, 'value') else str(entry.action)
                action_display, tag = self._get_action_display(action_str)
                
                # Format details
                details_str = self._format_details(entry.details)
                
                # Username
                username = entry.username or "system"
                
                # Insert with tag for coloring
                self.tree.insert("", "end", values=(
                    time_str,
                    action_display,
                    username,
                    details_str
                ), tags=(tag,) if tag else ())
            
            self.status_label.configure(text=f"Tổng cộng {len(entries)} hoạt động")
            
        except Exception as e:
            logging.error(f"Error loading timeline: {e}")
            self.status_label.configure(text=f"Lỗi: {str(e)[:50]}")
