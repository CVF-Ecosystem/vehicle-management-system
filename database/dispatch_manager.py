# database/dispatch_manager.py
import sqlite3
import logging
from datetime import datetime
from .base_manager import BaseManager
from .location_manager import LocationManager
from config import STATUS_IN_STOCK, STATUS_SHIPPED, STATUS_SHIPMENT_OPEN, STATUS_SHIPMENT_COMPLETED

class DispatchManager(BaseManager):
    """Quản lý các hoạt động liên quan đến bảng 'dispatches' (Phiếu xuất/Lô hàng xuất)."""
    
    def __init__(self):
        super().__init__()
        self.location_manager = LocationManager()

    def create_dispatch(self, driver_id, transport_vehicle_id):
        """Tạo một phiếu xuất mới với trạng thái 'OPEN'."""
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute("""
                    INSERT INTO dispatches (driver_id, transport_vehicle_id, created_at, status)
                    VALUES (?, ?, ?, ?)
                """, (driver_id, transport_vehicle_id, datetime.now().isoformat(), STATUS_SHIPMENT_OPEN))
                return cursor.lastrowid
        except Exception as e:
            logging.error(f"Lỗi khi tạo phiếu xuất: {e}")
            return None

    def add_vehicle_to_dispatch(self, vin, dispatch_id):
        """Gán một xe vào một phiếu xuất đang mở."""
        with self.conn:
            self.conn.execute("UPDATE vehicles SET dispatch_id = ? WHERE vin = ?", (dispatch_id, vin))

    def get_open_dispatch_details(self):
        """Lấy thông tin chi tiết về các phiếu xuất đang mở, bao gồm danh sách xe."""
        query = """
            SELECT d.id, dr.name as driver_name, tv.license_plate, v.vin, v.owner, v.vehicle_type
            FROM dispatches d
            LEFT JOIN drivers dr ON d.driver_id = dr.id
            LEFT JOIN transport_vehicles tv ON d.transport_vehicle_id = tv.id
            LEFT JOIN vehicles v ON v.dispatch_id = d.id
            WHERE d.status = ?
            ORDER BY d.id, v.vin
        """
        try:
            cur = self.conn.cursor()
            cur.execute(query, (STATUS_SHIPMENT_OPEN,))
            
            dispatches = {}
            for row in cur.fetchall():
                dispatch_id = row['id']
                if dispatch_id not in dispatches:
                    dispatches[dispatch_id] = {
                        'driver_name': row['driver_name'],
                        'license_plate': row['license_plate'],
                        'vehicles': []
                    }
                if row['vin']:
                    dispatches[dispatch_id]['vehicles'].append(dict(row))
            return dispatches
        except sqlite3.Error as e:
            logging.error(f"Lỗi khi lấy chi tiết phiếu xuất đang mở: {e}")
            return {}

    def cancel_dispatch(self, dispatch_id):
        """Hủy một phiếu xuất đang mở."""
        self.begin_transaction()
        try:
            self.conn.execute("UPDATE vehicles SET dispatch_id = NULL WHERE dispatch_id = ?", (dispatch_id,))
            self.conn.execute("DELETE FROM dispatches WHERE id = ?", (dispatch_id,))
            self.commit_transaction()
            logging.info(f"Đã hủy thành công phiếu xuất #{dispatch_id}.")
            return {"success": True, "message": f"Đã hủy phiếu xuất #{dispatch_id}."}
        except Exception as e:
            self.rollback_transaction()
            logging.error(f"Lỗi khi hủy phiếu xuất #{dispatch_id}: {e}")
            return {"success": False, "message": str(e)}

    def complete_dispatch(self, dispatch_id):
        """Hoàn tất một phiếu xuất: cập nhật trạng thái xe và giải phóng vị trí."""
        self.begin_transaction()
        try:
            cur = self.conn.cursor()
            cur.execute("""
                SELECT dr.name as driver_name, tv.license_plate
                FROM dispatches d
                JOIN drivers dr ON d.driver_id = dr.id
                JOIN transport_vehicles tv ON d.transport_vehicle_id = tv.id
                WHERE d.id = ?
            """, (dispatch_id,))
            dispatch_info = cur.fetchone()
            if not dispatch_info:
                self.rollback_transaction()
                return {"success": False, "message": "Không tìm thấy phiếu xuất."}

            cur.execute("SELECT location_id FROM vehicles WHERE dispatch_id = ? AND location_id IS NOT NULL", (dispatch_id,))
            location_ids_to_free = [row['location_id'] for row in cur.fetchall()]

            date_out_iso = datetime.now().isoformat()
            
            cur.execute("""
                UPDATE vehicles
                SET status = ?, date_out = ?, driver_name = ?, transport_vehicle = ?, location_id = NULL
                WHERE dispatch_id = ? AND status = ?
            """, (STATUS_SHIPPED, date_out_iso, dispatch_info['driver_name'], dispatch_info['license_plate'], dispatch_id, STATUS_IN_STOCK))
            
            num_updated = cur.rowcount

            self.conn.execute("UPDATE dispatches SET status = ?, completed_at = ? WHERE id = ?", (STATUS_SHIPMENT_COMPLETED, date_out_iso, dispatch_id))
            
            if location_ids_to_free:
                for loc_id in location_ids_to_free:
                    self.location_manager.set_location_occupied(loc_id, False)
                logging.info(f"Đã giải phóng {len(location_ids_to_free)} vị trí cho phiếu xuất #{dispatch_id}.")

            self.commit_transaction()
            return {"success": True, "message": f"Đã hoàn tất phiếu xuất, {num_updated} xe đã được xuất kho."}
        except Exception as e:
            self.rollback_transaction()
            logging.error(f"Lỗi khi hoàn tất phiếu xuất {dispatch_id}: {e}")
            return {"success": False, "message": str(e)}