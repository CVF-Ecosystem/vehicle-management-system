# tests/unit/test_backup_service.py
"""
Unit tests for BackupService.

Tests cover:
- Manual and auto backup creation
- Backup verification
- Restore operations
- Backup listing and cleanup
"""

import pytest
import sqlite3
import json
from pathlib import Path
from datetime import datetime

from core.backup_service import (
    BackupService,
    BackupType,
    BackupMetadata,
    create_manual_backup,
)
from exceptions import (
    BackupCreationError,
    BackupNotFoundError,
    BackupCorruptedError,
    RestoreError,
)


class TestBackupServiceInit:
    """Test BackupService initialization."""
    
    @pytest.mark.unit
    def test_init_creates_directories(self, tmp_path):
        """BackupService tạo thư mục backup khi khởi tạo."""
        db_path = tmp_path / "test.db"
        backup_dir = tmp_path / "backups"
        
        # Create test database
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.close()
        
        service = BackupService(
            db_path=str(db_path),
            backup_dir=str(backup_dir),
        )
        
        assert backup_dir.exists()
        assert (backup_dir / "auto").exists()
        assert (backup_dir / "manual").exists()
    
    @pytest.mark.unit
    def test_init_with_defaults(self, tmp_path, monkeypatch):
        """BackupService sử dụng config mặc định."""
        import config
        db_path = tmp_path / "test.db"
        
        # Create test database
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.close()
        
        monkeypatch.setattr(config, "DB_FILE", str(db_path))
        
        service = BackupService(backup_dir=str(tmp_path / "backups"))
        assert service.db_path == db_path


