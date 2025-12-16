# database/location_manager.py
import sqlite3
import logging
from .base_manager import BaseManager

class LocationManager(BaseManager):
    """
    Quản lý tất cả các hoạt động liên quan đến bảng 'locations'.
    Cung cấp một giao diện để thêm, truy vấn và cập nhật trạng thái vị trí.
    """
    def __init__(self):
        super().__init__()

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
            logging.error(f"Lỗi khi thêm hàng loạt vị trí: {e}")
            return False, 0, 0

    def get_all_free_locations(self):
        """Lấy danh sách tất cả các vị trí còn trống, sắp xếp theo thứ tự logic."""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT id, full_location_name FROM locations WHERE is_occupied = 0 ORDER BY block, row, slot")
            return [dict(r) for r in cur.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Lỗi khi lấy danh sách vị trí trống: {e}")
            return []

    def get_next_available_location(self):
        """Tìm vị trí trống đầu tiên theo thứ tự logic."""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT id, full_location_name FROM locations WHERE is_occupied = 0 ORDER BY block, row, slot LIMIT 1")
            row = cur.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logging.error(f"Lỗi khi tìm vị trí trống tiếp theo: {e}")
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
            logging.error(f"Lỗi khi cập nhật trạng thái cho location_id {location_id}: {e}")
            return False

    def find_location_by_name(self, full_name):
        """Tìm một vị trí bằng tên đầy đủ của nó (ví dụ: 'A-01-01')."""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM locations WHERE full_location_name = ?", (full_name,))
            row = cur.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logging.error(f"Lỗi khi tìm vị trí theo tên '{full_name}': {e}")
            return None