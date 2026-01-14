# tests/unit/test_notification_service.py
"""
Unit tests cho NotificationService - Phase 2.6
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from core.notification_service import (
    NotificationService,
    NotificationType,
    NotificationPriority,
    Notification,
    get_notification_service,
    notify,
    notify_info,
    notify_warning,
    notify_error,
    notify_success,
)


class TestNotificationService:
    """Tests for NotificationService class."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset singleton trước mỗi test."""
        NotificationService.reset_instance()
        self.service = NotificationService.get_instance()
        yield
        NotificationService.reset_instance()
    
    def test_singleton_pattern(self):
        """Test NotificationService là singleton."""
        service1 = NotificationService.get_instance()
        service2 = NotificationService.get_instance()
        assert service1 is service2
    
    def test_add_notification_basic(self):
        """Test thêm notification cơ bản."""
        notification = self.service.add_notification(
            title="Test Title",
            message="Test Message"
        )
        
        assert notification is not None
        assert notification.title == "Test Title"
        assert notification.message == "Test Message"
        assert notification.notification_type == NotificationType.INFO
        assert notification.priority == NotificationPriority.NORMAL
    
    def test_add_notification_with_type(self):
        """Test thêm notification với type khác nhau."""
        for ntype in NotificationType:
            self.service.clear_all()
            notification = self.service.add_notification(
                title=f"Test {ntype.value}",
                message="Message",
                notification_type=ntype
            )
            assert notification.notification_type == ntype
    
    def test_add_notification_with_priority(self):
        """Test thêm notification với priority khác nhau."""
        for priority in NotificationPriority:
            notification = self.service.add_notification(
                title=f"Test {priority.value}",
                message="Message",
                priority=priority
            )
            assert notification.priority == priority
    
    def test_get_all_notifications(self):
        """Test lấy tất cả notifications."""
        self.service.add_notification("Title 1", "Message 1")
        self.service.add_notification("Title 2", "Message 2")
        self.service.add_notification("Title 3", "Message 3")
        
        all_notifications = self.service.get_all()
        assert len(all_notifications) == 3
    
    def test_get_unread_notifications(self):
        """Test lấy notifications chưa đọc."""
        n1 = self.service.add_notification("Title 1", "Message 1")
        n2 = self.service.add_notification("Title 2", "Message 2")
        
        self.service.mark_as_read(n1.id)
        
        unread = self.service.get_unread()
        assert len(unread) == 1
        assert unread[0].id == n2.id
    
    def test_mark_as_read(self):
        """Test đánh dấu đã đọc."""
        notification = self.service.add_notification("Title", "Message")
        assert not notification.is_read
        
        self.service.mark_as_read(notification.id)
        assert notification.is_read
    
    def test_mark_all_as_read(self):
        """Test đánh dấu tất cả đã đọc."""
        self.service.add_notification("Title 1", "Message 1")
        self.service.add_notification("Title 2", "Message 2")
        
        self.service.mark_all_as_read()
        
        unread = self.service.get_unread()
        assert len(unread) == 0
    
    def test_dismiss_notification(self):
        """Test dismiss một notification."""
        notification = self.service.add_notification("Title", "Message")
        assert not notification.is_dismissed
        
        self.service.dismiss(notification.id)
        assert notification.is_dismissed
        
        # Không nên xuất hiện trong get_all() nữa
        assert len(self.service.get_all()) == 0
    
    def test_dismiss_all(self):
        """Test dismiss tất cả notifications."""
        self.service.add_notification("Title 1", "Message 1")
        self.service.add_notification("Title 2", "Message 2")
        
        self.service.dismiss_all()
        
        assert len(self.service.get_all()) == 0
    
    def test_clear_all(self):
        """Test xóa tất cả notifications."""
        self.service.add_notification("Title 1", "Message 1")
        self.service.add_notification("Title 2", "Message 2")
        
        self.service.clear_all()
        
        assert len(self.service.get_all(include_dismissed=True)) == 0
    
    def test_unique_key_prevents_spam(self):
        """Test unique_key ngăn spam notifications."""
        n1 = self.service.add_notification(
            "Title", "Message", unique_key="unique_1"
        )
        assert n1 is not None
        
        # Dismiss it
        self.service.dismiss(n1.id)
        
        # Try to add again with same key - should be None
        n2 = self.service.add_notification(
            "Title", "Message", unique_key="unique_1"
        )
        assert n2 is None
    
    def test_shortcut_functions(self):
        """Test shortcut functions."""
        info = self.service.add_info("Info", "Message")
        warning = self.service.add_warning("Warning", "Message")
        error = self.service.add_error("Error", "Message")
        success = self.service.add_success("Success", "Message")
        
        assert info.notification_type == NotificationType.INFO
        assert warning.notification_type == NotificationType.WARNING
        assert error.notification_type == NotificationType.ERROR
        assert success.notification_type == NotificationType.SUCCESS
    
    def test_listener_callback(self):
        """Test listener được gọi khi có notification mới."""
        callback_called = []
        
        def listener(notification):
            callback_called.append(notification)
        
        self.service.add_listener(listener)
        self.service.add_notification("Title", "Message")
        
        assert len(callback_called) == 1
        assert callback_called[0].title == "Title"
    
    def test_remove_listener(self):
        """Test remove listener."""
        callback_called = []
        
        def listener(notification):
            callback_called.append(notification)
        
        self.service.add_listener(listener)
        self.service.remove_listener(listener)
        self.service.add_notification("Title", "Message")
        
        assert len(callback_called) == 0
    
    def test_get_by_type(self):
        """Test filter notifications by type."""
        self.service.add_info("Info", "Message")
        self.service.add_warning("Warning", "Message")
        self.service.add_error("Error", "Message")
        
        warnings = self.service.get_by_type(NotificationType.WARNING)
        assert len(warnings) == 1
        assert warnings[0].notification_type == NotificationType.WARNING
    
    def test_get_by_priority(self):
        """Test filter notifications by priority."""
        self.service.add_notification("Low", "Message", priority=NotificationPriority.LOW)
        self.service.add_notification("Normal", "Message", priority=NotificationPriority.NORMAL)
        self.service.add_notification("High", "Message", priority=NotificationPriority.HIGH)
        
        high_priority = self.service.get_by_priority(NotificationPriority.HIGH)
        assert len(high_priority) == 1
    
    def test_settings(self):
        """Test get/update settings."""
        settings = self.service.get_settings()
        assert "enabled" in settings
        assert "long_stock_days" in settings
        assert "capacity_threshold" in settings
        
        self.service.update_settings(enabled=False, long_stock_days=60)
        
        new_settings = self.service.get_settings()
        assert new_settings["enabled"] == False
        assert new_settings["long_stock_days"] == 60
    
    def test_disabled_service(self):
        """Test không tạo notification khi service bị tắt."""
        self.service.update_settings(enabled=False)
        
        notification = self.service.add_notification("Title", "Message")
        assert notification is None
    
    def test_notification_to_dict(self):
        """Test serialize notification to dict."""
        notification = self.service.add_notification(
            "Title", "Message",
            notification_type=NotificationType.WARNING,
            priority=NotificationPriority.HIGH
        )
        
        data = notification.to_dict()
        assert data["title"] == "Title"
        assert data["message"] == "Message"
        assert data["type"] == "warning"
        assert data["priority"] == 3  # HIGH = 3