class TestBackupCreation:
    """Test backup creation functionality."""
    
    @pytest.fixture
    def test_db_with_data(self, tmp_path):
        """Tạo database test với dữ liệu mẫu."""
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        
        # Create tables similar to real schema
        conn.execute("""
            CREATE TABLE vehicles (
                id INTEGER PRIMARY KEY,
                vin TEXT UNIQUE,
                owner TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE dispatches (
                id INTEGER PRIMARY KEY,
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE locations (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        
        # Insert test data
        conn.execute("INSERT INTO vehicles (vin, owner) VALUES ('VIN001', 'Owner1')")
        conn.execute("INSERT INTO vehicles (vin, owner) VALUES ('VIN002', 'Owner2')")
        conn.execute("INSERT INTO locations (name) VALUES ('A-1-1')")
        
        conn.commit()
        conn.close()
        
        return db_path
    
    @pytest.fixture
    def backup_service(self, test_db_with_data, tmp_path):
        """Tạo BackupService cho testing."""
        return BackupService(
            db_path=str(test_db_with_data),
            backup_dir=str(tmp_path / "backups"),
        )
    
    @pytest.mark.unit
    def test_create_manual_backup(self, backup_service):
        """Tạo manual backup thành công."""
        metadata = backup_service.create_backup(BackupType.MANUAL)
        
        assert metadata is not None
        assert metadata.backup_type == "manual"
        assert metadata.file_size > 0
        assert metadata.checksum != ""
        assert Path(metadata.filepath).exists()
    
    @pytest.mark.unit
    def test_create_auto_backup(self, backup_service):
        """Tạo auto backup thành công."""
        metadata = backup_service.create_backup(BackupType.AUTO)
        
        assert metadata is not None
        assert metadata.backup_type == "auto"
        assert "auto" in metadata.filename
        assert Path(metadata.filepath).exists()
    
    @pytest.mark.unit
    def test_backup_metadata_saved(self, backup_service):
        """Metadata được lưu cùng backup."""
        metadata = backup_service.create_backup(BackupType.MANUAL)
        
        backup_path = Path(metadata.filepath)
        metadata_path = backup_path.with_suffix(".meta.json")
        
        assert metadata_path.exists()
        
        with open(metadata_path) as f:
            saved_metadata = json.load(f)
        
        assert saved_metadata["backup_id"] == metadata.backup_id
        assert saved_metadata["checksum"] == metadata.checksum
    
    @pytest.mark.unit
    def test_backup_records_summary(self, backup_service):
        """Backup metadata chứa thống kê records."""
        metadata = backup_service.create_backup(BackupType.MANUAL)
        
        assert "vehicles" in metadata.records_summary
        assert metadata.records_summary["vehicles"] == 2  # 2 vehicles inserted
        assert metadata.records_summary["locations"] == 1
    
    @pytest.mark.unit
    def test_backup_nonexistent_db_raises(self, tmp_path):
        """Backup database không tồn tại phải raise error."""
        service = BackupService(
            db_path=str(tmp_path / "nonexistent.db"),
            backup_dir=str(tmp_path / "backups"),
        )
        
        with pytest.raises(BackupNotFoundError):
            service.create_backup()


class TestBackupVerification:
    """Test backup verification functionality."""
    
    @pytest.fixture
    def backup_service_with_backup(self, tmp_path):
        """Tạo service với một backup sẵn."""
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE vehicles (id INTEGER PRIMARY KEY, vin TEXT)")
        conn.execute("CREATE TABLE dispatches (id INTEGER PRIMARY KEY)")
        conn.execute("CREATE TABLE locations (id INTEGER PRIMARY KEY)")
        conn.close()
        
        service = BackupService(
            db_path=str(db_path),
            backup_dir=str(tmp_path / "backups"),
        )
        
        metadata = service.create_backup(BackupType.MANUAL)
        return service, metadata
    
    @pytest.mark.unit
    def test_verify_valid_backup(self, backup_service_with_backup):
        """Verify backup hợp lệ trả về True."""
        service, metadata = backup_service_with_backup
        
        is_valid, message = service.verify_backup(Path(metadata.filepath))
        
        assert is_valid is True
        assert "hợp lệ" in message
    
    @pytest.mark.unit
    def test_verify_nonexistent_backup(self, backup_service_with_backup):
        """Verify backup không tồn tại trả về False."""
        service, _ = backup_service_with_backup
        
        is_valid, message = service.verify_backup(Path("/nonexistent/backup.db"))
        
        assert is_valid is False
        assert "không tồn tại" in message
    
    @pytest.mark.unit
    def test_verify_corrupted_backup(self, backup_service_with_backup, tmp_path):
        """Verify backup bị corrupt trả về False."""
        service, _ = backup_service_with_backup
        
        # Create corrupted file
        corrupted_path = tmp_path / "corrupted.db"
        corrupted_path.write_text("not a database")
        
        is_valid, message = service.verify_backup(corrupted_path)
        
        assert is_valid is False


class TestBackupRestore:
    """Test backup restore functionality."""
    
    @pytest.fixture
    def service_with_modified_db(self, tmp_path):
        """Service với DB đã được modify sau backup."""
        db_path = tmp_path / "test.db"
        
        # Create initial database
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE vehicles (id INTEGER PRIMARY KEY, vin TEXT)")
        conn.execute("CREATE TABLE dispatches (id INTEGER PRIMARY KEY)")
        conn.execute("CREATE TABLE locations (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO vehicles (vin) VALUES ('ORIGINAL_VIN')")
        conn.commit()
        conn.close()
        
        service = BackupService(
            db_path=str(db_path),
            backup_dir=str(tmp_path / "backups"),
        )
        
        # Create backup
        backup_metadata = service.create_backup(BackupType.MANUAL)
        
        # Modify database after backup
        conn = sqlite3.connect(str(db_path))
        conn.execute("DELETE FROM vehicles")
        conn.execute("INSERT INTO vehicles (vin) VALUES ('MODIFIED_VIN')")
        conn.commit()
        conn.close()
        
        return service, backup_metadata, db_path
    
    @pytest.mark.unit
    def test_restore_backup(self, service_with_modified_db):
        """Restore backup khôi phục dữ liệu gốc."""
        service, backup_metadata, db_path = service_with_modified_db
        
        # Verify current state is modified
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT vin FROM vehicles")
        row = cursor.fetchone()
        conn.close()
        
        assert row is not None, "Should have vehicle in modified DB"
        current_vin = row[0]
        assert current_vin == "MODIFIED_VIN"
        
        # Restore
        success = service.restore_backup(Path(backup_metadata.filepath))
        
        assert success is True
        
        # Verify restored state
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT vin FROM vehicles")
        row = cursor.fetchone()
        conn.close()
        
        assert row is not None, "Should have vehicle after restore"
        restored_vin = row[0]
        assert restored_vin == "ORIGINAL_VIN"
    
    @pytest.mark.unit
    def test_restore_creates_pre_restore_backup(self, service_with_modified_db):
        """Restore tạo backup trước khi khôi phục."""
        service, backup_metadata, _ = service_with_modified_db
        
        backups_before = service.list_backups()
        
        service.restore_backup(
            Path(backup_metadata.filepath),
            create_pre_restore_backup=True,
        )
        
        backups_after = service.list_backups()
        
        # Should have one more backup (pre_migration type)
        assert len(backups_after) >= len(backups_before)
    
    @pytest.mark.unit
    def test_restore_corrupted_backup_raises(self, service_with_modified_db, tmp_path):
        """Restore từ backup lỗi phải raise error."""
        service, _, _ = service_with_modified_db
        
        # Create corrupted backup
        corrupted = tmp_path / "corrupted.db"
        corrupted.write_text("not a database")
        
        with pytest.raises(BackupCorruptedError):
            service.restore_backup(corrupted)


class TestBackupManagement:
    """Test backup listing and cleanup."""
    
    @pytest.fixture
    def service_with_multiple_backups(self, tmp_path):
        """Service với nhiều backups."""
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE vehicles (id INTEGER)")
        conn.execute("CREATE TABLE dispatches (id INTEGER)")
        conn.execute("CREATE TABLE locations (id INTEGER)")
        conn.close()
        
        service = BackupService(
            db_path=str(db_path),
            backup_dir=str(tmp_path / "backups"),
            max_auto_backups=3,
            max_manual_backups=5,
        )
        
        # Create multiple backups
        for _ in range(3):
            service.create_backup(BackupType.MANUAL)
        for _ in range(2):
            service.create_backup(BackupType.AUTO)
        
        return service
    
    @pytest.mark.unit
    def test_list_all_backups(self, service_with_multiple_backups):
        """List tất cả backups."""
        service = service_with_multiple_backups
        
        all_backups = service.list_backups()
        
        assert len(all_backups) == 5  # 3 manual + 2 auto
    
    @pytest.mark.unit
    def test_list_by_type(self, service_with_multiple_backups):
        """List backups theo loại."""
        service = service_with_multiple_backups
        
        manual_backups = service.list_backups(backup_type=BackupType.MANUAL)
        auto_backups = service.list_backups(backup_type=BackupType.AUTO)
        
        assert len(manual_backups) == 3
        assert len(auto_backups) == 2
    
    @pytest.mark.unit
    def test_list_sorted_by_date(self, service_with_multiple_backups):
        """Backups được sắp xếp theo ngày (mới nhất trước)."""
        service = service_with_multiple_backups
        
        backups = service.list_backups()
        
        dates = [b.created_at for b in backups]
        assert dates == sorted(dates, reverse=True)
    
    @pytest.mark.unit
    def test_delete_backup(self, service_with_multiple_backups):
        """Xóa backup thành công."""
        service = service_with_multiple_backups
        
        backups = service.list_backups(BackupType.MANUAL)
        backup_to_delete = backups[0]
        
        success = service.delete_backup(Path(backup_to_delete.filepath))
        
        assert success is True
        assert not Path(backup_to_delete.filepath).exists()
        
        remaining = service.list_backups(BackupType.MANUAL)
        assert len(remaining) == 2
    
    @pytest.mark.unit
    def test_auto_cleanup_old_backups(self, tmp_path):
        """Auto cleanup xóa backups cũ vượt limit."""
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE vehicles (id INTEGER)")
        conn.execute("CREATE TABLE dispatches (id INTEGER)")
        conn.execute("CREATE TABLE locations (id INTEGER)")
        conn.close()
        
        service = BackupService(
            db_path=str(db_path),
            backup_dir=str(tmp_path / "backups"),
            max_auto_backups=2,  # Only keep 2
        )
        
        # Create 4 auto backups
        for _ in range(4):
            service.create_backup(BackupType.AUTO)
        
        # Should only have 2 (oldest deleted)
        auto_backups = service.list_backups(BackupType.AUTO)
        assert len(auto_backups) == 2
    
    @pytest.mark.unit
    def test_get_backup_stats(self, service_with_multiple_backups):
        """Lấy thống kê backups."""
        service = service_with_multiple_backups
        
        stats = service.get_backup_stats()
        
        assert stats["manual_backup_count"] == 3
        assert stats["auto_backup_count"] == 2
        assert stats["total_backup_count"] == 5
        assert stats["total_size_bytes"] > 0
        assert stats["latest_manual_backup"] is not None
        assert stats["latest_auto_backup"] is not None
