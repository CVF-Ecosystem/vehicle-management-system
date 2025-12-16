# database/base_manager.py
import sqlite3
import logging
import re

# Import config để lấy DB_FILE mặc định
# Nhưng cho phép override qua constructor parameter
import config

# Module-level logger
logger = logging.getLogger(__name__)

# Whitelist các tên bảng và cột hợp lệ trong hệ thống
VALID_TABLE_NAMES = {'vehicles', 'drivers', 'transport_vehicles', 'dispatches', 'locations'}
VALID_COLUMN_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

class BaseManager:
    """
    Lớp cơ sở quản lý kết nối duy nhất đến cơ sở dữ liệu và chịu trách nhiệm
    thiết lập toàn bộ schema (cấu trúc) của CSDL.
    
    Hỗ trợ:
    - Singleton pattern cho production (dùng config.DB_FILE)
    - Override db_path cho testing
    """
    _conn = None
    _db_path = None  # Track current DB path

    def __init__(self, db_path: str = None):
        """
        Khởi tạo BaseManager.
        
        Args:
            db_path: Đường dẫn tới database file. Nếu None, sử dụng config.DB_FILE.
                     Nếu khác với connection hiện tại, sẽ tạo connection mới.
        """
        # Xác định db_path sẽ sử dụng
        target_db = db_path if db_path is not None else config.DB_FILE
        
        # Nếu đã có connection và cùng db_path, reuse
        if BaseManager._conn is not None and BaseManager._db_path == target_db:
            self.conn = BaseManager._conn
            return
        
        # Đóng connection cũ nếu có (chuyển sang DB khác)
        if BaseManager._conn is not None:
            try:
                BaseManager._conn.close()
            except Exception:
                pass
            BaseManager._conn = None
        
        # Tạo connection mới
        logger.info(f"Đang tạo kết nối mới tới database: {target_db}")
        BaseManager._conn = sqlite3.connect(target_db, check_same_thread=False)
        BaseManager._conn.row_factory = sqlite3.Row
        BaseManager._db_path = target_db
        
        self.conn = BaseManager._conn
        
        self._setup_schema()

    def _setup_schema(self):
        """
        Hàm trung tâm để tạo và nâng cấp tất cả các bảng trong CSDL.
        """
        logger.info("Đang kiểm tra và cập nhật schema CSDL...")
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS drivers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    phone TEXT,
                    cccd TEXT,
                    notes TEXT,
                    is_active INTEGER DEFAULT 1
                )
            """)

            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS transport_vehicles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    license_plate TEXT NOT NULL UNIQUE,
                    type TEXT,
                    notes TEXT,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # === THAY ĐỔI: Đổi tên bảng 'shipments' -> 'dispatches' ===
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS dispatches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    driver_id INTEGER REFERENCES drivers(id),
                    transport_vehicle_id INTEGER REFERENCES transport_vehicles(id),
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    status TEXT NOT NULL
                )
            """)
            # =========================================================

            # === THAY ĐỔI: Đổi tên cột 'shipment_id' -> 'dispatch_id' ===
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS vehicles (
                    vin TEXT PRIMARY KEY,
                    owner TEXT NOT NULL,
                    vehicle_type TEXT,
                    date_in TEXT NOT NULL,
                    date_out TEXT,
                    status TEXT NOT NULL,
                    transport_vehicle TEXT,
                    driver_name TEXT,
                    is_active INTEGER DEFAULT 1,
                    dispatch_id INTEGER REFERENCES dispatches(id)
                )
            """)
            # ==========================================================

            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    block TEXT NOT NULL,
                    row TEXT NOT NULL,
                    slot INTEGER NOT NULL,
                    full_location_name TEXT UNIQUE NOT NULL,
                    is_occupied INTEGER DEFAULT 0 NOT NULL
                )
            """)
            
            # Nâng cấp Schema và Tạo Chỉ mục
            self._upgrade_table_if_needed('vehicles', 'location_id', 'INTEGER REFERENCES locations(id)')
            self._upgrade_table_if_needed('drivers', 'cccd', 'TEXT')
            self._create_indexes_if_needed()

        logger.info("Schema CSDL đã được cập nhật.")

    def _validate_identifier(self, name: str, identifier_type: str = "column") -> bool:
        """
        Validate SQL identifier (table name or column name) để ngăn chặn SQL injection.
        
        Args:
            name: Tên cần validate
            identifier_type: 'table' hoặc 'column'
        
        Returns:
            bool: True nếu hợp lệ
        
        Raises:
            ValueError: Nếu identifier không hợp lệ
        """
        if not name:
            raise ValueError(f"{identifier_type.capitalize()} name cannot be empty")
        
        if identifier_type == "table":
            if name.lower() not in VALID_TABLE_NAMES:
                raise ValueError(f"Invalid table name: '{name}'. Allowed tables: {VALID_TABLE_NAMES}")
        
        if not VALID_COLUMN_PATTERN.match(name):
            raise ValueError(f"Invalid {identifier_type} name: '{name}'. Must match pattern: [a-zA-Z_][a-zA-Z0-9_]*")
        
        return True

    def _upgrade_table_if_needed(self, table_name, column_name, column_definition):
        """Hàm tiện ích để thêm một cột vào bảng nếu nó chưa tồn tại."""
        # Validate inputs để ngăn chặn SQL injection
        try:
            self._validate_identifier(table_name, "table")
            self._validate_identifier(column_name, "column")
            # Validate column_definition chỉ chứa các keywords an toàn
            safe_definition_pattern = re.compile(r'^[A-Z\s]+(\s+REFERENCES\s+[a-zA-Z_]+\([a-zA-Z_]+\))?$', re.IGNORECASE)
            if not safe_definition_pattern.match(column_definition):
                raise ValueError(f"Invalid column definition: '{column_definition}'")
        except ValueError as e:
            logger.error(f"Security violation in _upgrade_table_if_needed: {e}")
            return
        
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [info[1] for info in cursor.fetchall()]
        if column_name not in columns:
            logger.info(f"Thêm cột '{column_name}' vào bảng '{table_name}'.")
            self.conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")

    def _create_indexes_if_needed(self):
        """Tạo các chỉ mục để tối ưu hóa truy vấn."""
        with self.conn:
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_vehicles_vin ON vehicles (vin)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_vehicles_owner ON vehicles (owner)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_vehicles_status ON vehicles (status)")
            
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_locations_full_name ON locations (full_location_name)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_locations_free ON locations (is_occupied, full_location_name)")

            self.conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_drivers_cccd ON drivers (cccd) WHERE cccd IS NOT NULL")

    def begin_transaction(self):
        """Bắt đầu một giao dịch CSDL."""
        self.conn.execute("BEGIN TRANSACTION")

    def commit_transaction(self):
        """Lưu lại các thay đổi trong giao dịch hiện tại."""
        self.conn.commit()

    def rollback_transaction(self):
        """Hủy bỏ các thay đổi trong giao dịch hiện tại."""
        self.conn.rollback()

    @staticmethod
    def get_new_connection(db_file_path):
        """Tạo và trả về một kết nối CSDL mới đến một file cụ thể."""
        try:
            conn = sqlite3.connect(db_file_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"Không thể tạo kết nối đến file CSDL: {db_file_path}. Lỗi: {e}")
            return None

    @staticmethod
    def close_connection():
        """Đóng kết nối CSDL khi ứng dụng thoát."""
        if BaseManager._conn:
            BaseManager._conn.close()
            BaseManager._conn = None
            logger.info("Đã đóng kết nối database.")
