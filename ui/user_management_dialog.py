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

logger = logging.getLogger(__name__)


class UserManagementDialog(ctk.CTkToplevel):
    """
    Dialog quản lý người dùng - Admin only.
    """
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.parent = parent
        self.auth_manager = AuthManager.get_instance()
        
        # Check permission
        if not self.auth_manager.has_permission(Permission.USER_VIEW):
            messagebox.showerror("Lỗi", "Bạn không có quyền truy cập chức năng này!")
            self.destroy()
            return
        
        self._setup_window()
        self._build_ui()
        self._load_users()
        
        self.transient(parent)
        self.grab_set()
    
    def _setup_window(self):
        """Cấu hình cửa sổ."""
        self.title("Quản lý người dùng")
        self.geometry("900x600")
        self.minsize(800, 500)
    
    def _build_ui(self):
        """Xây dựng giao diện."""
        # Toolbar
        toolbar = ctk.CTkFrame(self)
        toolbar.pack(fill="x", padx=10, pady=10)
        
        # Add user button
        if self.auth_manager.has_permission(Permission.USER_CREATE):
            add_btn = ctk.CTkButton(
                toolbar,
                text="➕ Thêm người dùng",
                width=150,
                command=self._add_user
            )
            add_btn.pack(side="left", padx=(0, 10))
        
        # Refresh button
        refresh_btn = ctk.CTkButton(
            toolbar,
            text="🔄 Làm mới",
            width=100,
            fg_color="gray",
            command=self._load_users
        )
        refresh_btn.pack(side="left")
        
        # Search
        search_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        search_frame.pack(side="right")
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            width=200,
            placeholder_text="Tìm kiếm..."
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
            ("Tên đăng nhập", 120),
            ("Họ tên", 150),
            ("Vai trò", 100),
            ("Trạng thái", 80),
            ("Đăng nhập cuối", 150),
            ("Thao tác", 200)
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
        
        # Get users
        result = self.auth_manager.list_users(include_inactive=True)
        
        if result['success']:
            self.all_users = result['users']
            self._display_users(self.all_users)
        else:
            messagebox.showerror("Lỗi", result['message'])
    
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
            
            # Role
            role_text = get_role_display_name(user['role'])
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
            status_text = "✅ Hoạt động" if is_active else "❌ Vô hiệu"
            status_color = "green" if is_active else "red"
            
            ctk.CTkLabel(
                row_frame,
                text=status_text,
                width=80,
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
                last_login_text = "Chưa đăng nhập"
            
            ctk.CTkLabel(
                row_frame,
                text=last_login_text,
                width=150
            ).pack(side="left", padx=5)
            
            # Actions
            action_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            action_frame.pack(side="left", padx=5)
            
            # Edit button
            if self.auth_manager.has_permission(Permission.USER_EDIT):
                edit_btn = ctk.CTkButton(
                    action_frame,
                    text="✏️",
                    width=40,
                    command=lambda u=user: self._edit_user(u)
                )
                edit_btn.pack(side="left", padx=2)
            
            # Change password button
            if self.auth_manager.has_permission(Permission.USER_EDIT):
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
            if self.auth_manager.has_permission(Permission.USER_DELETE):
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
        action = "vô hiệu hóa" if is_active else "kích hoạt lại"
        
        if not messagebox.askyesno(
            "Xác nhận",
            f"Bạn có chắc muốn {action} tài khoản '{user['username']}'?"
        ):
            return
        
        new_status = not is_active
        result = self.auth_manager.update_user(
            user['id'],
            is_active=new_status
        )
        
        if result['success']:
            messagebox.showinfo("Thành công", f"Đã {action} tài khoản!")
            self._load_users()
        else:
            messagebox.showerror("Lỗi", result['message'])


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
        
        self._setup_window()
        self._build_ui()
        
        if self.is_edit:
            self._load_user_data()
        
        self.transient(parent)
        self.grab_set()
    
    def _setup_window(self):
        """Cấu hình cửa sổ."""
        title = "Sửa người dùng" if self.is_edit else "Thêm người dùng"
        self.title(title)
        self.geometry("450x400")
        self.resizable(False, False)
    
    def _build_ui(self):
        """Xây dựng giao diện."""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Username
        ctk.CTkLabel(
            main_frame,
            text="Tên đăng nhập: *",
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL)
        ).pack(anchor="w", pady=(0, 5))
        
        self.username_entry = ctk.CTkEntry(main_frame, height=35)
        self.username_entry.pack(fill="x", pady=(0, 15))
        
        if self.is_edit:
            self.username_entry.configure(state="disabled")
        
        # Full name
        ctk.CTkLabel(
            main_frame,
            text="Họ tên:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL)
        ).pack(anchor="w", pady=(0, 5))
        
        self.fullname_entry = ctk.CTkEntry(main_frame, height=35)
        self.fullname_entry.pack(fill="x", pady=(0, 15))
        
        # Password (only for new user)
        if not self.is_edit:
            ctk.CTkLabel(
                main_frame,
                text="Mật khẩu: *",
                font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL)
            ).pack(anchor="w", pady=(0, 5))
            
            self.password_entry = ctk.CTkEntry(main_frame, height=35, show="●")
            self.password_entry.pack(fill="x", pady=(0, 15))
        
        # Role
        ctk.CTkLabel(
            main_frame,
            text="Vai trò: *",
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL)
        ).pack(anchor="w", pady=(0, 5))
        
        self.role_var = ctk.StringVar(value=ROLE_OPERATOR)
        role_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        role_frame.pack(fill="x", pady=(0, 15))
        
        roles = [
            (ROLE_ADMIN, "👑 Admin - Toàn quyền"),
            (ROLE_OPERATOR, "👤 Operator - Vận hành"),
            (ROLE_VIEWER, "👁️ Viewer - Chỉ xem")
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
                text="Trạng thái:",
                font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL)
            ).pack(anchor="w", pady=(0, 5))
            
            self.active_var = ctk.BooleanVar(value=True)
            active_cb = ctk.CTkCheckBox(
                main_frame,
                text="Đang hoạt động",
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
            text="💾 Lưu",
            width=120,
            command=self._save
        )
        save_btn.pack(side="left", expand=True, padx=(0, 5))
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Hủy",
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
            self.error_label.configure(text="Vui lòng nhập tên đăng nhập")
            return
        
        if not self.is_edit:
            password = self.password_entry.get()
            if len(password) < 6:
                self.error_label.configure(text="Mật khẩu phải có ít nhất 6 ký tự")
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
            action = "cập nhật" if self.is_edit else "tạo"
            messagebox.showinfo("Thành công", f"Đã {action} người dùng!")
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
        
        self._setup_window()
        self._build_ui()
        self._load_history()
        
        self.transient(parent)
        self.grab_set()
    
    def _setup_window(self):
        """Cấu hình cửa sổ."""
        self.title("Lịch sử đăng nhập")
        self.geometry("800x500")
    
    def _build_ui(self):
        """Xây dựng giao diện."""
        # Header
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            header,
            text="📋 Lịch sử đăng nhập",
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_LARGE, weight="bold")
        ).pack(side="left")
        
        # Scrollable list
        self.history_frame = ctk.CTkScrollableFrame(self)
        self.history_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Header row
        header_row = ctk.CTkFrame(self.history_frame)
        header_row.pack(fill="x", pady=(0, 5))
        
        headers = [
            ("Thời gian", 150),
            ("Người dùng", 100),
            ("Hành động", 100),
            ("Kết quả", 80),
            ("Lý do lỗi", 200),
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
                'login': 'Đăng nhập',
                'logout': 'Đăng xuất',
                'password_change': 'Đổi MK'
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
