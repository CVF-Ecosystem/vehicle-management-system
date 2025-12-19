# tests/unit/test_auth.py
"""
Unit tests cho Phase 1C - Authentication & RBAC
"""

import pytest
import os
import tempfile
from datetime import datetime, timedelta

from database.user_repository import UserRepository
from auth.auth_manager import AuthManager
from auth.permissions import (
    Permission, 
    has_permission, 
    get_role_permissions,
    get_role_display_name,
    ROLE_ADMIN, ROLE_OPERATOR, ROLE_VIEWER
)


class TestUserRepository:
    """Tests cho UserRepository."""
    
    @pytest.fixture
    def user_repo(self, tmp_path):
        """Tạo UserRepository với database tạm."""
        db_path = str(tmp_path / "test_users.db")
        repo = UserRepository(db_path)
        return repo
    
    def test_default_admin_created(self, user_repo):
        """Test admin mặc định được tạo khi khởi tạo."""
        result = user_repo.get_user_by_username("admin")
        
        assert result is not None
        assert result['username'] == "admin"
        assert result['role'] == ROLE_ADMIN
        assert result['is_active'] == 1
    
    def test_create_user(self, user_repo):
        """Test tạo user mới."""
        result = user_repo.create_user(
            username="testuser",
            password="test123456",
            full_name="Test User",
            role=ROLE_OPERATOR
        )
        
        assert result['success'] is True
        assert 'user_id' in result
        
        # Verify user exists
        user = user_repo.get_user_by_id(result['user_id'])
        assert user is not None
        assert user['username'] == "testuser"
        assert user['full_name'] == "Test User"
        assert user['role'] == ROLE_OPERATOR
    
    def test_create_user_duplicate_username(self, user_repo):
        """Test không thể tạo user trùng username."""
        # admin đã tồn tại
        result = user_repo.create_user(
            username="admin",
            password="somepassword",
            role=ROLE_VIEWER
        )
        
        assert result['success'] is False
        assert "đã tồn tại" in result['message']
    
    def test_create_user_short_password(self, user_repo):
        """Test không thể tạo user với password quá ngắn."""
        result = user_repo.create_user(
            username="shortpwd",
            password="12345",  # < 6 chars
            role=ROLE_VIEWER
        )
        
        assert result['success'] is False
        assert "6 ký tự" in result['message']
    
    def test_authenticate_success(self, user_repo):
        """Test đăng nhập thành công."""
        # Đăng nhập với admin mặc định
        result = user_repo.authenticate("admin", "admin123")
        
        assert result['success'] is True
        assert 'user' in result
        assert result['user']['username'] == "admin"
    
    def test_authenticate_wrong_password(self, user_repo):
        """Test đăng nhập sai mật khẩu."""
        result = user_repo.authenticate("admin", "wrongpassword")
        
        assert result['success'] is False
        assert "sai" in result['message'].lower() or "incorrect" in result['message'].lower()
    
    def test_authenticate_nonexistent_user(self, user_repo):
        """Test đăng nhập với user không tồn tại."""
        result = user_repo.authenticate("nonexistent", "anypassword")
        
        assert result['success'] is False
    
    def test_authenticate_inactive_user(self, user_repo):
        """Test không thể đăng nhập với tài khoản bị vô hiệu hóa."""
        # Tạo user
        create_result = user_repo.create_user(
            username="inactiveuser",
            password="password123",
            role=ROLE_VIEWER
        )
        
        # Vô hiệu hóa
        user_repo.update_user(create_result['user_id'], is_active=False)
        
        # Thử đăng nhập
        result = user_repo.authenticate("inactiveuser", "password123")
        
        assert result['success'] is False
        assert "vô hiệu" in result['message'].lower() or "disabled" in result['message'].lower()
    
    def test_change_password(self, user_repo):
        """Test đổi mật khẩu."""
        # Tạo user
        create_result = user_repo.create_user(
            username="pwduser",
            password="oldpassword",
            role=ROLE_VIEWER
        )
        user_id = create_result['user_id']
        
        # Đổi mật khẩu
        change_result = user_repo.change_password(user_id, "newpassword123")
        assert change_result['success'] is True
        
        # Verify đăng nhập với mật khẩu mới
        login_result = user_repo.authenticate("pwduser", "newpassword123")
        assert login_result['success'] is True
        
        # Verify không thể đăng nhập với mật khẩu cũ
        old_result = user_repo.authenticate("pwduser", "oldpassword")
        assert old_result['success'] is False
    
    def test_update_user(self, user_repo):
        """Test cập nhật thông tin user."""
        # Tạo user
        create_result = user_repo.create_user(
            username="updateuser",
            password="password123",
            full_name="Original Name",
            role=ROLE_VIEWER
        )
        user_id = create_result['user_id']
        
        # Cập nhật
        update_result = user_repo.update_user(
            user_id,
            full_name="Updated Name",
            role=ROLE_OPERATOR
        )
        assert update_result['success'] is True
        
        # Verify
        user = user_repo.get_user_by_id(user_id)
        assert user['full_name'] == "Updated Name"
        assert user['role'] == ROLE_OPERATOR
    
    def test_list_users(self, user_repo):
        """Test liệt kê users."""
        # Tạo thêm users
        user_repo.create_user("user1", "password1", role=ROLE_OPERATOR)
        user_repo.create_user("user2", "password2", role=ROLE_VIEWER)
        
        result = user_repo.list_users()
        
        # list_users returns list directly
        assert isinstance(result, list)
        assert len(result) >= 3  # admin + 2 users mới
    
    def test_soft_delete_user(self, user_repo):
        """Test soft delete user."""
        create_result = user_repo.create_user(
            username="todelete",
            password="password123",
            role=ROLE_VIEWER
        )
        user_id = create_result['user_id']
        
        # Delete
        delete_result = user_repo.delete_user(user_id)
        assert delete_result['success'] is True
        
        # User should not appear in list (default excludes inactive)
        list_result = user_repo.list_users(include_inactive=False)
        usernames = [u['username'] for u in list_result]
        assert "todelete" not in usernames
        
        # But should appear if include_inactive=True
        list_all = user_repo.list_users(include_inactive=True)
        usernames_all = [u['username'] for u in list_all]
        assert "todelete" in usernames_all
    
    def test_login_history(self, user_repo):
        """Test ghi lịch sử đăng nhập."""
        # Đăng nhập để tạo history
        user_repo.authenticate("admin", "admin123")
        user_repo.authenticate("admin", "wrongpwd")  # Failed attempt
        
        # Get history
        history = user_repo.get_login_history(limit=10)
        
        assert len(history) >= 2


