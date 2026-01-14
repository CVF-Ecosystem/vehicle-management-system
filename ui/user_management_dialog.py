# ui/user_management_dialog.py
"""
User Management Dialog - Phase 1C
Dialog quản lý người dùng (chỉ Admin).
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
import logging

from auth.auth_manager import AuthManager
from auth.permissions import Permission, ROLE_ADMIN, ROLE_OPERATOR, ROLE_VIEWER, get_role_display_name
from config import FONT_FAMILY, FONT_SIZE_NORMAL, FONT_SIZE_LARGE
from translations import get_translation

logger = logging.getLogger(__name__)


class UserManagementDialog(ctk.CTkToplevel):
    """
    Dialog quản lý người dùng - Admin only.
    """
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.parent = parent
        self.app = parent  # Reference to main app for translations
        self.auth_manager = AuthManager.get_instance()
        
        # Check permission
        if not self.auth_manager.has_permission(Permission.USER_VIEW):
            messagebox.showerror(
                self._t("dialog_error_title"),
                self._t("err_no_permission")
            )
            self.destroy()
            return
        
        self._setup_window()
        self._build_ui()
        self._load_users()
        
        self.transient(parent)
        self.grab_set()
    
    def _t(self, key: str) -> str:
        """Helper để lấy translation."""
        if hasattr(self.app, 'get_translation'):
            return self.app.get_translation(key)
        # Fallback: use get_translation directly with app's language
        lang = getattr(self.app, 'current_language', 'vi') if self.app else 'vi'
        return get_translation(key, lang)
    
    def _setup_window(self):
        """Cấu hình cửa sổ."""
        self.title(self._t("user_mgmt_title"))
        self.geometry("900x600")
        self.minsize(800, 500)
    
    def _build_ui(self):
        """Xây dựng giao diện."""
        # Toolbar
        toolbar = ctk.CTkFrame(self)
        toolbar.pack(fill="x", padx=10, pady=10)
        
        # Add user button
        if self.auth_manager.has_permission(Permission.USER_MANAGE):
            self.add_btn = ctk.CTkButton(
                toolbar,
                text=self._t("user_mgmt_add"),
                width=150,
                command=self._add_user
            )
            self.add_btn.pack(side="left", padx=(0, 10))
        
        # Refresh button
        self.refresh_btn = ctk.CTkButton(
            toolbar,
            text=self._t("btn_refresh"),
            width=100,
            fg_color="gray",
            command=self._load_users
        )
        self.refresh_btn.pack(side="left")
        
        # Search
        search_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        search_frame.pack(side="right")
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            width=200,
            placeholder_text=self._t("user_mgmt_search")
        )
        self.search_entry.pack(side="left", padx=(0, 5))
        self.search_entry.bind("<KeyRelease>", lambda e: self._filter_users())
        
        # User list container
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Header
        header_frame = ctk.CTkFrame(list_frame)
        header_frame.pack(fill="x", padx=5, pady=5)
        
        headers = [
            ("ID", 50),
            (self._t("user_mgmt_col_username"), 120),
            (self._t("user_mgmt_col_fullname"), 150),
            (self._t("user_mgmt_col_role"), 100),
            (self._t("user_mgmt_col_status"), 100),
            (self._t("user_mgmt_col_last_login"), 140),
            (self._t("user_mgmt_col_actions"), 160)
        ]
        
        for text, width in headers:
            ctk.CTkLabel(
                header_frame,
                text=text,
                width=width,
                font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL, weight="bold")
            ).pack(side="left", padx=5)
        
        # Scrollable user list
        self.user_list_frame = ctk.CTkScrollableFrame(list_frame)
        self.user_list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Store user rows
        self.user_rows = []
        self.all_users = []
    
    def _load_users(self):
        """Load danh sách người dùng."""
        # Clear existing rows
        for widget in self.user_list_frame.winfo_children():
            widget.destroy()
        self.user_rows = []
        
        # Get users - list_users returns a list directly, not a dict
        try:
            self.all_users = self.auth_manager.list_users(include_inactive=True)
            self._display_users(self.all_users)
        except Exception as e:
            logger.error(f"Error loading users: {e}")
            messagebox.showerror(self._t("dialog_error_title"), str(e))
    
    def _display_users(self, users):
        """Hiển thị danh sách người dùng."""
        for widget in self.user_list_frame.winfo_children():
            widget.destroy()
        
        current_user = self.auth_manager.get_current_user()
        
        for user in users:
            row_frame = ctk.CTkFrame(self.user_list_frame)
            row_frame.pack(fill="x", pady=2)
            
            # ID
            ctk.CTkLabel(
                row_frame,
                text=str(user['id']),
                width=50
            ).pack(side="left", padx=5)
            
            # Username
            ctk.CTkLabel(
                row_frame,
                text=user['username'],
                width=120
            ).pack(side="left", padx=5)
            
            # Full name
            ctk.CTkLabel(
                row_frame,
                text=user['full_name'] or "-",
                width=150
            ).pack(side="left", padx=5)
            
            # Role - use translations
            role_translation_key = {
                ROLE_ADMIN: "role_admin",
                ROLE_OPERATOR: "role_operator",
                ROLE_VIEWER: "role_viewer"
            }.get(user['role'], user['role'])
            role_text = self._t(role_translation_key)
            role_color = {
                ROLE_ADMIN: "#e74c3c",
                ROLE_OPERATOR: "#3498db",
                ROLE_VIEWER: "#95a5a6"
            }.get(user['role'], "gray")
            
            role_label = ctk.CTkLabel(
                row_frame,
                text=role_text,
                width=100,
                text_color=role_color,
                font=ctk.CTkFont(weight="bold")
            )
            role_label.pack(side="left", padx=5)
            
            # Status
            is_active = user.get('is_active', True)
            status_text = self._t("user_mgmt_status_active") if is_active else self._t("user_mgmt_status_inactive")
            status_color = "green" if is_active else "red"
            
            ctk.CTkLabel(
                row_frame,
                text=status_text,
                width=100,
                text_color=status_color
            ).pack(side="left", padx=5)
            
            # Last login
            last_login = user.get('last_login')
            if last_login:
                try:
                    dt = datetime.fromisoformat(last_login)
                    last_login_text = dt.strftime("%d/%m/%Y %H:%M")
                except:
                    last_login_text = last_login
            else:
                last_login_text = self._t("user_mgmt_never_logged_in")
            
            ctk.CTkLabel(
                row_frame,
                text=last_login_text,
                width=140
            ).pack(side="left", padx=5)
            
            # Actions
            action_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            action_frame.pack(side="left", padx=5)
            
            # Edit button
            if self.auth_manager.has_permission(Permission.USER_MANAGE):
                edit_btn = ctk.CTkButton(
                    action_frame,
                    text="✏️",
                    width=40,
                    command=lambda u=user: self._edit_user(u)
                )
                edit_btn.pack(side="left", padx=2)
            
            # Change password button
            if self.auth_manager.has_permission(Permission.USER_MANAGE):
                pwd_btn = ctk.CTkButton(
                    action_frame,
                    text="🔑",
                    width=40,
                    fg_color="#f39c12",
                    hover_color="#d68910",
                    command=lambda u=user: self._change_user_password(u)
                )
                pwd_btn.pack(side="left", padx=2)
            
            # Toggle active button
            if self.auth_manager.has_permission(Permission.USER_MANAGE):
                # Can't deactivate self
                if current_user and user['id'] != current_user['id']:
                    toggle_text = "🚫" if is_active else "✅"
                    toggle_color = "#e74c3c" if is_active else "#27ae60"
                    toggle_btn = ctk.CTkButton(
                        action_frame,
                        text=toggle_text,
                        width=40,
                        fg_color=toggle_color,
                        command=lambda u=user: self._toggle_user_active(u)
                    )
                    toggle_btn.pack(side="left", padx=2)
    
    def _filter_users(self):
        """Lọc danh sách theo từ khóa."""
        keyword = self.search_entry.get().lower().strip()
        
        if not keyword:
            self._display_users(self.all_users)
            return
        
        filtered = [
            u for u in self.all_users
            if keyword in u['username'].lower()
            or keyword in (u['full_name'] or "").lower()
            or keyword in u['role'].lower()
        ]
        
        self._display_users(filtered)
    
    def _add_user(self):
        """Mở dialog thêm người dùng."""
        dialog = UserEditDialog(self, user=None)
        self.wait_window(dialog)
        self._load_users()
    
    def _edit_user(self, user: dict):
        """Mở dialog sửa người dùng."""
        dialog = UserEditDialog(self, user=user)
        self.wait_window(dialog)
        self._load_users()
    
    def _change_user_password(self, user: dict):
        """Mở dialog đổi mật khẩu."""
        from ui.login_dialog import ChangePasswordDialog
        dialog = ChangePasswordDialog(self, user_id=user['id'], username=user['username'])
        self.wait_window(dialog)
    
    def _toggle_user_active(self, user: dict):
        """Bật/tắt trạng thái người dùng."""
        is_active = user.get('is_active', True)
        action_key = "user_mgmt_action_deactivate" if is_active else "user_mgmt_action_activate"
        
        confirm_msg = self._t("user_mgmt_confirm_toggle").format(
            action=self._t(action_key),
            username=user['username']
        )
        
        if not messagebox.askyesno(self._t("confirm_title"), confirm_msg):
            return
        
        new_status = not is_active
        result = self.auth_manager.update_user(
            user['id'],
            is_active=new_status
        )
        
        if result['success']:
            success_msg = self._t("user_mgmt_toggle_success").format(action=self._t(action_key))
            messagebox.showinfo(self._t("dialog_info_title"), success_msg)
            self._load_users()
        else:
            messagebox.showerror(self._t("dialog_error_title"), result['message'])


class UserEditDialog(ctk.CTkToplevel):
    """
    Dialog thêm/sửa người dùng.
    """
    
    def __init__(self, parent, user: dict = None):
        super().__init__(parent)
        
        self.parent = parent
        self.user = user
        self.auth_manager = AuthManager.get_instance()
        self.is_edit = user is not None
        
        # Get app reference for translations
        self.app = parent.app if hasattr(parent, 'app') else parent
        
        self._setup_window()
        self._build_ui()
        
        if self.is_edit:
            self._load_user_data()
        
        self.transient(parent)
        self.grab_set()
    
    def _t(self, key: str) -> str:
        """Helper để lấy translation."""
        if hasattr(self.app, 'get_translation'):
            return self.app.get_translation(key)
        # Fallback: use get_translation directly with app's language
        lang = getattr(self.app, 'current_language', 'vi') if self.app else 'vi'
        return get_translation(key, lang)
    
    def _setup_window(self):
        """Cấu hình cửa sổ."""
        title = self._t("user_edit_title") if self.is_edit else self._t("user_add_title")
        self.title(title)
        self.geometry("450x500")
        self.resizable(False, False)
    
    def _build_ui(self):
        """Xây dựng giao diện."""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Username
        ctk.CTkLabel(
            main_frame,
            text=self._t("user_edit_username") + " *",
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL)
        ).pack(anchor="w", pady=(0, 5))
        
        self.username_entry = ctk.CTkEntry(main_frame, height=35)
        self.username_entry.pack(fill="x", pady=(0, 15))
        
        if self.is_edit:
            self.username_entry.configure(state="disabled")
        
        # Full name
        ctk.CTkLabel(
            main_frame,
            text=self._t("user_edit_fullname"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL)
        ).pack(anchor="w", pady=(0, 5))
        
        self.fullname_entry = ctk.CTkEntry(main_frame, height=35)
        self.fullname_entry.pack(fill="x", pady=(0, 15))
        
        # Password (only for new user)
        if not self.is_edit:
            ctk.CTkLabel(
                main_frame,
                text=self._t("user_edit_password") + " *",
                font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL)
            ).pack(anchor="w", pady=(0, 5))
            
            self.password_entry = ctk.CTkEntry(main_frame, height=35, show="●")
            self.password_entry.pack(fill="x", pady=(0, 15))
        
        # Role
        ctk.CTkLabel(
            main_frame,
            text=self._t("user_edit_role") + " *",
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL)
        ).pack(anchor="w", pady=(0, 5))
        
        self.role_var = ctk.StringVar(value=ROLE_OPERATOR)
        role_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        role_frame.pack(fill="x", pady=(0, 15))
        
        roles = [
            (ROLE_ADMIN, self._t("role_admin_desc")),
            (ROLE_OPERATOR, self._t("role_operator_desc")),
            (ROLE_VIEWER, self._t("role_viewer_desc"))
        ]
        
        for role_value, role_text in roles:
            rb = ctk.CTkRadioButton(
                role_frame,
                text=role_text,
                variable=self.role_var,
                value=role_value
            )
            rb.pack(anchor="w", pady=2)
        
        # Active status (only for edit)
        if self.is_edit:
            ctk.CTkLabel(
                main_frame,
                text=self._t("user_edit_status"),
                font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL)
            ).pack(anchor="w", pady=(0, 5))
            
            self.active_var = ctk.BooleanVar(value=True)
            active_cb = ctk.CTkCheckBox(
                main_frame,
                text=self._t("user_edit_is_active"),
                variable=self.active_var
            )
            active_cb.pack(anchor="w", pady=(0, 15))
        
        # Error label
        self.error_label = ctk.CTkLabel(
            main_frame,
            text="",
            text_color="red"
        )
        self.error_label.pack(fill="x", pady=(0, 10))
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))
        
        save_btn = ctk.CTkButton(
            button_frame,
            text=self._t("btn_save"),
            width=120,
            command=self._save
        )
        save_btn.pack(side="left", expand=True, padx=(0, 5))
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text=self._t("btn_cancel"),
            width=120,
            fg_color="gray",
            command=self.destroy
        )
        cancel_btn.pack(side="right", expand=True, padx=(5, 0))
    
    def _load_user_data(self):
        """Load dữ liệu người dùng vào form."""
        if not self.user:
            return
        
        self.username_entry.insert(0, self.user['username'])
        self.fullname_entry.insert(0, self.user.get('full_name') or "")
        self.role_var.set(self.user['role'])
        
        if hasattr(self, 'active_var'):
            self.active_var.set(self.user.get('is_active', True))
    
    def _save(self):
        """Lưu thông tin người dùng."""
        username = self.username_entry.get().strip()
        full_name = self.fullname_entry.get().strip()
        role = self.role_var.get()
        
        # Validate
        if not username:
            self.error_label.configure(text=self._t("user_edit_err_no_username"))
            return
        
        if not self.is_edit:
            password = self.password_entry.get()
            if len(password) < 6:
                self.error_label.configure(text=self._t("user_edit_err_pwd_short"))
                return
        
        if self.is_edit:
            # Update
            result = self.auth_manager.update_user(
                self.user['id'],
                full_name=full_name or None,
                role=role,
                is_active=self.active_var.get()
            )
        else:
            # Create
            result = self.auth_manager.create_user(
                username=username,
                password=password,
                full_name=full_name or None,
                role=role
            )
        
        if result['success']:
            action_key = "user_edit_updated" if self.is_edit else "user_edit_created"
            messagebox.showinfo(self._t("dialog_info_title"), self._t(action_key))
            self.destroy()
        else:
            self.error_label.configure(text=result['message'])


class LoginHistoryDialog(ctk.CTkToplevel):
    """
    Dialog xem lịch sử đăng nhập.
    """
    
    def __init__(self, parent, user_id: int = None):
        super().__init__(parent)
        
        self.parent = parent
        self.user_id = user_id
        self.auth_manager = AuthManager.get_instance()
        
        # Get app reference for translations
        self.app = parent.app if hasattr(parent, 'app') else parent
        
        self._setup_window()
        self._build_ui()
        self._load_history()
        
        self.transient(parent)
        self.grab_set()
    
    def _t(self, key: str) -> str:
        """Helper để lấy translation."""
        if hasattr(self.app, 'get_translation'):
            return self.app.get_translation(key)
        # Fallback: use get_translation directly with app's language
        lang = getattr(self.app, 'current_language', 'vi') if self.app else 'vi'
        return get_translation(key, lang)
    
    def _setup_window(self):
        """Cấu hình cửa sổ."""
        self.title(self._t("login_history_title"))
        self.geometry("800x500")
    
    def _build_ui(self):
        """Xây dựng giao diện."""
        # Header
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            header,
            text="📋 " + self._t("login_history_title"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_LARGE, weight="bold")
        ).pack(side="left")
        
        # Scrollable list
        self.history_frame = ctk.CTkScrollableFrame(self)
        self.history_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Header row
        header_row = ctk.CTkFrame(self.history_frame)
        header_row.pack(fill="x", pady=(0, 5))
        
        headers = [
            (self._t("login_history_col_time"), 150),
            (self._t("login_history_col_user"), 100),
            (self._t("login_history_col_action"), 100),
            (self._t("login_history_col_result"), 80),
            (self._t("login_history_col_reason"), 200),
            ("IP", 120)
        ]
        
        for text, width in headers:
            ctk.CTkLabel(
                header_row,
                text=text,
                width=width,
                font=ctk.CTkFont(weight="bold")
            ).pack(side="left", padx=5)
    
    def _load_history(self):
        """Load lịch sử đăng nhập."""
        user_repo = self.auth_manager.get_user_repository()
        
        history = user_repo.get_login_history(
            user_id=self.user_id,
            limit=100
        )
        
        for record in history:
            row = ctk.CTkFrame(self.history_frame)
            row.pack(fill="x", pady=1)
            
            # Time
            created_at = record.get('created_at', '')
            try:
                dt = datetime.fromisoformat(created_at)
                time_text = dt.strftime("%d/%m/%Y %H:%M:%S")
            except:
                time_text = created_at
            
            ctk.CTkLabel(row, text=time_text, width=150).pack(side="left", padx=5)
            
            # Username
            ctk.CTkLabel(
                row, 
                text=record.get('username', '-'),
                width=100
            ).pack(side="left", padx=5)
            
            # Action
            action_map = {
                'login': self._t("login_history_action_login"),
                'logout': self._t("login_history_action_logout"),
                'password_change': self._t("login_history_action_pwd_change")
            }
            action = action_map.get(record.get('action'), record.get('action', '-'))
            ctk.CTkLabel(row, text=action, width=100).pack(side="left", padx=5)
            
            # Success
            success = record.get('success', False)
            success_text = "✅" if success else "❌"
            success_color = "green" if success else "red"
            ctk.CTkLabel(
                row,
                text=success_text,
                width=80,
                text_color=success_color
            ).pack(side="left", padx=5)
            
            # Failure reason
            reason = record.get('failure_reason') or "-"
            ctk.CTkLabel(row, text=reason, width=200).pack(side="left", padx=5)
            
            # IP
            ip = record.get('ip_address') or "-"
            ctk.CTkLabel(row, text=ip, width=120).pack(side="left", padx=5)
