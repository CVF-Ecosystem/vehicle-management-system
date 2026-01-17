# database/vehicle_manager.py
import sqlite3
import logging
from datetime import datetime, timezone, timedelta
import os

logger = logging.getLogger(__name__)
from .base_manager import BaseManager
from .location_manager import LocationManager
from config import DB_FILE, ARCHIVES_DIR, STATUS_IN_STOCK, STATUS_SHIPPED
from data_normalizer import validate_vin, normalize_vin, normalize_owner, normalize_vehicle_type
from exceptions import ValidationError, VINValidationError, DateValidationError, RequiredFieldError

class VehicleManager(BaseManager):
    def clear_archived_deleted_vehicles(self):
        """
        Xóa toàn bộ bản ghi trong bảng deleted_vehicles_archive (xe đã xóa vĩnh viễn).
        Returns:
            dict: {"success": bool, "message": str, "count": int}
        """
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT COUNT(*) FROM deleted_vehicles_archive")
            count = cur.fetchone()[0]
            cur.execute("DELETE FROM deleted_vehicles_archive")
            self.conn.commit()
            logger.info(f"Đã xóa toàn bộ {count} bản ghi trong deleted_vehicles_archive.")
            return {"success": True, "message": f"Đã xóa {count} bản ghi archive.", "count": count}
        except Exception as e:
            logger.exception(f"Lỗi khi xóa toàn bộ archive: {e}")
            return {"success": False, "message": str(e), "count": 0}
    def __init__(self):
        super().__init__()
        self.location_manager = LocationManager()

    def _validate_vehicle_data(self, vin: str, owner: str, date_in: datetime = None) -> dict:
        """
        Validate dữ liệu xe trước khi ghi vào database.
        
        Args:
            vin: Số khung xe
            owner: Tên chủ hàng
            date_in: Ngày nhập (datetime object hoặc None)
        
        Returns:
            dict: {
                "valid": bool,
                "vin": str (normalized),
                "owner": str (normalized),
                "errors": list[str]
            }
        
        Raises:
            VINValidationError: Nếu VIN không hợp lệ
            RequiredFieldError: Nếu thiếu trường bắt buộc
            DateValidationError: Nếu ngày không hợp lệ
        """
        errors = []
        
        # Validate VIN
        from config import VIN_STRICT_MODE
        vin_result = validate_vin(vin, strict=VIN_STRICT_MODE)
        if not vin_result["valid"]:
            logger.warning(f"VIN validation failed: {vin} - {vin_result['message']}")
            raise VINValidationError(
                vin=vin,
                message=vin_result["message"]
            )
        normalized_vin = vin_result["normalized"]
        
        # Cảnh báo nếu VIN không đủ 17 ký tự (khi strict=False)
        if not VIN_STRICT_MODE and len(normalized_vin) != 17:
            logger.warning(f"VIN không đủ 17 ký tự: {normalized_vin} ({len(normalized_vin)} ký tự) - Vui lòng kiểm tra lại!")
        
        # Validate Owner (required field)
        if not owner or not owner.strip():
            logger.warning(f"Owner validation failed: empty owner for VIN {normalized_vin}")
            raise RequiredFieldError(
                field_name="owner",
                message="Tên chủ hàng không được để trống"
            )
        normalized_owner = normalize_owner(owner)
        
        # Validate date_in
        if date_in is not None:
            if not isinstance(date_in, datetime):
                logger.warning(f"Date validation failed: date_in is not datetime object for VIN {normalized_vin}")
                raise DateValidationError(
                    field_name="date_in",
                    value=str(date_in),
                    expected_format="datetime object"
                )
            
            # CRITICAL FIX: Reject future dates
            # Use local date comparison to avoid timezone confusion for end users
            now_local = datetime.now()
            
            # Compare dates only (ignore time), using local timezone
            date_in_local = date_in.replace(tzinfo=None) if date_in.tzinfo else date_in
            
            if date_in_local.date() > now_local.date():
                logger.warning(f"Date validation failed: future date {date_in_local.date()} for VIN {normalized_vin}")
                raise DateValidationError(
                    field_name="date_in",
                    value=date_in.isoformat(),
                    expected_format="date cannot be in the future",
                    message=f"Ngày nhập không thể là ngày tương lai. Ngày nhập: {date_in_local.date()}, Hôm nay: {now_local.date()}"
                )
        
        return {
            "valid": True,
            "vin": normalized_vin,
            "owner": normalized_owner,
            "errors": []
        }

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
        
        Args:
            vin: Số khung xe (sẽ được validate và normalize)
            owner: Tên chủ hàng (sẽ được validate và normalize)
            vehicle_type: Loại xe (sẽ được normalize)
            date_in: Ngày nhập (datetime object)
            location_id: ID vị trí (có thể None)
        
        Returns:
            dict: {"success": bool, "message": str}
        """
        try:
            # === Phase 0.3: Data Integrity - Validate trước khi ghi DB ===
            validated = self._validate_vehicle_data(vin, owner, date_in)
            normalized_vin = validated["vin"]
            normalized_owner = validated["owner"]
            normalized_type = normalize_vehicle_type(vehicle_type) if vehicle_type else ""
            
            logger.debug(f"Validated data: VIN={normalized_vin}, Owner={normalized_owner}, Type={normalized_type}")
            
            with self.conn:
                self.conn.execute(
                    "INSERT INTO vehicles(vin, owner, vehicle_type, date_in, status, is_active, location_id) VALUES (?, ?, ?, ?, ?, 1, ?)",
                    (normalized_vin, normalized_owner, normalized_type, date_in.isoformat(), STATUS_IN_STOCK, location_id)
                )

            try:
                from database.audit_repository import log_create

                log_create(
                    table_name="vehicles",
                    record_id=normalized_vin,
                    new_value={
                        "vin": normalized_vin,
                        "owner": normalized_owner,
                        "vehicle_type": normalized_type,
                        "date_in": date_in.isoformat(),
                        "status": STATUS_IN_STOCK,
                        "location_id": location_id,
                    },
                )
            except Exception:
                # Audit must never break core flow
                pass
            return {"success": True, "message": "Thêm xe mới thành công."}
        
        except VINValidationError as e:
            logger.warning(f"VIN validation error: {e}")
            return {"success": False, "message": str(e)}
        except RequiredFieldError as e:
            logger.warning(f"Required field error: {e}")
            return {"success": False, "message": str(e)}
        except DateValidationError as e:
            logger.warning(f"Date validation error: {e}")
            return {"success": False, "message": str(e)}
        except sqlite3.IntegrityError as e:
            logger.warning(f"VIN đã tồn tại, đang xử lý nhập lại: {vin}. Chi tiết: {e}")
            # Sử dụng dữ liệu đã normalize cho việc nhập lại
            validated = self._validate_vehicle_data(vin, owner, date_in)
            return self._handle_existing_vin(
                validated["vin"], 
                validated["owner"], 
                normalize_vehicle_type(vehicle_type) if vehicle_type else "",
                date_in, 
                location_id
            )
        except sqlite3.OperationalError as e:
            logger.error(f"Lỗi thao tác CSDL khi thêm xe {vin}: {e}")
            return {"success": False, "message": f"Lỗi CSDL: {e}"}
        except sqlite3.DatabaseError as e:
            logger.error(f"Lỗi database khi thêm xe {vin}: {e}")
            return {"success": False, "message": f"Lỗi database: {e}"}
        except Exception as e:
            logger.exception(f"Lỗi không xác định khi thêm xe {vin}")
            return {"success": False, "message": f"Lỗi không xác định: {str(e)}"}

    def update_to_out(self, vin, date_out, transport_vehicle, driver_name):
        """
        Cập nhật trạng thái xe thành đã xuất.
        
        Returns:
            dict: {"success": bool, "message": str}
        """
        try:
            old_vehicle = None
            try:
                old_vehicle = self.get_vehicle_by_vin(vin)
            except Exception:
                old_vehicle = None

            with self.conn:
                cur = self.conn.cursor()
                cur.execute("""
                    UPDATE vehicles SET date_out=?, status=?, transport_vehicle=?, driver_name=?, location_id = NULL
                    WHERE vin=? AND status=? AND is_active = 1
                """, (date_out.isoformat(), STATUS_SHIPPED, transport_vehicle, driver_name, vin, STATUS_IN_STOCK))
                
                if cur.rowcount > 0:
                    try:
                        from database.audit_repository import log_update

                        log_update(
                            table_name="vehicles",
                            record_id=vin,
                            old_value=old_vehicle,
                            new_value={
                                "date_out": date_out.isoformat(),
                                "status": STATUS_SHIPPED,
                                "transport_vehicle": transport_vehicle,
                                "driver_name": driver_name,
                                "location_id": None,
                            },
                        )
                    except Exception:
                        pass
                    return {"success": True, "message": "Xuất xe thành công."}
                else:
                    return {"success": False, "message": "Không tìm thấy xe hoặc xe không ở trạng thái Tồn kho."}
        except sqlite3.OperationalError as e:
            logger.error(f"Lỗi thao tác CSDL khi xuất xe {vin}: {e}")
            return {"success": False, "message": f"Lỗi CSDL: {e}"}
        except sqlite3.DatabaseError as e:
            logger.error(f"Lỗi database khi xuất xe {vin}: {e}")
            return {"success": False, "message": f"Lỗi database: {e}"}
        except Exception as e:
            logger.exception(f"Lỗi khi xuất xe lẻ {vin}")
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
            logger.error(f"Lỗi khi tìm xe tồn kho theo VIN '{vin}': {e}")
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
            logger.error(f"Lỗi khi lấy danh sách tồn kho (phân trang): {e}")
            return []

    def get_in_stock_count(self, owner_filter=None, search_term=None):
        """Đếm tổng số xe tồn kho thỏa mãn điều kiện lọc."""
        query = "SELECT COUNT(vin) FROM vehicles WHERE status=? AND is_active = 1 AND is_deleted = 0"
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
            return count if count is not None else 0
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi đếm số xe tồn kho: {e}")
            return 0

    def get_vins_ordered_by_id(self, vins_list):
        """
        Lấy danh sách VINs theo thứ tự rowid trong database (thứ tự nhập vào) GIẢM DẦN.
        Xe nhập sau sẽ được gán vị trí trước (phù hợp với thứ tự hiển thị trong UI).
        
        Args:
            vins_list: List các VIN cần sắp xếp
            
        Returns:
            list: Danh sách VINs đã sắp xếp theo rowid giảm dần (xe mới nhất trước)
        """
        if not vins_list:
            return []
        
        try:
            placeholders = ','.join('?' * len(vins_list))
            cur = self.conn.cursor()
            cur.execute(f"""
                SELECT vin FROM vehicles 
                WHERE vin IN ({placeholders}) AND status=? AND is_active = 1
                ORDER BY rowid DESC
            """, vins_list + [STATUS_IN_STOCK])
            return [row['vin'] for row in cur.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi lấy VINs theo thứ tự: {e}")
            return list(vins_list)  # Fallback to original list

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
            logger.error(f"Lỗi khi lấy lịch sử xuất kho: {e}")
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
            logger.error(f"Lỗi khi lấy dữ liệu báo cáo tổng hợp: {e}")
            return []

    def get_distinct_owners(self):
        """Lấy tất cả các chủ hàng riêng biệt đã từng tồn tại."""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT DISTINCT owner FROM vehicles WHERE owner IS NOT NULL AND owner != '' AND is_active = 1 ORDER BY owner COLLATE NOCASE")
            return [row['owner'] for row in cur.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi lấy danh sách chủ hàng: {e}")
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
            logger.error(f"Lỗi khi lấy danh sách loại xe: {e}")
            return []

    def get_distinct_owners_in_stock(self):
        """Chỉ lấy các chủ hàng đang có xe trong kho."""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT DISTINCT owner FROM vehicles WHERE status = ? AND owner IS NOT NULL AND owner != '' AND is_active = 1 ORDER BY owner COLLATE NOCASE", (STATUS_IN_STOCK,))
            return [row['owner'] for row in cur.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi lấy danh sách chủ hàng tồn kho: {e}")
            return []

    def get_distinct_vehicle_types_in_stock(self):
        """Chỉ lấy các loại xe đang có trong kho."""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT DISTINCT vehicle_type FROM vehicles WHERE status = ? AND vehicle_type IS NOT NULL AND vehicle_type != '' AND is_active = 1 ORDER BY vehicle_type COLLATE NOCASE", (STATUS_IN_STOCK,))
            return [row['vehicle_type'] for row in cur.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi lấy danh sách loại xe tồn kho: {e}")
            return []

    def update_vehicle_details(self, vin, owner, vehicle_type):
        try:
            old_vehicle = None
            try:
                old_vehicle = self.get_vehicle_by_vin(vin)
            except Exception:
                old_vehicle = None

            with self.conn:
                self.conn.execute("UPDATE vehicles SET owner = ?, vehicle_type = ? WHERE vin = ? AND is_active = 1", (owner, vehicle_type, vin))

            try:
                from database.audit_repository import log_update

                log_update(
                    table_name="vehicles",
                    record_id=str(vin),
                    old_value=old_vehicle or {},
                    new_value={"owner": owner, "vehicle_type": vehicle_type},
                )
            except Exception:
                pass
            return {"success": True, "message": "Cập nhật thành công."}
        except Exception as e:
            logger.exception(f"Lỗi khi cập nhật chi tiết cho VIN {vin}")
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

            try:
                from database.audit_repository import log_update

                log_update(
                    table_name="vehicles",
                    record_id=str(old_vin),
                    old_value=old_record,
                    new_value={
                        "vin": new_vin,
                        "owner": owner,
                        "vehicle_type": vehicle_type,
                        "date_in": old_record.get("date_in"),
                        "date_out": old_record.get("date_out"),
                        "status": old_record.get("status"),
                        "transport_vehicle": old_record.get("transport_vehicle"),
                        "driver_name": old_record.get("driver_name"),
                        "dispatch_id": old_record.get("dispatch_id"),
                        "location_id": old_record.get("location_id"),
                    },
                )
            except Exception:
                pass
            return {"success": True, "message": f"Đã cập nhật VIN từ {old_vin} sang {new_vin}."}
        except sqlite3.IntegrityError:
            self.rollback_transaction()
            return {"success": False, "message": f"VIN mới '{new_vin}' đã tồn tại. Vui lòng chọn một VIN khác."}
        except Exception as e:
            self.rollback_transaction()
            logger.exception(f"Lỗi khi cập nhật VIN từ {old_vin} sang {new_vin}")
            return {"success": False, "message": str(e)}

    def soft_delete_vehicle(self, vin, deleted_by: str = None, delete_reason: str = None):
        """
        Soft delete một xe - đánh dấu is_deleted=1 thay vì xóa thực sự.
        
        Args:
            vin: VIN của xe cần xóa
            deleted_by: Người thực hiện xóa (username)
            delete_reason: Lý do xóa
            
        Returns:
            dict: {"success": bool, "message": str}
        """
        self.begin_transaction()
        try:
            vehicle = self.get_vehicle_by_vin(vin)
            if not vehicle:
                self.rollback_transaction()
                return {"success": False, "message": f"Không tìm thấy xe với VIN: {vin}"}
            
            # Giải phóng vị trí nếu có
            if vehicle.get('location_id'):
                self.location_manager.set_location_occupied(vehicle['location_id'], False)

            cur = self.conn.cursor()
            deleted_at = datetime.now(timezone.utc).isoformat()
            
            cur.execute("""
                UPDATE vehicles 
                SET is_active = 0, 
                    is_deleted = 1, 
                    deleted_at = ?, 
                    deleted_by = ?, 
                    delete_reason = ?,
                    location_id = NULL 
                WHERE vin = ? AND is_deleted = 0
            """, (deleted_at, deleted_by, delete_reason, vin))
            
            self.commit_transaction()
            if cur.rowcount > 0:
                logger.info(f"Soft deleted vehicle {vin} by {deleted_by}. Reason: {delete_reason}")

                try:
                    from database.audit_repository import log_audit, AuditAction

                    log_audit(
                        action=AuditAction.DELETE,
                        table_name="vehicles",
                        record_id=str(vin),
                        old_value=vehicle,
                        new_value={
                            "is_active": 0,
                            "is_deleted": 1,
                            "deleted_at": deleted_at,
                            "deleted_by": deleted_by,
                            "delete_reason": delete_reason,
                            "location_id": None,
                        },
                        details={
                            "soft_delete": True,
                            "source": "VehicleManager.soft_delete_vehicle",
                        },
                    )
                except Exception:
                    pass

                return {"success": True, "message": "Xóa xe thành công."}
            else:
                return {"success": False, "message": "Không tìm thấy xe để xóa hoặc xe đã bị xóa trước đó."}
        except Exception as e:
            self.rollback_transaction()
            logger.exception(f"Lỗi khi xóa mềm VIN {vin}: {e}")
            return {"success": False, "message": str(e)}

    def restore_deleted_vehicle(self, vin, restored_by: str = None):
        """
        Khôi phục một xe đã bị soft delete.
        
        Args:
            vin: VIN của xe cần khôi phục
            restored_by: Người thực hiện khôi phục
            
        Returns:
            dict: {"success": bool, "message": str}
        """
        self.begin_transaction()
        try:
            # Tìm xe đã bị xóa
            cur = self.conn.cursor()
            cur.execute("""
                SELECT * FROM vehicles 
                WHERE vin = ? AND is_deleted = 1
            """, (vin,))
            vehicle = cur.fetchone()
            
            if not vehicle:
                self.rollback_transaction()
                return {"success": False, "message": f"Không tìm thấy xe đã xóa với VIN: {vin}"}

            old_value = dict(vehicle)
            
            # Khôi phục xe
            cur.execute("""
                UPDATE vehicles 
                SET is_active = 1, 
                    is_deleted = 0, 
                    deleted_at = NULL, 
                    deleted_by = NULL, 
                    delete_reason = NULL
                WHERE vin = ? AND is_deleted = 1
            """, (vin,))
            
            self.commit_transaction()
            if cur.rowcount > 0:
                logger.info(f"Restored vehicle {vin} by {restored_by}")

                try:
                    from database.audit_repository import log_audit, AuditAction

                    log_audit(
                        action=AuditAction.UPDATE,
                        table_name="vehicles",
                        record_id=str(vin),
                        old_value=old_value,
                        new_value={
                            "is_active": 1,
                            "is_deleted": 0,
                            "deleted_at": None,
                            "deleted_by": None,
                            "delete_reason": None,
                        },
                        details={
                            "source": "VehicleManager.restore_deleted_vehicle",
                            "restored_by": restored_by,
                        },
                    )
                except Exception:
                    pass

                return {"success": True, "message": f"Khôi phục xe {vin} thành công."}
            else:
                return {"success": False, "message": "Không thể khôi phục xe."}
        except Exception as e:
            self.rollback_transaction()
            logger.exception(f"Lỗi khi khôi phục VIN {vin}: {e}")
            return {"success": False, "message": str(e)}

    def list_deleted_vehicles(self, limit: int = 100, offset: int = 0, 
                               search_term: str = None, owner_filter: str = None):
        """
        Lấy danh sách các xe đã bị soft delete.
        
        Args:
            limit: Số bản ghi tối đa
            offset: Vị trí bắt đầu
            search_term: Từ khóa tìm kiếm (VIN hoặc owner)
            owner_filter: Lọc theo chủ hàng
            
        Returns:
            list[dict]: Danh sách xe đã xóa
        """
        query = """
            SELECT v.*, l.full_location_name
            FROM vehicles v
            LEFT JOIN locations l ON v.location_id = l.id
            WHERE v.is_deleted = 1
        """
        params = []
        
        if owner_filter:
            query += " AND v.owner = ?"
            params.append(owner_filter)
        if search_term:
            query += " AND (v.vin LIKE ? OR v.owner LIKE ?)"
            params.extend([f"%{search_term}%", f"%{search_term}%"])
        
        query += " ORDER BY v.deleted_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        try:
            cur = self.conn.cursor()
            cur.execute(query, params)
            results = [dict(r) for r in cur.fetchall()]
            return results
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi lấy danh sách xe đã xóa: {e}")
            return []

    def count_deleted_vehicles(self, search_term: str = None, owner_filter: str = None):
        """Đếm số xe đã bị soft delete."""
        query = "SELECT COUNT(vin) FROM vehicles WHERE is_deleted = 1"
        params = []
        
        if owner_filter:
            query += " AND owner = ?"
            params.append(owner_filter)
        if search_term:
            query += " AND (vin LIKE ? OR owner LIKE ?)"
            params.extend([f"%{search_term}%", f"%{search_term}%"])
        
        try:
            cur = self.conn.cursor()
            cur.execute(query, params)
            return cur.fetchone()[0]
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi đếm xe đã xóa: {e}")
            return 0

    def hard_delete_vehicle(self, vin, deleted_by: str = None, delete_reason: str = None):
        """
        Xóa vĩnh viễn một xe đã bị soft delete.
        Lưu bản ghi vào deleted_vehicles_archive trước khi xóa.
        
        Args:
            vin: VIN của xe cần xóa vĩnh viễn
            deleted_by: Người thực hiện xóa
            delete_reason: Lý do xóa vĩnh viễn
            
        Returns:
            dict: {"success": bool, "message": str}
        """
        import json
        
        self.begin_transaction()
        try:
            # Tìm xe đã bị soft delete
            cur = self.conn.cursor()
            cur.execute("""
                SELECT * FROM vehicles 
                WHERE vin = ? AND is_deleted = 1
            """, (vin,))
            vehicle = cur.fetchone()
            
            if not vehicle:
                self.rollback_transaction()
                return {"success": False, "message": f"Không tìm thấy xe đã xóa với VIN: {vin}. Chỉ có thể xóa vĩnh viễn xe đã soft delete."}
            
            vehicle_dict = dict(vehicle)
            hard_deleted_at = datetime.now(timezone.utc).isoformat()
            
            # Lưu vào archive trước khi xóa
            cur.execute("""
                INSERT INTO deleted_vehicles_archive (
                    vin, owner, vehicle_type, date_in, date_out,
                    original_status, soft_deleted_at, hard_deleted_at,
                    deleted_by, delete_reason, full_record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                vehicle_dict['vin'],
                vehicle_dict['owner'],
                vehicle_dict.get('vehicle_type'),
                vehicle_dict.get('date_in'),
                vehicle_dict.get('date_out'),
                vehicle_dict.get('status'),
                vehicle_dict.get('deleted_at'),
                hard_deleted_at,
                deleted_by,
                delete_reason,
                json.dumps(vehicle_dict, ensure_ascii=False)
            ))
            
            # Xóa khỏi bảng vehicles
            cur.execute("DELETE FROM vehicles WHERE vin = ?", (vin,))
            
            self.commit_transaction()
            logger.info(f"Hard deleted vehicle {vin} by {deleted_by}. Archived to deleted_vehicles_archive.")

            try:
                from database.audit_repository import log_audit, AuditAction

                log_audit(
                    action=AuditAction.DELETE,
                    table_name="vehicles",
                    record_id=str(vin),
                    old_value=vehicle_dict,
                    details={
                        "hard_delete": True,
                        "source": "VehicleManager.hard_delete_vehicle",
                        "deleted_by": deleted_by,
                        "delete_reason": delete_reason,
                        "archived_to": "deleted_vehicles_archive",
                    },
                )
            except Exception:
                pass

            return {"success": True, "message": f"Đã xóa vĩnh viễn xe {vin} và lưu trữ bản ghi."}
        except Exception as e:
            self.rollback_transaction()
            logger.exception(f"Lỗi khi xóa vĩnh viễn VIN {vin}: {e}")
            return {"success": False, "message": str(e)}

    def get_archived_deleted_vehicles(self, limit: int = 100, offset: int = 0):
        """
        Lấy danh sách các xe đã bị xóa vĩnh viễn từ archive.
        
        Returns:
            list[dict]: Danh sách xe trong archive
        """
        try:
            cur = self.conn.cursor()
            cur.execute("""
                SELECT * FROM deleted_vehicles_archive
                ORDER BY hard_deleted_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            return [dict(r) for r in cur.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi lấy archive xe đã xóa: {e}")
            return []

    def get_vehicle_by_vin(self, vin):
        """Lấy thông tin chi tiết của một xe bằng VIN, kèm thông tin vị trí."""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT v.*, l.full_location_name FROM vehicles v LEFT JOIN locations l ON v.location_id = l.id WHERE v.vin=?", (vin,))
            row = cur.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi lấy xe theo VIN '{vin}': {e}")
            return None

    def search_all_vehicles(self, vin="", owner="", vehicle_type="", transport="", driver="",
                            status_filter="all", date_from="", date_to="", date_field="date_in",
                            block=""):
        """
        Tìm kiếm toàn cục trên lịch sử xe, kèm thông tin vị trí.
        
        Args:
            vin: Lọc theo VIN (LIKE)
            owner: Lọc theo chủ hàng (LIKE)
            vehicle_type: Lọc theo loại xe (LIKE)
            transport: Lọc theo xe vận chuyển (LIKE)
            driver: Lọc theo tài xế (LIKE)
            status_filter: "all" / "in_stock" / "shipped"
            date_from: Ngày bắt đầu (YYYY-MM-DD)
            date_to: Ngày kết thúc (YYYY-MM-DD)
            date_field: "date_in" hoặc "date_out"
            block: Lọc theo block vị trí
        """
        query = "SELECT v.*, l.full_location_name, l.block FROM vehicles v LEFT JOIN locations l ON v.location_id = l.id WHERE v.is_active = 1"
        params = []
        conditions = []
        
        # Text filters
        if vin: conditions.append("v.vin LIKE ?"); params.append(f"%{vin}%")
        if owner: conditions.append("v.owner LIKE ?"); params.append(f"%{owner}%")
        if vehicle_type: conditions.append("v.vehicle_type LIKE ?"); params.append(f"%{vehicle_type}%")
        if transport: conditions.append("v.transport_vehicle LIKE ?"); params.append(f"%{transport}%")
        if driver: conditions.append("v.driver_name LIKE ?"); params.append(f"%{driver}%")
        
        # Status filter
        if status_filter == "in_stock":
            conditions.append("v.status != ?"); params.append(STATUS_SHIPPED)
        elif status_filter == "shipped":
            conditions.append("v.status = ?"); params.append(STATUS_SHIPPED)
        
        # Date range filter
        if date_from:
            conditions.append(f"DATE(v.{date_field}) >= ?"); params.append(date_from)
        if date_to:
            conditions.append(f"DATE(v.{date_field}) <= ?"); params.append(date_to)
        
        # Block filter
        if block:
            conditions.append("l.block = ?"); params.append(block)
        
        if conditions: query += " AND " + " AND ".join(conditions)
        query += " ORDER BY v.date_in DESC"
        
        try:
            cur = self.conn.cursor()
            cur.execute(query, params)
            return [dict(r) for r in cur.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi tìm kiếm toàn cục: {e}")
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

            try:
                from database.audit_repository import log_update

                log_update(
                    table_name="vehicles",
                    record_id=vin,
                    old_value={"location_id": old_location_id},
                    new_value={"location_id": new_location_id},
                )
            except Exception:
                pass
            
            self.commit_transaction()
            logger.info(f"Đã di chuyển xe {vin} từ vị trí ID {old_location_id} sang {new_location_id}.")
            return {"success": True, "message": "Đảo vị trí thành công."}
        except Exception as e:
            self.rollback_transaction()
            logger.error(f"Lỗi khi đảo vị trí cho xe {vin}: {e}")
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

            logger.info(f"Đã lưu trữ thành công {len(vins_to_delete)} bản ghi vào file: {archive_db_path}")

            try:
                from database.audit_repository import log_audit, AuditAction

                log_audit(
                    action=AuditAction.ARCHIVE,
                    table_name="vehicles",
                    record_id=f"date_out:{start_date.isoformat()}:{end_date.isoformat()}",
                    details={
                        "source": "VehicleManager.archive_shipped_vehicles",
                        "date_from": start_date.isoformat(),
                        "date_to": end_date.isoformat(),
                        "count": len(vins_to_delete),
                        "archive_db_path": archive_db_path,
                        "vins_sample": vins_to_delete[:50],
                    },
                )
            except Exception:
                pass

            return {"success": True, "message": f"Đã lưu trữ thành công {len(vins_to_delete)} bản ghi.", "count": len(vins_to_delete)}

        except Exception as e:
            if self.conn: self.rollback_transaction()
            if archive_conn: archive_conn.rollback()
            logger.exception("Lỗi trong quá trình lưu trữ dữ liệu.")
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
            logger.exception(f"Lỗi khi đọc file lưu trữ {archive_path}")
            return {"success": False, "data": [], "message": str(e)}
        finally:
            if archive_conn:
                archive_conn.close()            