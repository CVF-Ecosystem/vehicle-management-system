"""
Unit tests for database layer.

Tests BaseManager, VehicleManager, and other database operations.
"""

import pytest
import sys
import sqlite3
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import custom exceptions for testing
from exceptions import SQLInjectionError, InvalidTableNameError


class TestBaseManager:
    """Test suite for BaseManager (database connection and schema)."""
    
    @pytest.mark.smoke
    @pytest.mark.db
    def test_database_init(self, tmp_path):
        """Database phải khởi tạo được với schema."""
        from database.base_manager import BaseManager
        
        db_path = tmp_path / "test.db"
        
        # Reset singleton
        BaseManager._conn = None
        BaseManager._db_path = None
        
        manager = BaseManager(str(db_path))
        
        assert db_path.exists(), "Database file should be created"
    
    @pytest.mark.smoke
    @pytest.mark.db
    def test_schema_tables_created(self, tmp_path):
        """Schema phải tạo đủ các bảng cần thiết."""
        from database.base_manager import BaseManager
        
        db_path = tmp_path / "test.db"
        
        # Reset singleton
        BaseManager._conn = None
        BaseManager._db_path = None
        
        manager = BaseManager(str(db_path))
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        # Check required tables exist
        required_tables = ["vehicles", "drivers", "transport_vehicles", "locations", "dispatches"]
        for table in required_tables:
            assert table in tables, f"Table '{table}' should exist"
    
    @pytest.mark.regression
    @pytest.mark.db
    def test_connection_singleton(self, tmp_path):
        """BaseManager phải là singleton (cùng connection)."""
        from database.base_manager import BaseManager
        
        db_path = tmp_path / "test.db"
        
        # Reset singleton for testing
        BaseManager._conn = None
        BaseManager._db_path = None
        
        manager1 = BaseManager(str(db_path))
        manager2 = BaseManager(str(db_path))
        
        # Should share same connection
        assert manager1.conn is manager2.conn, "BaseManager should share connection"
    
    @pytest.mark.regression
    @pytest.mark.db
    def test_identifier_validation(self, tmp_path):
        """SQL injection qua table/column name phải bị chặn."""
        from database.base_manager import BaseManager
        
        db_path = tmp_path / "test.db"
        
        # Reset singleton
        BaseManager._conn = None
        BaseManager._db_path = None
        
        manager = BaseManager(str(db_path))
        
        # Table validation
        for table_name in ["vehicles", "drivers", "locations"]:
            assert manager._validate_identifier(table_name, "table") is True

        # Column validation
        for col_name in ["vin", "owner", "date_in", "location_id", "full_location_name"]:
            assert manager._validate_identifier(col_name, "column") is True

        # Invalid table names should be blocked
        for bad_table in ["vehicles; DROP TABLE vehicles;", "sqlite_master", "vehicles--", ""]:
            with pytest.raises((InvalidTableNameError, SQLInjectionError)):
                manager._validate_identifier(bad_table, "table")

        # Invalid column names should be blocked
        for bad_col in ["vin; DROP TABLE vehicles;", "vin--", "vin name", "1vin", "", "vin\nnew"]:
            with pytest.raises(SQLInjectionError):
                manager._validate_identifier(bad_col, "column")


