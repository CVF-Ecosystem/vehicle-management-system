# ui/login_dialog.py
"""
Login Dialog - Phase 1C
Dialog đăng nhập khi khởi động ứng dụng.
"""

import customtkinter as ctk
from tkinter import messagebox
import logging

from auth.auth_manager import AuthManager
from config import APP_VERSION, APP_NAME, FONT_FAMILY, FONT_SIZE_NORMAL, FONT_SIZE_LARGE

logger = logging.getLogger(__name__)


class LoginDialog(ctk.CTkToplevel):
    """
    Dialog đăng nhập.
    """
    
    def __init__(self, parent, on_success_callback=None):
        super().__init__(parent)
        
        self.parent = parent
        self.on_success_callback = on_success_callback
        self.auth_manager = AuthManager.get_instance()
        self.login_successful = False
        
        self._setup_window()
        self._build_ui()
        
        # Focus on username entry
        self.after(100, lambda: self.username_entry.focus())
        
        # Bind Enter key
        self.bind('<Return>', lambda e: self._do_login())
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.after(10, self._center_on_parent)
    
    def _setup_window(self):
        """Cấu hình cửa sổ."""
        self.title("Đăng nhập")
        self.geometry("400x350")
        self.resizable(False, False)
        
        # Disable close button behavior
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
    
    def _center_on_parent(self):
        """Center dialog on parent window."""
        self.update_idletasks()
        
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_w = self.parent.winfo_width()
        parent_h = self.parent.winfo_height()
        
        dialog_w = self.winfo_width()
        dialog_h = self.winfo_height()
        
        x = parent_x + (parent_w - dialog_w) // 2
        y = parent_y + (parent_h - dialog_h) // 2
        
        self.geometry(f"+{x}+{y}")
    
    def _build_ui(self):
        """Xây dựng giao diện."""
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Logo/Title
        title_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 20))
        
        title_label = ctk.CTkLabel(
            title_frame,
            text=f"🚗 {APP_NAME}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_LARGE, weight="bold")
        )
        title_label.pack()
        
        version_label = ctk.CTkLabel(
            title_frame,
            text=f"Version {APP_VERSION}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color="gray"
        )
        version_label.pack()
        
        # Login form
        form_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        form_frame.pack(fill="x", pady=10)
        
        # Username
        username_label = ctk.CTkLabel(
            form_frame,
            text="Tên đăng nhập:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL)
        )
        username_label.pack(anchor="w", pady=(0, 5))
        
        self.username_entry = ctk.CTkEntry(
            form_frame,
            width=340,
            height=40,
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL),
            placeholder_text="Nhập tên đăng nhập..."
        )
        self.username_entry.pack(fill="x", pady=(0, 15))
        
        # Password
        password_label = ctk.CTkLabel(
            form_frame,
            text="Mật khẩu:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL)
        )
        password_label.pack(anchor="w", pady=(0, 5))
        
        self.password_entry = ctk.CTkEntry(
            form_frame,
            width=340,
            height=40,
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL),
            placeholder_text="Nhập mật khẩu...",
            show="●"
        )
        self.password_entry.pack(fill="x", pady=(0, 5))
        
        # Show password checkbox
        self.show_password_var = ctk.BooleanVar(value=False)
        show_password_cb = ctk.CTkCheckBox(
            form_frame,
            text="Hiển thị mật khẩu",
            variable=self.show_password_var,
            command=self._toggle_password_visibility,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12)
        )
        show_password_cb.pack(anchor="w", pady=(0, 20))
        
        # Error message label
        self.error_label = ctk.CTkLabel(
            form_frame,
            text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color="red"
        )
        self.error_label.pack(fill="x", pady=(0, 10))
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))
        
        self.login_button = ctk.CTkButton(
            button_frame,
            text="🔐 Đăng nhập",
            width=160,
            height=40,
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL, weight="bold"),
            command=self._do_login
        )
        self.login_button.pack(side="left", expand=True, padx=(0, 5))
        
        cancel_button = ctk.CTkButton(
            button_frame,
            text="❌ Thoát",
            width=160,
            height=40,
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL),
            fg_color="gray",
            hover_color="darkgray",
            command=self._on_cancel
        )
        cancel_button.pack(side="right", expand=True, padx=(5, 0))
        
        # Default credentials hint (for first time)
        hint_label = ctk.CTkLabel(
            main_frame,
            text="Lần đầu: admin / admin123",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, slant="italic"),
            text_color="gray"
        )
        hint_label.pack(side="bottom", pady=(10, 0))
    
    def _toggle_password_visibility(self):
        """Toggle hiển thị/ẩn mật khẩu."""
        if self.show_password_var.get():
            self.password_entry.configure(show="")
        else:
            self.password_entry.configure(show="●")
    
    def _do_login(self):
        """Thực hiện đăng nhập."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username:
            self._show_error("Vui lòng nhập tên đăng nhập")
            self.username_entry.focus()
            return
        
        if not password:
            self._show_error("Vui lòng nhập mật khẩu")
            self.password_entry.focus()
            return
        
        # Disable button during login
        self.login_button.configure(state="disabled", text="Đang đăng nhập...")
        self.update()
        
        # Attempt login
        result = self.auth_manager.login(username, password)
        
        # Re-enable button
        self.login_button.configure(state="normal", text="🔐 Đăng nhập")
        
        if result['success']:
            self.login_successful = True
            self.error_label.configure(text="")
            
            logger.info(f"Login successful: {username}")
            
            if self.on_success_callback:
                self.on_success_callback(result['user'])
            
            self.destroy()
        else:
            self._show_error(result['message'])
            self.password_entry.delete(0, 'end')
            self.password_entry.focus()
    
    def _show_error(self, message: str):
        """Hiển thị thông báo lỗi."""
        self.error_label.configure(text=message)
    
    def _on_cancel(self):
        """Xử lý khi nhấn Cancel hoặc đóng cửa sổ."""
        if not self.login_successful:
            if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn thoát?"):
                self.parent.destroy()  # Close main app
        else:
            self.destroy()


class ChangePasswordDialog(ctk.CTkToplevel):
    """
    Dialog đổi mật khẩu.
    """
    
    def __init__(self, parent, user_id: int = None, username: str = None):
        super().__init__(parent)
        
        self.parent = parent
        self.auth_manager = AuthManager.get_instance()
        
        # Nếu không truyền user_id, đổi mật khẩu cho current user
        if user_id is None:
            current = self.auth_manager.get_current_user()
            if current:
                user_id = current['id']
                username = current['username']
        
        self.user_id = user_id
        self.username = username
        
        self._setup_window()
        self._build_ui()
        
        self.transient(parent)
        self.grab_set()
    
    def _setup_window(self):
        """Cấu hình cửa sổ."""
        title = f"Đổi mật khẩu - {self.username}" if self.username else "Đổi mật khẩu"
        self.title(title)
        self.geometry("400x300")
        self.resizable(False, False)
    
    def _build_ui(self):
        """Xây dựng giao diện."""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Current password (only if changing own password)
        current_user = self.auth_manager.get_current_user()
        self.need_current_password = (
            current_user and 
            current_user['id'] == self.user_id and 
            not self.auth_manager.is_admin()
        )
        
        if self.need_current_password:
            current_label = ctk.CTkLabel(
                main_frame,
                text="Mật khẩu hiện tại:",
                font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL)
            )
            current_label.pack(anchor="w", pady=(0, 5))
            
            self.current_password_entry = ctk.CTkEntry(
                main_frame,
                height=35,
                show="●"
            )
            self.current_password_entry.pack(fill="x", pady=(0, 15))
        
        # New password
        new_label = ctk.CTkLabel(
            main_frame,
            text="Mật khẩu mới:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL)
        )
        new_label.pack(anchor="w", pady=(0, 5))
        
        self.new_password_entry = ctk.CTkEntry(
            main_frame,
            height=35,
            show="●"
        )
        self.new_password_entry.pack(fill="x", pady=(0, 15))
        
        # Confirm password
        confirm_label = ctk.CTkLabel(
            main_frame,
            text="Xác nhận mật khẩu mới:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL)
        )
        confirm_label.pack(anchor="w", pady=(0, 5))
        
        self.confirm_password_entry = ctk.CTkEntry(
            main_frame,
            height=35,
            show="●"
        )
        self.confirm_password_entry.pack(fill="x", pady=(0, 15))
        
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
        
        save_button = ctk.CTkButton(
            button_frame,
            text="💾 Lưu",
            width=120,
            command=self._save_password
        )
        save_button.pack(side="left", expand=True, padx=(0, 5))
        
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Hủy",
            width=120,
            fg_color="gray",
            command=self.destroy
        )
        cancel_button.pack(side="right", expand=True, padx=(5, 0))
    
    def _save_password(self):
        """Lưu mật khẩu mới."""
        new_password = self.new_password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        
        # Validate
        if len(new_password) < 6:
            self.error_label.configure(text="Mật khẩu mới phải có ít nhất 6 ký tự")
            return
        
        if new_password != confirm_password:
            self.error_label.configure(text="Mật khẩu xác nhận không khớp")
            return
        
        # If need to verify current password
        if self.need_current_password:
            current_password = self.current_password_entry.get()
            # Verify current password by attempting login
            user_repo = self.auth_manager.get_user_repository()
            user = user_repo.get_user_by_username(self.username)
            if not user_repo._verify_password(current_password, user['password_hash']):
                self.error_label.configure(text="Mật khẩu hiện tại không đúng")
                return
        
        # Change password
        result = self.auth_manager.change_password(self.user_id, new_password)
        
        if result['success']:
            messagebox.showinfo("Thành công", "Đổi mật khẩu thành công!")
            self.destroy()
        else:
            self.error_label.configure(text=result['message'])
