# ui/login_dialog.py
"""
Login Dialog - Phase 1C
Dialog đăng nhập khi khởi động ứng dụng.
"""

import customtkinter as ctk
from tkinter import messagebox
import logging
import os
import json
import base64

from auth.auth_manager import AuthManager
from config import APP_VERSION, APP_NAME, FONT_FAMILY, FONT_SIZE_NORMAL, FONT_SIZE_LARGE
from translations import get_translation

logger = logging.getLogger(__name__)

# File lưu credentials (trong thư mục config)
CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", ".saved_credentials")


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
        self._load_saved_credentials()  # Load saved credentials if any
        self._resize_to_content()
        
        # Focus on password if username is filled, else username
        self.after(100, self._set_initial_focus)
        
        # Bind Enter key
        self.bind('<Return>', lambda e: self._do_login())
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.after(10, self._center_on_parent)
    
    def _set_initial_focus(self):
        """Đặt focus ban đầu: nếu đã có username thì focus vào password."""
        if self.username_entry.get().strip():
            self.password_entry.focus()
        else:
            self.username_entry.focus()

    def _resize_to_content(self):
        """Tự động điều chỉnh kích thước để không bị khuất nội dung."""
        self.update_idletasks()
        req_w = self.winfo_reqwidth() + 20  # small padding so content is not tight
        req_h = self.winfo_reqheight() + 20
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        dialog_w = min(max(req_w, 400), screen_w - 40)
        dialog_h = min(max(req_h, 420), screen_h - 80)
        self.geometry(f"{dialog_w}x{dialog_h}")
    
    def _setup_window(self):
        """Cấu hình cửa sổ."""
        self.title("Đăng nhập")
        self.resizable(False, False)
        
        # Disable close button behavior
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
    
    def _center_on_parent(self):
        """Center dialog on screen (parent may be withdrawn/hidden)."""
        self.update_idletasks()
        
        # Get screen dimensions
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        
        dialog_w = self.winfo_width()
        dialog_h = self.winfo_height()
        
        # Center on screen
        x = (screen_w - dialog_w) // 2
        y = (screen_h - dialog_h) // 2
        
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
        
        # Checkbox frame for both options
        checkbox_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        checkbox_frame.pack(fill="x", pady=(0, 15))
        
        # Show password checkbox
        self.show_password_var = ctk.BooleanVar(value=False)
        show_password_cb = ctk.CTkCheckBox(
            checkbox_frame,
            text="Hiển thị mật khẩu",
            variable=self.show_password_var,
            command=self._toggle_password_visibility,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12)
        )
        show_password_cb.pack(side="left", padx=(0, 20))
        
        # Remember password checkbox
        self.remember_password_var = ctk.BooleanVar(value=False)
        remember_password_cb = ctk.CTkCheckBox(
            checkbox_frame,
            text="Nhớ mật khẩu",
            variable=self.remember_password_var,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12)
        )
        remember_password_cb.pack(side="left")
        
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
            width=120,
            height=40,
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL, weight="bold"),
            command=self._do_login
        )
        self.login_button.pack(side="left", expand=True, padx=(0, 5))

        unlock_button = ctk.CTkButton(
            button_frame,
            text="🛡️ Mở khóa admin",
            width=120,
            height=40,
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL),
            fg_color="#f7c873",
            hover_color="#e6b800",
            command=self._show_unlock_admin_dialog
        )
        unlock_button.pack(side="left", expand=True, padx=(0, 5))

        cancel_button = ctk.CTkButton(
            button_frame,
            text="❌ Thoát",
            width=120,
            height=40,
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL),
            fg_color="gray",
            hover_color="darkgray",
            command=self._on_cancel
        )
        cancel_button.pack(side="right", expand=True, padx=(5, 0))

    def _show_unlock_admin_dialog(self):
        # Hiển thị dialog nhập mã bảo mật để mở khóa admin
        def do_unlock():
            code = code_entry.get().strip()
            # Mã bảo mật do IT quy định, ví dụ: "ADMIN-2025"
            SECRET_CODE = "ADMIN@2026"
            if code == SECRET_CODE:
                from database.user_repository import UserRepository
                user_repo = UserRepository()
                admin = user_repo.get_user_by_username("admin")
                if admin:
                    user_repo.change_password(admin['id'], "admin123")
                    user_repo._reset_failed_attempts(admin['id'])
                    user_repo.update_user(admin['id'], is_active=True)
                    messagebox.showinfo("Thành công", "Đã mở khóa và reset mật khẩu admin về mặc định (admin123)", parent=unlock_win)
                else:
                    messagebox.showerror("Lỗi", "Không tìm thấy tài khoản admin", parent=unlock_win)
                unlock_win.destroy()
            else:
                messagebox.showerror("Sai mã bảo mật", "Mã bảo mật không đúng! Vui lòng liên hệ IT.", parent=unlock_win)

        unlock_win = ctk.CTkToplevel(self)
        unlock_win.title("Mở khóa tài khoản admin")
        unlock_win.geometry("350x160")
        unlock_win.resizable(False, False)
        unlock_win.transient(self)
        unlock_win.grab_set()

        label = ctk.CTkLabel(unlock_win, text="Nhập mã bảo mật do IT cung cấp để mở khóa admin:", wraplength=320)
        label.pack(pady=(20, 10))
        code_entry = ctk.CTkEntry(unlock_win, width=220, font=ctk.CTkFont(size=14))
        code_entry.pack(pady=(0, 10))
        code_entry.focus()
        btn = ctk.CTkButton(unlock_win, text="Mở khóa", command=do_unlock)
        btn.pack(pady=(0, 10))
        

        # Default credentials hint (for first time) - chỉ để ở _build_ui, không để trong _show_unlock_admin_dialog
    
    def _load_saved_credentials(self):
        """Load credentials đã lưu nếu có."""
        try:
            if os.path.exists(CREDENTIALS_FILE):
                with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    username = data.get('username', '')
                    # Decode password from base64
                    encoded_pwd = data.get('password', '')
                    if encoded_pwd:
                        password = base64.b64decode(encoded_pwd.encode()).decode('utf-8')
                    else:
                        password = ''
                    
                    if username:
                        self.username_entry.insert(0, username)
                    if password:
                        self.password_entry.insert(0, password)
                        self.remember_password_var.set(True)
                        
                    logger.info(f"Đã load credentials cho user: {username}")
        except Exception as e:
            logger.warning(f"Không thể load saved credentials: {e}")
    
    def _save_credentials(self, username: str, password: str):
        """Lưu credentials vào file."""
        try:
            # Encode password to base64 (simple obfuscation, not secure encryption)
            encoded_pwd = base64.b64encode(password.encode('utf-8')).decode('utf-8')
            data = {
                'username': username,
                'password': encoded_pwd
            }
            with open(CREDENTIALS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            logger.info(f"Đã lưu credentials cho user: {username}")
        except Exception as e:
            logger.warning(f"Không thể lưu credentials: {e}")
    
    def _clear_saved_credentials(self):
        """Xóa credentials đã lưu."""
        try:
            if os.path.exists(CREDENTIALS_FILE):
                os.remove(CREDENTIALS_FILE)
                logger.info("Đã xóa saved credentials")
        except Exception as e:
            logger.warning(f"Không thể xóa saved credentials: {e}")
    
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
            
            # Save or clear credentials based on checkbox
            if self.remember_password_var.get():
                self._save_credentials(username, password)
            else:
                self._clear_saved_credentials()
            
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
        
        # Get app reference for translations
        self.app = parent.app if hasattr(parent, 'app') else parent
        
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
        
        # Center on parent window
        self.after(10, self._center_on_parent)
    
    def _t(self, key: str) -> str:
        """Helper để lấy translation."""
        if hasattr(self.app, 'get_translation'):
            return self.app.get_translation(key)
        # Fallback: use get_translation directly with app's language
        lang = getattr(self.app, 'current_language', 'vi') if self.app else 'vi'
        return get_translation(key, lang)
    
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
    
    def _setup_window(self):
        """Cấu hình cửa sổ."""
        title = f"{self._t('change_pwd_title')} - {self.username}" if self.username else self._t('change_pwd_title')
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
                text=self._t("change_pwd_current"),
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
            text=self._t("change_pwd_new"),
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
            text=self._t("change_pwd_confirm"),
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
            text=f"💾 {self._t('btn_save')}",
            width=120,
            command=self._save_password
        )
        save_button.pack(side="left", expand=True, padx=(0, 5))
        
        cancel_button = ctk.CTkButton(
            button_frame,
            text=self._t("btn_cancel"),
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
            self.error_label.configure(text=self._t("change_pwd_err_short"))
            return
        
        if new_password != confirm_password:
            self.error_label.configure(text=self._t("change_pwd_err_mismatch"))
            return
        
        # If need to verify current password
        if self.need_current_password:
            current_password = self.current_password_entry.get()
            # Verify current password by attempting login
            user_repo = self.auth_manager.get_user_repository()
            user = user_repo.get_user_by_username(self.username)
            if not user_repo._verify_password(current_password, user['password_hash']):
                self.error_label.configure(text=self._t("change_pwd_err_wrong_current"))
                return
        
        # Change password
        result = self.auth_manager.change_password(self.user_id, new_password)
        
        if result['success']:
            messagebox.showinfo(self._t("dialog_info_title"), self._t("change_pwd_success"))
            self.destroy()
        else:
            self.error_label.configure(text=result['message'])
