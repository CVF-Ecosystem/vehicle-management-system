# core/backup_service.py
"""
Backup Service - Database backup and restore operations.

Provides:
- Manual backup: User-triggered backup
- Auto backup: Scheduled automatic backups
- Pre-archive backup: Backup before archiving data
- Restore: Restore database from backup file
- Verify: Validate backup integrity and schema compatibility

Usage:
    from core.backup_service import BackupService
    
    service = BackupService()
    
    # Manual backup
    result = service.create_backup(backup_type='manual')
    
    # Restore
    success = service.restore_backup('/path/to/backup.db')
"""

import os
import shutil
import sqlite3
import hashlib
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

import config
from exceptions import (
    BackupError,
    BackupCreationError,
    RestoreError,
    BackupNotFoundError,
    BackupCorruptedError,
    SchemaVersionMismatchError,
)

logger = logging.getLogger(__name__)


class BackupType(Enum):
    """Loại backup."""
    MANUAL = "manual"
    AUTO = "auto"
    PRE_ARCHIVE = "pre_archive"
    PRE_MIGRATION = "pre_migration"


@dataclass
class BackupMetadata:
    """Metadata cho backup file."""
    backup_id: str
    filename: str
    filepath: str
    backup_type: str
    created_at: str
    db_version: str
    app_version: str
    file_size: int
    checksum: str
    tables_count: int
    records_summary: Dict[str, int]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BackupMetadata':
        return cls(**data)


