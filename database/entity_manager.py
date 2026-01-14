# database/entity_manager.py
import sqlite3
import logging

logger = logging.getLogger(__name__)

from .base_manager import BaseManager

class EntityManager(BaseManager):
    """Quản lý các đối tượng phụ như Tài xế và Xe vận chuyển."""
    
    def __init__(self):
        super().__init__()

    def get_all_active_drivers(self):
        """Lấy danh sách tất cả các tài xế đang hoạt động."""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM drivers WHERE is_active = 1 ORDER BY name COLLATE NOCASE")
            return [dict(r) for r in cur.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi lấy danh sách tài xế: {e}")
            return []

    def add_driver(self, name, phone, cccd, notes):
        """Thêm một tài xế mới."""
        try:
            # Xử lý giá trị cccd rỗng thành NULL để tránh lỗi UNIQUE
            cccd_to_insert = cccd if cccd else None
            with self.conn:
                cursor = self.conn.execute(
                    "INSERT INTO drivers (name, phone, cccd, notes) VALUES (?, ?, ?, ?)",
                    (name, phone, cccd_to_insert, notes)
                )
                driver_id = cursor.lastrowid
            return {"success": True, "message": "Thêm tài xế thành công.", "id": driver_id}
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: drivers.name" in str(e):
                return {"success": False, "message": f"Tên tài xế '{name}' đã tồn tại."}
            if "UNIQUE constraint failed: drivers.cccd" in str(e):
                return {"success": False, "message": f"Số CCCD '{cccd}' đã tồn tại."}
            return {"success": False, "message": f"Lỗi trùng lặp dữ liệu: {e}"}
        except Exception as e:
            logger.error(f"Lỗi không xác định khi thêm tài xế: {e}")
            return {"success": False, "message": str(e)}

    def update_driver(self, driver_id, name, phone, cccd, notes):
        """Cập nhật thông tin một tài xế."""
        try:
            cccd_to_update = cccd if cccd else None
            with self.conn:
                self.conn.execute(
                    "UPDATE drivers SET name=?, phone=?, cccd=?, notes=? WHERE id=?",
                    (name, phone, cccd_to_update, notes, driver_id)
                )
            return {"success": True, "message": "Cập nhật tài xế thành công."}
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: drivers.name" in str(e):
                return {"success": False, "message": f"Tên tài xế '{name}' đã tồn tại."}
            if "UNIQUE constraint failed: drivers.cccd" in str(e):
                return {"success": False, "message": f"Số CCCD '{cccd}' đã tồn tại."}
            return {"success": False, "message": f"Lỗi trùng lặp dữ liệu: {e}"}
        except Exception as e:
            logger.error(f"Lỗi không xác định khi cập nhật tài xế: {e}")
            return {"success": False, "message": str(e)}

    def soft_delete_driver(self, driver_id):
        """"Xóa mềm" một tài xế bằng cách đánh dấu là không hoạt động."""
        try:
            with self.conn:
                self.conn.execute("UPDATE drivers SET is_active = 0 WHERE id=?", (driver_id,))
            return {"success": True, "message": "Xóa tài xế thành công."}
        except Exception as e:
            logger.error(f"Lỗi khi xóa mềm tài xế: {e}")
            return {"success": False, "message": str(e)}

    def get_all_active_transport_vehicles(self):
        """Lấy danh sách tất cả các xe vận chuyển đang hoạt động."""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM transport_vehicles WHERE is_active = 1 ORDER BY license_plate COLLATE NOCASE")
            return [dict(r) for r in cur.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi lấy danh sách xe vận chuyển: {e}")
            return []

    def add_transport_vehicle(self, license_plate, vehicle_type, notes):
        """Thêm một xe vận chuyển mới."""
        try:
            with self.conn:
                cursor = self.conn.execute(
                    "INSERT INTO transport_vehicles (license_plate, type, notes) VALUES (?, ?, ?)",
                    (license_plate, vehicle_type, notes)
                )
                vehicle_id = cursor.lastrowid
            return {"success": True, "message": "Thêm xe vận chuyển thành công.", "id": vehicle_id}
        except sqlite3.IntegrityError:
            return {"success": False, "message": f"Biển số xe '{license_plate}' đã tồn tại."}
        except Exception as e:
            logger.error(f"Lỗi không xác định khi thêm xe vận chuyển: {e}")
            return {"success": False, "message": str(e)}

    def update_transport_vehicle(self, vehicle_id, license_plate, vehicle_type, notes):
        """Cập nhật thông tin một xe vận chuyển."""
        try:
            with self.conn:
                self.conn.execute("UPDATE transport_vehicles SET license_plate=?, type=?, notes=? WHERE id=?", (license_plate, vehicle_type, notes, vehicle_id))
            return {"success": True, "message": "Cập nhật xe vận chuyển thành công."}
        except sqlite3.IntegrityError:
            return {"success": False, "message": f"Biển số xe '{license_plate}' đã tồn tại."}
        except Exception as e:
            logger.error(f"Lỗi không xác định khi cập nhật xe vận chuyển: {e}")
            return {"success": False, "message": str(e)}

    def soft_delete_transport_vehicle(self, vehicle_id):
        """"Xóa mềm" một xe vận chuyển."""
        try:
            with self.conn:
                self.conn.execute("UPDATE transport_vehicles SET is_active = 0 WHERE id=?", (vehicle_id,))
            return {"success": True, "message": "Xóa xe vận chuyển thành công."}
        except Exception as e:
            logger.error(f"Lỗi khi xóa mềm xe vận chuyển: {e}")
            return {"success": False, "message": str(e)}