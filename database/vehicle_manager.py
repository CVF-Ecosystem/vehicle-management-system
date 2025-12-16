# database/vehicle_manager.py
import sqlite3
import logging
from datetime import datetime, timezone
import os
from .base_manager import BaseManager
from .location_manager import LocationManager
from config import DB_FILE, ARCHIVES_DIR, STATUS_IN_STOCK, STATUS_SHIPPED

class VehicleManager(BaseManager):
    def __init__(self):
        super().__init__()
        self.location_manager = LocationManager()

    def _handle_existing_vin(self, vin, owner, vehicle_type, date_in, location_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT status, is_active, location_id FROM vehicles WHERE vin=?", (vin,))
        result = cursor.fetchone()

        if not result:
             return {"success": False, "message": f"Lỗi không xác định khi xử lý VIN {vin}."}

        if result['status'] == STATUS_IN_STOCK and result['is_active'] == 1:
            return {"success": False, "message": f"VIN {vin} đã tồn tại trong bãi."}

        if result['location_id']:
            self.location_manager.set_location_occupied(result['location_id'], False)

        # === THAY ĐỔI: Đổi tên cột 'shipment_id' -> 'dispatch_id' ===
        self.conn.execute("""
            UPDATE vehicles SET owner=?, vehicle_type=?, date_in=?, status=?,
            date_out=NULL, transport_vehicle=NULL, driver_name=NULL, is_active=1, dispatch_id=NULL, location_id=?
            WHERE vin=?
        """, (owner, vehicle_type, date_in.isoformat(), STATUS_IN_STOCK, location_id, vin))
        # =========================================================
        return {"success": True, "message": f"VIN {vin} đã được nhập lại thành công."}

    def add_vehicle(self, vin, owner, vehicle_type, date_in, location_id):
        """
        Thêm một xe mới vào CSDL.
        
        Returns:
            dict: {"success": bool, "message": str}
        """
        try:
            with self.conn:
                self.conn.execute(
                    "INSERT INTO vehicles(vin, owner, vehicle_type, date_in, status, is_active, location_id) VALUES (?, ?, ?, ?, ?, 1, ?)",
                    (vin, owner, vehicle_type, date_in.isoformat(), STATUS_IN_STOCK, location_id)
                )
            return {"success": True, "message": "Thêm xe mới thành công."}
        except sqlite3.IntegrityError as e:
            logging.warning(f"VIN đã tồn tại, đang xử lý nhập lại: {vin}. Chi tiết: {e}")
            return self._handle_existing_vin(vin, owner, vehicle_type, date_in, location_id)
        except sqlite3.OperationalError as e:
            logging.error(f"Lỗi thao tác CSDL khi thêm xe {vin}: {e}")
            return {"success": False, "message": f"Lỗi CSDL: {e}"}
        except sqlite3.DatabaseError as e:
            logging.error(f"Lỗi database khi thêm xe {vin}: {e}")
            return {"success": False, "message": f"Lỗi database: {e}"}
        except Exception as e:
            logging.exception(f"Lỗi không xác định khi thêm xe {vin}")
            return {"success": False, "message": f"Lỗi không xác định: {str(e)}"}

    def update_to_out(self, vin, date_out, transport_vehicle, driver_name):
        """
        Cập nhật trạng thái xe thành đã xuất.
        
        Returns:
            dict: {"success": bool, "message": str}
        """
        try:
            with self.conn:
                cur = self.conn.cursor()
                cur.execute("""
                    UPDATE vehicles SET date_out=?, status=?, transport_vehicle=?, driver_name=?, location_id = NULL
                    WHERE vin=? AND status=? AND is_active = 1
                """, (date_out.isoformat(), STATUS_SHIPPED, transport_vehicle, driver_name, vin, STATUS_IN_STOCK))
                
                if cur.rowcount > 0:
                    return {"success": True, "message": "Xuất xe thành công."}
                else:
                    return {"success": False, "message": "Không tìm thấy xe hoặc xe không ở trạng thái Tồn kho."}
        except sqlite3.OperationalError as e:
            logging.error(f"Lỗi thao tác CSDL khi xuất xe {vin}: {e}")
            return {"success": False, "message": f"Lỗi CSDL: {e}"}
        except sqlite3.DatabaseError as e:
            logging.error(f"Lỗi database khi xuất xe {vin}: {e}")
            return {"success": False, "message": f"Lỗi database: {e}"}
        except Exception as e:
            logging.exception(f"Lỗi khi xuất xe lẻ {vin}")
            return {"success": False, "message": f"Lỗi không xác định: {str(e)}"}

    def find_vehicle_in_stock(self, vin):
        """Tìm một xe cụ thể đang có trong kho và chưa được gán vào phiếu xuất nào."""
        try:
            cur = self.conn.cursor()
            # === THAY ĐỔI: Đổi tên cột 'shipment_id' -> 'dispatch_id' ===
            cur.execute("SELECT * FROM vehicles WHERE vin=? AND status=? AND is_active = 1 AND dispatch_id IS NULL", (vin, STATUS_IN_STOCK))
            # =========================================================
            row = cur.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logging.error(f"Lỗi khi tìm xe tồn kho theo VIN '{vin}': {e}")
            return None

    def get_in_stock(self, owner_filter=None, search_term=None, limit=100, offset=0):
        """
        Lấy một "trang" dữ liệu các xe đang tồn kho, hỗ trợ phân trang.
        """
        query = """
            SELECT v.*, l.full_location_name
            FROM vehicles v
            LEFT JOIN locations l ON v.location_id = l.id
            WHERE v.status=? AND v.is_active = 1
        """
        params = [STATUS_IN_STOCK]
        if owner_filter:
            query += " AND v.owner = ?"
            params.append(owner_filter)
        if search_term:
            query += " AND (v.vin LIKE ? OR v.owner LIKE ?)"
            params.extend([f"%{search_term}%", f"%{search_term}%"])
        
        query += " ORDER BY v.date_in DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        try:
            cur = self.conn.cursor()
            cur.execute(query, params)
            
            results = []
            now_utc = datetime.now(timezone.utc)
            for r in cur.fetchall():
                row_dict = dict(r)
                date_in_naive = datetime.fromisoformat(row_dict['date_in'])
                date_in_aware = date_in_naive.replace(tzinfo=timezone.utc)
                
                delta = now_utc - date_in_aware
                row_dict['days_in_stock'] = delta.days + (1 if delta.seconds > 0 else 0)
                results.append(row_dict)
            return results
        except sqlite3.Error as e:
            logging.error(f"Lỗi khi lấy danh sách tồn kho (phân trang): {e}")
            return []

    def get_in_stock_count(self, owner_filter=None, search_term=None):
        """Đếm tổng số xe tồn kho thỏa mãn điều kiện lọc."""
        query = "SELECT COUNT(vin) FROM vehicles WHERE status=? AND is_active = 1"
        params = [STATUS_IN_STOCK]
        if owner_filter:
            query += " AND owner = ?"
            params.append(owner_filter)
        if search_term:
            query += " AND (vin LIKE ? OR owner LIKE ?)"
            params.extend([f"%{search_term}%", f"%{search_term}%"])
        
        try:
            cur = self.conn.cursor()
            cur.execute(query, params)
            count = cur.fetchone()[0]
            return count
        except sqlite3.Error as e:
            logging.error(f"Lỗi khi đếm số xe tồn kho: {e}")
            return 0

    def get_shipped_vehicles_history(self, start_date=None, end_date=None):
        """Lấy lịch sử các xe đã xuất trong một khoảng thời gian."""
        query = "SELECT * FROM vehicles WHERE status=? AND is_active = 1"
        params = [STATUS_SHIPPED]
        if start_date:
            query += " AND date_out >= ?"
            params.append(start_date.isoformat())
        if end_date:
            end_date_inclusive = end_date.replace(hour=23, minute=59, second=59)
            query += " AND date_out <= ?"
            params.append(end_date_inclusive.isoformat())
        query += " ORDER BY date_out DESC"
        
        try:
            cur = self.conn.cursor()
            cur.execute(query, params)

            results = []
            for r in cur.fetchall():
                row_dict = dict(r)
                if row_dict['date_in'] and row_dict['date_out']:
                    # === SỬA LỖI: Ở đây cả hai đều là naive nên không cần sửa, nhưng để an toàn, chúng ta có thể làm rõ ===
                    date_in = datetime.fromisoformat(row_dict['date_in'])
                    date_out = datetime.fromisoformat(row_dict['date_out'])
                    delta = date_out - date_in
                    row_dict['days_in_stock'] = delta.days + 1
                else:
                    row_dict['days_in_stock'] = 0
                results.append(row_dict)
            return results
        except sqlite3.Error as e:
            logging.error(f"Lỗi khi lấy lịch sử xuất kho: {e}")
            return []
    # === HÀM ĐƯỢC VIẾT LẠI HOÀN TOÀN ===
    def get_summary_report_data(self, start_date, end_date):
        """
        Lấy dữ liệu báo cáo tổng hợp một cách chính xác và hiệu quả.
        - total_in: Số xe có date_in trong khoảng thời gian.
        - total_out: Số xe có date_out trong khoảng thời gian.
        - stock: Số xe tồn kho tại thời điểm cuối của khoảng thời gian.
        """
        try:
            start_iso = start_date.isoformat()
            end_iso = end_date.isoformat()
            
            cur = self.conn.cursor()

            # Lấy danh sách tất cả các chủ hàng có liên quan
            cur.execute("""
                SELECT DISTINCT owner FROM vehicles 
                WHERE is_active = 1 AND owner IS NOT NULL AND owner != ''
            """)
            all_owners = [row['owner'] for row in cur.fetchall()]
            summary = {owner: {'total_in': 0, 'total_out': 0, 'stock': 0} for owner in all_owners}

            # 1. Tính TOTAL IN trong kỳ
            cur.execute("""
                SELECT owner, COUNT(vin) as count 
                FROM vehicles 
                WHERE is_active = 1 AND date_in BETWEEN ? AND ? 
                GROUP BY owner
            """, (start_iso, end_iso))
            for row in cur.fetchall():
                if row['owner'] in summary:
                    summary[row['owner']]['total_in'] = row['count']

            # 2. Tính TOTAL OUT trong kỳ
            cur.execute("""
                SELECT owner, COUNT(vin) as count 
                FROM vehicles 
                WHERE is_active = 1 AND date_out BETWEEN ? AND ? 
                GROUP BY owner
            """, (start_iso, end_iso))
            for row in cur.fetchall():
                if row['owner'] in summary:
                    summary[row['owner']]['total_out'] = row['count']

            # 3. Tính STOCK cuối kỳ
            cur.execute("""
                SELECT owner, COUNT(vin) as count 
                FROM vehicles 
                WHERE is_active = 1 AND date_in <= ? AND (date_out IS NULL OR date_out > ?)
                GROUP BY owner
            """, (end_iso, end_iso))
            for row in cur.fetchall():
                if row['owner'] in summary:
                    summary[row['owner']]['stock'] = row['count']
            
            # Chuyển đổi dictionary thành list và chỉ giữ lại các chủ hàng có hoạt động hoặc tồn kho
            final_report = [{'owner': owner, **data} for owner, data in summary.items() if any(val > 0 for val in data.values())]
            
            return sorted(final_report, key=lambda x: x['owner'])

        except sqlite3.Error as e:
            logging.error(f"Lỗi khi lấy dữ liệu báo cáo tổng hợp: {e}")
            return []

    def get_distinct_owners(self):
        """Lấy tất cả các chủ hàng riêng biệt đã từng tồn tại."""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT DISTINCT owner FROM vehicles WHERE owner IS NOT NULL AND owner != '' AND is_active = 1 ORDER BY owner COLLATE NOCASE")
            return [row['owner'] for row in cur.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Lỗi khi lấy danh sách chủ hàng: {e}")
            return []

    def get_distinct_vehicle_types(self, owner_filter=None):
        """Lấy tất cả các loại xe riêng biệt đã từng tồn tại."""
        try:
            query = "SELECT DISTINCT vehicle_type FROM vehicles WHERE vehicle_type IS NOT NULL AND vehicle_type != '' AND is_active = 1"
            params = []
            if owner_filter:
                query += " AND owner = ?"
                params.append(owner_filter)
            query += " ORDER BY vehicle_type COLLATE NOCASE"
            
            cur = self.conn.cursor()
            cur.execute(query, params)
            return [row['vehicle_type'] for row in cur.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Lỗi khi lấy danh sách loại xe: {e}")
            return []

    def get_distinct_owners_in_stock(self):
        """Chỉ lấy các chủ hàng đang có xe trong kho."""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT DISTINCT owner FROM vehicles WHERE status = ? AND owner IS NOT NULL AND owner != '' AND is_active = 1 ORDER BY owner COLLATE NOCASE", (STATUS_IN_STOCK,))
            return [row['owner'] for row in cur.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Lỗi khi lấy danh sách chủ hàng tồn kho: {e}")
            return []

    def get_distinct_vehicle_types_in_stock(self):
        """Chỉ lấy các loại xe đang có trong kho."""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT DISTINCT vehicle_type FROM vehicles WHERE status = ? AND vehicle_type IS NOT NULL AND vehicle_type != '' AND is_active = 1 ORDER BY vehicle_type COLLATE NOCASE", (STATUS_IN_STOCK,))
            return [row['vehicle_type'] for row in cur.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Lỗi khi lấy danh sách loại xe tồn kho: {e}")
            return []

    def update_vehicle_details(self, vin, owner, vehicle_type):
        try:
            with self.conn:
                self.conn.execute("UPDATE vehicles SET owner = ?, vehicle_type = ? WHERE vin = ? AND is_active = 1", (owner, vehicle_type, vin))
            return {"success": True, "message": "Cập nhật thành công."}
        except Exception as e:
            logging.exception(f"Lỗi khi cập nhật chi tiết cho VIN {vin}")
            return {"success": False, "message": str(e)}

    def update_vin(self, old_vin, new_vin, owner, vehicle_type):
        self.begin_transaction()
        try:
            old_record = self.get_vehicle_by_vin(old_vin)
            if not old_record:
                self.rollback_transaction()
                return {"success": False, "message": f"Không tìm thấy xe với VIN cũ: {old_vin}"}
            
            self.conn.execute("DELETE FROM vehicles WHERE vin = ?", (old_vin,))
            
            # === THAY ĐỔI: Đổi tên cột 'shipment_id' -> 'dispatch_id' ===
            self.conn.execute("""
                INSERT INTO vehicles (vin, owner, vehicle_type, date_in, date_out, status, 
                                      transport_vehicle, driver_name, is_active, dispatch_id, location_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                new_vin, owner, vehicle_type, old_record['date_in'], old_record['date_out'],
                old_record['status'], old_record['transport_vehicle'], old_record['driver_name'], 
                old_record['is_active'], old_record['dispatch_id'], old_record['location_id']
            ))
            # =========================================================
            
            self.commit_transaction()
            return {"success": True, "message": f"Đã cập nhật VIN từ {old_vin} sang {new_vin}."}
        except sqlite3.IntegrityError:
            self.rollback_transaction()
            return {"success": False, "message": f"VIN mới '{new_vin}' đã tồn tại. Vui lòng chọn một VIN khác."}
        except Exception as e:
            self.rollback_transaction()
            logging.exception(f"Lỗi khi cập nhật VIN từ {old_vin} sang {new_vin}")
            return {"success": False, "message": str(e)}

    def soft_delete_vehicle(self, vin):
        self.begin_transaction()
        try:
            vehicle = self.get_vehicle_by_vin(vin)
            if vehicle and vehicle.get('location_id'):
                self.location_manager.set_location_occupied(vehicle['location_id'], False)

            cur = self.conn.cursor()
            cur.execute("UPDATE vehicles SET is_active = 0, location_id = NULL WHERE vin = ?", (vin,))
            
            self.commit_transaction()
            if cur.rowcount > 0:
                return {"success": True, "message": "Xóa xe thành công."}
            else:
                return {"success": False, "message": "Không tìm thấy xe để xóa."}
        except Exception as e:
            self.rollback_transaction()
            logging.exception(f"Lỗi khi xóa mềm VIN {vin}: {e}")
            return {"success": False, "message": str(e)}

    def get_vehicle_by_vin(self, vin):
        """Lấy thông tin chi tiết của một xe bằng VIN, kèm thông tin vị trí."""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT v.*, l.full_location_name FROM vehicles v LEFT JOIN locations l ON v.location_id = l.id WHERE v.vin=?", (vin,))
            row = cur.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logging.error(f"Lỗi khi lấy xe theo VIN '{vin}': {e}")
            return None

    def search_all_vehicles(self, vin="", owner="", vehicle_type="", transport="", driver=""):
        """Tìm kiếm toàn cục trên lịch sử xe, kèm thông tin vị trí."""
        query = "SELECT v.*, l.full_location_name FROM vehicles v LEFT JOIN locations l ON v.location_id = l.id WHERE v.is_active = 1"
        params = []
        conditions = []
        if vin: conditions.append("v.vin LIKE ?"); params.append(f"%{vin}%")
        if owner: conditions.append("v.owner LIKE ?"); params.append(f"%{owner}%")
        if vehicle_type: conditions.append("v.vehicle_type LIKE ?"); params.append(f"%{vehicle_type}%")
        if transport: conditions.append("v.transport_vehicle LIKE ?"); params.append(f"%{transport}%")
        if driver: conditions.append("v.driver_name LIKE ?"); params.append(f"%{driver}%")
        
        if conditions: query += " AND " + " AND ".join(conditions)
        query += " ORDER BY v.date_in DESC"
        
        try:
            cur = self.conn.cursor()
            cur.execute(query, params)
            return [dict(r) for r in cur.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Lỗi khi tìm kiếm toàn cục: {e}")
            return []

    def swap_vehicle_location(self, vin, new_location_id):
        self.begin_transaction()
        try:
            vehicle = self.get_vehicle_by_vin(vin)
            if not vehicle:
                self.rollback_transaction()
                return {"success": False, "message": f"Không tìm thấy xe với VIN: {vin}"}

            old_location_id = vehicle.get('location_id')

            self.conn.execute("UPDATE vehicles SET location_id = ? WHERE vin = ?", (new_location_id, vin))
            self.location_manager.set_location_occupied(new_location_id, True)
            if old_location_id:
                self.location_manager.set_location_occupied(old_location_id, False)
            
            self.commit_transaction()
            logging.info(f"Đã di chuyển xe {vin} từ vị trí ID {old_location_id} sang {new_location_id}.")
            return {"success": True, "message": "Đảo vị trí thành công."}
        except Exception as e:
            self.rollback_transaction()
            logging.error(f"Lỗi khi đảo vị trí cho xe {vin}: {e}")
            return {"success": False, "message": f"Đã xảy ra lỗi: {e}"}
    def archive_shipped_vehicles(self, start_date, end_date):
        """
        Di chuyển các xe đã xuất trong một khoảng thời gian từ CSDL chính
        vào một file CSDL lưu trữ DUY NHẤT.
        """
        records_to_archive = self.get_shipped_vehicles_history(start_date, end_date)
        
        if not records_to_archive:
            return {"success": True, "message": "Không có dữ liệu nào để lưu trữ trong khoảng thời gian đã chọn.", "count": 0}

        # === LOGIC MỚI: Luôn sử dụng một file archive duy nhất ===
        os.makedirs(ARCHIVES_DIR, exist_ok=True)
        archive_db_path = os.path.join(ARCHIVES_DIR, f"{os.path.splitext(os.path.basename(DB_FILE))[0]}_ARCHIVE.db")
        # =======================================================
        
        archive_conn = None
        try:
            archive_conn = self.get_new_connection(archive_db_path)
            if not archive_conn:
                return {"success": False, "message": "Không thể tạo hoặc kết nối đến file CSDL lưu trữ."}

            cursor = self.conn.cursor()
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='vehicles'")
            create_table_sql = cursor.fetchone()['sql']
            archive_conn.execute(create_table_sql) # Lệnh này sẽ không làm gì nếu bảng đã tồn tại
            archive_conn.commit()

            self.begin_transaction()
            archive_conn.execute("BEGIN TRANSACTION")

            vins_to_delete = []
            for record in records_to_archive:
                record_dict = dict(record)
                vins_to_delete.append(record_dict['vin'])
                
                record_keys = [key for key in record_dict.keys() if key in record.keys()]
                
                columns = ', '.join(record_keys)
                placeholders = ', '.join(['?'] * len(record_keys))
                # Sử dụng INSERT OR IGNORE để tránh lỗi nếu cố gắng lưu trữ lại một bản ghi đã có
                sql = f'INSERT OR IGNORE INTO vehicles ({columns}) VALUES ({placeholders})'
                
                values_tuple = tuple(record_dict[key] for key in record_keys)
                archive_conn.execute(sql, values_tuple)

            if vins_to_delete:
                placeholders = ', '.join(['?'] * len(vins_to_delete))
                self.conn.execute(f"DELETE FROM vehicles WHERE vin IN ({placeholders})", vins_to_delete)

            self.commit_transaction()
            archive_conn.commit()

            logging.info(f"Đã lưu trữ thành công {len(vins_to_delete)} bản ghi vào file: {archive_db_path}")
            return {"success": True, "message": f"Đã lưu trữ thành công {len(vins_to_delete)} bản ghi.", "count": len(vins_to_delete)}

        except Exception as e:
            if self.conn: self.rollback_transaction()
            if archive_conn: archive_conn.rollback()
            logging.exception("Lỗi trong quá trình lưu trữ dữ liệu.")
            return {"success": False, "message": f"Lỗi lưu trữ: {e}"}
        
        finally:
            if archive_conn:
                archive_conn.close()

    # === HÀM MỚI: Để đọc dữ liệu từ file archive ===
    def get_archived_vehicles(self, archive_path, start_date, end_date):
        if not os.path.exists(archive_path):
            # === SỬA LỖI: Trả về key thay vì chuỗi hardcode ===
            return {"success": False, "data": [], "message": "err_archive_file_not_exist"}
            # ===============================================
        
        archive_conn = None
        try:
            archive_conn = self.get_new_connection(archive_path)
            if not archive_conn:
                return {"success": False, "data": [], "message": "Không thể kết nối đến file lưu trữ."}

            query = "SELECT * FROM vehicles WHERE date_out BETWEEN ? AND ? ORDER BY date_out DESC"
            params = (start_date.isoformat(), end_date.isoformat())
            
            cursor = archive_conn.cursor()
            cursor.execute(query, params)
            
            results = [dict(row) for row in cursor.fetchall()]
            return {"success": True, "data": results, "message": f"Tìm thấy {len(results)} bản ghi."}

        except Exception as e:
            logging.exception(f"Lỗi khi đọc file lưu trữ {archive_path}")
            return {"success": False, "data": [], "message": str(e)}
        finally:
            if archive_conn:
                archive_conn.close()            