class BackupService:
    """
    Service quản lý backup và restore database.
    
    Features:
    - Create manual/auto/pre-archive backups
    - Restore database from backup
    - Verify backup integrity
    - List and manage backup history
    - Auto-cleanup old backups
    """
    
    # Configuration defaults
    DEFAULT_BACKUP_DIR = "backups"
    DEFAULT_AUTO_BACKUP_DIR = "backups/auto"
    DEFAULT_MANUAL_BACKUP_DIR = "backups/manual"
    DEFAULT_MAX_AUTO_BACKUPS = 7  # Keep 7 auto backups
    DEFAULT_MAX_MANUAL_BACKUPS = 30  # Keep 30 manual backups
    BACKUP_EXTENSION = ".db"
    METADATA_EXTENSION = ".meta.json"
    
    def __init__(
        self,
        db_path: Optional[str] = None,
        backup_dir: Optional[str] = None,
        max_auto_backups: int = DEFAULT_MAX_AUTO_BACKUPS,
        max_manual_backups: int = DEFAULT_MAX_MANUAL_BACKUPS,
    ):
        """
        Initialize BackupService.
        
        Args:
            db_path: Path to the database file. Defaults to project-root/DB_FILE.
            backup_dir: Root backup directory. Defaults to project-root/backups/.
            max_auto_backups: Maximum number of auto backups to keep.
            max_manual_backups: Maximum number of manual backups to keep.
        """

        # Anchor to project root so backups are predictable even if CWD changes.
        project_root = Path(__file__).resolve().parents[1]
        default_db = project_root / config.DB_FILE
        default_backup_root = project_root / self.DEFAULT_BACKUP_DIR

        self.db_path = Path(db_path) if db_path else default_db
        self.backup_dir = Path(backup_dir) if backup_dir else default_backup_root
        self.auto_backup_dir = self.backup_dir / "auto"
        self.manual_backup_dir = self.backup_dir / "manual"
        self.max_auto_backups = max_auto_backups
        self.max_manual_backups = max_manual_backups
        
        # Ensure backup directories exist
        self._ensure_directories()
        
        logger.info(f"BackupService initialized. DB: {self.db_path}, Backup dir: {self.backup_dir}")
    
    def _ensure_directories(self) -> None:
        """Tạo các thư mục backup nếu chưa tồn tại."""
        for directory in [self.backup_dir, self.auto_backup_dir, self.manual_backup_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")
    
    def _get_backup_dir_for_type(self, backup_type: BackupType) -> Path:
        """Lấy thư mục backup phù hợp với loại backup."""
        if backup_type == BackupType.AUTO:
            return self.auto_backup_dir
        return self.manual_backup_dir
    
    def _generate_backup_filename(self, backup_type: BackupType) -> str:
        """Tạo tên file backup với timestamp (bao gồm microseconds để tránh trùng)."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        type_prefix = backup_type.value
        return f"backup_{type_prefix}_{timestamp}{self.BACKUP_EXTENSION}"
    
    def _calculate_checksum(self, filepath: Path) -> str:
        """Tính SHA-256 checksum của file."""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _get_db_version(self, db_path: Path) -> str:
        """Lấy version của database schema."""
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            # Check user_version pragma
            cursor.execute("PRAGMA user_version")
            version = cursor.fetchone()[0]
            conn.close()
            return str(version) if version else "5.0"
        except sqlite3.Error:
            return "unknown"
    
    def _get_records_summary(self, db_path: Path) -> Dict[str, int]:
        """Lấy tóm tắt số lượng records trong các bảng chính."""
        summary = {}
        tables_to_check = ['vehicles', 'dispatches', 'locations', 'drivers', 'transport_vehicles']
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            for table in tables_to_check:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    summary[table] = count
                except sqlite3.OperationalError:
                    # Table doesn't exist
                    summary[table] = 0
            
            conn.close()
        except sqlite3.Error as e:
            logger.warning(f"Could not get records summary: {e}")
        
        return summary
    
    def _get_tables_count(self, db_path: Path) -> int:
        """Đếm số lượng tables trong database."""
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except sqlite3.Error:
            return 0
    
    def _create_metadata(
        self,
        backup_path: Path,
        backup_type: BackupType,
    ) -> BackupMetadata:
        """Tạo metadata cho backup file."""
        backup_id = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + hashlib.md5(
            str(backup_path).encode()
        ).hexdigest()[:8]
        
        return BackupMetadata(
            backup_id=backup_id,
            filename=backup_path.name,
            filepath=str(backup_path.absolute()),
            backup_type=backup_type.value,
            created_at=datetime.now().isoformat(),
            db_version=self._get_db_version(backup_path),
            app_version=config.APP_VERSION,
            file_size=backup_path.stat().st_size,
            checksum=self._calculate_checksum(backup_path),
            tables_count=self._get_tables_count(backup_path),
            records_summary=self._get_records_summary(backup_path),
        )
    
    def _save_metadata(self, metadata: BackupMetadata, backup_path: Path) -> None:
        """Lưu metadata vào file JSON."""
        metadata_path = backup_path.with_suffix(self.METADATA_EXTENSION)
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata.to_dict(), f, indent=2, ensure_ascii=False)
        logger.debug(f"Saved metadata to: {metadata_path}")
    
    def _load_metadata(self, backup_path: Path) -> Optional[BackupMetadata]:
        """Load metadata từ file JSON."""
        metadata_path = backup_path.with_suffix(self.METADATA_EXTENSION)
        if not metadata_path.exists():
            return None
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return BackupMetadata.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Could not load metadata from {metadata_path}: {e}")
            return None
    
    def create_backup(
        self,
        backup_type: BackupType = BackupType.MANUAL,
        description: Optional[str] = None,
    ) -> BackupMetadata:
        """
        Tạo backup mới.
        
        Args:
            backup_type: Loại backup (manual, auto, pre_archive).
            description: Mô tả tùy chọn cho backup.
        
        Returns:
            BackupMetadata: Thông tin về backup đã tạo.
        
        Raises:
            BackupCreationError: Nếu không thể tạo backup.
            BackupNotFoundError: Nếu database source không tồn tại.
        """
        if not self.db_path.exists():
            raise BackupNotFoundError(f"Database không tồn tại: {self.db_path}")
        
        backup_dir = self._get_backup_dir_for_type(backup_type)
        backup_filename = self._generate_backup_filename(backup_type)
        backup_path = backup_dir / backup_filename
        
        try:
            logger.info(f"Creating {backup_type.value} backup: {backup_path}")
            
            # Use SQLite backup API for consistency
            source_conn = sqlite3.connect(str(self.db_path))
            dest_conn = sqlite3.connect(str(backup_path))
            
            with dest_conn:
                source_conn.backup(dest_conn)
            
            source_conn.close()
            dest_conn.close()
            
            # Create and save metadata
            metadata = self._create_metadata(backup_path, backup_type)
            self._save_metadata(metadata, backup_path)
            
            logger.info(
                f"Backup created successfully: {backup_path} "
                f"(size: {metadata.file_size} bytes, checksum: {metadata.checksum[:16]}...)"
            )
            
            # Cleanup old backups
            self._cleanup_old_backups(backup_type)
            
            return metadata
            
        except sqlite3.Error as e:
            # Clean up failed backup
            if backup_path.exists():
                backup_path.unlink()
            raise BackupCreationError(f"Lỗi khi tạo backup: {e}") from e
        except OSError as e:
            raise BackupCreationError(f"Lỗi hệ thống khi tạo backup: {e}") from e
    
    def verify_backup(self, backup_path: Path) -> Tuple[bool, str]:
        """
        Kiểm tra tính toàn vẹn của backup file.
        
        Args:
            backup_path: Đường dẫn đến file backup.
        
        Returns:
            Tuple[bool, str]: (is_valid, message)
        """
        backup_path = Path(backup_path)
        
        if not backup_path.exists():
            return False, f"Backup file không tồn tại: {backup_path}"
        
        # Check if it's a valid SQLite database
        try:
            conn = sqlite3.connect(str(backup_path))
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            conn.close()
            
            if result != "ok":
                return False, f"Database integrity check failed: {result}"
        except sqlite3.Error as e:
            return False, f"Không thể đọc backup file: {e}"
        
        # Verify checksum if metadata exists
        metadata = self._load_metadata(backup_path)
        if metadata:
            current_checksum = self._calculate_checksum(backup_path)
            if current_checksum != metadata.checksum:
                return False, "Checksum không khớp - file có thể đã bị thay đổi"
        
        # Verify required tables exist
        required_tables = ['vehicles', 'dispatches', 'locations']
        try:
            conn = sqlite3.connect(str(backup_path))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = {row[0] for row in cursor.fetchall()}
            conn.close()
            
            missing_tables = set(required_tables) - existing_tables
            if missing_tables:
                return False, f"Thiếu các bảng quan trọng: {', '.join(missing_tables)}"
        except sqlite3.Error as e:
            return False, f"Lỗi khi kiểm tra schema: {e}"
        
        return True, "Backup hợp lệ"
    
    def restore_backup(
        self,
        backup_path: Path,
        create_pre_restore_backup: bool = True,
    ) -> bool:
        """
        Khôi phục database từ backup.
        
        Args:
            backup_path: Đường dẫn đến file backup.
            create_pre_restore_backup: Tạo backup trước khi restore.
        
        Returns:
            bool: True nếu restore thành công.
        
        Raises:
            RestoreError: Nếu không thể restore.
            BackupCorruptedError: Nếu backup file bị lỗi.
        """
        backup_path = Path(backup_path)
        
        # Verify backup first
        is_valid, message = self.verify_backup(backup_path)
        if not is_valid:
            raise BackupCorruptedError(f"Backup không hợp lệ: {message}")
        
        # Create pre-restore backup for safety
        pre_restore_backup = None
        if create_pre_restore_backup and self.db_path.exists():
            try:
                logger.info("Creating pre-restore backup...")
                pre_restore_backup = self.create_backup(
                    backup_type=BackupType.PRE_MIGRATION,
                )
            except BackupError as e:
                logger.warning(f"Could not create pre-restore backup: {e}")
        
        try:
            logger.info(f"Restoring database from: {backup_path}")
            
            # Close any existing connections (important!)
            # Note: In production, you'd need to ensure all connections are closed
            
            # Use SQLite backup API for restore
            source_conn = sqlite3.connect(str(backup_path))
            dest_conn = sqlite3.connect(str(self.db_path))
            
            with dest_conn:
                source_conn.backup(dest_conn)
            
            source_conn.close()
            dest_conn.close()
            
            logger.info("Database restored successfully")
            return True
            
        except sqlite3.Error as e:
            # Attempt to restore from pre-restore backup
            if pre_restore_backup:
                logger.error(f"Restore failed, attempting rollback: {e}")
                try:
                    shutil.copy2(pre_restore_backup.filepath, str(self.db_path))
                    logger.info("Rollback successful")
                except OSError as rollback_error:
                    logger.critical(f"Rollback also failed: {rollback_error}")
            raise RestoreError(f"Lỗi khi restore: {e}") from e
    
    def list_backups(
        self,
        backup_type: Optional[BackupType] = None,
        limit: int = 50,
    ) -> List[BackupMetadata]:
        """
        Liệt kê các backup đã tạo.
        
        Args:
            backup_type: Lọc theo loại backup (None = tất cả).
            limit: Số lượng tối đa trả về.
        
        Returns:
            List[BackupMetadata]: Danh sách backup, mới nhất trước.
        """
        backups = []
        
        dirs_to_search = []
        if backup_type is None:
            dirs_to_search = [self.auto_backup_dir, self.manual_backup_dir]
        else:
            dirs_to_search = [self._get_backup_dir_for_type(backup_type)]
        
        for search_dir in dirs_to_search:
            if not search_dir.exists():
                continue
            
            for backup_file in search_dir.glob(f"*{self.BACKUP_EXTENSION}"):
                metadata = self._load_metadata(backup_file)
                if metadata:
                    backups.append(metadata)
                else:
                    # Create minimal metadata for backups without metadata file
                    backups.append(BackupMetadata(
                        backup_id=backup_file.stem,
                        filename=backup_file.name,
                        filepath=str(backup_file.absolute()),
                        backup_type="unknown",
                        created_at=datetime.fromtimestamp(
                            backup_file.stat().st_mtime
                        ).isoformat(),
                        db_version="unknown",
                        app_version="unknown",
                        file_size=backup_file.stat().st_size,
                        checksum="",
                        tables_count=0,
                        records_summary={},
                    ))
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x.created_at, reverse=True)
        
        return backups[:limit]
    
    def delete_backup(self, backup_path: Path) -> bool:
        """
        Xóa một backup.
        
        Args:
            backup_path: Đường dẫn đến file backup.
        
        Returns:
            bool: True nếu xóa thành công.
        """
        backup_path = Path(backup_path)
        metadata_path = backup_path.with_suffix(self.METADATA_EXTENSION)
        
        try:
            if backup_path.exists():
                backup_path.unlink()
                logger.info(f"Deleted backup: {backup_path}")
            
            if metadata_path.exists():
                metadata_path.unlink()
                logger.debug(f"Deleted metadata: {metadata_path}")
            
            return True
        except OSError as e:
            logger.error(f"Could not delete backup {backup_path}: {e}")
            return False
    
    def _cleanup_old_backups(self, backup_type: BackupType) -> int:
        """
        Xóa các backup cũ vượt quá giới hạn.
        
        Args:
            backup_type: Loại backup để cleanup.
        
        Returns:
            int: Số lượng backup đã xóa.
        """
        if backup_type == BackupType.AUTO:
            max_backups = self.max_auto_backups
        else:
            max_backups = self.max_manual_backups
        
        backups = self.list_backups(backup_type=backup_type)
        
        if len(backups) <= max_backups:
            return 0
        
        deleted_count = 0
        backups_to_delete = backups[max_backups:]
        
        for backup in backups_to_delete:
            if self.delete_backup(Path(backup.filepath)):
                deleted_count += 1
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old {backup_type.value} backup(s)")
        
        return deleted_count
    
    def get_backup_stats(self) -> Dict[str, Any]:
        """
        Lấy thống kê về backup.
        
        Returns:
            Dict với thống kê backup.
        """
        auto_backups = self.list_backups(BackupType.AUTO)
        manual_backups = self.list_backups(BackupType.MANUAL)
        
        total_size = sum(b.file_size for b in auto_backups + manual_backups)
        
        return {
            "auto_backup_count": len(auto_backups),
            "manual_backup_count": len(manual_backups),
            "total_backup_count": len(auto_backups) + len(manual_backups),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "latest_auto_backup": auto_backups[0].created_at if auto_backups else None,
            "latest_manual_backup": manual_backups[0].created_at if manual_backups else None,
            "backup_dir": str(self.backup_dir),
        }


# Convenience functions for quick access
_default_service: Optional[BackupService] = None


def get_backup_service() -> BackupService:
    """Lấy instance mặc định của BackupService."""
    global _default_service
    if _default_service is None:
        _default_service = BackupService()
    return _default_service


def create_manual_backup() -> BackupMetadata:
    """Tạo manual backup nhanh."""
    return get_backup_service().create_backup(BackupType.MANUAL)


def create_auto_backup() -> BackupMetadata:
    """Tạo auto backup nhanh."""
    return get_backup_service().create_backup(BackupType.AUTO)
