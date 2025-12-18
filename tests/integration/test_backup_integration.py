"""
Integration tests for backup and audit system.
Tests the interaction between BackupService and AuditRepository.
"""

import gc
import pytest
import sqlite3
from pathlib import Path
from datetime import datetime

from core.backup_service import BackupService, BackupType, BackupMetadata
from database.audit_repository import AuditRepository, AuditAction
from database.base_manager import BaseManager


class TestBackupServiceIntegration:
    """Integration tests for BackupService with real database."""
    
    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create temporary database with sample data."""
        db_file = tmp_path / "test.db"
        
        # Initialize schema
        BaseManager(str(db_file))
        
        # Add sample data (vehicles table has NOT NULL: owner, date_in, status)
        conn = sqlite3.connect(str(db_file))
        for i in range(10):
            vin = f"VIN{i:015d}"
            conn.execute(
                "INSERT INTO vehicles (vin, owner, date_in, status) VALUES (?, ?, ?, ?)",
                (vin, f"Owner_{i}", "2024-01-01", "in_stock")
            )
        conn.commit()
        conn.close()
        
        gc.collect()
        return str(db_file)
    
    @pytest.fixture
    def backup_service(self, temp_db, tmp_path):
        """Create backup service."""
        backup_dir = tmp_path / "backups"
        return BackupService(temp_db, str(backup_dir))
    
    def test_backup_preserves_all_data(self, backup_service, temp_db):
        """Test that backup contains all original data."""
        # Count original records
        conn = sqlite3.connect(temp_db)
        original_count = conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
        conn.close()
        
        # Create backup
        metadata = backup_service.create_backup(BackupType.MANUAL)
        
        # Verify backup file exists and has data
        assert Path(metadata.filepath).exists()
        
        backup_conn = sqlite3.connect(metadata.filepath)
        backup_count = backup_conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
        backup_conn.close()
        
        assert backup_count == original_count == 10
    
    def test_backup_metadata_correct(self, backup_service):
        """Test backup metadata is correct."""
        metadata = backup_service.create_backup(BackupType.MANUAL)
        
        assert metadata.backup_id is not None
        assert metadata.filename.startswith("backup_manual_")
        assert metadata.backup_type == "manual"
        assert metadata.file_size > 0
        assert metadata.checksum is not None
    
    def test_restore_recovers_data(self, backup_service, temp_db):
        """Test restore recovers deleted data."""
        # Create backup
        metadata = backup_service.create_backup(BackupType.MANUAL)
        
        # Delete all data
        conn = sqlite3.connect(temp_db)
        conn.execute("DELETE FROM vehicles")
        conn.commit()
        remaining = conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
        conn.close()
        assert remaining == 0
        
        # Restore
        backup_service.restore_backup(metadata.filepath)
        
        # Verify data recovered
        conn = sqlite3.connect(temp_db)
        recovered = conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
        conn.close()
        
        assert recovered == 10
    
    def test_backup_verify_works(self, backup_service):
        """Test backup verification works."""
        metadata = backup_service.create_backup(BackupType.MANUAL)
        
        # Verify should return True for valid backup
        is_valid, message = backup_service.verify_backup(metadata.filepath)
        assert is_valid is True
    
    def test_corrupted_backup_fails_verify(self, backup_service):
        """Test corrupted backup fails verification."""
        metadata = backup_service.create_backup(BackupType.MANUAL)
        
        # Corrupt the backup
        with open(metadata.filepath, 'ab') as f:
            f.write(b'CORRUPTED')
        
        # Verify should fail
        is_valid, message = backup_service.verify_backup(metadata.filepath)
        assert is_valid is False
    
    def test_list_backups(self, backup_service):
        """Test listing backups."""
        # Create some backups
        backup_service.create_backup(BackupType.MANUAL)
        backup_service.create_backup(BackupType.MANUAL)
        backup_service.create_backup(BackupType.AUTO)
        
        # List all
        all_backups = backup_service.list_backups()
        assert len(all_backups) == 3
        
        # List by type
        manual = backup_service.list_backups(BackupType.MANUAL)
        auto = backup_service.list_backups(BackupType.AUTO)
        assert len(manual) == 2
        assert len(auto) == 1
    
    def test_delete_backup(self, backup_service):
        """Test deleting backup."""
        metadata = backup_service.create_backup(BackupType.MANUAL)
        
        # Backup exists
        assert Path(metadata.filepath).exists()
        
        # Delete
        backup_service.delete_backup(metadata.filepath)
        
        # Backup no longer exists
        assert not Path(metadata.filepath).exists()
        
        # Not in list
        backups = backup_service.list_backups()
        assert len(backups) == 0
    
    def test_backup_stats(self, backup_service):
        """Test backup statistics."""
        backup_service.create_backup(BackupType.MANUAL)
        backup_service.create_backup(BackupType.MANUAL)
        backup_service.create_backup(BackupType.AUTO)
        
        stats = backup_service.get_backup_stats()
        
        assert stats["total_backup_count"] == 3
        assert stats["manual_backup_count"] == 2
        assert stats["auto_backup_count"] == 1
        assert stats["total_size_bytes"] > 0


class TestAuditRepositoryIntegration:
    """Integration tests for AuditRepository."""
    
    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create temporary database."""
        db_file = tmp_path / "audit_test.db"
        BaseManager(str(db_file))
        gc.collect()
        return str(db_file)
    
    @pytest.fixture
    def audit_repo(self, temp_db):
        """Create audit repository."""
        return AuditRepository(temp_db)
    
    def test_log_entry(self, audit_repo):
        """Test logging audit entry."""
        entry_id = audit_repo.log(
            action=AuditAction.CREATE,
            table_name="vehicles",
            record_id="1",
            new_value={"vin": "TEST123", "owner": "Test"}
        )
        
        assert entry_id > 0
    
    def test_query_entries(self, audit_repo):
        """Test querying entries."""
        # Log some entries
        audit_repo.log(action=AuditAction.CREATE, table_name="vehicles", record_id="1")
        audit_repo.log(action=AuditAction.UPDATE, table_name="vehicles", record_id="1")
        audit_repo.log(action=AuditAction.DELETE, table_name="vehicles", record_id="1")
        
        # Query all
        entries = audit_repo.query()
        assert len(entries) == 3
    
    def test_statistics(self, audit_repo):
        """Test statistics."""
        # Log entries
        for i in range(5):
            audit_repo.log(action=AuditAction.CREATE, table_name="vehicles")
        for i in range(3):
            audit_repo.log(action=AuditAction.UPDATE, table_name="vehicles")
        
        stats = audit_repo.get_statistics()
        
        assert stats["total_entries"] == 8
        assert stats["by_action"]["CREATE"] == 5
        assert stats["by_action"]["UPDATE"] == 3


