# database/dispatch_manager.py
import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
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
                created_at = datetime.now().isoformat()
                cursor.execute("""
                    INSERT INTO dispatches (driver_id, transport_vehicle_id, created_at, status)
                    VALUES (?, ?, ?, ?)
                """, (driver_id, transport_vehicle_id, created_at, STATUS_SHIPMENT_OPEN))
                new_id = cursor.lastrowid

            try:
                from database.audit_repository import log_audit, AuditAction

                log_audit(
                    action=AuditAction.CREATE,
                    table_name="dispatches",
                    record_id=str(new_id),
                    new_value={
                        "id": new_id,
                        "driver_id": driver_id,
                        "transport_vehicle_id": transport_vehicle_id,
                        "created_at": created_at,
                        "status": STATUS_SHIPMENT_OPEN,
                    },
                    details={"source": "DispatchManager.create_dispatch"},
                )
            except Exception:
                pass

            return new_id
        except Exception as e:
            logger.error(f"Lỗi khi tạo phiếu xuất: {e}")
            return None

    def add_vehicle_to_dispatch(self, vin, dispatch_id):
        """Gán một xe vào một phiếu xuất đang mở."""
        try:
            with self.conn:
                cur = self.conn.cursor()
                # Check if vehicle exists
                cur.execute("SELECT dispatch_id FROM vehicles WHERE vin = ?", (vin,))
                row = cur.fetchone()
                
                if not row:
                    # Vehicle doesn't exist
                    return False
                    
                old_dispatch_id = row["dispatch_id"] if row and "dispatch_id" in row.keys() else (row[0] if row else None)

                # Update vehicle's dispatch_id
                self.conn.execute("UPDATE vehicles SET dispatch_id = ? WHERE vin = ?", (dispatch_id, vin))

            try:
                from database.audit_repository import log_update

                log_update(
                    table_name="vehicles",
                    record_id=str(vin),
                    old_value={"dispatch_id": old_dispatch_id},
                    new_value={"dispatch_id": dispatch_id},
                )
            except Exception:
                pass
            
            return True
        except Exception as e:
            logger.error(f"Lỗi khi gán xe vào phiếu xuất: {e}")
            return False

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
            logger.error(f"Lỗi khi lấy chi tiết phiếu xuất đang mở: {e}")
            return {}

    def cancel_dispatch(self, dispatch_id):
        """Hủy một phiếu xuất đang mở."""
        self.begin_transaction()
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT vin FROM vehicles WHERE dispatch_id = ?", (dispatch_id,))
            vins = [r["vin"] if "vin" in r.keys() else r[0] for r in cur.fetchall()]

            self.conn.execute("UPDATE vehicles SET dispatch_id = NULL WHERE dispatch_id = ?", (dispatch_id,))
            self.conn.execute("DELETE FROM dispatches WHERE id = ?", (dispatch_id,))
            self.commit_transaction()

            try:
                from database.audit_repository import log_audit, AuditAction

                log_audit(
                    action=AuditAction.DELETE,
                    table_name="dispatches",
                    record_id=str(dispatch_id),
                    details={
                        "source": "DispatchManager.cancel_dispatch",
                        "vehicles_unassigned": len(vins),
                        "vins_sample": vins[:20],
                    },
                )
            except Exception:
                pass

            logger.info(f"Đã hủy thành công phiếu xuất #{dispatch_id}.")
            return {"success": True, "message": f"Đã hủy phiếu xuất #{dispatch_id}."}
        except Exception as e:
            self.rollback_transaction()
            logger.error(f"Lỗi khi hủy phiếu xuất #{dispatch_id}: {e}")
            return {"success": False, "message": str(e)}

    def complete_dispatch(self, dispatch_id):
        """
        Hoàn tất một phiếu xuất: cập nhật trạng thái xe và giải phóng vị trí.
        FIXED Issue #10: Wrapped in transaction for atomicity.
        """
        # BEGIN TRANSACTION - All-or-nothing operation
        self.begin_transaction()
        try:
            cur = self.conn.cursor()
            
            # Step 1: Get dispatch info
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

            # Step 2: Get locations to free
            cur.execute("SELECT location_id FROM vehicles WHERE dispatch_id = ? AND location_id IS NOT NULL", (dispatch_id,))
            location_ids_to_free = [row['location_id'] for row in cur.fetchall()]

            # Step 3: Get VINs to ship
            cur.execute("SELECT vin FROM vehicles WHERE dispatch_id = ? AND status = ?", (dispatch_id, STATUS_IN_STOCK))
            vins_to_ship = [r["vin"] if "vin" in r.keys() else r[0] for r in cur.fetchall()]

            date_out_iso = datetime.now().isoformat()
            
            # Step 4: Update vehicles status (CRITICAL - must be atomic)
            cur.execute("""
                UPDATE vehicles
                SET status = ?, date_out = ?, driver_name = ?, transport_vehicle = ?, location_id = NULL
                WHERE dispatch_id = ? AND status = ?
            """, (STATUS_SHIPPED, date_out_iso, dispatch_info['driver_name'], dispatch_info['license_plate'], dispatch_id, STATUS_IN_STOCK))
            
            num_updated = cur.rowcount

            # Step 5: Update dispatch status
            self.conn.execute("UPDATE dispatches SET status = ?, completed_at = ? WHERE id = ?", (STATUS_SHIPMENT_COMPLETED, date_out_iso, dispatch_id))
            
            # Step 6: Free locations (within same transaction)
            if location_ids_to_free:
                for loc_id in location_ids_to_free:
                    self.location_manager.set_location_occupied(loc_id, False)
                logger.info(f"Đã giải phóng {len(location_ids_to_free)} vị trí cho phiếu xuất #{dispatch_id}.")

            # COMMIT TRANSACTION - All operations succeeded
            self.commit_transaction()
            
            logger.info(f"Successfully completed dispatch #{dispatch_id} with {num_updated} vehicles (ATOMIC)")

            # Audit logging (after successful commit)
            try:
                from database.audit_repository import log_audit, AuditAction

                log_audit(
                    action=AuditAction.UPDATE,
                    table_name="dispatches",
                    record_id=str(dispatch_id),
                    new_value={"status": STATUS_SHIPMENT_COMPLETED, "completed_at": date_out_iso},
                    details={
                        "source": "DispatchManager.complete_dispatch",
                        "vehicles_shipped": num_updated,
                        "driver_name": dispatch_info.get("driver_name"),
                        "transport_vehicle": dispatch_info.get("license_plate"),
                        "vins_sample": vins_to_ship[:20],
                    },
                )

                # Batch audit for vehicles
                if vins_to_ship:
                    log_audit(
                        action=AuditAction.UPDATE,
                        table_name="vehicles",
                        record_id=f"dispatch:{dispatch_id}",
                        new_value={
                            "status": STATUS_SHIPPED,
                            "date_out": date_out_iso,
                            "driver_name": dispatch_info.get("driver_name"),
                            "transport_vehicle": dispatch_info.get("license_plate"),
                            "location_id": None,
                        },
                        details={
                            "source": "DispatchManager.complete_dispatch",
                            "vins_count": len(vins_to_ship),
                            "vins_sample": vins_to_ship[:50],
                        },
                    )
            except Exception as e:
                logger.warning(f"Audit logging failed (non-critical): {e}")

            return {"success": True, "message": f"Đã hoàn tất phiếu xuất, {num_updated} xe đã được xuất kho."}
            
        except Exception as e:
            # ROLLBACK on any error - maintain data integrity
            self.rollback_transaction()
            logger.error(f"Lỗi khi hoàn tất phiếu xuất {dispatch_id} - ROLLED BACK: {e}")
            return {"success": False, "message": f"Lỗi: {e}. Tất cả thay đổi đã được hoàn tác."}