# database/audit_repository.py
"""
Audit Repository - Quản lý audit logs cho hệ thống.

Ghi lại tất cả các thay đổi dữ liệu quan trọng:
- CREATE: Thêm mới record
- UPDATE: Cập nhật record  
- DELETE: Xóa record
- LOGIN/LOGOUT: Đăng nhập/đăng xuất (cho Phase 1B)
- BACKUP/RESTORE: Sao lưu/phục hồi dữ liệu
- ARCHIVE: Lưu trữ dữ liệu
- IMPORT/EXPORT: Nhập/xuất dữ liệu
"""

import sqlite3
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Union
from pathlib import Path

import config

logger = logging.getLogger(__name__)


class AuditAction(Enum):
    """Các loại hành động có thể ghi audit log."""
    # Data operations
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    
    # Authentication (Phase 1B)
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    LOGIN_FAILED = "LOGIN_FAILED"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    
    # Data management
    BACKUP = "BACKUP"
    RESTORE = "RESTORE"
    ARCHIVE = "ARCHIVE"
    IMPORT = "IMPORT"
    EXPORT = "EXPORT"
    
    # System operations
    SCHEMA_UPGRADE = "SCHEMA_UPGRADE"
    CONFIG_CHANGE = "CONFIG_CHANGE"


@dataclass
class AuditEntry:
    """
    Đại diện cho một bản ghi audit log.
    
    Attributes:
        id: ID của audit entry (auto-generated)
        user_id: ID của user thực hiện hành động (None nếu chưa có auth)
        username: Tên user (để hiển thị, không cần join)
        action: Loại hành động (AuditAction)
        table_name: Tên bảng bị ảnh hưởng (nếu có)
        record_id: ID của record bị ảnh hưởng
        old_value: Giá trị cũ (JSON string hoặc dict)
        new_value: Giá trị mới (JSON string hoặc dict)
        details: Chi tiết bổ sung (dict)
        ip_address: Địa chỉ IP của client (optional)
        created_at: Thời điểm thực hiện
    """
    id: Optional[int] = None
    user_id: Optional[int] = None
    username: str = "System"  # Default cho operations không cần đăng nhập
    action: AuditAction = AuditAction.CREATE
    table_name: Optional[str] = None
    record_id: Optional[str] = None
    old_value: Optional[Union[str, Dict]] = None
    new_value: Optional[Union[str, Dict]] = None
    details: Optional[Dict[str, Any]] = field(default_factory=dict)
    ip_address: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi sang dict để lưu database."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'action': self.action.value if isinstance(self.action, AuditAction) else self.action,
            'table_name': self.table_name,
            'record_id': self.record_id,
            'old_value': json.dumps(self.old_value) if isinstance(self.old_value, dict) else self.old_value,
            'new_value': json.dumps(self.new_value) if isinstance(self.new_value, dict) else self.new_value,
            'details': json.dumps(self.details) if self.details else None,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }
    
    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'AuditEntry':
        """Tạo AuditEntry từ database row."""
        # Parse old_value
        old_value = row['old_value']
        if old_value:
            try:
                old_value = json.loads(old_value)
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Parse new_value
        new_value = row['new_value']
        if new_value:
            try:
                new_value = json.loads(new_value)
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Parse details
        details = row['details']
        if details:
            try:
                details = json.loads(details)
            except (json.JSONDecodeError, TypeError):
                details = {}
        else:
            details = {}
        
        # Parse created_at
        created_at = row['created_at']
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                created_at = datetime.now()
        
        # Parse action
        action_str = row['action']
        try:
            action = AuditAction(action_str)
        except ValueError:
            action = AuditAction.CREATE  # fallback
        
        return cls(
            id=row['id'],
            user_id=row['user_id'],
            username=row['username'] or "System",
            action=action,
            table_name=row['table_name'],
            record_id=row['record_id'],
            old_value=old_value,
            new_value=new_value,
            details=details,
            ip_address=row['ip_address'],
            created_at=created_at
        )


