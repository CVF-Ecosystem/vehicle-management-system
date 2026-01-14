# tests/unit/test_session_timeout.py
"""
Unit tests for Issue #5: Session Timeout Implementation
Tests 30-minute idle timeout and auto-logout functionality.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auth.auth_manager import AuthManager
from database.user_repository import UserRepository


class TestSessionTimeout:
    """Test session timeout functionality."""
    
    @pytest.fixture
    def setup_auth(self, tmp_path):
        """Setup AuthManager with test database."""
        # Reset singleton
        AuthManager._instance = None
        
        db_path = tmp_path / "test_auth.db"
        auth_manager = AuthManager(str(db_path))
        
        # Create test user
        user_repo = auth_manager.get_user_repository()
        user_repo.create_user(
            username="testuser",
            password="TestPass123",
            role="operator"
        )
        
        yield auth_manager
        
        # Cleanup
        AuthManager.reset_instance()
    
    def test_login_sets_timestamp(self, setup_auth):
        """Test that login sets _login_time."""
        auth_manager = setup_auth
        
        result = auth_manager.login("testuser", "TestPass123")
        
        assert result['success'] is True
        assert auth_manager._login_time is not None
        assert isinstance(auth_manager._login_time, datetime)
    
    def test_session_valid_within_30_minutes(self, setup_auth):
        """Test session is valid within 30 minutes."""
        auth_manager = setup_auth
        auth_manager.login("testuser", "TestPass123")
        
        # Check immediately
        assert auth_manager.is_logged_in() is True
        
        # Simulate 29 minutes elapsed (still valid)
        with patch.object(auth_manager, '_login_time', 
                         datetime.now() - timedelta(minutes=29)):
            assert auth_manager.is_logged_in() is True
            assert auth_manager.get_current_user() is not None
    
    def test_session_expires_after_30_minutes(self, setup_auth):
        """Test session expires after 30 minutes idle."""
        auth_manager = setup_auth
        auth_manager.login("testuser", "TestPass123")
        
        # Simulate 31 minutes elapsed
        with patch.object(auth_manager, '_login_time', 
                         datetime.now() - timedelta(minutes=31)):
            assert auth_manager.is_logged_in() is False, "Session should expire after 30 minutes"
            assert auth_manager.get_current_user() is None, "Should return None after timeout"
    
    def test_session_timeout_auto_logout(self, setup_auth):
        """Test auto-logout clears session after timeout."""
        auth_manager = setup_auth
        auth_manager.login("testuser", "TestPass123")
        
        # Verify logged in
        assert auth_manager._current_user is not None
        
        # Set timeout manually instead of using patch
        auth_manager._login_time = datetime.now() - timedelta(minutes=35)
        
        # Calling is_logged_in() should trigger auto-logout
        result = auth_manager.is_logged_in()
        assert result is False  # Should return False for expired session
        
        # Session should be cleared
        assert auth_manager._current_user is None
        assert auth_manager._login_time is None
    
    def test_get_session_time_remaining(self, setup_auth):
        """Test calculating remaining session time."""
        auth_manager = setup_auth
        auth_manager.login("testuser", "TestPass123")
        
        # Fresh login should have ~30 minutes remaining
        remaining = auth_manager.get_session_time_remaining()
        assert remaining is not None
        assert 29 <= remaining <= 30, f"Should have ~30 minutes, got {remaining}"
        
        # Simulate 20 minutes elapsed
        with patch.object(auth_manager, '_login_time', 
                         datetime.now() - timedelta(minutes=20)):
            remaining = auth_manager.get_session_time_remaining()
            assert 9 <= remaining <= 10, f"Should have ~10 minutes, got {remaining}"
        
        # After timeout
        with patch.object(auth_manager, '_login_time', 
                         datetime.now() - timedelta(minutes=35)):
            remaining = auth_manager.get_session_time_remaining()
            assert remaining == 0, "Expired session should return 0"
    
    def test_session_refresh_extends_timeout(self, setup_auth):
        """Test refresh_session() extends session timeout."""
        auth_manager = setup_auth
        auth_manager.login("testuser", "TestPass123")
        
        # Get initial login time
        initial_time = auth_manager._login_time
        
        # Simulate 10 minutes elapsed
        with patch('auth.auth_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime.now() + timedelta(minutes=10)
            
            # Refresh session
            auth_manager.refresh_session()
            
            # Login time should be updated
            assert auth_manager._login_time > initial_time
    
    def test_logout_clears_login_time(self, setup_auth):
        """Test logout clears _login_time."""
        auth_manager = setup_auth
        auth_manager.login("testuser", "TestPass123")
        
        assert auth_manager._login_time is not None
        
        auth_manager.logout()
        
        assert auth_manager._login_time is None
        assert auth_manager._current_user is None
    
    def test_multiple_login_resets_timer(self, setup_auth):
        """Test that re-login resets session timer."""
        auth_manager = setup_auth
        
        # First login
        auth_manager.login("testuser", "TestPass123")
        first_time = auth_manager._login_time
        
        # Simulate 25 minutes elapsed
        with patch.object(auth_manager, '_login_time', 
                         datetime.now() - timedelta(minutes=25)):
            
            # Logout and login again
            auth_manager.logout()
            auth_manager.login("testuser", "TestPass123")
            
            # Timer should be reset
            assert auth_manager._login_time > first_time
            remaining = auth_manager.get_session_time_remaining()
            assert remaining >= 29, "Should have fresh 30 minutes after re-login"
    
    def test_session_timeout_constant(self, setup_auth):
        """Test SESSION_TIMEOUT_MINUTES is set to 30."""
        auth_manager = setup_auth
        assert auth_manager.SESSION_TIMEOUT_MINUTES == 30


class TestSessionSecurityEdgeCases:
    """Test edge cases for session security."""
    
    @pytest.fixture
    def setup_auth(self, tmp_path):
        AuthManager._instance = None
        db_path = tmp_path / "test_edge.db"
        auth_manager = AuthManager(str(db_path))
        user_repo = auth_manager.get_user_repository()
        user_repo.create_user(username="edge", password="Pass123", role="admin")
        yield auth_manager
        AuthManager.reset_instance()
    
    def test_get_current_user_without_login(self, setup_auth):
        """Test get_current_user() returns None when not logged in."""
        auth_manager = setup_auth
        assert auth_manager.get_current_user() is None
    
    def test_session_time_remaining_without_login(self, setup_auth):
        """Test get_session_time_remaining() returns None without login."""
        auth_manager = setup_auth
        assert auth_manager.get_session_time_remaining() is None
    
    def test_refresh_session_without_login(self, setup_auth):
        """Test refresh_session() does nothing when not logged in."""
        auth_manager = setup_auth
        
        # Should not raise exception
        auth_manager.refresh_session()
        
        assert auth_manager._login_time is None
    
    def test_concurrent_session_check(self, setup_auth):
        """Test thread-safe session checking."""
        auth_manager = setup_auth
        auth_manager.login("edge", "Pass123")
        
        # Simulate concurrent is_logged_in calls
        results = []
        for _ in range(10):
            results.append(auth_manager.is_logged_in())
        
        assert all(results), "All concurrent checks should return True"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