class TestNotificationBusinessLogic:
    """Tests for business logic checks."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset singleton trước mỗi test."""
        NotificationService.reset_instance()
        self.service = NotificationService.get_instance()
        yield
        NotificationService.reset_instance()
    
    def test_check_long_stock_vehicles(self):
        """Test kiểm tra xe tồn lâu."""
        # Mock vehicle manager
        mock_vm = MagicMock()
        
        # Create vehicles with old date_in
        old_date = (datetime.now() - timedelta(days=40)).isoformat()
        mock_vm.get_in_stock.return_value = [
            {"vin": "VIN001", "date_in": old_date},
            {"vin": "VIN002", "date_in": old_date},
        ]
        
        notification = self.service.check_long_stock_vehicles(mock_vm, days_threshold=30)
        
        assert notification is not None
        assert notification.notification_type == NotificationType.WARNING
        assert "2" in notification.message  # 2 vehicles
    
    def test_check_long_stock_vehicles_no_alert(self):
        """Test không cảnh báo nếu không có xe tồn lâu."""
        mock_vm = MagicMock()
        
        # All vehicles are recent
        recent_date = datetime.now().isoformat()
        mock_vm.get_in_stock.return_value = [
            {"vin": "VIN001", "date_in": recent_date},
        ]
        
        notification = self.service.check_long_stock_vehicles(mock_vm, days_threshold=30)
        
        assert notification is None
    
    def test_check_yard_capacity_warning(self):
        """Test cảnh báo bãi sắp đầy."""
        mock_lm = MagicMock()
        mock_lm.get_statistics.return_value = {
            "total": 100,
            "occupied": 92,
        }
        
        notification = self.service.check_yard_capacity(mock_lm, threshold_percent=90)
        
        assert notification is not None
        assert notification.notification_type == NotificationType.WARNING
    
    def test_check_yard_capacity_critical(self):
        """Test cảnh báo bãi gần đầy (critical)."""
        mock_lm = MagicMock()
        mock_lm.get_statistics.return_value = {
            "total": 100,
            "occupied": 98,
        }
        
        notification = self.service.check_yard_capacity(mock_lm, threshold_percent=90)
        
        assert notification is not None
        assert notification.notification_type == NotificationType.ERROR  # Critical
    
    def test_check_yard_capacity_no_alert(self):
        """Test không cảnh báo nếu bãi còn trống."""
        mock_lm = MagicMock()
        mock_lm.get_statistics.return_value = {
            "total": 100,
            "occupied": 50,
        }
        
        notification = self.service.check_yard_capacity(mock_lm, threshold_percent=90)
        
        assert notification is None


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset singleton trước mỗi test."""
        NotificationService.reset_instance()
        yield
        NotificationService.reset_instance()
    
    def test_get_notification_service(self):
        """Test get_notification_service function."""
        service = get_notification_service()
        assert isinstance(service, NotificationService)
    
    def test_notify_function(self):
        """Test notify function."""
        notification = notify("Title", "Message")
        assert notification is not None
        assert notification.title == "Title"
    
    def test_notify_info_function(self):
        """Test notify_info function."""
        notification = notify_info("Info", "Message")
        assert notification.notification_type == NotificationType.INFO
    
    def test_notify_warning_function(self):
        """Test notify_warning function."""
        notification = notify_warning("Warning", "Message")
        assert notification.notification_type == NotificationType.WARNING
    
    def test_notify_error_function(self):
        """Test notify_error function."""
        notification = notify_error("Error", "Message")
        assert notification.notification_type == NotificationType.ERROR
    
    def test_notify_success_function(self):
        """Test notify_success function."""
        notification = notify_success("Success", "Message")
        assert notification.notification_type == NotificationType.SUCCESS
