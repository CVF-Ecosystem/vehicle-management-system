# database/migrations/migration_runner.py
"""
Schema migration runner.

Đảm bảo DB luôn ở schema version mới nhất khi app khởi động.
Mỗi migration chạy trong transaction — rollback tự động nếu lỗi.

Cách thêm migration mới:
1. Tăng CURRENT_VERSION lên 1.
2. Thêm function migrate_vN_to_vM(conn) vào phần MIGRATION FUNCTIONS.
3. Đăng ký vào MIGRATIONS dict.
"""

from __future__ import annotations

import logging
import sqlite3
from typing import Callable, Dict

logger = logging.getLogger(__name__)

# === Phiên bản schema hiện tại ===
CURRENT_VERSION: int = 2

# === MIGRATION FUNCTIONS ===

def _migrate_v0_to_v1(conn: sqlite3.Connection) -> None:
    """
    Version 1: Thêm cột must_change_password vào bảng users.
    Cần thiết cho TASK-SEC-01 (bắt buộc đổi mật khẩu lần đầu đăng nhập).
    """
    cursor = conn.execute("PRAGMA table_info(users)")
    existing_cols = {row[1] for row in cursor.fetchall()}
    if "must_change_password" not in existing_cols:
        conn.execute(
            "ALTER TABLE users ADD COLUMN must_change_password INTEGER NOT NULL DEFAULT 0"
        )
        logger.info("Migration v1: Đã thêm cột users.must_change_password")
    else:
        logger.debug("Migration v1: users.must_change_password đã tồn tại, bỏ qua.")


def _migrate_v1_to_v2(conn: sqlite3.Connection) -> None:
    """
    Version 2: Tạo bảng audit_logs_archive cho TASK-CQ-03.
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs_archive (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            username TEXT DEFAULT 'System',
            action TEXT NOT NULL,
            table_name TEXT,
            record_id TEXT,
            old_value TEXT,
            new_value TEXT,
            details TEXT,
            ip_address TEXT,
            created_at TEXT NOT NULL,
            archived_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_archive_audit_created_at
        ON audit_logs_archive(created_at)
    """)
    logger.info("Migration v2: Đã tạo bảng audit_logs_archive")


# === REGISTRY ===
# Key: from_version (int), Value: migration function
MIGRATIONS: Dict[int, Callable[[sqlite3.Connection], None]] = {
    0: _migrate_v0_to_v1,
    1: _migrate_v1_to_v2,
}


class MigrationRunner:
    """
    Chạy các migration cần thiết để đưa DB lên CURRENT_VERSION.
    """

    META_TABLE = "_schema_meta"

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def _ensure_meta_table(self) -> None:
        """Create _schema_meta if it does not exist. Uses its own transaction."""
        with self.conn:
            self.conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.META_TABLE} (
                    key   TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

    def get_current_version(self) -> int:
        """Đọc schema_version từ _schema_meta. Trả về 0 nếu chưa có."""
        self._ensure_meta_table()
        row = self.conn.execute(
            f"SELECT value FROM {self.META_TABLE} WHERE key = 'schema_version'"
        ).fetchone()
        if row is None:
            return 0
        try:
            return int(row[0])
        except (TypeError, ValueError):
            return 0

    def _set_version(self, version: int) -> None:
        """Update schema_version in the meta table.

        Must be called inside an active transaction managed by the caller.
        Does NOT commit — the caller is responsible for committing.
        """
        self.conn.execute(
            f"INSERT OR REPLACE INTO {self.META_TABLE} (key, value) VALUES ('schema_version', ?)",
            (str(version),),
        )

    def run(self) -> int:
        """
        Chạy tất cả migration còn thiếu theo thứ tự.

        Returns:
            Số migration đã chạy thành công.
        """
        current = self.get_current_version()
        ran = 0

        if current >= CURRENT_VERSION:
            logger.debug(f"Schema đã ở version {current}, không cần migrate.")
            return 0

        for from_ver in range(current, CURRENT_VERSION):
            migrate_fn = MIGRATIONS.get(from_ver)
            if migrate_fn is None:
                logger.warning(f"Không tìm thấy migration từ v{from_ver} → v{from_ver + 1}, bỏ qua.")
                with self.conn:
                    self._set_version(from_ver + 1)
                ran += 1
                continue

            logger.info(f"Đang chạy migration v{from_ver} → v{from_ver + 1}: {migrate_fn.__name__}")
            try:
                with self.conn:
                    migrate_fn(self.conn)
                    self._set_version(from_ver + 1)
                logger.info(f"Migration v{from_ver} → v{from_ver + 1} hoàn thành.")
                ran += 1
            except Exception as exc:
                logger.error(
                    f"Migration v{from_ver} → v{from_ver + 1} thất bại, rollback: {exc}",
                    exc_info=True,
                )
                raise RuntimeError(
                    f"Schema migration từ v{from_ver} sang v{from_ver + 1} thất bại: {exc}"
                ) from exc

        return ran


def run_migrations(conn: sqlite3.Connection) -> int:
    """Convenience function: tạo MigrationRunner và chạy."""
    return MigrationRunner(conn).run()
