import customtkinter as ctk
from tkinter import ttk, messagebox
import logging
from typing import Optional, Callable, List
from datetime import datetime
from translations import get_translation
from core.notification_service import (
    NotificationService, 
    Notification, 
    NotificationType,
    NotificationPriority,
)



class NotificationSettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, notification_service: Optional[NotificationService] = None):
        super().__init__(parent)
        self.service = notification_service or NotificationService.get_instance()
        self.settings = self.service.get_settings()
        self.app = parent if hasattr(parent, 'get_translation') else None
        self.lang = self.app.current_lang.get() if self.app and hasattr(self.app, 'current_lang') else 'vi'
        self.title(get_translation("notification_settings_title", self.lang))
        self.geometry("400x300")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._build_ui()

    def _save(self):
        """Save notification settings."""
        try:
            enabled = self.enabled_var.get()
            long_stock_days = int(self.days_entry.get())
            capacity_threshold = int(self.capacity_entry.get())
            self.service.save_settings({
                "enabled": enabled,
                "long_stock_days": long_stock_days,
                "capacity_threshold": capacity_threshold
            })
            messagebox.showinfo(
                get_translation("success_title", self.lang),
                get_translation("notification_save_success", self.lang),
                parent=self
            )
            self.destroy()
        except Exception as e:
            messagebox.showerror(
                get_translation("error_title", self.lang),
                f"{e}",
                parent=self
            )

    def _build_ui(self):
        # Checkbox: Enable notifications
        self.enabled_var = ctk.BooleanVar(value=self.settings.get("enabled", True))
        enabled_checkbox = ctk.CTkCheckBox(
            self,
            text=get_translation("notification_enabled", self.lang),
            variable=self.enabled_var
        )
        enabled_checkbox.pack(pady=(20, 10), anchor="w", padx=30)

        # Entry: Long stock days
        days_label = ctk.CTkLabel(self, text=get_translation("notification_long_stock_days", self.lang))
        days_label.pack(anchor="w", padx=30)
        self.days_entry = ctk.CTkEntry(self)
        self.days_entry.insert(0, str(self.settings.get("long_stock_days", 30)))
        self.days_entry.pack(fill="x", padx=30, pady=(0, 10))

        # Entry: Capacity threshold
        capacity_label = ctk.CTkLabel(self, text=get_translation("notification_capacity_threshold", self.lang))
        capacity_label.pack(anchor="w", padx=30)
        self.capacity_entry = ctk.CTkEntry(self)
        self.capacity_entry.insert(0, str(self.settings.get("capacity_threshold", 80)))
        self.capacity_entry.pack(fill="x", padx=30, pady=(0, 20))

        # Save button
        save_btn = ctk.CTkButton(self, text=get_translation("save", self.lang), command=self._save)
        save_btn.pack(pady=(0, 20))

logger = logging.getLogger(__name__)


