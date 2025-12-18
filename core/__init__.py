# core/__init__.py
"""
Business Logic Layer - Core Services

This module contains the core business logic services for the application.
Services handle complex business operations that span multiple repositories.
"""

from .backup_service import BackupService

__all__ = [
    'BackupService',
]
