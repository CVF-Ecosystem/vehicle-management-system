"""
tests/test_logic_pytest.py
==========================
Pytest-compatible version of test_full_logic.py.
Refactored from custom test runner to standard pytest assertions (CQ-4.2).

Run with: pytest tests/test_logic_pytest.py -v
"""

import sqlite3
import pytest
from datetime import datetime, timedelta


# =============================================================================
# 1. DATABASE STRUCTURE TESTS
# =============================================================================

class TestDatabaseStructure:
    """Kiểm tra cấu trúc database."""

    @pytest.mark.db
    def test_required_tables_exist(self, fresh_db):
        """Tất cả bảng bắt buộc phải tồn tại."""
        conn = sqlite3.connect(str(fresh_db))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r['name'] for r in cur.fetchall()}
        conn.close()

        required_tables = ['vehicles', 'locations', 'dispatches', 'users', 'drivers']
        for table in required_tables:
            assert table in tables, f"Bảng '{table}' không tồn tại trong database"

    @pytest.mark.db
    def test_vehicles_schema(self, fresh_db):
        """Bảng vehicles phải có đủ các cột bắt buộc."""
        conn = sqlite3.connect(str(fresh_db))
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(vehicles)")
        cols = {r[1] for r in cur.fetchall()}
        conn.close()

        required_cols = ['vin', 'owner', 'vehicle_type', 'status', 'date_in',
                         'location_id', 'is_active', 'is_deleted']
        for col in required_cols:
            assert col in cols, f"Cột 'vehicles.{col}' không tồn tại"

    @pytest.mark.db
    def test_locations_schema(self, fresh_db):
        """Bảng locations phải có đủ các cột bắt buộc."""
        conn = sqlite3.connect(str(fresh_db))
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(locations)")
        cols = {r[1] for r in cur.fetchall()}
        conn.close()

        required_cols = ['id', 'block', 'row', 'slot', 'full_location_name', 'is_occupied']
        for col in required_cols:
            assert col in cols, f"Cột 'locations.{col}' không tồn tại"

    @pytest.mark.db
    def test_no_null_vins(self, fresh_db):
        """Không được có VIN NULL hoặc rỗng trong database."""
        conn = sqlite3.connect(str(fresh_db))
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM vehicles WHERE vin IS NULL OR vin = ''")
        null_vins = cur.fetchone()[0]
        conn.close()
        assert null_vins == 0, f"Tìm thấy {null_vins} xe có VIN NULL/rỗng"


# =============================================================================
# 2. VEHICLE MANAGER TESTS
# =============================================================================