class NotificationToast(ctk.CTkFrame):
    """
    Widget hiển thị một notification dạng toast.
    """
    
    # Color scheme for different types
    COLORS = {
        NotificationType.INFO: {"bg": "#3498db", "fg": "white"},
        NotificationType.WARNING: {"bg": "#f39c12", "fg": "white"},
        NotificationType.ERROR: {"bg": "#e74c3c", "fg": "white"},
        NotificationType.SUCCESS: {"bg": "#27ae60", "fg": "white"},
    }
    
    ICONS = {
        NotificationType.INFO: "ℹ️",
        NotificationType.WARNING: "⚠️",
        NotificationType.ERROR: "❌",
        NotificationType.SUCCESS: "✅",
    }
    
    def __init__(
        self, 
        parent, 
        notification: Notification,
        on_dismiss: Optional[Callable[[str], None]] = None,
        on_action: Optional[Callable[[Notification], None]] = None,
        width: int = 320,
        **kwargs
    ):
        colors = self.COLORS.get(notification.notification_type, self.COLORS[NotificationType.INFO])
        
        super().__init__(
            parent, 
            fg_color=colors["bg"],
            corner_radius=8,
            **kwargs
        )
        
        self.notification = notification
        self.on_dismiss = on_dismiss
        self.on_action = on_action
        self._auto_dismiss_id = None
        
        self.configure(width=width)
        self._build_ui(colors)
        
        # Setup auto-dismiss
        if notification.auto_dismiss:
            self._schedule_auto_dismiss()
    
    def _build_ui(self, colors: dict):
        """Xây dựng UI của toast."""
        text_color = colors["fg"]
        icon = self.ICONS.get(self.notification.notification_type, "ℹ️")
        
        # Main container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Header row (icon + title + close button)
        header_frame = ctk.CTkFrame(container, fg_color="transparent")
        header_frame.pack(fill="x")
        
        # Icon + Title
        title_label = ctk.CTkLabel(
            header_frame,
            text=f"{icon} {self.notification.title}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=text_color,
            anchor="w",
        )
        title_label.pack(side="left", fill="x", expand=True)
        
        # Close button
        close_btn = ctk.CTkButton(
            header_frame,
            text="✕",
            width=24,
            height=24,
            fg_color="transparent",
            hover_color=self._darken_color(colors["bg"]),
            text_color=text_color,
            command=self._dismiss,
        )
        close_btn.pack(side="right")
        
        # Message
        message_label = ctk.CTkLabel(
            container,
            text=self.notification.message,
            font=ctk.CTkFont(size=12),
            text_color=text_color,
            anchor="w",
            justify="left",
            wraplength=280,
        )
        message_label.pack(fill="x", pady=(4, 0))
        
        # Action button (if any)
        if self.notification.action_label and self.notification.action_callback:
            action_btn = ctk.CTkButton(
                container,
                text=self.notification.action_label,
                height=28,
                fg_color="white",
                text_color=colors["bg"],
                hover_color="#f0f0f0",
                command=self._handle_action,
            )
            action_btn.pack(anchor="e", pady=(8, 0))
        
        # Timestamp
        time_str = self.notification.created_at.strftime("%H:%M")
        time_label = ctk.CTkLabel(
            container,
            text=time_str,
            font=ctk.CTkFont(size=10),
            text_color=self._lighten_color(text_color),
            anchor="e",
        )
        time_label.pack(fill="x", pady=(4, 0))
    
    def _darken_color(self, hex_color: str) -> str:
        """Làm tối màu một chút."""
        # Simple darkening - just return a darker shade
        return "#2c2c2c"
    
    def _lighten_color(self, color: str) -> str:
        """Làm sáng màu."""
        return "#e0e0e0"
    
    def _dismiss(self):
        """Dismiss notification này."""
        if self._auto_dismiss_id:
            self.after_cancel(self._auto_dismiss_id)
        
        if self.on_dismiss:
            self.on_dismiss(self.notification.id)
        
        self.destroy()
    
    def _handle_action(self):
        """Xử lý khi click action button."""
        if self.notification.action_callback:
            try:
                self.notification.action_callback()
            except Exception as e:
                logger.error(f"Error in notification action: {e}")
        
        if self.on_action:
            self.on_action(self.notification)
        
        self._dismiss()
    
    def _schedule_auto_dismiss(self):
        """Lên lịch tự động dismiss."""
        delay_ms = self.notification.auto_dismiss_seconds * 1000
        self._auto_dismiss_id = self.after(delay_ms, self._dismiss)


