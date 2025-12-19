# auth/__init__.py
"""
Authentication and Authorization module - Phase 1C
"""

from auth.permissions import (
    ROLE_ADMIN, ROLE_OPERATOR, ROLE_VIEWER,
    Permission, has_permission, get_role_permissions
)
from auth.auth_manager import AuthManager, get_current_user, require_permission

__all__ = [
    'ROLE_ADMIN', 'ROLE_OPERATOR', 'ROLE_VIEWER',
    'Permission', 'has_permission', 'get_role_permissions',
    'AuthManager', 'get_current_user', 'require_permission'
]
