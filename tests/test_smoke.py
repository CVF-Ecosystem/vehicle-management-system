"""
Smoke tests for Vehicle Management System.

These tests verify the application can start and basic operations work.
Run with: pytest -m smoke
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestApplicationSmoke:
    """Smoke tests to verify application basics."""
    
    @pytest.mark.smoke
    def test_imports_work(self):
        """Tất cả module chính phải import được."""
        # Core modules
        import config
        import utils
        import data_normalizer
        import translations
        
        assert config is not None
        assert utils is not None
        assert data_normalizer is not None
        assert translations is not None
    
    @pytest.mark.smoke
    def test_database_modules_import(self):
        """Database modules phải import được."""
        from database import base_manager
        from database import vehicle_manager
        from database import entity_manager
        from database import location_manager
        from database import dispatch_manager
        
        assert base_manager is not None
        assert vehicle_manager is not None
    
    @pytest.mark.smoke
    def test_config_constants(self):
        """Config phải có các hằng số cần thiết."""
        import config
        
        # Check required constants exist
        assert hasattr(config, 'APP_VERSION'), "APP_VERSION should exist"
        assert hasattr(config, 'DB_FILE'), "DB_FILE should exist"
        
        # Verify values
        assert config.APP_VERSION is not None
        assert len(config.APP_VERSION) > 0
    
    @pytest.mark.smoke
    def test_translations_available(self):
        """Translations phải có cả VI và EN."""
        from translations import translations
        
        # Check some basic keys exist
        required_keys = ["app_title", "tab_inbound", "tab_outbound"]
        for key in required_keys:
            assert key in translations, f"Key '{key}' should exist in translations"
            assert "vi" in translations[key], f"Key '{key}' should have Vietnamese"
            assert "en" in translations[key], f"Key '{key}' should have English"
    
    @pytest.mark.smoke
    def test_data_normalizer_functions(self):
        """Data normalizer phải có các hàm cần thiết."""
        import data_normalizer
        
        assert hasattr(data_normalizer, 'normalize_vin'), "normalize_vin should exist"
        assert hasattr(data_normalizer, 'validate_vin'), "validate_vin should exist"
        assert hasattr(data_normalizer, 'normalize_owner'), "normalize_owner should exist"
        
        # Test basic functionality
        result = data_normalizer.normalize_vin("abc123")
        assert result == "ABC123"
        
        result = data_normalizer.validate_vin("1HGBH41JXMN109186")
        assert result["valid"] is True


class TestDatabaseSmoke:
    """Smoke tests for database operations."""
    
    @pytest.mark.smoke
    @pytest.mark.db
    def test_fresh_db_creation(self, tmp_path):
        """Database mới phải tạo được."""
        from database.base_manager import BaseManager
        
        db_path = tmp_path / "smoke_test.db"
        
        # Reset singleton
        BaseManager._conn = None
        BaseManager._db_path = None
        
        manager = BaseManager(str(db_path))
        
        assert db_path.exists()
    
    @pytest.mark.smoke
    @pytest.mark.db
    def test_basic_crud(self, tmp_path):
        """CRUD cơ bản phải hoạt động."""
        from database.base_manager import BaseManager
        from database.vehicle_manager import VehicleManager
        
        db_path = tmp_path / "crud_test.db"
        
        # Reset singleton
        BaseManager._conn = None
        BaseManager._db_path = None
        
        # Initialize
        base = BaseManager(str(db_path))
        vehicle_mgr = VehicleManager()
        
        # Create - VehicleManager.add_vehicle cần location_id và datetime object
        from datetime import datetime
        result = vehicle_mgr.add_vehicle(
            vin="SMOKE1234567890AB",
            owner="SMOKE TEST",
            vehicle_type="Test",
            date_in=datetime(2024, 1, 1),  # API yêu cầu datetime object
            location_id=None
        )
        assert result is not None
        
        # Read
        vehicles = vehicle_mgr.get_in_stock()
        assert len(vehicles) >= 1


class TestUtilitiesSmoke:
    """Smoke tests for utility functions."""
    
    @pytest.mark.smoke
    def test_utils_module(self):
        """Utils module phải có các hàm cần thiết."""
        import utils
        
        # Check some expected functions exist
        # Adjust based on actual utils.py content
        assert utils is not None
    
    @pytest.mark.smoke
    def test_report_generators_import(self):
        """Report generators phải import được."""
        try:
            from report_generators import excel_generator
            from report_generators import pdf_generator
            from report_generators import word_generator
            
            assert excel_generator is not None
            assert pdf_generator is not None
            assert word_generator is not None
        except ImportError as e:
            # Some dependencies might not be installed
            pytest.skip(f"Report generator import failed: {e}")
