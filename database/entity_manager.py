# database/entity_manager.py
import sqlite3
import logging

logger = logging.getLogger(__name__)

from .base_manager import BaseManager

class EntityManager(BaseManager):
    """Quản lý các đối tượng phụ như Tài xế và Xe vận chuyển."""
    
    def __init__(self):
        super().__init__()
        # Bước 1: Chuẩn hóa và gộp các tài xế trùng lặp trong DB
        self._normalize_all_existing_drivers()
        # Bước 2: Nạp danh sách tài xế vào normalizer
        self._refresh_known_drivers()

    def _refresh_known_drivers(self):
        """Nạp danh sách tên tài xế hiện có vào normalizer."""
        try:
            from data_normalizer import normalizer as _normalizer
            cur = self.conn.cursor()
            cur.execute("SELECT name FROM drivers WHERE is_active = 1 ORDER BY name COLLATE NOCASE")
            drivers = [row[0] for row in cur.fetchall()]
            _normalizer.set_known_drivers(drivers)
        except Exception as e:
            logger.warning(f"Không thể nạp danh sách tài xế cho normalizer: {e}")

    def _normalize_all_existing_drivers(self):
        """
        Chuẩn hóa toàn bộ tên tài xế và gộp các tài xế bị trùng lặp do viết hoa/thường,
        khoảng trắng hoặc thiếu dấu (ví dụ: 'pham van lam' và 'PHAM VAN LAM').
        
        Quy trình gộp:
        1. Tìm ra tên chuẩn (nhiều dấu hơn, viết hoa, đang active).
        2. Chuyển các dispatches (phiếu xuất) tham chiếu tài xế cũ sang ID tài xế chuẩn.
        3. Cập nhật driver_name tương ứng trong lịch sử xe (vehicles).
        4. Gộp thông tin số điện thoại, CCCD, ghi chú nếu tài xế chuẩn bị thiếu.
        5. Xóa tài xế trùng lặp khỏi bảng drivers.
        """
        try:
            import unidecode as _unidecode
            from collections import defaultdict
            from data_normalizer import normalize_driver_name as _norm_name

            from data_normalizer import normalizer as _normalizer

            cur = self.conn.cursor()
            cur.execute("SELECT id, name, phone, cccd, notes, is_active FROM drivers")
            rows = cur.fetchall()
            if not rows:
                return

            def _count_diacritics(text: str) -> int:
                return sum(1 for c in text if ord(c) > 127)

            def _phonetic_key(text: str) -> str:
                return _unidecode.unidecode(text.lower()).replace(' ', '')

            # Nhóm các tài xế có cùng âm đọc không dấu
            groups = defaultdict(list)
            for r in rows:
                d = dict(r)
                # Trim & sanitize thông minh bằng normalizer (áp dụng từ điển lỗi chính tả)
                d['clean_name'] = _normalizer._sanitize_driver_text(d['name'])
                key = _phonetic_key(d['clean_name'])
                d['diacritics'] = _count_diacritics(d['clean_name'])
                groups[key].append(d)

            total_merged = 0
            self.begin_transaction()
            try:
                for key, members in groups.items():
                    if len(members) <= 1:
                        # Chỉ có 1 tài xế trong nhóm, nhưng hãy chắc chắn tên đã được viết hoa chuẩn
                        d = members[0]
                        if d['name'] != d['clean_name']:
                            # Kiểm tra xem có bị xung đột UNIQUE không
                            cur.execute("SELECT id FROM drivers WHERE name = ? AND id != ?", (d['clean_name'], d['id']))
                            conflict = cur.fetchone()
                            if not conflict:
                                cur.execute("UPDATE drivers SET name = ? WHERE id = ?", (d['clean_name'], d['id']))
                                cur.execute("UPDATE vehicles SET driver_name = ? WHERE driver_name = ?", (d['clean_name'], d['name']))
                        continue

                    # Sắp xếp để chọn tài xế chuẩn (Canonical): nhiều dấu nhất -> viết hoa -> active -> có đầy đủ phone/cccd
                    members.sort(key=lambda x: (
                        x['diacritics'],
                        1 if x['name'].isupper() else 0,
                        x['is_active'],
                        1 if x['phone'] or x['cccd'] else 0
                    ), reverse=True)

                    canonical = members[0]
                    
                    # Cập nhật tên chuẩn thành viết hoa sạch sẽ
                    if canonical['name'] != canonical['clean_name']:
                        # Bỏ qua các ID nằm trong danh sách gộp vì chúng sẽ bị xóa
                        member_ids = [m['id'] for m in members]
                        placeholders = ','.join(['?'] * len(member_ids))
                        cur.execute(
                            f"SELECT id FROM drivers WHERE name = ? AND id NOT IN ({placeholders})", 
                            (canonical['clean_name'], *member_ids)
                        )
                        if not cur.fetchone():
                            cur.execute("UPDATE drivers SET name = ? WHERE id = ?", (canonical['clean_name'], canonical['id']))
                            canonical['name'] = canonical['clean_name']

                    # Gộp các tài xế trùng lặp khác vào tài xế chuẩn
                    for m in members[1:]:
                        # Merge thông tin còn thiếu sang canonical
                        phone_to_update = canonical['phone'] if canonical['phone'] else m['phone']
                        cccd_to_update = canonical['cccd'] if canonical['cccd'] else m['cccd']
                        notes_to_update = canonical['notes'] if canonical['notes'] else m['notes']
                        
                        cur.execute(
                            "UPDATE drivers SET phone=?, cccd=?, notes=? WHERE id=?",
                            (phone_to_update, cccd_to_update, notes_to_update, canonical['id'])
                        )
                        canonical['phone'], canonical['cccd'], canonical['notes'] = phone_to_update, cccd_to_update, notes_to_update

                        # Cập nhật các liên kết dispatches (driver_id)
                        cur.execute("UPDATE dispatches SET driver_id = ? WHERE driver_id = ?", (canonical['id'], m['id']))
                        # Cập nhật driver_name trong lịch sử vehicles
                        cur.execute("UPDATE vehicles SET driver_name = ? WHERE driver_name = ?", (canonical['name'], m['name']))
                        
                        # Xóa tài xế trùng lặp
                        cur.execute("DELETE FROM drivers WHERE id = ?", (m['id'],))
                        total_merged += 1
                        logger.info(f"Merged duplicate driver: '{m['name']}' (ID {m['id']}) -> '{canonical['name']}' (ID {canonical['id']})")

                self.commit_transaction()
                if total_merged > 0:
                    logger.info(f"Driver cleanup: Đã gộp thành công {total_merged} tài xế trùng lặp.")
            except Exception as e:
                self.rollback_transaction()
                logger.error(f"Lỗi khi thực hiện gộp tài xế trùng lặp: {e}")

        except Exception as e:
            logger.warning(f"Driver cleanup bị bỏ qua: {e}")

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
            from data_normalizer import normalize_driver_name as _norm_name
            normalized_name = _norm_name(name)
            
            # Xử lý giá trị cccd rỗng thành NULL để tránh lỗi UNIQUE
            cccd_to_insert = cccd if cccd else None
            with self.conn:
                cursor = self.conn.execute(
                    "INSERT INTO drivers (name, phone, cccd, notes) VALUES (?, ?, ?, ?)",
                    (normalized_name, phone, cccd_to_insert, notes)
                )
                driver_id = cursor.lastrowid
            
            # Cập nhật danh sách in-memory trong normalizer
            try:
                from data_normalizer import normalizer as _normalizer
                if normalized_name not in _normalizer._known_drivers:
                    _normalizer._known_drivers.append(normalized_name)
                    _normalizer._known_drivers.sort(key=lambda x: x.lower())
            except Exception:
                pass
                
            return {"success": True, "message": "Thêm tài xế thành công.", "id": driver_id, "normalized_name": normalized_name}
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: drivers.name" in str(e):
                return {"success": False, "message": f"Tên tài xế '{normalized_name}' đã tồn tại."}
            if "UNIQUE constraint failed: drivers.cccd" in str(e):
                return {"success": False, "message": f"Số CCCD '{cccd}' đã tồn tại."}
            return {"success": False, "message": f"Lỗi trùng lặp dữ liệu: {e}"}
        except Exception as e:
            logger.error(f"Lỗi không xác định khi thêm tài xế: {e}")
            return {"success": False, "message": str(e)}

    def update_driver(self, driver_id, name, phone, cccd, notes):
        """Cập nhật thông tin một tài xế."""
        try:
            from data_normalizer import normalize_driver_name as _norm_name
            normalized_name = _norm_name(name)
            
            cccd_to_update = cccd if cccd else None
            
            # Lấy tên cũ trước khi cập nhật để đồng bộ bảng vehicles
            cur = self.conn.cursor()
            cur.execute("SELECT name FROM drivers WHERE id = ?", (driver_id,))
            old_name_row = cur.fetchone()
            old_name = old_name_row[0] if old_name_row else None
            
            with self.conn:
                self.conn.execute(
                    "UPDATE drivers SET name=?, phone=?, cccd=?, notes=? WHERE id=?",
                    (normalized_name, phone, cccd_to_update, notes, driver_id)
                )
                if old_name and old_name != normalized_name:
                    self.conn.execute(
                        "UPDATE vehicles SET driver_name=? WHERE driver_name=?",
                        (normalized_name, old_name)
                    )
            
            # Refresh list tài xế
            self._refresh_known_drivers()
            
            return {"success": True, "message": "Cập nhật tài xế thành công."}
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: drivers.name" in str(e):
                return {"success": False, "message": f"Tên tài xế '{normalized_name}' đã tồn tại."}
            if "UNIQUE constraint failed: drivers.cccd" in str(e):
                return {"success": False, "message": f"Số CCCD '{cccd}' đã tồn tại."}
            return {"success": False, "message": f"Lỗi trùng lặp dữ liệu: {e}"}
        except Exception as e:
            logger.error(f"Lỗi không xác định khi cập nhật tài xế: {e}")
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