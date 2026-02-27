# ui/onboarding_dialog.py
"""
Onboarding wizard cho người dùng mới.
Hướng dẫn qua các tính năng chính của ứng dụng.
"""
import customtkinter as ctk
from PIL import Image
import os
import sys

class OnboardingDialog(ctk.CTkToplevel):
    """Dialog hướng dẫn người dùng mới."""
    
    def __init__(self, parent, on_complete_callback=None):
        super().__init__(parent)
        self.app = parent
        self.transient(parent)
        self.on_complete = on_complete_callback
        
        self.title(self.app.get_translation("onboarding_title"))
        self.geometry("800x600")
        self.resizable(True, True)
        
        self.current_step = 0
        self.steps = self._define_steps()
        
        self._build_ui()
        self.grab_set()
        self.center_window()
        
        self._show_step(0)
    
    def center_window(self):
        """Căn giữa cửa sổ."""
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")
    
    def _define_steps(self):
        """Định nghĩa các bước hướng dẫn."""
        return [
            {
                "icon": "🚗",
                "title_key": "onboarding_step1_title",
                "content_key": "onboarding_step1_content",
                "highlight": "tab_inbound"
            },
            {
                "icon": "📋",
                "title_key": "onboarding_step2_title",
                "content_key": "onboarding_step2_content",
                "highlight": "tab_dispatch"
            },
            {
                "icon": "📦",
                "title_key": "onboarding_step3_title",
                "content_key": "onboarding_step3_content",
                "highlight": "tab_stock"
            },
            {
                "icon": "🔍",
                "title_key": "onboarding_step4_title",
                "content_key": "onboarding_step4_content",
                "highlight": "tab_search"
            },
            {
                "icon": "🗺️",
                "title_key": "onboarding_step5_title",
                "content_key": "onboarding_step5_content",
                "highlight": "tab_yard_map"
            },
            {
                "icon": "📊",
                "title_key": "onboarding_step6_title",
                "content_key": "onboarding_step6_content",
                "highlight": "tab_dashboard"
            },
            {
                "icon": "⌨️",
                "title_key": "onboarding_step7_title",
                "content_key": "onboarding_step7_content",
                "highlight": None
            },
            {
                "icon": "✅",
                "title_key": "onboarding_final_title",
                "content_key": "onboarding_final_content",
                "highlight": None
            },
        ]
    
    def _build_ui(self):
        """Xây dựng giao diện."""
        # Progress bar at top
        self.progress_frame = ctk.CTkFrame(self, height=30)
        self.progress_frame.pack(fill="x", padx=20, pady=(15, 0))
        
        self.step_labels = []
        for i in range(len(self.steps)):
            lbl = ctk.CTkLabel(
                self.progress_frame,
                text=f"●",
                font=ctk.CTkFont(size=16),
                text_color="gray"
            )
            lbl.pack(side="left", expand=True)
            self.step_labels.append(lbl)
        
        # Main content area
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Icon
        self.icon_label = ctk.CTkLabel(
            self.content_frame,
            text="🚗",
            font=ctk.CTkFont(size=60)
        )
        self.icon_label.pack(pady=(30, 15))
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.content_frame,
            text="",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.title_label.pack(pady=(0, 15))
        
        # Content
        self.content_label = ctk.CTkLabel(
            self.content_frame,
            text="",
            font=ctk.CTkFont(size=14),
            wraplength=550,
            justify="center"
        )
        self.content_label.pack(pady=10, padx=20)
        
        # Step indicator
        self.step_indicator = ctk.CTkLabel(
            self.content_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.step_indicator.pack(pady=(20, 0))
        
        # Navigation buttons
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", padx=30, pady=15)
        
        # Skip button
        self.skip_btn = ctk.CTkButton(
            nav_frame,
            text=self.app.get_translation("onboarding_skip"),
            command=self._skip,
            width=100,
            fg_color="gray"
        )
        self.skip_btn.pack(side="left")
        
        # Next/Finish button
        self.next_btn = ctk.CTkButton(
            nav_frame,
            text=self.app.get_translation("onboarding_next"),
            command=self._next,
            width=120,
            fg_color="#3498db"
        )
        self.next_btn.pack(side="right")
        
        # Back button
        self.back_btn = ctk.CTkButton(
            nav_frame,
            text=self.app.get_translation("onboarding_back"),
            command=self._back,
            width=100,
            fg_color="transparent",
            border_width=1
        )
        self.back_btn.pack(side="right", padx=10)
        
        # Checkbox to not show again
        self.dont_show_var = ctk.BooleanVar(value=False)
        self.dont_show_check = ctk.CTkCheckBox(
            nav_frame,
            text=self.app.get_translation("onboarding_dont_show"),
            variable=self.dont_show_var
        )
        self.dont_show_check.pack(side="left", padx=20)
    
    def _show_step(self, step_index):
        """Hiển thị bước hướng dẫn."""
        if step_index < 0 or step_index >= len(self.steps):
            return
        
        self.current_step = step_index
        step = self.steps[step_index]
        
        # Update progress indicators
        for i, lbl in enumerate(self.step_labels):
            if i < step_index:
                lbl.configure(text_color="#2ecc71")  # Completed
            elif i == step_index:
                lbl.configure(text_color="#3498db")  # Current
            else:
                lbl.configure(text_color="gray")  # Future
        
        # Update content
        self.icon_label.configure(text=step["icon"])
        self.title_label.configure(text=self.app.get_translation(step["title_key"]))
        self.content_label.configure(text=self.app.get_translation(step["content_key"]))
        
        # Update step indicator
        self.step_indicator.configure(
            text=f"{self.app.get_translation('onboarding_step')} {step_index + 1}/{len(self.steps)}"
        )
        
        # Update buttons
        self.back_btn.configure(state="normal" if step_index > 0 else "disabled")
        
        if step_index == len(self.steps) - 1:
            self.next_btn.configure(
                text=self.app.get_translation("onboarding_finish"),
                fg_color="#2ecc71"
            )
            self.skip_btn.pack_forget()
        else:
            self.next_btn.configure(
                text=self.app.get_translation("onboarding_next"),
                fg_color="#3498db"
            )
            self.skip_btn.pack(side="left")
    
    def _next(self):
        """Đi đến bước tiếp theo."""
        if self.current_step < len(self.steps) - 1:
            self._show_step(self.current_step + 1)
        else:
            self._finish()
    
    def _back(self):
        """Quay lại bước trước."""
        if self.current_step > 0:
            self._show_step(self.current_step - 1)
    
    def _skip(self):
        """Bỏ qua hướng dẫn."""
        self._finish()
    
    def _finish(self):
        """Hoàn thành hướng dẫn."""
        # Save preference
        if self.dont_show_var.get():
            try:
                self.app.config.set("Settings", "show_onboarding", "false")
            except Exception:
                pass
        
        if self.on_complete:
            self.on_complete()
        
        self.destroy()


def should_show_onboarding(app):
    """Kiểm tra có nên hiển thị onboarding không."""
    try:
        show = app.config.get("Settings", "show_onboarding", fallback="true")
        return show.lower() == "true"
    except Exception:
        return True