class TestVehicleManager:
    """Kiểm tra VehicleManager."""

    @pytest.mark.db
    def test_get_in_stock_count_returns_int(self, fresh_db):
        """get_in_stock_count() phải trả về int."""
        from database.vehicle_manager import VehicleManager
        vm = VehicleManager()
        count = vm.get_in_stock_count()
        assert isinstance(count, int), f"get_in_stock_count() trả về {type(count)}, mong đợi int"
        assert count >= 0

    @pytest.mark.db
    def test_get_in_stock_returns_list(self, fresh_db):
        """get_in_stock() phải trả về list."""
        from database.vehicle_manager import VehicleManager
        vm = VehicleManager()
        data = vm.get_in_stock(limit=10, offset=0)
        assert isinstance(data, list), f"get_in_stock() trả về {type(data)}, mong đợi list"

    @pytest.mark.db
    def test_get_in_stock_has_vin_field(self, fresh_db):
        """Mỗi item trong get_in_stock() phải có trường 'vin'."""
        from database.vehicle_manager import VehicleManager
        vm = VehicleManager()
        # Add a vehicle first
        result = vm.add_vehicle(
            vin="1HGBH41JXMN109999",
            owner="TEST OWNER",
            vehicle_type="Sedan",
            date_in=datetime(2024, 1, 1),
            location_id=None
        )
        assert result["success"] is True

        data = vm.get_in_stock(limit=10, offset=0)
        assert len(data) >= 1
        assert 'vin' in data[0], "Dữ liệu thiếu trường 'vin'"

    @pytest.mark.db
    def test_get_vins_ordered_by_id_returns_list(self, fresh_db):
        """get_vins_ordered_by_id() phải trả về list."""
        from database.vehicle_manager import VehicleManager
        vm = VehicleManager()
        result = vm.get_vins_ordered_by_id(['TEST1', 'TEST2', 'TEST3'])
        assert isinstance(result, list)

    @pytest.mark.db
    def test_empty_vin_list_returns_empty(self, fresh_db):
        """get_vins_ordered_by_id([]) phải trả về []."""
        from database.vehicle_manager import VehicleManager
        vm = VehicleManager()
        result = vm.get_vins_ordered_by_id([])
        assert result == [], f"Empty list trả về: {result}"

    @pytest.mark.db
    def test_nonexistent_vin_returns_none(self, fresh_db):
        """get_vehicle_by_vin() với VIN không tồn tại phải trả về None."""
        from database.vehicle_manager import VehicleManager
        vm = VehicleManager()
        result = vm.get_vehicle_by_vin("NON_EXISTENT_VIN_12345")
        assert result is None

    @pytest.mark.db
    def test_owner_filter_works(self, fresh_db):
        """Lọc theo owner phải hoạt động."""
        from database.vehicle_manager import VehicleManager
        vm = VehicleManager()
        count = vm.get_in_stock_count(owner_filter="OWNER_THAT_DOES_NOT_EXIST_12345")
        assert count == 0, f"Owner không tồn tại nhưng trả về {count}"

    @pytest.mark.db
    def test_large_offset_returns_empty(self, fresh_db):
        """Offset lớn phải trả về list rỗng."""
        from database.vehicle_manager import VehicleManager
        vm = VehicleManager()
        data = vm.get_in_stock(limit=10, offset=999999)
        assert data == [], f"Large offset trả về {len(data)} items"

    @pytest.mark.db
    def test_add_vehicle_success(self, fresh_db):
        """add_vehicle() phải thành công với dữ liệu hợp lệ."""
        from database.vehicle_manager import VehicleManager
        vm = VehicleManager()
        result = vm.add_vehicle(
            vin="1HGBH41JXMN109186",
            owner="THACO",
            vehicle_type="Sedan",
            date_in=datetime(2024, 6, 15),
            location_id=None
        )
        assert result["success"] is True, f"add_vehicle thất bại: {result['message']}"

    @pytest.mark.db
    def test_add_vehicle_duplicate_vin(self, fresh_db):
        """Thêm VIN trùng phải xử lý gracefully (không crash)."""
        from database.vehicle_manager import VehicleManager
        vm = VehicleManager()
        vin = "1HGBH41JXMN109186"
        vm.add_vehicle(vin=vin, owner="THACO", vehicle_type="Sedan",
                       date_in=datetime(2024, 6, 15), location_id=None)
        # Second add should not raise exception
        result = vm.add_vehicle(vin=vin, owner="THACO", vehicle_type="Sedan",
                                date_in=datetime(2024, 6, 15), location_id=None)
        assert isinstance(result, dict)
        assert "success" in result


# =============================================================================
# 3. LOCATION MANAGER TESTS
# =============================================================================

class TestLocationManager:
    """Kiểm tra LocationManager."""

    @pytest.mark.db
    def test_get_all_free_locations_returns_list(self, fresh_db):
        """get_all_free_locations() phải trả về list."""
        from database.location_manager import LocationManager
        lm = LocationManager()
        free_locs = lm.get_all_free_locations()
        assert isinstance(free_locs, list)

    @pytest.mark.db
    def test_get_all_blocks_returns_list(self, fresh_db):
        """get_all_blocks() phải trả về list."""
        from database.location_manager import LocationManager
        lm = LocationManager()
        blocks = lm.get_all_blocks()
        assert isinstance(blocks, list)


# =============================================================================
# 4. CODE CONSISTENCY TESTS
# =============================================================================

