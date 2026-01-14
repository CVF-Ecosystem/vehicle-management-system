# core/notification_service.py
"""
Notification Service - Phase 2.6
Quản lý thông báo và cảnh báo trong ứng dụng.

Features:
- Alert xe tồn lâu trong bãi
- Cảnh báo bãi sắp đầy
- Thông báo hệ thống
- Notification queue với priority
- Auto-dismiss và manual dismiss
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
import uuid

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Loại thông báo."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class NotificationPriority(Enum):
    """Mức độ ưu tiên."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Notification:
    """Data class cho một thông báo."""
    id: str
    title: str
    message: str
    notification_type: NotificationType = NotificationType.INFO
    priority: NotificationPriority = NotificationPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    auto_dismiss: bool = True
    auto_dismiss_seconds: int = 5
    is_read: bool = False
    is_dismissed: bool = False
    action_callback: Optional[Callable] = None
    action_label: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "type": self.notification_type.value,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "auto_dismiss": self.auto_dismiss,
            "is_read": self.is_read,
            "is_dismissed": self.is_dismissed,
            "data": self.data,
        }


class NotificationService:
    """
    Singleton service quản lý thông báo.
    
    Usage:
        service = NotificationService.get_instance()
        service.add_notification("Title", "Message", NotificationType.WARNING)
        
        # Với callback action
        service.add_notification(
            "Xe tồn lâu", 
            "Có 5 xe tồn quá 30 ngày",
            action_callback=lambda: show_long_stock_vehicles(),
            action_label="Xem chi tiết"
        )
    """
    
    _instance = None
    _lock = Lock()
    
    # Configuration
    DEFAULT_LONG_STOCK_DAYS = 30
    DEFAULT_YARD_CAPACITY_THRESHOLD = 90  # percent
    CHECK_INTERVAL_MINUTES = 30
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._notifications: List[Notification] = []
        self._listeners: List[Callable[[Notification], None]] = []
        self._dismissed_ids: set = set()  # Track dismissed to prevent spam
        self._last_check: Optional[datetime] = None
        self._settings = {
            "long_stock_days": self.DEFAULT_LONG_STOCK_DAYS,
            "capacity_threshold": self.DEFAULT_YARD_CAPACITY_THRESHOLD,
            "enabled": True,
            "sound_enabled": False,
        }
        self._initialized = True
        logger.info("NotificationService initialized")
    
    @classmethod
    def get_instance(cls) -> 'NotificationService':
        """Lấy instance singleton."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """Reset instance (for testing)."""
        cls._instance = None
    
    # ==================== Settings ====================
    
    def get_settings(self) -> Dict[str, Any]:
        """Lấy cài đặt hiện tại."""
        return self._settings.copy()
    
    def update_settings(self, **kwargs):
        """Cập nhật cài đặt."""
        for key, value in kwargs.items():
            if key in self._settings:
                self._settings[key] = value
                logger.info(f"Notification setting updated: {key}={value}")
    
    def is_enabled(self) -> bool:
        """Kiểm tra notification có được bật không."""
        return self._settings.get("enabled", True)
    
    # ==================== Core Methods ====================
    
    def add_notification(
        self,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        auto_dismiss: bool = True,
        auto_dismiss_seconds: int = 5,
        expires_in_minutes: Optional[int] = None,
        action_callback: Optional[Callable] = None,
        action_label: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        unique_key: Optional[str] = None,
    ) -> Optional[Notification]:
        """
        Thêm một thông báo mới.
        
        Args:
            title: Tiêu đề thông báo
            message: Nội dung thông báo
            notification_type: Loại (info/warning/error/success)
            priority: Mức độ ưu tiên
            auto_dismiss: Tự động ẩn sau một thời gian
            auto_dismiss_seconds: Số giây trước khi ẩn
            expires_in_minutes: Thời gian hết hạn (phút)
            action_callback: Hàm callback khi click action
            action_label: Label cho nút action
            data: Dữ liệu bổ sung
            unique_key: Key duy nhất để tránh spam (nếu đã dismiss sẽ không show lại)
        
        Returns:
            Notification object hoặc None nếu bị filter
        """
        if not self.is_enabled():
            return None
        
        # Check unique_key to prevent spam
        if unique_key and unique_key in self._dismissed_ids:
            logger.debug(f"Notification with key '{unique_key}' was dismissed, skipping")
            return None
        
        notification_id = unique_key or str(uuid.uuid4())
        
        expires_at = None
        if expires_in_minutes:
            expires_at = datetime.now() + timedelta(minutes=expires_in_minutes)
        
        notification = Notification(
            id=notification_id,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            auto_dismiss=auto_dismiss,
            auto_dismiss_seconds=auto_dismiss_seconds,
            expires_at=expires_at,
            action_callback=action_callback,
            action_label=action_label,
            data=data or {},
        )
        
        self._notifications.append(notification)
        logger.info(f"Notification added: [{notification_type.value}] {title}")
        
        # Notify listeners
        self._notify_listeners(notification)
        
        return notification
    
    def add_info(self, title: str, message: str, **kwargs) -> Optional[Notification]:
        """Shortcut cho INFO notification."""
        return self.add_notification(title, message, NotificationType.INFO, **kwargs)
    
    def add_warning(self, title: str, message: str, **kwargs) -> Optional[Notification]:
        """Shortcut cho WARNING notification."""
        return self.add_notification(
            title, message, NotificationType.WARNING,
            priority=NotificationPriority.HIGH,
            auto_dismiss=False,
            **kwargs
        )
    
    def add_error(self, title: str, message: str, **kwargs) -> Optional[Notification]:
        """Shortcut cho ERROR notification."""
        return self.add_notification(
            title, message, NotificationType.ERROR,
            priority=NotificationPriority.CRITICAL,
            auto_dismiss=False,
            **kwargs
        )
    
    def add_success(self, title: str, message: str, **kwargs) -> Optional[Notification]:
        """Shortcut cho SUCCESS notification."""
        return self.add_notification(title, message, NotificationType.SUCCESS, **kwargs)
    
    # ==================== Query Methods ====================
    
    def get_all(self, include_dismissed: bool = False) -> List[Notification]:
        """Lấy tất cả notifications."""
        self._cleanup_expired()
        
        if include_dismissed:
            return list(self._notifications)
        return [n for n in self._notifications if not n.is_dismissed]
    
    def get_unread(self) -> List[Notification]:
        """Lấy notifications chưa đọc."""
        return [n for n in self.get_all() if not n.is_read]
    
    def get_by_type(self, notification_type: NotificationType) -> List[Notification]:
        """Lấy notifications theo loại."""
        return [n for n in self.get_all() if n.notification_type == notification_type]
    
    def get_by_priority(self, min_priority: NotificationPriority) -> List[Notification]:
        """Lấy notifications có priority >= min_priority."""
        return [n for n in self.get_all() if n.priority.value >= min_priority.value]
    
    def get_count(self) -> int:
        """Đếm số notifications chưa dismiss."""
        return len(self.get_all())
    
    def get_unread_count(self) -> int:
        """Đếm số notifications chưa đọc."""
        return len(self.get_unread())
    
    # ==================== Actions ====================
    
    def mark_as_read(self, notification_id: str):
        """Đánh dấu notification là đã đọc."""
        for n in self._notifications:
            if n.id == notification_id:
                n.is_read = True
                logger.debug(f"Notification marked as read: {notification_id}")
                break
    
    def mark_all_as_read(self):
        """Đánh dấu tất cả là đã đọc."""
        for n in self._notifications:
            n.is_read = True
    
    def dismiss(self, notification_id: str):
        """Dismiss một notification."""
        for n in self._notifications:
            if n.id == notification_id:
                n.is_dismissed = True
                self._dismissed_ids.add(notification_id)
                logger.debug(f"Notification dismissed: {notification_id}")
                break
    
    def dismiss_all(self):
        """Dismiss tất cả notifications."""
        for n in self._notifications:
            n.is_dismissed = True
            self._dismissed_ids.add(n.id)
    
    def clear_all(self):
        """Xóa toàn bộ notifications."""
        self._notifications.clear()
        logger.info("All notifications cleared")
    
    def reset_dismissed(self):
        """Reset danh sách dismissed (cho phép show lại)."""
        self._dismissed_ids.clear()
        logger.info("Dismissed notifications reset")
    
    # ==================== Listeners ====================
    
    def add_listener(self, callback: Callable[[Notification], None]):
        """Đăng ký listener để nhận notification mới."""
        if callback not in self._listeners:
            self._listeners.append(callback)
    
    def remove_listener(self, callback: Callable[[Notification], None]):
        """Hủy đăng ký listener."""
        if callback in self._listeners:
            self._listeners.remove(callback)
    
    def _notify_listeners(self, notification: Notification):
        """Gọi tất cả listeners."""
        for listener in self._listeners:
            try:
                listener(notification)
            except Exception as e:
                logger.error(f"Error in notification listener: {e}")
    
    # ==================== Business Logic Checks ====================
    
    def check_long_stock_vehicles(
        self, 
        vehicle_manager,
        days_threshold: Optional[int] = None
    ) -> Optional[Notification]:
        """
        Kiểm tra và cảnh báo xe tồn lâu trong bãi.
        
        Args:
            vehicle_manager: VehicleManager instance
            days_threshold: Số ngày coi là tồn lâu (mặc định từ settings)
        
        Returns:
            Notification nếu có xe tồn lâu, None nếu không
        """
        threshold = days_threshold or self._settings["long_stock_days"]
        
        try:
            # Query vehicles in stock over threshold days
            vehicles = vehicle_manager.get_in_stock()
            cutoff_date = datetime.now() - timedelta(days=threshold)
            
            long_stock = []
            for v in vehicles:
                date_in = v.get("date_in")
                if date_in:
                    if isinstance(date_in, str):
                        try:
                            date_in = datetime.fromisoformat(date_in)
                        except ValueError:
                            continue
                    if date_in < cutoff_date:
                        long_stock.append(v)
            
            if long_stock:
                unique_key = f"long_stock_{datetime.now().strftime('%Y%m%d')}"
                return self.add_warning(
                    title="⚠️ Xe tồn lâu trong bãi",
                    message=f"Có {len(long_stock)} xe tồn quá {threshold} ngày trong bãi.",
                    unique_key=unique_key,
                    data={"vehicles": [v.get("vin") for v in long_stock[:10]]},
                    action_label="Xem danh sách",
                )
            
        except Exception as e:
            logger.error(f"Error checking long stock vehicles: {e}")
        
        return None
    
    def check_yard_capacity(
        self, 
        location_manager,
        threshold_percent: Optional[int] = None
    ) -> Optional[Notification]:
        """
        Kiểm tra và cảnh báo bãi sắp đầy.
        
        Args:
            location_manager: LocationManager instance
            threshold_percent: Ngưỡng % để cảnh báo (mặc định từ settings)
        
        Returns:
            Notification nếu bãi sắp đầy, None nếu không
        """
        threshold = threshold_percent or self._settings["capacity_threshold"]
        
        try:
            # Get location statistics
            stats = location_manager.get_statistics()
            total = stats.get("total", 0)
            occupied = stats.get("occupied", 0)
            
            if total > 0:
                usage_percent = (occupied / total) * 100
                
                if usage_percent >= threshold:
                    unique_key = f"capacity_{datetime.now().strftime('%Y%m%d_%H')}"
                    
                    if usage_percent >= 95:
                        return self.add_error(
                            title="🚨 Bãi gần đầy!",
                            message=f"Bãi đã sử dụng {usage_percent:.1f}% ({occupied}/{total} vị trí).",
                            unique_key=unique_key,
                        )
                    else:
                        return self.add_warning(
                            title="⚠️ Bãi sắp đầy",
                            message=f"Bãi đã sử dụng {usage_percent:.1f}% ({occupied}/{total} vị trí).",
                            unique_key=unique_key,
                        )
        
        except Exception as e:
            logger.error(f"Error checking yard capacity: {e}")
        
        return None
    
    def run_all_checks(self, vehicle_manager=None, location_manager=None):
        """
        Chạy tất cả các kiểm tra tự động.
        
        Args:
            vehicle_manager: VehicleManager instance
            location_manager: LocationManager instance
        """
        now = datetime.now()
        
        # Throttle: chỉ check mỗi X phút
        if self._last_check:
            elapsed = (now - self._last_check).total_seconds() / 60
            if elapsed < self.CHECK_INTERVAL_MINUTES:
                return
        
        self._last_check = now
        logger.info("Running notification checks...")
        
        if vehicle_manager:
            self.check_long_stock_vehicles(vehicle_manager)
        
        if location_manager:
            self.check_yard_capacity(location_manager)
    
    # ==================== Cleanup ====================
    
    def _cleanup_expired(self):
        """Xóa notifications đã hết hạn."""
        now = datetime.now()
        expired = [n for n in self._notifications if n.expires_at and n.expires_at < now]
        
        for n in expired:
            n.is_dismissed = True
        
        # Remove very old notifications (> 24 hours)
        cutoff = now - timedelta(hours=24)
        self._notifications = [
            n for n in self._notifications 
            if n.created_at > cutoff or not n.is_dismissed
        ]


# ==================== Convenience Functions ====================

def get_notification_service() -> NotificationService:
    """Lấy notification service instance."""
    return NotificationService.get_instance()


def notify(
    title: str,
    message: str,
    notification_type: NotificationType = NotificationType.INFO,
    **kwargs
) -> Optional[Notification]:
    """Shortcut function để gửi notification."""
    return get_notification_service().add_notification(
        title, message, notification_type, **kwargs
    )


def notify_info(title: str, message: str, **kwargs) -> Optional[Notification]:
    """Shortcut cho INFO notification."""
    return get_notification_service().add_info(title, message, **kwargs)


def notify_warning(title: str, message: str, **kwargs) -> Optional[Notification]:
    """Shortcut cho WARNING notification."""
    return get_notification_service().add_warning(title, message, **kwargs)


def notify_error(title: str, message: str, **kwargs) -> Optional[Notification]:
    """Shortcut cho ERROR notification."""
    return get_notification_service().add_error(title, message, **kwargs)


def notify_success(title: str, message: str, **kwargs) -> Optional[Notification]:
    """Shortcut cho SUCCESS notification."""
    return get_notification_service().add_success(title, message, **kwargs)