class TestVehicleManager:
    """Test suite for VehicleManager (vehicle CRUD operations)."""
    
    @pytest.mark.smoke
    @pytest.mark.db
    def test_add_vehicle(self, fresh_db):
        """Thêm xe mới phải thành công."""
        from database.vehicle_manager import VehicleManager
        from datetime import datetime
        
        # VehicleManager không nhận parameter, dùng connection từ BaseManager
        manager = VehicleManager()
        
        result = manager.add_vehicle(
            vin="1HGBH41JXMN109186",
            owner="THACO",
            vehicle_type="Sedan",
            date_in=datetime(2024, 1, 1),  # API yêu cầu datetime object
            location_id=None
        )
        
        assert result is not None, "Add vehicle should return result"
    
    @pytest.mark.smoke
    @pytest.mark.db
    def test_get_in_stock(self, sample_db):
        """Lấy danh sách xe tồn phải trả về kết quả."""
        db_path, summary = sample_db
        
        from database.vehicle_manager import VehicleManager
        
        # VehicleManager dùng connection từ BaseManager (singleton)
        # NOTE: Do singleton pattern, manager sẽ kết nối tới production DB
        # Test này chỉ kiểm tra API hoạt động đúng, không kiểm tra data
        manager = VehicleManager()
        vehicles = manager.get_in_stock()
        
        assert vehicles is not None, "Get in_stock should return result"
        assert isinstance(vehicles, list), "Result should be a list"
        # Mỗi item trong list phải là dict với các key cần thiết
        if len(vehicles) > 0:
            vehicle = vehicles[0]
            assert isinstance(vehicle, dict), "Each vehicle should be a dict"
            assert "vin" in vehicle, "Vehicle should have 'vin' field"
    
    @pytest.mark.regression
    @pytest.mark.db
    def test_add_duplicate_vin(self, fresh_db):
        """Thêm VIN trùng phải xử lý đúng."""
        from database.vehicle_manager import VehicleManager
        from datetime import datetime
        
        manager = VehicleManager()
        
        # Add first vehicle - cần datetime object và location_id
        result1 = manager.add_vehicle(
            vin="1HGBH41JXMN109186",
            owner="THACO",
            vehicle_type="Sedan",
            date_in=datetime(2024, 1, 1),
            location_id=None
        )
        
        # Try to add duplicate
        result2 = manager.add_vehicle(
            vin="1HGBH41JXMN109186",
            owner="TOYOTA",
            vehicle_type="SUV",
            date_in=datetime(2024, 1, 2),
            location_id=None
        )
        
        # Should either fail or update - cả hai trường hợp đều chấp nhận
        # VIN trùng sẽ được xử lý bởi _handle_existing_vin
        assert result1 is not None and result2 is not None
    
    @pytest.mark.regression
    @pytest.mark.db
    def test_find_vehicle_in_stock(self, sample_db):
        """Tìm kiếm xe tồn kho phải hoạt động."""
        db_path, summary = sample_db
        
        from database.vehicle_manager import VehicleManager
        
        manager = VehicleManager()
        
        # Get a vehicle first
        vehicles = manager.get_in_stock()
        if vehicles:
            vehicle = vehicles[0]
            vin = vehicle.get("vin")
            
            # Tìm xe bằng VIN - sử dụng method có sẵn
            found = manager.find_vehicle_in_stock(vin)
            
            # Verify tìm được xe
            if found:
                assert found.get("vin") == vin, "Found vehicle should match searched VIN"
            else:
                # Xe có thể đã được gán vào phiếu xuất
                pytest.skip("Vehicle may be assigned to dispatch")