class NotificationPanel(ctk.CTkFrame):
    """
    Panel hiển thị danh sách notifications ở góc màn hình.
    """
    
    MAX_VISIBLE_TOASTS = 5
    TOAST_SPACING = 8
    
    def __init__(
        self, 
        parent,
        notification_service: Optional[NotificationService] = None,
        position: str = "bottom-right",  # top-right, top-left, bottom-right, bottom-left
        **kwargs
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self.service = notification_service or NotificationService.get_instance()
        self.position = position
        self._toasts: List[NotificationToast] = []
        
        # Register as listener
        self.service.add_listener(self._on_new_notification)
        
        self._build_ui()
    
    def _build_ui(self):
        """Xây dựng UI của panel."""
        # Container for toasts
        self.toast_container = ctk.CTkFrame(self, fg_color="transparent")
        self.toast_container.pack(fill="both", expand=True, padx=8, pady=8)
    
    def _on_new_notification(self, notification: Notification):
        """Callback khi có notification mới."""
        self._add_toast(notification)
    
    def _add_toast(self, notification: Notification):
        """Thêm một toast mới."""
        # Nếu panel đang bị ẩn thì hiện lại
        if not self.winfo_ismapped():
            try:
                self.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-40)
            except Exception:
                pass

        # Limit number of visible toasts
        while len(self._toasts) >= self.MAX_VISIBLE_TOASTS:
            oldest = self._toasts.pop(0)
            oldest.destroy()

        # Create new toast
        toast = NotificationToast(
            self.toast_container,
            notification,
            on_dismiss=self._on_toast_dismiss,
        )

        # Pack based on position
        if "top" in self.position:
            toast.pack(fill="x", pady=(0, self.TOAST_SPACING))
        else:
            toast.pack(fill="x", pady=(self.TOAST_SPACING, 0))

        self._toasts.append(toast)

        # Mark as read
        self.service.mark_as_read(notification.id)
    
    def _on_toast_dismiss(self, notification_id: str):
        """Callback khi toast bị dismiss."""
        self.service.dismiss(notification_id)
        # Remove from list
        self._toasts = [t for t in self._toasts if t.notification.id != notification_id]
        # Nếu không còn toast nào thì ẩn panel
        if not self._toasts:
            try:
                self.place_forget()
            except Exception:
                pass
    
    def show_existing_notifications(self, max_count: int = 3):
        """Hiển thị các notifications chưa đọc đang có."""
        unread = self.service.get_unread()[:max_count]
        for notification in unread:
            self._add_toast(notification)
    
    def clear_all(self):
        """Xóa tất cả toasts."""
        for toast in self._toasts:
            toast.destroy()
        self._toasts.clear()
        self.service.dismiss_all()
    
    def destroy(self):
        """Override destroy để cleanup."""
        self.service.remove_listener(self._on_new_notification)
        super().destroy()


class NotificationBell(ctk.CTkButton):
    """
    Widget icon chuông thông báo với badge số lượng.
    """
    
    def __init__(
        self,
        parent,
        notification_service: Optional[NotificationService] = None,
        on_click: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(
            parent,
            text="🔔",
            width=40,
            height=40,
            fg_color="transparent",
            hover_color="#e0e0e0",
            **kwargs
        )
        
        self.service = notification_service or NotificationService.get_instance()
        self.on_click_callback = on_click
        
        self.configure(command=self._handle_click)
        
        # Badge label
        self.badge_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="white",
            fg_color="#e74c3c",
            corner_radius=8,
            width=18,
            height=18,
        )
        
        # Update periodically
        self._update_badge()
        self._schedule_update()
    
    def _update_badge(self):
        """Cập nhật số trên badge."""
        count = self.service.get_unread_count()
        
        if count > 0:
            text = str(count) if count <= 99 else "99+"
            self.badge_label.configure(text=text)
            self.badge_label.place(relx=0.7, rely=0.1)
        else:
            self.badge_label.place_forget()
    
    def _schedule_update(self):
        """Lên lịch cập nhật badge."""
        self.after(5000, self._periodic_update)  # Every 5 seconds
    
    def _periodic_update(self):
        """Cập nhật định kỳ."""
        try:
            if self.winfo_exists():
                self._update_badge()
                self._schedule_update()
        except Exception:
            pass
    
    def _handle_click(self):
        """Xử lý khi click vào bell."""
        if self.on_click_callback:
            self.on_click_callback()
        self._update_badge()


