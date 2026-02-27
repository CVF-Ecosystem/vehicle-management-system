# auth/auth_manager.py
"""
Authentication Manager - Phase 1C
Singleton quản lý session và authentication state của ứng dụng.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from functools import wraps

from database.user_repository import UserRepository
from auth.permissions import Permission, has_permission, ROLE_ADMIN
import config

logger = logging.getLogger(__name__)


class AuthManager:
    """
    Singleton quản lý authentication state với session timeout.
    """
    _instance = None
    _current_user: Optional[Dict[str, Any]] = None
    _user_repository: Optional[UserRepository] = None
    _login_time: Optional[datetime] = None
    
    # Session timeout: 30 minutes idle
    SESSION_TIMEOUT_MINUTES = 30
    
    def __new__(cls, db_path: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: str = None):
        if self._initialized:
            return

        # Default to dedicated security DB (separate from vehicle DB)
        target_db = db_path if db_path is not None else getattr(config, "SECURITY_DB_FILE", None)
        self._user_repository = UserRepository(target_db)
        self._current_user = None
        self._login_time = None
        self._initialized = True
        logger.info("AuthManager initialized")
    
    @classmethod
    def get_instance(cls) -> 'AuthManager':
        """Lấy instance hiện tại của AuthManager."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """Reset instance (dùng cho testing)."""
        cls._instance = None
    
    # ==================== Authentication ====================
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Đăng nhập user với session timeout tracking.
        
        Args:
            username: Tên đăng nhập
            password: Mật khẩu
        
        Returns:
            dict: {"success": bool, "message": str, "user": dict or None}
        """
        result = self._user_repository.authenticate(username, password)
        
        if result['success']:
            self._current_user = result['user']
            self._login_time = datetime.now()
            logger.info(f"User '{username}' logged in (role: {self._current_user['role']})")
        
        return result
    
    def logout(self):
        """Đăng xuất user hiện tại."""
        if self._current_user:
            username = self._current_user['username']
            user_id = self._current_user['id']
            
            self._user_repository.log_logout(user_id, username)
            
            logger.info(f"User '{username}' logged out")
        
        # Always clear state, even if no current user
        self._current_user = None
        self._login_time = None
    
    def is_logged_in(self) -> bool:
        """Kiểm tra có user đang đăng nhập và session chưa timeout."""
        if self._current_user is None:
            return False
        
        # Check session timeout
        if self._is_session_expired():
            logger.warning(f"Session expired for user: {self._current_user['username']}")
            self.logout()
            return False
        
        return True
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Lấy thông tin user đang đăng nhập (auto logout nếu session timeout)."""
        if self._current_user and self._is_session_expired():
            logger.warning(f"Session expired for user: {self._current_user['username']}")
            self.logout()
            return None
        
        return self._current_user
    
    def get_current_user_id(self) -> Optional[int]:
        """Lấy ID của user đang đăng nhập."""
        if self._current_user:
            return self._current_user['id']
        return None
    
    def _is_session_expired(self) -> bool:
        """
        Kiểm tra session có hết hạn không (30 phút idle timeout).
        
        Returns:
            bool: True nếu session đã timeout
        """
        if self._login_time is None:
            return True
        
        elapsed = datetime.now() - self._login_time
        timeout = timedelta(minutes=self.SESSION_TIMEOUT_MINUTES)
        
        return elapsed > timeout
    
    def refresh_session(self):
        """
        Refresh session timeout (gọi khi user có hoạt động).
        Dùng cho các thao tác quan trọng để giữ session active.
        """
        if self._current_user:
            self._login_time = datetime.now()
            logger.debug(f"Session refreshed for user: {self._current_user['username']}")
    
    def get_session_time_remaining(self) -> Optional[int]:
        """
        Lấy thời gian còn lại của session (phút).
        
        Returns:
            int: Số phút còn lại, hoặc None nếu không có session
        """
        if not self._current_user or self._login_time is None:
            return None
        
        elapsed = datetime.now() - self._login_time
        timeout = timedelta(minutes=self.SESSION_TIMEOUT_MINUTES)
        remaining = timeout - elapsed
        
        if remaining.total_seconds() <= 0:
            return 0
        
        return int(remaining.total_seconds() // 60)
    
    def get_current_username(self) -> Optional[str]:
        """Lấy username của user đang đăng nhập."""
        if self._current_user:
            return self._current_user['username']
        return None
    
    def get_current_role(self) -> Optional[str]:
        """Lấy role của user đang đăng nhập."""
        if self._current_user:
            return self._current_user['role']
        return None
    
    # ==================== Authorization ====================
    
    def has_permission(self, permission: Permission) -> bool:
        """
        Kiểm tra user hiện tại có quyền cụ thể không.
        
        Args:
            permission: Quyền cần kiểm tra
        
        Returns:
            bool: True nếu có quyền
        """
        if not self._current_user:
            return False
        
        return has_permission(self._current_user['role'], permission)
    
    def is_admin(self) -> bool:
        """Kiểm tra user hiện tại có phải admin không."""
        if not self._current_user:
            return False
        return self._current_user['role'] == ROLE_ADMIN
    
    def check_permission(self, permission: Permission) -> Dict[str, Any]:
        """
        Kiểm tra quyền và trả về kết quả chi tiết.
        
        Returns:
            dict: {"allowed": bool, "message": str}
        """
        if not self._current_user:
            return {
                "allowed": False,
                "message": "Vui lòng đăng nhập để thực hiện thao tác này"
            }
        
        if self.has_permission(permission):
            return {"allowed": True, "message": "OK"}
        
        return {
            "allowed": False,
            "message": "Bạn không có quyền thực hiện thao tác này"
        }
    
    # ==================== User Management ====================
    
    def get_user_repository(self) -> UserRepository:
        """Lấy UserRepository để quản lý users."""
        return self._user_repository
    
    def create_user(self, **kwargs) -> Dict[str, Any]:
        """Tạo user mới (proxy to UserRepository)."""
        if not self.has_permission(Permission.USER_MANAGE):
            return {"success": False, "message": "Không có quyền tạo user", "user_id": None}
        
        # Set created_by to current user
        kwargs['created_by_id'] = self.get_current_user_id()
        return self._user_repository.create_user(**kwargs)
    
    def list_users(self, include_inactive: bool = False):
        """Liệt kê users."""
        if not self.has_permission(Permission.USER_VIEW):
            return []
        return self._user_repository.list_users(include_inactive)
    
    def update_user(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Cập nhật user."""
        if not self.has_permission(Permission.USER_MANAGE):
            return {"success": False, "message": "Không có quyền cập nhật user"}
        
        # Check if trying to change role
        if 'role' in kwargs and not self.has_permission(Permission.USER_CHANGE_ROLE):
            return {"success": False, "message": "Không có quyền đổi role"}
        
        return self._user_repository.update_user(user_id, **kwargs)
    
    def change_password(self, user_id: int, new_password: str) -> Dict[str, Any]:
        """Đổi mật khẩu user."""
        # User can change their own password, or admin can change anyone's
        if self.get_current_user_id() != user_id and not self.is_admin():
            return {"success": False, "message": "Không có quyền đổi mật khẩu user khác"}
        
        return self._user_repository.change_password(user_id, new_password)
    
    def delete_user(self, user_id: int) -> Dict[str, Any]:
        """Xóa (vô hiệu hóa) user."""
        if not self.has_permission(Permission.USER_MANAGE):
            return {"success": False, "message": "Không có quyền xóa user"}
        
        # Cannot delete yourself
        if self.get_current_user_id() == user_id:
            return {"success": False, "message": "Không thể xóa chính mình"}
        
        return self._user_repository.delete_user(user_id)
    
    # ==================== Audit ====================
    
    def get_login_history(self, user_id: int = None, limit: int = 100):
        """Lấy lịch sử đăng nhập."""
        if not self.has_permission(Permission.AUDIT_VIEW):
            # User can see their own history
            if user_id != self.get_current_user_id():
                return []
        
        return self._user_repository.get_login_history(user_id, limit)


# ==================== Helper Functions ====================

def get_current_user() -> Optional[Dict[str, Any]]:
    """Shortcut để lấy user hiện tại."""
    return AuthManager.get_instance().get_current_user()


def get_current_username() -> Optional[str]:
    """Shortcut để lấy username hiện tại."""
    return AuthManager.get_instance().get_current_username()


def is_logged_in() -> bool:
    """Shortcut kiểm tra đăng nhập."""
    return AuthManager.get_instance().is_logged_in()


def require_permission(permission: Permission):
    """
    Decorator để yêu cầu permission cho một hàm.
    
    Usage:
        @require_permission(Permission.VEHICLE_CREATE)
        def add_vehicle(...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            auth = AuthManager.get_instance()
            if not auth.has_permission(permission):
                raise PermissionError(f"Không có quyền: {permission.name}")
            return func(*args, **kwargs)
        return wrapper
    return decorator