class TestBackupWithAuditIntegration:
    """Test backup and audit working together."""
    
    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create temporary database."""
        db_file = tmp_path / "combined_test.db"
        BaseManager(str(db_file))
        gc.collect()
        return str(db_file)
    
    @pytest.fixture
    def services(self, temp_db, tmp_path):
        """Create both services."""
        backup_dir = tmp_path / "backups"
        return {
            "backup": BackupService(temp_db, str(backup_dir)),
            "audit": AuditRepository(temp_db)
        }
    
    def test_backup_and_audit_share_db(self, services):
        """Test backup service and audit repository can work together."""
        backup_svc = services["backup"]
        audit_repo = services["audit"]
        
        # Create audit entry
        audit_repo.log(action=AuditAction.CREATE, table_name="test", record_id="1")
        
        # Create backup
        metadata = backup_svc.create_backup(BackupType.MANUAL)
        
        # Both should work
        assert metadata.file_size > 0
        assert audit_repo.count() == 1
    
    def test_backup_includes_audit_logs(self, services):
        """Test backup includes audit log table."""
        backup_svc = services["backup"]
        audit_repo = services["audit"]
        
        # Create audit entries
        for i in range(5):
            audit_repo.log(action=AuditAction.CREATE, table_name="test", record_id=str(i))
        
        # Create backup
        metadata = backup_svc.create_backup(BackupType.MANUAL)
        
        # Check backup has audit_logs table with data
        conn = sqlite3.connect(metadata.filepath)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'"
        ).fetchall()
        assert len(tables) == 1
        
        count = conn.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0]
        conn.close()
        
        assert count == 5
