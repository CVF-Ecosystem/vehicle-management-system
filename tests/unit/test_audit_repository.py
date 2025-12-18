# tests/unit/test_audit_repository.py
"""
Unit tests for AuditRepository.
"""

import pytest
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path

from database.audit_repository import (
    AuditRepository,
    AuditEntry,
    AuditAction,
    AuditFilter,
    log_audit,
    log_create,
    log_update,
    log_delete,
    log_backup,
    log_restore,
)


class TestAuditEntry:
    """Tests for AuditEntry dataclass."""
    
    def test_create_basic_entry(self):
        """Test tạo entry cơ bản."""
        entry = AuditEntry(
            action=AuditAction.CREATE,
            table_name="vehicles",
            record_id="ABC123"
        )
        
        assert entry.action == AuditAction.CREATE
        assert entry.table_name == "vehicles"
        assert entry.record_id == "ABC123"
        assert entry.username == "System"  # default
    
    def test_entry_to_dict(self):
        """Test chuyển đổi entry sang dict."""
        entry = AuditEntry(
            user_id=1,
            username="admin",
            action=AuditAction.UPDATE,
            table_name="vehicles",
            record_id="VIN123",
            old_value={"status": "in_stock"},
            new_value={"status": "dispatched"},
            details={"reason": "customer pickup"}
        )
        
        data = entry.to_dict()
        
        assert data['user_id'] == 1
        assert data['username'] == "admin"
        assert data['action'] == "UPDATE"
        assert data['table_name'] == "vehicles"
        assert json.loads(data['old_value']) == {"status": "in_stock"}
        assert json.loads(data['new_value']) == {"status": "dispatched"}
        assert json.loads(data['details']) == {"reason": "customer pickup"}
    
    def test_entry_from_row(self, tmp_path):
        """Test tạo entry từ database row."""
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        
        # Create table and insert test data
        conn.execute("""
            CREATE TABLE audit_logs (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                username TEXT,
                action TEXT,
                table_name TEXT,
                record_id TEXT,
                old_value TEXT,
                new_value TEXT,
                details TEXT,
                ip_address TEXT,
                created_at TEXT
            )
        """)
        conn.execute("""
            INSERT INTO audit_logs 
            (id, user_id, username, action, table_name, record_id, 
             old_value, new_value, details, ip_address, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            1, 2, "admin", "CREATE", "vehicles", "VIN123",
            '{"key": "old"}', '{"key": "new"}', '{"note": "test"}',
            "192.168.1.1", "2024-01-15T10:30:00"
        ))
        conn.commit()
        
        cursor = conn.execute("SELECT * FROM audit_logs WHERE id = 1")
        row = cursor.fetchone()
        
        entry = AuditEntry.from_row(row)
        
        assert entry.id == 1
        assert entry.user_id == 2
        assert entry.username == "admin"
        assert entry.action == AuditAction.CREATE
        assert entry.table_name == "vehicles"
        assert entry.old_value == {"key": "old"}
        assert entry.new_value == {"key": "new"}
        assert entry.details == {"note": "test"}
        
        conn.close()


class TestAuditRepositoryInit:
    """Tests for AuditRepository initialization."""
    
    def test_init_creates_table(self, tmp_path):
        """Test khởi tạo tạo bảng audit_logs."""
        db_path = tmp_path / "test.db"
        repo = AuditRepository(str(db_path))
        
        # Check table exists
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'"
        )
        assert cursor.fetchone() is not None
        conn.close()
    
    def test_init_creates_indexes(self, tmp_path):
        """Test khởi tạo tạo các indexes."""
        db_path = tmp_path / "test.db"
        repo = AuditRepository(str(db_path))
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )
        indexes = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        assert "idx_audit_action" in indexes
        assert "idx_audit_table" in indexes
        assert "idx_audit_created_at" in indexes


class TestAuditRepositoryLogging:
    """Tests for logging audit entries."""
    
    @pytest.fixture
    def repo(self, tmp_path):
        """Create a test repository."""
        db_path = tmp_path / "test.db"
        return AuditRepository(str(db_path))
    
    def test_log_basic_entry(self, repo):
        """Test log entry cơ bản."""
        entry_id = repo.log(
            action=AuditAction.CREATE,
            table_name="vehicles",
            record_id="VIN123",
            new_value={"owner": "Test Owner"},
            username="admin"
        )
        
        assert entry_id > 0
        
        # Verify entry was saved
        entry = repo.get_by_id(entry_id)
        assert entry is not None
        assert entry.action == AuditAction.CREATE
        assert entry.table_name == "vehicles"
        assert entry.record_id == "VIN123"
        assert entry.username == "admin"
    
    def test_log_update_with_old_new_values(self, repo):
        """Test log UPDATE với old và new values."""
        old_data = {"status": "in_stock", "location": "A1"}
        new_data = {"status": "dispatched", "location": None}
        
        entry_id = repo.log(
            action=AuditAction.UPDATE,
            table_name="vehicles",
            record_id="VIN456",
            old_value=old_data,
            new_value=new_data,
            username="operator"
        )
        
        entry = repo.get_by_id(entry_id)
        assert entry.old_value == old_data
        assert entry.new_value == new_data
    
    def test_log_delete(self, repo):
        """Test log DELETE."""
        deleted_data = {"vin": "VIN789", "owner": "Deleted Owner"}
        
        entry_id = repo.log(
            action=AuditAction.DELETE,
            table_name="vehicles",
            record_id="VIN789",
            old_value=deleted_data,
            username="admin"
        )
        
        entry = repo.get_by_id(entry_id)
        assert entry.action == AuditAction.DELETE
        assert entry.old_value == deleted_data
        assert entry.new_value is None
    
    def test_add_entry_object(self, repo):
        """Test add với AuditEntry object."""
        entry = AuditEntry(
            user_id=5,
            username="test_user",
            action=AuditAction.BACKUP,
            details={"backup_type": "manual", "size": 1024}
        )
        
        entry_id = repo.add(entry)
        
        saved_entry = repo.get_by_id(entry_id)
        assert saved_entry.user_id == 5
        assert saved_entry.username == "test_user"
        assert saved_entry.action == AuditAction.BACKUP


class TestAuditRepositoryQuery:
    """Tests for querying audit entries."""
    
    @pytest.fixture
    def repo_with_data(self, tmp_path):
        """Create repository with test data."""
        db_path = tmp_path / "test.db"
        repo = AuditRepository(str(db_path))
        
        # Add various test entries
        repo.log(AuditAction.CREATE, "vehicles", "VIN001", 
                 new_value={"owner": "Owner1"}, username="admin")
        repo.log(AuditAction.CREATE, "vehicles", "VIN002", 
                 new_value={"owner": "Owner2"}, username="admin")
        repo.log(AuditAction.UPDATE, "vehicles", "VIN001", 
                 old_value={"status": "in_stock"}, 
                 new_value={"status": "dispatched"}, username="operator")
        repo.log(AuditAction.DELETE, "drivers", "DRV001", 
                 old_value={"name": "Driver1"}, username="admin")
        repo.log(AuditAction.BACKUP, details={"type": "auto"}, username="System")
        
        return repo
    
    def test_query_all(self, repo_with_data):
        """Test query tất cả entries."""
        entries = repo_with_data.query()
        assert len(entries) == 5
    
    def test_query_by_action(self, repo_with_data):
        """Test query theo action."""
        filter_criteria = AuditFilter(action=AuditAction.CREATE)
        entries = repo_with_data.query(filter_criteria)
        
        assert len(entries) == 2
        for entry in entries:
            assert entry.action == AuditAction.CREATE
    
    def test_query_by_table(self, repo_with_data):
        """Test query theo table_name."""
        filter_criteria = AuditFilter(table_name="vehicles")
        entries = repo_with_data.query(filter_criteria)
        
        assert len(entries) == 3
        for entry in entries:
            assert entry.table_name == "vehicles"
    
    def test_query_by_username(self, repo_with_data):
        """Test query theo username."""
        filter_criteria = AuditFilter(username="admin")
        entries = repo_with_data.query(filter_criteria)
        
        assert len(entries) == 3
    
    def test_query_by_multiple_actions(self, repo_with_data):
        """Test query theo nhiều actions."""
        filter_criteria = AuditFilter(
            actions=[AuditAction.CREATE, AuditAction.UPDATE]
        )
        entries = repo_with_data.query(filter_criteria)
        
        assert len(entries) == 3
    
    def test_query_with_limit(self, repo_with_data):
        """Test query với limit."""
        filter_criteria = AuditFilter(limit=2)
        entries = repo_with_data.query(filter_criteria)
        
        assert len(entries) == 2
    
    def test_query_with_offset(self, repo_with_data):
        """Test query với offset."""
        # Get all first
        all_entries = repo_with_data.query(AuditFilter(limit=10))
        
        # Get with offset
        filter_criteria = AuditFilter(limit=10, offset=2)
        offset_entries = repo_with_data.query(filter_criteria)
        
        assert len(offset_entries) == len(all_entries) - 2
    
    def test_get_recent(self, repo_with_data):
        """Test lấy entries gần đây."""
        recent = repo_with_data.get_recent(limit=3)
        assert len(recent) == 3
    
    def test_get_for_record(self, repo_with_data):
        """Test lấy entries cho một record."""
        entries = repo_with_data.get_for_record("vehicles", "VIN001")
        
        assert len(entries) == 2  # CREATE + UPDATE
    
    def test_get_by_action(self, repo_with_data):
        """Test lấy entries theo action type."""
        entries = repo_with_data.get_by_action(AuditAction.DELETE)
        
        assert len(entries) == 1
        assert entries[0].action == AuditAction.DELETE


class TestAuditRepositoryStatistics:
    """Tests for statistics methods."""
    
    @pytest.fixture
    def repo_with_data(self, tmp_path):
        """Create repository with diverse test data."""
        db_path = tmp_path / "test.db"
        repo = AuditRepository(str(db_path))
        
        # Add test entries
        for i in range(5):
            repo.log(AuditAction.CREATE, "vehicles", f"VIN{i:03d}", username="admin")
        
        for i in range(3):
            repo.log(AuditAction.UPDATE, "vehicles", f"VIN{i:03d}", username="operator")
        
        repo.log(AuditAction.DELETE, "drivers", "DRV001", username="admin")
        repo.log(AuditAction.BACKUP, username="System")
        
        return repo
    
    def test_count_all(self, repo_with_data):
        """Test đếm tổng entries."""
        count = repo_with_data.count()
        assert count == 10
    
    def test_count_by_action(self, repo_with_data):
        """Test đếm theo action."""
        count = repo_with_data.count(AuditFilter(action=AuditAction.CREATE))
        assert count == 5
    
    def test_count_by_table(self, repo_with_data):
        """Test đếm theo table."""
        count = repo_with_data.count(AuditFilter(table_name="vehicles"))
        assert count == 8  # 5 CREATE + 3 UPDATE
    
    def test_get_statistics(self, repo_with_data):
        """Test lấy thống kê tổng hợp."""
        stats = repo_with_data.get_statistics()
        
        assert stats['total_entries'] == 10
        assert stats['by_action']['CREATE'] == 5
        assert stats['by_action']['UPDATE'] == 3
        assert stats['by_action']['DELETE'] == 1
        assert stats['by_action']['BACKUP'] == 1
        assert stats['by_table']['vehicles'] == 8
        assert stats['by_user']['admin'] == 6
        assert stats['by_user']['operator'] == 3
        assert stats['by_user']['System'] == 1


class TestAuditRepositoryMaintenance:
    """Tests for maintenance operations."""
    
    @pytest.fixture
    def repo_with_old_data(self, tmp_path):
        """Create repository with old entries."""
        db_path = tmp_path / "test.db"
        repo = AuditRepository(str(db_path))
        
        # Add recent entries
        repo.log(AuditAction.CREATE, "vehicles", "VIN001", username="admin")
        
        # Manually insert old entries (older than 30 days)
        old_date = (datetime.now() - timedelta(days=60)).isoformat()
        with repo._get_connection() as conn:
            conn.execute("""
                INSERT INTO audit_logs (action, table_name, record_id, username, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, ("CREATE", "vehicles", "OLD001", "admin", old_date))
            conn.execute("""
                INSERT INTO audit_logs (action, table_name, record_id, username, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, ("UPDATE", "vehicles", "OLD002", "admin", old_date))
            conn.commit()
        
        return repo
    
    def test_cleanup_old_entries(self, repo_with_old_data):
        """Test xóa entries cũ."""
        # Initial count
        initial_count = repo_with_old_data.count()
        assert initial_count == 3
        
        # Cleanup entries older than 30 days
        deleted = repo_with_old_data.cleanup_old_entries(days_to_keep=30)
        
        assert deleted == 2
        assert repo_with_old_data.count() == 1


class TestAuditRepositoryExport:
    """Tests for export functionality."""
    
    @pytest.fixture
    def repo_with_data(self, tmp_path):
        """Create repository with test data."""
        db_path = tmp_path / "test.db"
        repo = AuditRepository(str(db_path))
        
        repo.log(AuditAction.CREATE, "vehicles", "VIN001", 
                 new_value={"owner": "Test"}, username="admin")
        repo.log(AuditAction.UPDATE, "vehicles", "VIN001", 
                 old_value={"status": "old"}, 
                 new_value={"status": "new"}, username="operator")
        
        return repo
    
    def test_export_to_json(self, repo_with_data, tmp_path):
        """Test export ra file JSON."""
        export_path = tmp_path / "export.json"
        
        count = repo_with_data.export_to_json(str(export_path))
        
        assert count == 2
        assert export_path.exists()
        
        # Verify content
        with open(export_path, 'r') as f:
            data = json.load(f)
        
        assert data['total_entries'] == 2
        assert len(data['entries']) == 2


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""
    
    @pytest.fixture(autouse=True)
    def reset_global_repo(self):
        """Reset global repository instance before each test."""
        import database.audit_repository as ar
        ar._audit_repo = None
        yield
        ar._audit_repo = None
    
    def test_log_create_function(self, tmp_path, monkeypatch):
        """Test log_create convenience function."""
        import database.audit_repository as ar
        
        # Set up test repo
        db_path = tmp_path / "test.db"
        ar._audit_repo = AuditRepository(str(db_path))
        
        entry_id = log_create(
            table_name="vehicles",
            record_id="VIN123",
            new_value={"owner": "Test"},
            username="admin"
        )
        
        assert entry_id > 0
        entry = ar._audit_repo.get_by_id(entry_id)
        assert entry.action == AuditAction.CREATE
    
    def test_log_update_function(self, tmp_path):
        """Test log_update convenience function."""
        import database.audit_repository as ar
        
        db_path = tmp_path / "test.db"
        ar._audit_repo = AuditRepository(str(db_path))
        
        entry_id = log_update(
            table_name="vehicles",
            record_id="VIN123",
            old_value={"status": "old"},
            new_value={"status": "new"},
            username="operator"
        )
        
        entry = ar._audit_repo.get_by_id(entry_id)
        assert entry.action == AuditAction.UPDATE
        assert entry.old_value == {"status": "old"}
        assert entry.new_value == {"status": "new"}
    
    def test_log_delete_function(self, tmp_path):
        """Test log_delete convenience function."""
        import database.audit_repository as ar
        
        db_path = tmp_path / "test.db"
        ar._audit_repo = AuditRepository(str(db_path))
        
        entry_id = log_delete(
            table_name="vehicles",
            record_id="VIN123",
            old_value={"owner": "Deleted"},
            username="admin"
        )
        
        entry = ar._audit_repo.get_by_id(entry_id)
        assert entry.action == AuditAction.DELETE
    
    def test_log_backup_function(self, tmp_path):
        """Test log_backup convenience function."""
        import database.audit_repository as ar
        
        db_path = tmp_path / "test.db"
        ar._audit_repo = AuditRepository(str(db_path))
        
        entry_id = log_backup(
            backup_id="backup_001",
            backup_type="manual",
            filepath="/backups/backup_001.db",
            username="admin"
        )
        
        entry = ar._audit_repo.get_by_id(entry_id)
        assert entry.action == AuditAction.BACKUP
        assert entry.details['backup_type'] == "manual"
    
    def test_log_restore_function(self, tmp_path):
        """Test log_restore convenience function."""
        import database.audit_repository as ar
        
        db_path = tmp_path / "test.db"
        ar._audit_repo = AuditRepository(str(db_path))
        
        entry_id = log_restore(
            backup_id="backup_001",
            filepath="/backups/backup_001.db",
            username="admin"
        )
        
        entry = ar._audit_repo.get_by_id(entry_id)
        assert entry.action == AuditAction.RESTORE
