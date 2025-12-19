# database/user_repository.py
"""
User Repository - Phase 1C: Authentication
Quản lý CRUD operations cho bảng users và login_history.
"""

import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from database.base_manager import BaseManager

logger = logging.getLogger(__name__)

# Constants
ROLE_ADMIN = 'admin'
ROLE_OPERATOR = 'operator'
ROLE_VIEWER = 'viewer'
VALID_ROLES = {ROLE_ADMIN, ROLE_OPERATOR, ROLE_VIEWER}

# Security settings
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15
PASSWORD_MIN_LENGTH = 6


class UserRepository(BaseManager):
    """
    Repository cho quản lý users và authentication.
    """
    
    def __init__(self, db_path: str = None):
        super().__init__(db_path)
        self._ensure_default_admin()
    
    def _ensure_default_admin(self):
        """Tạo admin mặc định nếu chưa có user nào."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        
        if count == 0:
            logger.info("Tạo tài khoản admin mặc định...")
            self.create_user(
                username='admin',
                password='admin123',  # Should be changed on first login
                full_name='Administrator',
                role=ROLE_ADMIN,
                created_by_id=None  # System created
            )
            logger.info("Đã tạo tài khoản admin mặc định (username: admin, password: admin123)")
    
    # ==================== Password Hashing ====================
    
    @staticmethod
    def _hash_password(password: str, salt: str = None) -> tuple[str, str]:
        """
        Hash password using SHA-256 with salt.
        
        Returns:
            tuple: (password_hash, salt)
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        salted_password = f"{salt}{password}"
        password_hash = hashlib.sha256(salted_password.encode()).hexdigest()
        
        # Store as salt:hash format
        return f"{salt}:{password_hash}", salt
    
    @staticmethod
    def _verify_password(password: str, stored_hash: str) -> bool:
        """
        Verify password against stored hash.
        
        Args:
            password: Plain text password to verify
            stored_hash: Stored hash in format salt:hash
        
        Returns:
            bool: True if password matches
        """
        try:
            salt, hash_value = stored_hash.split(':')
            salted_password = f"{salt}{password}"
            computed_hash = hashlib.sha256(salted_password.encode()).hexdigest()
            return secrets.compare_digest(computed_hash, hash_value)
        except (ValueError, AttributeError):
            return False
    
    # ==================== User CRUD ====================
    
    def create_user(
        self,
        username: str,
        password: str,
        full_name: str = None,
        role: str = ROLE_OPERATOR,
        created_by_id: int = None
    ) -> Dict[str, Any]:
        """
        Tạo user mới.
        
        Args:
            username: Tên đăng nhập (unique)
            password: Mật khẩu
            full_name: Họ tên đầy đủ
            role: Vai trò (admin/operator/viewer)
            created_by_id: ID của user tạo
        
        Returns:
            dict: {"success": bool, "message": str, "user_id": int or None}
        """
        # Validate inputs
        if not username or len(username.strip()) < 3:
            return {"success": False, "message": "Username phải có ít nhất 3 ký tự", "user_id": None}
        
        if not password or len(password) < PASSWORD_MIN_LENGTH:
            return {"success": False, "message": f"Mật khẩu phải có ít nhất {PASSWORD_MIN_LENGTH} ký tự", "user_id": None}
        
        if role not in VALID_ROLES:
            return {"success": False, "message": f"Role không hợp lệ. Chọn: {', '.join(VALID_ROLES)}", "user_id": None}
        
        username = username.strip().lower()
        
        # Check if username exists
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            return {"success": False, "message": f"Username '{username}' đã tồn tại", "user_id": None}
        
        # Hash password
        password_hash, _ = self._hash_password(password)
        
        # Insert user
        try:
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, role, is_active, created_at, created_by)
                VALUES (?, ?, ?, ?, 1, ?, ?)
            """, (
                username,
                password_hash,
                full_name,
                role,
                datetime.now().isoformat(),
                created_by_id
            ))
            self.conn.commit()
            
            user_id = cursor.lastrowid
            logger.info(f"Đã tạo user: {username} (ID: {user_id}, Role: {role})")
            
            return {"success": True, "message": "Tạo user thành công", "user_id": user_id}
            
        except Exception as e:
            logger.error(f"Lỗi tạo user: {e}")
            return {"success": False, "message": f"Lỗi tạo user: {e}", "user_id": None}
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Lấy thông tin user theo ID."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, username, full_name, role, is_active, created_at, last_login,
                   failed_login_attempts, locked_until
            FROM users WHERE id = ?
        """, (user_id,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin user theo username (bao gồm password_hash để verify)."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, username, password_hash, full_name, role, is_active, 
                   created_at, last_login, failed_login_attempts, locked_until
            FROM users WHERE username = ?
        """, (username.strip().lower(),))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
    
    def list_users(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Liệt kê tất cả users."""
        cursor = self.conn.cursor()
        
        if include_inactive:
            cursor.execute("""
                SELECT id, username, full_name, role, is_active, created_at, last_login
                FROM users ORDER BY username
            """)
        else:
            cursor.execute("""
                SELECT id, username, full_name, role, is_active, created_at, last_login
                FROM users WHERE is_active = 1 ORDER BY username
            """)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def update_user(
        self,
        user_id: int,
        full_name: str = None,
        role: str = None,
        is_active: bool = None
    ) -> Dict[str, Any]:
        """Cập nhật thông tin user."""
        user = self.get_user_by_id(user_id)
        if not user:
            return {"success": False, "message": "User không tồn tại"}
        
        updates = []
        params = []
        
        if full_name is not None:
            updates.append("full_name = ?")
            params.append(full_name)
        
        if role is not None:
            if role not in VALID_ROLES:
                return {"success": False, "message": f"Role không hợp lệ"}
            updates.append("role = ?")
            params.append(role)
        
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if is_active else 0)
        
        if not updates:
            return {"success": False, "message": "Không có thông tin cần cập nhật"}
        
        params.append(user_id)
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"""
                UPDATE users SET {', '.join(updates)} WHERE id = ?
            """, params)
            self.conn.commit()
            
            logger.info(f"Đã cập nhật user ID {user_id}")
            return {"success": True, "message": "Cập nhật thành công"}
            
        except Exception as e:
            logger.error(f"Lỗi cập nhật user: {e}")
            return {"success": False, "message": f"Lỗi: {e}"}
    
    def change_password(self, user_id: int, new_password: str) -> Dict[str, Any]:
        """Đổi mật khẩu user."""
        if not new_password or len(new_password) < PASSWORD_MIN_LENGTH:
            return {"success": False, "message": f"Mật khẩu phải có ít nhất {PASSWORD_MIN_LENGTH} ký tự"}
        
        password_hash, _ = self._hash_password(new_password)
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE users SET password_hash = ?, failed_login_attempts = 0, locked_until = NULL
                WHERE id = ?
            """, (password_hash, user_id))
            self.conn.commit()
            
            logger.info(f"Đã đổi mật khẩu cho user ID {user_id}")
            return {"success": True, "message": "Đổi mật khẩu thành công"}
            
        except Exception as e:
            logger.error(f"Lỗi đổi mật khẩu: {e}")
            return {"success": False, "message": f"Lỗi: {e}"}
    
    def delete_user(self, user_id: int) -> Dict[str, Any]:
        """Xóa user (soft delete - set is_active = 0)."""
        user = self.get_user_by_id(user_id)
        if not user:
            return {"success": False, "message": "User không tồn tại"}
        
        if user['username'] == 'admin':
            return {"success": False, "message": "Không thể xóa tài khoản admin mặc định"}
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
            self.conn.commit()
            
            logger.info(f"Đã vô hiệu hóa user ID {user_id}")
            return {"success": True, "message": "Đã vô hiệu hóa user"}
            
        except Exception as e:
            logger.error(f"Lỗi xóa user: {e}")
            return {"success": False, "message": f"Lỗi: {e}"}
    
    # ==================== Authentication ====================
    
    def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """
        Xác thực user.
        
        Args:
            username: Tên đăng nhập
            password: Mật khẩu
        
        Returns:
            dict: {"success": bool, "message": str, "user": dict or None}
        """
        user = self.get_user_by_username(username)
        
        if not user:
            self._log_login_attempt(None, username, False, "User không tồn tại")
            return {"success": False, "message": "Sai tên đăng nhập hoặc mật khẩu", "user": None}
        
        # Check if account is locked
        if user['locked_until']:
            locked_until = datetime.fromisoformat(user['locked_until'])
            if datetime.now() < locked_until:
                remaining = (locked_until - datetime.now()).seconds // 60 + 1
                self._log_login_attempt(user['id'], username, False, "Tài khoản bị khóa")
                return {
                    "success": False,
                    "message": f"Tài khoản bị khóa. Vui lòng thử lại sau {remaining} phút",
                    "user": None
                }
            else:
                # Unlock account
                self._reset_failed_attempts(user['id'])
        
        # Check if account is active
        if not user['is_active']:
            self._log_login_attempt(user['id'], username, False, "Tài khoản bị vô hiệu hóa")
            return {"success": False, "message": "Tài khoản đã bị vô hiệu hóa", "user": None}
        
        # Verify password
        if not self._verify_password(password, user['password_hash']):
            self._increment_failed_attempts(user['id'])
            self._log_login_attempt(user['id'], username, False, "Sai mật khẩu")
            
            # Check if should lock account
            if user['failed_login_attempts'] + 1 >= MAX_FAILED_ATTEMPTS:
                return {
                    "success": False,
                    "message": f"Tài khoản đã bị khóa do nhập sai mật khẩu {MAX_FAILED_ATTEMPTS} lần",
                    "user": None
                }
            
            return {"success": False, "message": "Sai tên đăng nhập hoặc mật khẩu", "user": None}
        
        # Successful login
        self._reset_failed_attempts(user['id'])
        self._update_last_login(user['id'])
        self._log_login_attempt(user['id'], username, True, None)
        
        # Return user info without password_hash
        user_info = {
            'id': user['id'],
            'username': user['username'],
            'full_name': user['full_name'],
            'role': user['role']
        }
        
        logger.info(f"User '{username}' đăng nhập thành công")
        return {"success": True, "message": "Đăng nhập thành công", "user": user_info}
    
    def _increment_failed_attempts(self, user_id: int):
        """Tăng số lần đăng nhập thất bại."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET failed_login_attempts = failed_login_attempts + 1
            WHERE id = ?
        """, (user_id,))
        
        # Check if should lock
        cursor.execute("SELECT failed_login_attempts FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if row and row[0] >= MAX_FAILED_ATTEMPTS:
            locked_until = (datetime.now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)).isoformat()
            cursor.execute("UPDATE users SET locked_until = ? WHERE id = ?", (locked_until, user_id))
            logger.warning(f"User ID {user_id} bị khóa do nhập sai mật khẩu quá nhiều lần")
        
        self.conn.commit()
    
    def _reset_failed_attempts(self, user_id: int):
        """Reset số lần đăng nhập thất bại."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE users SET failed_login_attempts = 0, locked_until = NULL
            WHERE id = ?
        """, (user_id,))
        self.conn.commit()
    
    def _update_last_login(self, user_id: int):
        """Cập nhật thời gian đăng nhập cuối."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE users SET last_login = ? WHERE id = ?
        """, (datetime.now().isoformat(), user_id))
        self.conn.commit()
    
    # ==================== Login History ====================
    
    def _log_login_attempt(
        self,
        user_id: int,
        username: str,
        success: bool,
        failure_reason: str = None
    ):
        """Ghi log đăng nhập."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO login_history (user_id, username, action, success, failure_reason, created_at)
                VALUES (?, ?, 'LOGIN', ?, ?, ?)
            """, (
                user_id,
                username,
                1 if success else 0,
                failure_reason,
                datetime.now().isoformat()
            ))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Lỗi ghi login history: {e}")
    
    def log_logout(self, user_id: int, username: str):
        """Ghi log đăng xuất."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO login_history (user_id, username, action, success, created_at)
                VALUES (?, ?, 'LOGOUT', 1, ?)
            """, (user_id, username, datetime.now().isoformat()))
            self.conn.commit()
            logger.info(f"User '{username}' đã đăng xuất")
        except Exception as e:
            logger.error(f"Lỗi ghi logout history: {e}")
    
    def get_login_history(
        self,
        user_id: int = None,
        limit: int = 100,
        success_only: bool = None
    ) -> List[Dict[str, Any]]:
        """Lấy lịch sử đăng nhập."""
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM login_history WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if success_only is not None:
            query += " AND success = ?"
            params.append(1 if success_only else 0)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_failed_login_attempts(self, since_hours: int = 24) -> List[Dict[str, Any]]:
        """Lấy danh sách đăng nhập thất bại trong N giờ qua."""
        since = (datetime.now() - timedelta(hours=since_hours)).isoformat()
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT username, COUNT(*) as attempt_count, MAX(created_at) as last_attempt
            FROM login_history
            WHERE success = 0 AND created_at >= ?
            GROUP BY username
            ORDER BY attempt_count DESC
        """, (since,))
        
        return [dict(row) for row in cursor.fetchall()]
