# database/location_manager.py
import sqlite3
import logging
from typing import Optional

logger = logging.getLogger(__name__)

from .base_manager import BaseManager

class LocationManager(BaseManager):
    """
    Quản lý tất cả các hoạt động liên quan đến bảng 'locations'.
    Cung cấp một giao diện để thêm, truy vấn và cập nhật trạng thái vị trí.
    """
    def __init__(self, db_path: Optional[str] = None):
        super().__init__(db_path)

    def add_locations_batch(self, locations_data):
        """
        Thêm hàng loạt vị trí vào cơ sở dữ liệu.
        Bỏ qua các vị trí đã tồn tại dựa trên ràng buộc UNIQUE của 'full_location_name'.
        
        Args:
            locations_data (list): Một danh sách các dictionary, mỗi dict chứa 'block', 'row', 'slot'.

        Returns:
            tuple: (bool success, int added_count, int skipped_count)
        """
        added_count = 0
        skipped_count = 0
        try:
            with self.conn:
                cursor = self.conn.cursor()
                for loc in locations_data:
                    full_name = f"{loc['block']}-{loc['row']}-{loc['slot']}"
                    try:
                        cursor.execute(
                            "INSERT INTO locations (block, row, slot, full_location_name) VALUES (?, ?, ?, ?)",
                            (loc['block'], loc['row'], loc['slot'], full_name)
                        )
                        if cursor.rowcount > 0:
                            added_count += 1
                    except sqlite3.IntegrityError:
                        skipped_count += 1
            return True, added_count, skipped_count
        except Exception as e:
            logger.error(f"Lỗi khi thêm hàng loạt vị trí: {e}")
            return False, 0, 0

    def get_statistics(self):
        """Trả về thống kê tổng số vị trí và số vị trí đã chiếm trong bãi."""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT COUNT(*) FROM locations")
            total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM locations WHERE is_occupied = 1")
            occupied = cur.fetchone()[0]
            return {"total": total, "occupied": occupied}
        except Exception as e:
            logger.error(f"Lỗi khi lấy thống kê vị trí: {e}")
            return {"total": 0, "occupied": 0}

    def get_all_free_locations(self):
        """Lấy danh sách tất cả các vị trí còn trống, sắp xếp theo thứ tự: Khu -> Dãy -> Vị trí."""
        try:
            cur = self.conn.cursor()
            # Sắp xếp theo: block (tên khu), row (số dãy), slot (số vị trí)
            cur.execute("""
                SELECT id, full_location_name 
                FROM locations 
                WHERE is_occupied = 0 
                ORDER BY block, CAST(row AS INTEGER), slot
            """)
            return [dict(r) for r in cur.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi lấy danh sách vị trí trống: {e}")
            return []

    def get_next_available_location(self):
        """Tìm vị trí trống đầu tiên theo thứ tự: Khu -> Dãy -> Vị trí."""
        try:
            cur = self.conn.cursor()
            # Sắp xếp theo: block (tên khu), row (số dãy), slot (số vị trí)
            cur.execute("""
                SELECT id, full_location_name 
                FROM locations 
                WHERE is_occupied = 0 
                ORDER BY block, CAST(row AS INTEGER), slot
                LIMIT 1
            """)
            row = cur.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi tìm vị trí trống tiếp theo: {e}")
            return None

    def set_location_occupied(self, location_id, status: bool):
        """
        Cập nhật trạng thái của một vị trí (bận hoặc trống).
        
        Args:
            location_id (int): ID của vị trí cần cập nhật.
            status (bool): True nếu bận (is_occupied=1), False nếu trống (is_occupied=0).
        """
        try:
            with self.conn:
                self.conn.execute("UPDATE locations SET is_occupied = ? WHERE id = ?", (1 if status else 0, location_id))
            return True
        except Exception as e:
            logger.error(f"Lỗi khi cập nhật trạng thái cho location_id {location_id}: {e}")
            return False

    def find_location_by_name(self, full_name):
        """Tìm một vị trí bằng tên đầy đủ của nó (ví dụ: 'A-01-01')."""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM locations WHERE full_location_name = ?", (full_name,))
            row = cur.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi tìm vị trí theo tên '{full_name}': {e}")
            return None

    def get_all_blocks(self):
        """Lấy danh sách tất cả các block có trong bãi."""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT DISTINCT block FROM locations ORDER BY block")
            return [row['block'] for row in cur.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi lấy danh sách blocks: {e}")
            return []

    def get_block_statistics(self, block_name):
        """Lấy thống kê của một block cụ thể."""
        try:
            cur = self.conn.cursor()
            cur.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN is_occupied = 1 THEN 1 ELSE 0 END) as occupied,
                    SUM(CASE WHEN is_occupied = 0 THEN 1 ELSE 0 END) as free
                FROM locations 
                WHERE block = ?
            """, (block_name,))
            row = cur.fetchone()
            if row:
                return {
                    'total': row['total'] or 0,
                    'occupied': row['occupied'] or 0,
                    'free': row['free'] or 0
                }
            return None
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi lấy thống kê block '{block_name}': {e}")
            return None

    def rename_block(self, old_name, new_name):
        """Đổi tên một block."""
        try:
            with self.conn:
                # Cập nhật tên block
                self.conn.execute(
                    "UPDATE locations SET block = ? WHERE block = ?",
                    (new_name, old_name)
                )
                # Cập nhật full_location_name
                self.conn.execute("""
                    UPDATE locations 
                    SET full_location_name = ? || '-' || row || '-' || slot
                    WHERE block = ?
                """, (new_name, new_name))
            logger.info(f"Đã đổi tên block từ '{old_name}' thành '{new_name}'")
            return True
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi đổi tên block '{old_name}': {e}")
            return False

    def delete_block(self, block_name):
        """Xóa một block và tất cả vị trí của nó."""
        try:
            with self.conn:
                # Đầu tiên, xóa liên kết location_id trong vehicles
                self.conn.execute("""
                    UPDATE vehicles 
                    SET location_id = NULL 
                    WHERE location_id IN (SELECT id FROM locations WHERE block = ?)
                """, (block_name,))
                
                # Xóa các vị trí
                cur = self.conn.execute(
                    "DELETE FROM locations WHERE block = ?",
                    (block_name,)
                )
                deleted_count = cur.rowcount
            
            logger.info(f"Đã xóa block '{block_name}' với {deleted_count} vị trí")
            return True, deleted_count
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi xóa block '{block_name}': {e}")
            return False, 0