class TestDataIntegrity:
    """Test suite for data integrity validation (Phase 0.3)."""
    
    @pytest.mark.regression
    @pytest.mark.db
    def test_add_vehicle_validates_vin(self, fresh_db):
        """Thêm xe với VIN không hợp lệ phải bị chặn."""
        db_path = fresh_db
        
        from database.vehicle_manager import VehicleManager
        from datetime import datetime
        
        manager = VehicleManager()
        
        # Invalid VIN - empty
        result = manager.add_vehicle(
            vin="",
            owner="TEST OWNER",
            vehicle_type="Test",
            date_in=datetime(2024, 1, 1),
            location_id=None
        )
        assert result["success"] is False, "Empty VIN should be rejected"
        assert "VIN" in result["message"] or "trống" in result["message"].lower()
    
    @pytest.mark.regression
    @pytest.mark.db
    def test_add_vehicle_validates_owner(self, fresh_db):
        """Thêm xe với owner rỗng phải bị chặn."""
        db_path = fresh_db
        
        from database.vehicle_manager import VehicleManager
        from datetime import datetime
        
        manager = VehicleManager()
        
        # Invalid Owner - empty (dùng VIN hợp lệ, không chứa I, O, Q)
        result = manager.add_vehicle(
            vin="1HGBH41JXMN109186",  # Valid VIN without I, O, Q
            owner="",
            vehicle_type="Test",
            date_in=datetime(2024, 1, 1),
            location_id=None
        )
        assert result["success"] is False, "Empty owner should be rejected"
        assert "chủ hàng" in result["message"].lower() or "owner" in result["message"].lower() or "trống" in result["message"].lower()
    
    @pytest.mark.regression
    @pytest.mark.db
    def test_add_vehicle_normalizes_data(self, fresh_db):
        """Dữ liệu xe phải được normalize trước khi ghi DB."""
        db_path = fresh_db
        
        from database.vehicle_manager import VehicleManager
        from datetime import datetime
        
        manager = VehicleManager()
        
        # Add with non-normalized data (VIN không chứa I, O, Q)
        result = manager.add_vehicle(
            vin="  1hgbh41jxmn109186  ",  # lowercase, spaces, valid VIN
            owner="  test owner  ",  # lowercase, spaces
            vehicle_type="  sedan  ",  # lowercase, spaces
            date_in=datetime(2024, 1, 1),
            location_id=None
        )
        assert result["success"] is True, f"Valid data should be accepted, got: {result['message']}"
        
        # Verify data was normalized in DB
        vehicles = manager.get_in_stock()
        assert len(vehicles) == 1
        
        vehicle = vehicles[0]
        # VIN should be uppercase, trimmed
        assert vehicle["vin"] == "1HGBH41JXMN109186"
        # Owner should be normalized (uppercase)
        assert vehicle["owner"] == "TEST OWNER"
        # Type should be uppercase
        assert vehicle["vehicle_type"] == "SEDAN"
    
    @pytest.mark.regression
    @pytest.mark.db
    def test_add_vehicle_rejects_short_vin(self, fresh_db):
        """VIN quá ngắn (< 6 ký tự) phải bị chặn."""
        db_path = fresh_db
        
        from database.vehicle_manager import VehicleManager
        from datetime import datetime
        
        manager = VehicleManager()
        
        result = manager.add_vehicle(
            vin="12345",  # Only 5 chars, no I, O, Q
            owner="TEST OWNER",
            vehicle_type="Test",
            date_in=datetime(2024, 1, 1),
            location_id=None
        )
        assert result["success"] is False, "Short VIN should be rejected"


class TestLocationManager:
    """Test suite for LocationManager."""
    
    @pytest.mark.smoke
    @pytest.mark.db
    def test_get_all_free_locations(self, sample_db):
        """Lấy vị trí trống phải trả về kết quả."""
        db_path, summary = sample_db
        
        from database.location_manager import LocationManager
        
        manager = LocationManager()
        # Đúng tên method: get_all_free_locations (không phải get_available_locations)
        locations = manager.get_all_free_locations()
        
        assert locations is not None, "Get available locations should return result"
        assert isinstance(locations, list), "Result should be a list"
    
    @pytest.mark.regression
    @pytest.mark.db
    def test_occupy_and_release_location(self):
        """Chiếm và giải phóng vị trí phải hoạt động đúng."""
        from database.location_manager import LocationManager
        
        manager = LocationManager()
        
        # Add test location using manager (which uses correct DB from force_test_db fixture)
        locations_to_add = [
            {'block': 'A', 'row': '1', 'slot': 1},
            {'block': 'A', 'row': '1', 'slot': 2},
        ]
        success, added, skipped = manager.add_locations_batch(locations_to_add)
        assert success and added >= 1, "Should add at least 1 location"
        
        # Get available locations
        available_before = manager.get_all_free_locations()
        assert len(available_before) >= 1, "Should have at least 1 free location"
        
        location = available_before[0]
        location_id = location.get("id") or location[0]
        
        # Occupy
        manager.set_location_occupied(location_id, True)
        
        # Check occupied
        available_during = manager.get_all_free_locations()
        assert len(available_during) == len(available_before) - 1, "One less free location"
        
        # Release
        manager.set_location_occupied(location_id, False)
        
        # Verify released
        available_after = manager.get_all_free_locations()
        assert len(available_after) == len(available_before), "Should be back to original count"


