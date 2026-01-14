# core/__init__.py
"""
Business Logic Layer - Core Services

This module contains the core business logic services for the application.
Services handle complex business operations that span multiple repositories.
"""

from .backup_service import BackupService
from .notification_service import (
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

__all__ = [
    'BackupService',
    # Notification
    'NotificationService',
    'NotificationType',
    'NotificationPriority',
    'Notification',
    'get_notification_service',
    'notify',
    'notify_info',
    'notify_warning',
    'notify_error',
    'notify_success',
]
