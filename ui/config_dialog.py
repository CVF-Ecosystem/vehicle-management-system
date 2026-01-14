# ui/config_dialog.py
"""
Dialog cho phép xuất/nhập cấu hình ứng dụng.
- Xuất settings ra file JSON
- Nhập settings từ file JSON
- Reset về mặc định
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import json
import os
from datetime import datetime

class ConfigDialog(ctk.CTkToplevel):
    """Dialog quản lý cấu hình (export/import)."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.app = parent
        self.transient(parent)
        
        self.title(self.app.get_translation("config_dialog_title"))
        self.geometry("550x550")
        self.resizable(True, True)
        
        self._build_ui()
        self.grab_set()
        self.center_window()
    
    def center_window(self):
        """Căn giữa cửa sổ."""
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")
    
    def _build_ui(self):
        """Xây dựng giao diện."""
        # Header
        header = ctk.CTkLabel(
            self,
            text="⚙️ " + self.app.get_translation("config_dialog_title"),
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header.pack(pady=(20, 15))
        
        # Description
        desc = ctk.CTkLabel(
            self,
            text=self.app.get_translation("config_description"),
            wraplength=380,
            justify="center"
        )
        desc.pack(pady=(0, 20))
        
        # Current config info
        info_frame = ctk.CTkFrame(self)
        info_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(
            info_frame,
            text=self.app.get_translation("config_current_settings"),
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        # Display current settings
        current_lang = self.app.current_lang.get()
        current_theme = self.app.current_theme.get()
        
        settings_text = f"""• {self.app.get_translation("menu_language")}: {current_lang.upper()}
• {self.app.get_translation("menu_theme")}: {current_theme}"""
        
        ctk.CTkLabel(
            info_frame,
            text=settings_text,
            justify="left"
        ).pack(anchor="w", padx=25, pady=(0, 10))
        
        # Action buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=20)
        
        # Export button
        export_btn = ctk.CTkButton(
            btn_frame,
            text="📤 " + self.app.get_translation("config_btn_export"),
            command=self._export_config,
            width=180,
            height=40,
            fg_color="#3498db"
        )
        export_btn.pack(pady=8)
        
        # Import button
        import_btn = ctk.CTkButton(
            btn_frame,
            text="📥 " + self.app.get_translation("config_btn_import"),
            command=self._import_config,
            width=180,
            height=40,
            fg_color="#2ecc71"
        )
        import_btn.pack(pady=8)
        
        # Reset button
        reset_btn = ctk.CTkButton(
            btn_frame,
            text="🔄 " + self.app.get_translation("config_btn_reset"),
            command=self._reset_config,
            width=180,
            height=40,
            fg_color="#e74c3c"
        )
        reset_btn.pack(pady=8)
        
        # Close button
        ctk.CTkButton(
            self,
            text=self.app.get_translation("btn_close"),
            command=self.destroy,
            width=100,
            fg_color="gray"
        ).pack(pady=15)
    
    def _get_config_data(self):
        """Thu thập cấu hình hiện tại."""
        return {
            "app_version": "5.2.0",
            "export_date": datetime.now().isoformat(),
            "settings": {
                "language": self.app.current_lang.get(),
                "theme": self.app.current_theme.get(),
            },
            "notification_settings": self._get_notification_settings(),
        }
    
    def _get_notification_settings(self):
        """Lấy cài đặt thông báo."""
        try:
            if hasattr(self.app, 'notification_service'):
                settings = self.app.notification_service.get_settings()
                return {
                    "enabled": settings.get("enabled", True),
                    "long_stock_days": settings.get("long_stock_days", 30),
                }
        except:
            pass
        return {"enabled": True, "long_stock_days": 30}
    
    def _export_config(self):
        """Xuất cấu hình ra file JSON."""
        default_name = f"config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        file_path = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile=default_name,
            title=self.app.get_translation("config_export_title")
        )
        
        if not file_path:
            return
        
        try:
            config_data = self._get_config_data()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo(
                self.app.get_translation("success_title"),
                self.app.get_translation("config_export_success").format(path=file_path),
                parent=self
            )
        except Exception as e:
            messagebox.showerror(
                self.app.get_translation("error_title"),
                f"{self.app.get_translation('config_export_error')}: {e}",
                parent=self
            )
    
    def _import_config(self):
        """Nhập cấu hình từ file JSON."""
        file_path = filedialog.askopenfilename(
            parent=self,
            filetypes=[("JSON files", "*.json")],
            title=self.app.get_translation("config_import_title")
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Validate
            if "settings" not in config_data:
                raise ValueError("Invalid config file format")
            
            # Preview changes
            settings = config_data["settings"]
            preview = f"""
{self.app.get_translation("config_preview_changes")}:

• {self.app.get_translation("menu_language")}: {settings.get('language', 'vi').upper()}
• {self.app.get_translation("menu_theme")}: {settings.get('theme', 'System')}
"""
            
            if not messagebox.askyesno(
                self.app.get_translation("config_import_confirm_title"),
                preview + "\n" + self.app.get_translation("config_import_confirm"),
                parent=self
            ):
                return
            
            # Apply settings
            self._apply_settings(settings)
            
            # Apply notification settings if present
            if "notification_settings" in config_data:
                self._apply_notification_settings(config_data["notification_settings"])
            
            messagebox.showinfo(
                self.app.get_translation("success_title"),
                self.app.get_translation("config_import_success"),
                parent=self
            )
            
            self.destroy()
            
        except Exception as e:
            messagebox.showerror(
                self.app.get_translation("error_title"),
                f"{self.app.get_translation('config_import_error')}: {e}",
                parent=self
            )
    
    def _apply_settings(self, settings):
        """Áp dụng cài đặt."""
        # Language
        if "language" in settings:
            self.app.current_lang.set(settings["language"])
            self.app.config.set("Settings", "language", settings["language"])
        
        # Theme
        if "theme" in settings:
            self.app.current_theme.set(settings["theme"])
            ctk.set_appearance_mode(settings["theme"])
            self.app.config.set("Settings", "theme", settings["theme"])
        
        # Rebuild UI
        self.app._build_ui()
    
    def _apply_notification_settings(self, notif_settings):
        """Áp dụng cài đặt thông báo."""
        try:
            if hasattr(self.app, 'notification_service'):
                self.app.notification_service.update_settings(
                    enabled=notif_settings.get("enabled", True),
                    long_stock_days=notif_settings.get("long_stock_days", 30)
                )
        except:
            pass
    
    def _reset_config(self):
        """Reset về cấu hình mặc định."""
        if not messagebox.askyesno(
            self.app.get_translation("config_reset_confirm_title"),
            self.app.get_translation("config_reset_confirm"),
            parent=self
        ):
            return
        
        default_settings = {
            "language": "vi",
            "theme": "System"
        }
        
        self._apply_settings(default_settings)
        
        messagebox.showinfo(
            self.app.get_translation("success_title"),
            self.app.get_translation("config_reset_success"),
            parent=self
        )
        
        self.destroy()