class TestPermissions:
    """Tests cho RBAC permissions."""
    
    def test_admin_has_all_permissions(self):
        """Test admin có tất cả permissions."""
        for perm in Permission:
            assert has_permission(ROLE_ADMIN, perm) is True
    
    def test_operator_limited_permissions(self):
        """Test operator có quyền hạn chế."""
        # Có quyền xem xe
        assert has_permission(ROLE_OPERATOR, Permission.VEHICLE_VIEW) is True
        # Có quyền thêm xe
        assert has_permission(ROLE_OPERATOR, Permission.VEHICLE_CREATE) is True
        # Không có quyền quản lý user
        assert has_permission(ROLE_OPERATOR, Permission.USER_MANAGE) is False
        assert has_permission(ROLE_OPERATOR, Permission.USER_CHANGE_ROLE) is False
    
    def test_viewer_read_only(self):
        """Test viewer chỉ có quyền xem."""
        assert has_permission(ROLE_VIEWER, Permission.VEHICLE_VIEW) is True
        assert has_permission(ROLE_VIEWER, Permission.VEHICLE_CREATE) is False
        assert has_permission(ROLE_VIEWER, Permission.VEHICLE_UPDATE) is False
        assert has_permission(ROLE_VIEWER, Permission.VEHICLE_DELETE) is False
    
    def test_get_permissions_for_role(self):
        """Test lấy danh sách permissions cho role."""
        admin_perms = get_role_permissions(ROLE_ADMIN)
        operator_perms = get_role_permissions(ROLE_OPERATOR)
        viewer_perms = get_role_permissions(ROLE_VIEWER)
        
        assert len(admin_perms) > len(operator_perms)
        assert len(operator_perms) > len(viewer_perms)
    
    def test_role_display_name(self):
        """Test tên hiển thị của role."""
        # Vietnamese display names - just check it returns a non-empty string
        admin_name = get_role_display_name(ROLE_ADMIN)
        operator_name = get_role_display_name(ROLE_OPERATOR)
        viewer_name = get_role_display_name(ROLE_VIEWER)
        
        assert len(admin_name) > 0
        assert len(operator_name) > 0
        assert len(viewer_name) > 0