@dataclass
class AuditFilter:
    """Filter criteria cho việc query audit logs."""
    user_id: Optional[int] = None
    username: Optional[str] = None
    action: Optional[AuditAction] = None
    actions: Optional[List[AuditAction]] = None  # Cho phép filter nhiều actions
    table_name: Optional[str] = None
    record_id: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search_text: Optional[str] = None  # Search trong old_value, new_value, details
    limit: int = 100
    offset: int = 0


class AuditRepository:
    """
    Repository quản lý audit logs.
    
    Cung cấp các phương thức để:
    - Ghi audit log mới
    - Query audit logs với các filter
    - Thống kê audit logs
    - Export audit logs
    """
    
    # Table name
    TABLE_NAME = "audit_logs"
    
    # Default limits
    DEFAULT_QUERY_LIMIT = 100
    MAX_QUERY_LIMIT = 1000
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Khởi tạo AuditRepository.
        
        Args:
            db_path: Đường dẫn tới database. Nếu None, sử dụng config.DB_FILE.
        """
        default_db = getattr(config, "AUDIT_DB_FILE", None) or config.DB_FILE
        self.db_path = db_path or default_db
        self._ensure_table_exists()
        logger.info(f"AuditRepository initialized. DB: {self.db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Tạo connection mới đến database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA cache_size = -5000")  # 5MB cache
        except sqlite3.Error:
            pass
        return conn
    
    def _ensure_table_exists(self):
        """Tạo bảng audit_logs nếu chưa tồn tại."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT DEFAULT 'System',
                    action TEXT NOT NULL,
                    table_name TEXT,
                    record_id TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    details TEXT,
                    ip_address TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            
            # Tạo indexes để tăng tốc query
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_action 
                ON audit_logs(action)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_table 
                ON audit_logs(table_name)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_created_at 
                ON audit_logs(created_at)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_user 
                ON audit_logs(user_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_record 
                ON audit_logs(table_name, record_id)
            """)
            
            conn.commit()
    
    def log(
        self,
        action: AuditAction,
        table_name: Optional[str] = None,
        record_id: Optional[str] = None,
        old_value: Optional[Union[str, Dict]] = None,
        new_value: Optional[Union[str, Dict]] = None,
        user_id: Optional[int] = None,
        username: str = "System",
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> int:
        """
        Ghi một audit log entry.
        
        Args:
            action: Loại hành động
            table_name: Tên bảng bị ảnh hưởng
            record_id: ID của record
            old_value: Giá trị cũ (dict sẽ được convert sang JSON)
            new_value: Giá trị mới (dict sẽ được convert sang JSON)
            user_id: ID của user thực hiện
            username: Tên user
            details: Chi tiết bổ sung
            ip_address: Địa chỉ IP
        
        Returns:
            int: ID của audit entry vừa tạo
        """
        entry = AuditEntry(
            user_id=user_id,
            username=username,
            action=action,
            table_name=table_name,
            record_id=record_id,
            old_value=old_value,
            new_value=new_value,
            details=details or {},
            ip_address=ip_address,
            created_at=datetime.now()
        )
        
        return self.add(entry)
    
    def add(self, entry: AuditEntry) -> int:
        """
        Thêm một AuditEntry vào database.
        
        Args:
            entry: AuditEntry object
        
        Returns:
            int: ID của entry vừa tạo
        """
        data = entry.to_dict()
        
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO audit_logs 
                (user_id, username, action, table_name, record_id, 
                 old_value, new_value, details, ip_address, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['user_id'],
                data['username'],
                data['action'],
                data['table_name'],
                data['record_id'],
                data['old_value'],
                data['new_value'],
                data['details'],
                data['ip_address'],
                data['created_at']
            ))
            conn.commit()
            entry_id = cursor.lastrowid
            
        logger.debug(
            f"Audit log added: id={entry_id}, action={data['action']}, "
            f"table={data['table_name']}, record={data['record_id']}"
        )
        return entry_id
    
    def get_by_id(self, entry_id: int) -> Optional[AuditEntry]:
        """
        Lấy một audit entry theo ID.
        
        Args:
            entry_id: ID của entry
        
        Returns:
            AuditEntry hoặc None nếu không tìm thấy
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM audit_logs WHERE id = ?",
                (entry_id,)
            )
            row = cursor.fetchone()
            
        if row:
            return AuditEntry.from_row(row)
        return None
    
    def query(self, filter_criteria: Optional[AuditFilter] = None) -> List[AuditEntry]:
        """
        Query audit logs với các filter.
        
        Args:
            filter_criteria: AuditFilter object hoặc None để lấy tất cả
        
        Returns:
            List[AuditEntry]: Danh sách các audit entries
        """
        if filter_criteria is None:
            filter_criteria = AuditFilter()
        
        # Build WHERE clause
        conditions = []
        params = []
        
        if filter_criteria.user_id is not None:
            conditions.append("user_id = ?")
            params.append(filter_criteria.user_id)
        
        if filter_criteria.username:
            conditions.append("username LIKE ?")
            params.append(f"%{filter_criteria.username}%")
        
        if filter_criteria.action:
            conditions.append("action = ?")
            params.append(filter_criteria.action.value)
        
        if filter_criteria.actions:
            placeholders = ",".join(["?" for _ in filter_criteria.actions])
            conditions.append(f"action IN ({placeholders})")
            params.extend([a.value for a in filter_criteria.actions])
        
        if filter_criteria.table_name:
            conditions.append("table_name = ?")
            params.append(filter_criteria.table_name)
        
        if filter_criteria.record_id:
            conditions.append("record_id = ?")
            params.append(filter_criteria.record_id)
        
        if filter_criteria.date_from:
            conditions.append("created_at >= ?")
            params.append(filter_criteria.date_from.isoformat())
        
        if filter_criteria.date_to:
            conditions.append("created_at <= ?")
            params.append(filter_criteria.date_to.isoformat())
        
        if filter_criteria.search_text:
            search_pattern = f"%{filter_criteria.search_text}%"
            conditions.append("""
                (old_value LIKE ? OR new_value LIKE ? OR details LIKE ?)
            """)
            params.extend([search_pattern, search_pattern, search_pattern])
        
        # Build query
        query = "SELECT * FROM audit_logs"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY created_at DESC"
        
        # Apply limits
        limit = min(filter_criteria.limit, self.MAX_QUERY_LIMIT)
        query += f" LIMIT {limit} OFFSET {filter_criteria.offset}"
        
        # Execute
        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
        
        return [AuditEntry.from_row(row) for row in rows]
    
    def get_recent(self, limit: int = 50) -> List[AuditEntry]:
        """Lấy các audit entries gần đây nhất."""
        return self.query(AuditFilter(limit=limit))
    
    def get_for_record(
        self, 
        table_name: str, 
        record_id: str,
        limit: int = 100
    ) -> List[AuditEntry]:
        """Lấy tất cả audit entries cho một record cụ thể."""
        return self.query(AuditFilter(
            table_name=table_name,
            record_id=record_id,
            limit=limit
        ))
    
    def get_for_user(
        self, 
        user_id: int,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEntry]:
        """Lấy tất cả audit entries của một user."""
        return self.query(AuditFilter(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            limit=limit
        ))
    
    def get_by_action(
        self,
        action: AuditAction,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEntry]:
        """Lấy audit entries theo loại action."""
        return self.query(AuditFilter(
            action=action,
            date_from=date_from,
            date_to=date_to,
            limit=limit
        ))
    
    def count(self, filter_criteria: Optional[AuditFilter] = None) -> int:
        """
        Đếm số lượng audit entries theo filter.
        
        Args:
            filter_criteria: AuditFilter object
        
        Returns:
            int: Số lượng entries
        """
        if filter_criteria is None:
            filter_criteria = AuditFilter()
        
        # Build WHERE clause (similar to query)
        conditions = []
        params = []
        
        if filter_criteria.user_id is not None:
            conditions.append("user_id = ?")
            params.append(filter_criteria.user_id)
        
        if filter_criteria.action:
            conditions.append("action = ?")
            params.append(filter_criteria.action.value)
        
        if filter_criteria.actions:
            placeholders = ",".join(["?" for _ in filter_criteria.actions])
            conditions.append(f"action IN ({placeholders})")
            params.extend([a.value for a in filter_criteria.actions])
        
        if filter_criteria.table_name:
            conditions.append("table_name = ?")
            params.append(filter_criteria.table_name)
        
        if filter_criteria.date_from:
            conditions.append("created_at >= ?")
            params.append(filter_criteria.date_from.isoformat())
        
        if filter_criteria.date_to:
            conditions.append("created_at <= ?")
            params.append(filter_criteria.date_to.isoformat())
        
        # Build query
        query = "SELECT COUNT(*) FROM audit_logs"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            result = cursor.fetchone()
        
        return result[0] if result else 0
    
    def get_statistics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Lấy thống kê audit logs.
        
        Args:
            date_from: Ngày bắt đầu
            date_to: Ngày kết thúc
        
        Returns:
            Dict với các thống kê:
            - total_entries: Tổng số entries
            - by_action: Dict[action, count]
            - by_table: Dict[table_name, count]
            - by_user: Dict[username, count]
            - recent_activity: List[Dict] (10 entries gần nhất)
        """
        conditions = []
        params = []
        
        if date_from:
            conditions.append("created_at >= ?")
            params.append(date_from.isoformat())
        
        if date_to:
            conditions.append("created_at <= ?")
            params.append(date_to.isoformat())
        
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        with self._get_connection() as conn:
            # Total count
            total = conn.execute(
                f"SELECT COUNT(*) FROM audit_logs{where_clause}",
                params
            ).fetchone()[0]
            
            # By action
            by_action = {}
            cursor = conn.execute(
                f"SELECT action, COUNT(*) as count FROM audit_logs{where_clause} GROUP BY action",
                params
            )
            for row in cursor.fetchall():
                by_action[row['action']] = row['count']
            
            # By table
            by_table = {}
            cursor = conn.execute(
                f"SELECT table_name, COUNT(*) as count FROM audit_logs{where_clause} "
                f"WHERE table_name IS NOT NULL GROUP BY table_name",
                params
            )
            for row in cursor.fetchall():
                by_table[row['table_name']] = row['count']
            
            # By user
            by_user = {}
            cursor = conn.execute(
                f"SELECT username, COUNT(*) as count FROM audit_logs{where_clause} GROUP BY username",
                params
            )
            for row in cursor.fetchall():
                by_user[row['username']] = row['count']
            
            # Recent activity
            recent_query = f"SELECT * FROM audit_logs{where_clause} ORDER BY created_at DESC LIMIT 10"
            cursor = conn.execute(recent_query, params)
            recent = [AuditEntry.from_row(row).to_dict() for row in cursor.fetchall()]
        
        return {
            'total_entries': total,
            'by_action': by_action,
            'by_table': by_table,
            'by_user': by_user,
            'recent_activity': recent
        }
    
    def cleanup_old_entries(self, days_to_keep: int = 365) -> int:
        """
        Xóa vĩnh viễn các audit entries cũ hơn số ngày chỉ định.

        Lưu ý: Dùng archive_old_logs() nếu muốn giữ lại records trong bảng archive
        thay vì xóa hoàn toàn.

        Args:
            days_to_keep: Số ngày giữ lại (mặc định 365)

        Returns:
            int: Số entries đã xóa
        """
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        with self._get_connection() as conn:
            count_result = conn.execute(
                "SELECT COUNT(*) FROM audit_logs WHERE created_at < ?",
                (cutoff_date.isoformat(),)
            ).fetchone()
            count_to_delete = count_result[0] if count_result else 0

            if count_to_delete > 0:
                conn.execute(
                    "DELETE FROM audit_logs WHERE created_at < ?",
                    (cutoff_date.isoformat(),)
                )
                conn.commit()
                logger.info(f"Cleaned up {count_to_delete} old audit entries (older than {days_to_keep} days)")

        return count_to_delete

    def _ensure_archive_table(self, conn: sqlite3.Connection) -> None:
        """Tạo bảng audit_logs_archive nếu chưa tồn tại (cùng schema với audit_logs)."""
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

    def archive_old_logs(self, before_days: int = 365) -> int:
        """
        Di chuyển các audit entries cũ hơn before_days ngày sang bảng audit_logs_archive.

        Idempotent: chạy lại sẽ SKIP records đã archive (theo id).

        Args:
            before_days: Số ngày; entries cũ hơn sẽ được archive (mặc định 365)

        Returns:
            int: Số entries đã được archive
        """
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=before_days)
        archived_at = datetime.now().isoformat()

        with self._get_connection() as conn:
            self._ensure_archive_table(conn)

            count_result = conn.execute(
                "SELECT COUNT(*) FROM audit_logs WHERE created_at < ?",
                (cutoff_date.isoformat(),)
            ).fetchone()
            count_to_archive = count_result[0] if count_result else 0

            if count_to_archive == 0:
                logger.info(f"archive_old_logs: không có entries nào cũ hơn {before_days} ngày.")
                return 0

            # Copy sang archive (IGNORE để idempotent)
            conn.execute("""
                INSERT OR IGNORE INTO audit_logs_archive
                    (id, user_id, username, action, table_name, record_id,
                     old_value, new_value, details, ip_address, created_at, archived_at)
                SELECT id, user_id, username, action, table_name, record_id,
                       old_value, new_value, details, ip_address, created_at, ?
                FROM audit_logs
                WHERE created_at < ?
            """, (archived_at, cutoff_date.isoformat()))

            # Xóa khỏi bảng chính sau khi đã copy
            conn.execute(
                "DELETE FROM audit_logs WHERE created_at < ?",
                (cutoff_date.isoformat(),)
            )
            conn.commit()

        logger.info(f"archive_old_logs: đã archive {count_to_archive} entries (cũ hơn {before_days} ngày).")
        return count_to_archive

    def get_log_stats(self) -> Dict[str, Any]:
        """
        Trả về thống kê tổng quan về audit logs.

        Returns:
            dict với các keys:
                - total_records: tổng số entries trong bảng chính
                - oldest_record: ISO timestamp entry cũ nhất (None nếu rỗng)
                - newest_record: ISO timestamp entry mới nhất (None nếu rỗng)
                - archived_records: tổng số entries trong bảng archive
                - size_estimate_bytes: ước tính kích thước (dùng page_count * page_size)
        """
        with self._get_connection() as conn:
            total_result = conn.execute("SELECT COUNT(*) FROM audit_logs").fetchone()
            total_records = total_result[0] if total_result else 0

            oldest_result = conn.execute(
                "SELECT MIN(created_at) FROM audit_logs"
            ).fetchone()
            oldest_record = oldest_result[0] if oldest_result else None

            newest_result = conn.execute(
                "SELECT MAX(created_at) FROM audit_logs"
            ).fetchone()
            newest_record = newest_result[0] if newest_result else None

            # Archive table stats (create if missing to avoid error)
            self._ensure_archive_table(conn)
            archived_result = conn.execute(
                "SELECT COUNT(*) FROM audit_logs_archive"
            ).fetchone()
            archived_records = archived_result[0] if archived_result else 0

            # Ước tính kích thước DB (page_count * page_size)
            page_count = conn.execute("PRAGMA page_count").fetchone()[0]
            page_size = conn.execute("PRAGMA page_size").fetchone()[0]
            size_estimate_bytes = page_count * page_size

        return {
            "total_records": total_records,
            "oldest_record": oldest_record,
            "newest_record": newest_record,
            "archived_records": archived_records,
            "size_estimate_bytes": size_estimate_bytes,
        }
    
    def export_to_json(
        self,
        filepath: str,
        filter_criteria: Optional[AuditFilter] = None
    ) -> int:
        """
        Export audit logs ra file JSON.
        
        Args:
            filepath: Đường dẫn file JSON
            filter_criteria: Filter (optional)
        
        Returns:
            int: Số entries đã export
        """
        # Query all matching entries (increase limit for export)
        if filter_criteria is None:
            filter_criteria = AuditFilter()
        filter_criteria.limit = self.MAX_QUERY_LIMIT
        
        entries = self.query(filter_criteria)
        
        # Convert to JSON-serializable format
        export_data = {
            'exported_at': datetime.now().isoformat(),
            'total_entries': len(entries),
            'entries': [entry.to_dict() for entry in entries]
        }
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Exported {len(entries)} audit entries to {filepath}")
        return len(entries)


# === Convenience functions for logging audit entries ===

# Module-level instance (lazy initialization)
_audit_repo: Optional[AuditRepository] = None


def get_audit_repository(db_path: Optional[str] = None) -> AuditRepository:
    """
    Lấy instance của AuditRepository (singleton pattern).
    
    Args:
        db_path: Đường dẫn database (optional, chỉ cần cho lần đầu)
    
    Returns:
        AuditRepository instance
    """
    global _audit_repo
    if _audit_repo is None:
        _audit_repo = AuditRepository(db_path)
    return _audit_repo


def log_audit(
    action: AuditAction,
    table_name: Optional[str] = None,
    record_id: Optional[str] = None,
    old_value: Optional[Union[str, Dict]] = None,
    new_value: Optional[Union[str, Dict]] = None,
    user_id: Optional[int] = None,
    username: str = "System",
    details: Optional[Dict[str, Any]] = None
) -> int:
    """
    Convenience function để log audit entry.
    
    Args:
        action: Loại hành động
        table_name: Tên bảng
        record_id: ID record
        old_value: Giá trị cũ
        new_value: Giá trị mới
        username: Tên user
        details: Chi tiết bổ sung
    
    Returns:
        int: ID của audit entry
    """
    # Best-effort: bind audit entry to the currently logged-in user.
    # Keep this import local to avoid hard dependency/circular imports.
    if (not user_id) or (not username) or username == "System":
        try:
            from auth.auth_manager import AuthManager  # local import

            auth = AuthManager.get_instance()
            if not user_id:
                user_id = auth.get_current_user_id()
            if (not username) or username == "System":
                username = auth.get_current_username() or username
        except Exception:
            pass

    repo = get_audit_repository()
    return repo.log(
        action=action,
        table_name=table_name,
        record_id=record_id,
        old_value=old_value,
        new_value=new_value,
        user_id=user_id,
        username=username,
        details=details
    )


def log_create(
    table_name: str,
    record_id: str,
    new_value: Dict,
    username: str = "System"
) -> int:
    """Log một CREATE operation."""
    return log_audit(
        action=AuditAction.CREATE,
        table_name=table_name,
        record_id=record_id,
        new_value=new_value,
        username=username
    )


def log_update(
    table_name: str,
    record_id: str,
    old_value: Dict,
    new_value: Dict,
    username: str = "System"
) -> int:
    """Log một UPDATE operation."""
    return log_audit(
        action=AuditAction.UPDATE,
        table_name=table_name,
        record_id=record_id,
        old_value=old_value,
        new_value=new_value,
        username=username
    )


def log_delete(
    table_name: str,
    record_id: str,
    old_value: Dict,
    username: str = "System"
) -> int:
    """Log một DELETE operation."""
    return log_audit(
        action=AuditAction.DELETE,
        table_name=table_name,
        record_id=record_id,
        old_value=old_value,
        username=username
    )


def log_backup(
    backup_id: str,
    backup_type: str,
    filepath: str,
    username: str = "System"
) -> int:
    """Log một BACKUP operation."""
    return log_audit(
        action=AuditAction.BACKUP,
        details={
            'backup_id': backup_id,
            'backup_type': backup_type,
            'filepath': filepath
        },
        username=username
    )


def log_restore(
    backup_id: str,
    filepath: str,
    username: str = "System"
) -> int:
    """Log một RESTORE operation."""
    return log_audit(
        action=AuditAction.RESTORE,
        details={
            'backup_id': backup_id,
            'filepath': filepath
        },
        username=username
    )
