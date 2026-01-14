# tests/unit/test_password_security.py
"""
Unit tests for Issue #1: Password Security with bcrypt
Tests password hashing, verification, and auto-migration.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.user_repository import UserRepository


class TestPasswordHashing:
    """Test bcrypt password hashing implementation."""
    
    @pytest.fixture
    def user_repo(self, tmp_path):
        """Create temporary UserRepository for testing."""
        db_path = tmp_path / "test_security.db"
        return UserRepository(str(db_path))
    
    def test_bcrypt_hash_generation(self, user_repo):
        """Test that passwords are hashed with bcrypt."""
        password = "TestPassword123!"
        hash1, salt1 = user_repo._hash_password(password)
        
        # bcrypt hash starts with $2b$
        assert hash1.startswith("$2b$"), "Password should be hashed with bcrypt"
        assert salt1 == "", "bcrypt includes salt in hash"
        
        # Same password should generate different hashes (unique salt)
        hash2, salt2 = user_repo._hash_password(password)
        assert hash1 != hash2, "Each hash should have unique salt"
    
    def test_bcrypt_verification_success(self, user_repo):
        """Test successful password verification."""
        password = "MySecurePass456"
        password_hash, _ = user_repo._hash_password(password)
        
        is_valid, needs_migration = user_repo._verify_password(password, password_hash)
        
        assert is_valid is True, "Correct password should verify"
        assert needs_migration is False, "bcrypt hash doesn't need migration"
    
    def test_bcrypt_verification_failure(self, user_repo):
        """Test password verification with wrong password."""
        password = "CorrectPassword"
        wrong_password = "WrongPassword"
        password_hash, _ = user_repo._hash_password(password)
        
        is_valid, needs_migration = user_repo._verify_password(wrong_password, password_hash)
        
        assert is_valid is False, "Wrong password should not verify"
        assert needs_migration is False, "Migration flag only set on success"
    
    def test_legacy_password_verification(self, user_repo):
        """Test verification of legacy SHA256 passwords."""
        # Simulate legacy hash (salt:sha256)
        import hashlib
        password = "LegacyPassword"
        salt = "abc123"
        salted = f"{salt}{password}"
        hash_value = hashlib.sha256(salted.encode()).hexdigest()
        legacy_hash = f"{salt}:{hash_value}"
        
        is_valid, needs_migration = user_repo._verify_password(password, legacy_hash)
        
        assert is_valid is True, "Legacy password should verify"
        assert needs_migration is True, "Legacy hash should be flagged for migration"
    
    def test_password_auto_migration_on_login(self, user_repo):
        """Test automatic password migration during authentication."""
        # Create user with legacy password
        import hashlib
        username = "testuser"
        password = "TestPass123"
        salt = "legacy_salt"
        salted = f"{salt}{password}"
        hash_value = hashlib.sha256(salted.encode()).hexdigest()
        legacy_hash = f"{salt}:{hash_value}"
        
        # Manually insert user with legacy hash
        user_repo.conn.execute("""
            INSERT INTO users (username, password_hash, role, created_at)
            VALUES (?, ?, 'operator', datetime('now'))
        """, (username, legacy_hash))
        user_repo.conn.commit()
        
        # Authenticate - should trigger migration
        result = user_repo.authenticate(username, password)
        
        assert result['success'] is True, "Authentication should succeed"
        
        # Verify password was migrated to bcrypt
        user = user_repo.get_user_by_username(username)
        assert user['password_hash'].startswith("$2b$"), "Password should be migrated to bcrypt"
        
        # Verify can still login with same password
        result2 = user_repo.authenticate(username, password)
        assert result2['success'] is True, "Should login with bcrypt hash"
    
    def test_password_minimum_length(self, user_repo):
        """Test password minimum length requirement."""
        result = user_repo.create_user(
            username="shortpass",
            password="12345",  # Only 5 chars
            role="operator"
        )
        
        assert result['success'] is False, "Should reject short password"
        assert "ít nhất 6 ký tự" in result['message'].lower()
    
    def test_empty_password_rejection(self, user_repo):
        """Test empty password rejection."""
        result = user_repo.create_user(
            username="emptypass",
            password="",
            role="operator"
        )
        
        assert result['success'] is False, "Should reject empty password"
    
    def test_bcrypt_rounds(self, user_repo):
        """Test bcrypt uses 12 rounds (security standard)."""
        password = "TestRounds123"
        password_hash, _ = user_repo._hash_password(password)
        
        # bcrypt hash format: $2b$12$... (12 = rounds)
        assert "$12$" in password_hash, "Should use 12 rounds for security"
    
    def test_multiple_failed_logins_lockout(self, user_repo):
        """Test account lockout after 5 failed attempts."""
        # Create user
        username = "locktest"
        password = "CorrectPass123"
        user_repo.create_user(username=username, password=password, role="operator")
        
        # Attempt 5 failed logins
        for i in range(5):
            result = user_repo.authenticate(username, "WrongPassword")
            assert result['success'] is False
        
        # 6th attempt should mention account locked
        result = user_repo.authenticate(username, "WrongPassword")
        assert "khóa" in result['message'].lower(), "Should mention account locked"


class TestPasswordSecurity:
    """Test password security edge cases."""
    
    @pytest.fixture
    def user_repo(self, tmp_path):
        db_path = tmp_path / "test_security2.db"
        return UserRepository(str(db_path))
    
    def test_sql_injection_in_password(self, user_repo):
        """Test SQL injection attempts in password field."""
        malicious_password = "'; DROP TABLE users; --"
        
        result = user_repo.create_user(
            username="sqlinjection",
            password=malicious_password,
            role="operator"
        )
        
        # Should succeed - password is hashed safely
        assert result['success'] is True
        
        # Table should still exist
        cursor = user_repo.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        assert count >= 1, "Users table should still exist"
    
    def test_unicode_password_support(self, user_repo):
        """Test password with unicode characters."""
        password = "Mật_Khẩu_Tiếng_Việt_123!"
        
        result = user_repo.create_user(
            username="unicodeuser",
            password=password,
            role="operator"
        )
        
        assert result['success'] is True
        
        # Should authenticate with unicode password
        auth_result = user_repo.authenticate("unicodeuser", password)
        assert auth_result['success'] is True
    
    def test_very_long_password(self, user_repo):
        """Test password with 100 characters."""
        long_password = "A" * 100
        
        result = user_repo.create_user(
            username="longpass",
            password=long_password,
            role="operator"
        )
        
        assert result['success'] is True
        
        # Should authenticate
        auth_result = user_repo.authenticate("longpass", long_password)
        assert auth_result['success'] is True
    
    def test_special_characters_in_password(self, user_repo):
        """Test password with special characters."""
        password = "P@ssw0rd!#$%^&*()_+-=[]{}|;:,.<>?"
        
        result = user_repo.create_user(
            username="specialchars",
            password=password,
            role="operator"
        )
        
        assert result['success'] is True
        
        auth_result = user_repo.authenticate("specialchars", password)
        assert auth_result['success'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