class TestCodeConsistency:
    """Kiểm tra tính nhất quán của code."""

    def test_status_constants_exist(self):
        """STATUS constants phải tồn tại và có giá trị đúng."""
        from config import STATUS_IN_STOCK, STATUS_SHIPPED
        assert STATUS_IN_STOCK == "IN_STOCK", f"STATUS_IN_STOCK sai: {STATUS_IN_STOCK}"
        assert STATUS_SHIPPED == "SHIPPED", f"STATUS_SHIPPED sai: {STATUS_SHIPPED}"

    def test_translations_have_required_keys(self):
        """Translations phải có các key bắt buộc với cả vi và en."""
        from translations import translations
        required_keys = ['app_title', 'tab_inbound', 'tab_outbound', 'tab_stock']
        for key in required_keys:
            assert key in translations, f"Translation key '{key}' không tồn tại"
            assert 'vi' in translations[key], f"Key '{key}' thiếu bản dịch tiếng Việt"
            assert 'en' in translations[key], f"Key '{key}' thiếu bản dịch tiếng Anh"

    def test_config_has_required_constants(self):
        """Config phải có đủ các hằng số bắt buộc."""
        import config
        required_attrs = ['APP_VERSION', 'DB_FILE', 'STATUS_IN_STOCK', 'STATUS_SHIPPED',
                          'FONT_FAMILY', 'FONT_SIZE_NORMAL']
        for attr in required_attrs:
            assert hasattr(config, attr), f"config.{attr} không tồn tại"

    def test_app_version_semver(self):
        """APP_VERSION phải theo định dạng SemVer (x.y.z)."""
        from config import APP_VERSION
        parts = APP_VERSION.split('.')
        assert len(parts) == 3, f"APP_VERSION '{APP_VERSION}' không theo SemVer (x.y.z)"
        for part in parts:
            assert part.isdigit(), f"APP_VERSION '{APP_VERSION}' chứa phần không phải số: '{part}'"

    def test_exceptions_hierarchy(self):
        """Exception hierarchy phải đúng."""
        from exceptions import (
            VehicleManagementError, DatabaseError, ValidationError,
            BusinessError, VINValidationError, DuplicateVINError
        )
        assert issubclass(DatabaseError, VehicleManagementError)
        assert issubclass(ValidationError, VehicleManagementError)
        assert issubclass(BusinessError, VehicleManagementError)
        assert issubclass(VINValidationError, ValidationError)
        assert issubclass(DuplicateVINError, BusinessError)


# =============================================================================
# 5. VIN VALIDATION TESTS
# =============================================================================

class TestVINValidation:
    """Kiểm tra validate VIN."""

    def test_valid_vin_passes(self):
        """VIN hợp lệ 17 ký tự phải pass."""
        from data_normalizer import validate_vin
        result = validate_vin("1HGBH41JXMN109186")
        assert result["valid"] is True

    def test_empty_vin_fails(self):
        """VIN rỗng phải fail."""
        from data_normalizer import validate_vin
        result = validate_vin("")
        assert result["valid"] is False

    def test_vin_with_invalid_chars_fails(self):
        """VIN chứa I, O, Q phải fail."""
        from data_normalizer import validate_vin
        result = validate_vin("1HGBH41JXIN109186")  # Contains I
        assert result["valid"] is False

    def test_short_vin_flexible_mode(self):
        """VIN ngắn (6-17 ký tự) phải pass trong flexible mode."""
        from data_normalizer import validate_vin
        result = validate_vin("ABC123", strict=False)
        assert result["valid"] is True

    def test_short_vin_strict_mode_fails(self):
        """VIN ngắn phải fail trong strict mode."""
        from data_normalizer import validate_vin
        result = validate_vin("ABC123", strict=True)
        assert result["valid"] is False

    def test_vin_normalized_to_uppercase(self):
        """VIN phải được normalize thành uppercase."""
        from data_normalizer import validate_vin
        result = validate_vin("1hgbh41jxmn109186")
        assert result["normalized"] == "1HGBH41JXMN109186"