class TestAuthManager:
    """Tests cho AuthManager singleton."""
    
    @pytest.fixture(autouse=True)
    def reset_auth_manager(self):
        """Reset AuthManager trước mỗi test."""
        AuthManager.reset_instance()
        yield
        AuthManager.reset_instance()
    
    @pytest.fixture
    def auth_manager(self, tmp_path):
        """Tạo AuthManager với database tạm."""
        db_path = str(tmp_path / "test_auth.db")
        return AuthManager(db_path)
    
    def test_singleton(self, tmp_path):
        """Test AuthManager là singleton."""
        db_path = str(tmp_path / "test_singleton.db")
        
        manager1 = AuthManager(db_path)
        manager2 = AuthManager.get_instance()
        
        assert manager1 is manager2
    
    def test_login_success(self, auth_manager):
        """Test đăng nhập thành công."""
        result = auth_manager.login("admin", "admin123")
        
        assert result['success'] is True
        assert auth_manager.is_logged_in() is True
        assert auth_manager.get_current_user()['username'] == "admin"
    
    def test_login_failure(self, auth_manager):
        """Test đăng nhập thất bại."""
        result = auth_manager.login("admin", "wrongpassword")
        
        assert result['success'] is False
        assert auth_manager.is_logged_in() is False
        assert auth_manager.get_current_user() is None
    
    def test_logout(self, auth_manager):
        """Test đăng xuất."""
        # Login first
        auth_manager.login("admin", "admin123")
        assert auth_manager.is_logged_in() is True
        
        # Logout
        auth_manager.logout()
        assert auth_manager.is_logged_in() is False
        assert auth_manager.get_current_user() is None
    
    def test_has_permission_logged_in(self, auth_manager):
        """Test kiểm tra quyền khi đã đăng nhập."""
        auth_manager.login("admin", "admin123")
        
        assert auth_manager.has_permission(Permission.USER_MANAGE) is True
        assert auth_manager.has_permission(Permission.VEHICLE_VIEW) is True
    
    def test_has_permission_not_logged_in(self, auth_manager):
        """Test kiểm tra quyền khi chưa đăng nhập."""
        assert auth_manager.has_permission(Permission.VEHICLE_VIEW) is False
    
    def test_is_admin(self, auth_manager):
        """Test kiểm tra admin."""
        auth_manager.login("admin", "admin123")
        assert auth_manager.is_admin() is True
        
        # Tạo user operator và đăng nhập
        auth_manager.create_user(
            username="operator1",
            password="pass123456",
            role=ROLE_OPERATOR
        )
        auth_manager.logout()
        auth_manager.login("operator1", "pass123456")
        
        assert auth_manager.is_admin() is False
    
    def test_create_user_through_manager(self, auth_manager):
        """Test tạo user qua AuthManager."""
        auth_manager.login("admin", "admin123")
        
        result = auth_manager.create_user(
            username="newuser",
            password="newpass123",
            full_name="New User",
            role=ROLE_VIEWER
        )
        
        assert result['success'] is True
    
    def test_list_users_through_manager(self, auth_manager):
        """Test liệt kê users qua AuthManager."""
        auth_manager.login("admin", "admin123")
        
        result = auth_manager.list_users()
        
        # list_users returns list directly
        assert isinstance(result, list)
        assert len(result) >= 1


class TestAccountLockout:
    """Tests cho tính năng khóa tài khoản sau nhiều lần đăng nhập sai."""
    
    @pytest.fixture
    def user_repo(self, tmp_path):
        """Tạo UserRepository với database tạm."""
        db_path = str(tmp_path / "test_lockout.db")
        return UserRepository(db_path)
    
    def test_account_locks_after_failed_attempts(self, user_repo):
        """Test tài khoản bị khóa sau 5 lần đăng nhập sai."""
        # Thử đăng nhập sai 5 lần
        for i in range(5):
            result = user_repo.authenticate("admin", "wrongpassword")
            assert result['success'] is False
        
        # Lần thứ 6 với mật khẩu đúng cũng phải bị khóa
        result = user_repo.authenticate("admin", "admin123")
        assert result['success'] is False
        assert "khóa" in result['message'].lower() or "locked" in result['message'].lower()
    
    def test_successful_login_resets_failed_count(self, user_repo):
        """Test đăng nhập thành công reset số lần thất bại."""
        # 3 lần sai
        for i in range(3):
            user_repo.authenticate("admin", "wrongpassword")
        
        # Đăng nhập đúng
        result = user_repo.authenticate("admin", "admin123")
        assert result['success'] is True
        
        # Verify failed count reset
        user = user_repo.get_user_by_username("admin")
        assert user['failed_login_attempts'] == 0