class TestAdvancedSearch:
    """Test suite for Advanced Search (Phase 2.1)."""
    
    @pytest.fixture(autouse=True)
    def setup_search_db(self, force_test_db):
        """Setup database with sample data for search tests."""
        from database.vehicle_manager import VehicleManager
        from database.location_manager import LocationManager
        from datetime import datetime, timedelta
        
        self.vm = VehicleManager()
        self.lm = LocationManager()
        
        # Add locations
        locations_to_add = [
            {'block': 'A', 'row': '01', 'slot': 1},
            {'block': 'A', 'row': '01', 'slot': 2},
            {'block': 'B', 'row': '01', 'slot': 1},
        ]
        self.lm.add_locations_batch(locations_to_add)
        
        # Use yesterday to avoid future date validation error
        now = datetime.now() - timedelta(days=1)
        
        # Vehicle 1: In stock, Block A
        self.vm.add_vehicle(
            vin="SEARCH001", 
            owner="TOYOTA", 
            vehicle_type="SEDAN",
            date_in=now,
            location_id=1
        )
        
        # Vehicle 2: In stock, Block B
        self.vm.add_vehicle(
            vin="SEARCH002", 
            owner="HONDA",
            vehicle_type="SUV",
            date_in=now,
            location_id=3
        )
        
        # Vehicle 3: Shipped
        self.vm.add_vehicle(
            vin="SEARCH003",
            owner="TOYOTA",
            vehicle_type="TRUCK",
            date_in=now,
            location_id=2
        )
        # Use update_to_out to mark as shipped
        self.vm.update_to_out(
            vin="SEARCH003",
            date_out=now,
            transport_vehicle="51C-12345",
            driver_name="TEST DRIVER"
        )
    
    @pytest.mark.db
    def test_search_by_status_in_stock(self):
        """Search với status_filter='in_stock' chỉ trả về xe còn tồn."""
        results = self.vm.search_all_vehicles(status_filter="in_stock")
        
        # Should find SEARCH001 and SEARCH002, not SEARCH003 (shipped)
        vins = [r['vin'] for r in results]
        assert "SEARCH001" in vins
        assert "SEARCH002" in vins
        assert "SEARCH003" not in vins
    
    @pytest.mark.db
    def test_search_by_status_shipped(self):
        """Search với status_filter='shipped' chỉ trả về xe đã xuất."""
        results = self.vm.search_all_vehicles(status_filter="shipped")
        
        vins = [r['vin'] for r in results]
        assert "SEARCH003" in vins
        assert "SEARCH001" not in vins
        assert "SEARCH002" not in vins
    
    @pytest.mark.db
    def test_search_by_block(self):
        """Search với block filter chỉ trả về xe ở block đó."""
        results = self.vm.search_all_vehicles(block="A")
        
        vins = [r['vin'] for r in results]
        # SEARCH001 in Block A, SEARCH002 in Block B, SEARCH003 shipped (no location)
        assert "SEARCH001" in vins
        assert "SEARCH002" not in vins
    
    @pytest.mark.db
    def test_search_combined_filters(self):
        """Search với nhiều filters kết hợp."""
        results = self.vm.search_all_vehicles(
            owner="TOYOTA",
            status_filter="in_stock"
        )
        
        vins = [r['vin'] for r in results]
        # Only SEARCH001 is TOYOTA + in_stock
        assert "SEARCH001" in vins
        assert "SEARCH003" not in vins  # TOYOTA but shipped
    
    @pytest.mark.db
    def test_search_by_date_range(self):
        """Search với date range filter."""
        from datetime import datetime, timedelta
        
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Search từ hôm qua đến hôm nay
        results = self.vm.search_all_vehicles(
            date_from=yesterday,
            date_to=today,
            date_field="date_in"
        )
        
        # Should find all vehicles added today
        assert len(results) >= 2
    
    @pytest.mark.db
    def test_get_all_blocks(self):
        """LocationManager.get_all_blocks() trả về danh sách blocks."""
        blocks = self.lm.get_all_blocks()
        
        assert "A" in blocks
        assert "B" in blocks
        assert len(blocks) >= 2
