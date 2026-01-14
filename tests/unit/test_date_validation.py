# tests/unit/test_date_validation.py
"""
Unit tests for Issue #4: Future Date Validation
Tests date validation preventing future dates for vehicle entry.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.vehicle_manager import VehicleManager
from exceptions import DateValidationError, VINValidationError


class TestDateValidation:
    """Test future date validation for vehicle date_in."""
    
    @pytest.fixture
    def vehicle_manager(self, tmp_path):
        """Create VehicleManager with temporary database."""
        import config
        # Use temporary database
        original_db = config.DB_FILE
        config.DB_FILE = str(tmp_path / "test_vehicles.db")
        
        vm = VehicleManager()
        
        yield vm
        
        # Restore original config
        config.DB_FILE = original_db
    
    def test_current_date_accepted(self, vehicle_manager):
        """Test that current date/time is accepted."""
        now = datetime.now(timezone.utc)
        
        # Should not raise exception
        result = vehicle_manager._validate_vehicle_data(
            vin="1HGBH41JXMN109186",
            owner="Test Owner",
            date_in=now
        )
        
        assert result['valid'] is True
    
    def test_past_date_accepted(self, vehicle_manager):
        """Test that past dates are accepted."""
        past_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        result = vehicle_manager._validate_vehicle_data(
            vin="1HGBH41JXMN109186",
            owner="Test Owner",
            date_in=past_date
        )
        
        assert result['valid'] is True
    
    def test_future_date_rejected(self, vehicle_manager):
        """Test that future dates are rejected."""
        future_date = datetime.now(timezone.utc) + timedelta(days=1)
        
        with pytest.raises(DateValidationError) as exc_info:
            vehicle_manager._validate_vehicle_data(
                vin="1HGBH41JXMN109186",
                owner="Test Owner",
                date_in=future_date
            )
        
        assert "tương lai" in str(exc_info.value).lower()
    
    def test_far_future_date_rejected(self, vehicle_manager):
        """Test that dates far in future (year 2099) are rejected."""
        future_date = datetime(2099, 12, 31, tzinfo=timezone.utc)
        
        with pytest.raises(DateValidationError):
            vehicle_manager._validate_vehicle_data(
                vin="1HGBH41JXMN109186",
                owner="Test Owner",
                date_in=future_date
            )
    
    def test_tomorrow_rejected(self, vehicle_manager):
        """Test that tomorrow's date is rejected."""
        tomorrow = datetime.now(timezone.utc) + timedelta(hours=25)
        
        with pytest.raises(DateValidationError):
            vehicle_manager._validate_vehicle_data(
                vin="1HGBH41JXMN109186",
                owner="Test Owner",
                date_in=tomorrow
            )
    
    def test_one_minute_future_rejected(self, vehicle_manager):
        """Test that even 1 minute in future is rejected."""
        one_min_future = datetime.now(timezone.utc) + timedelta(minutes=1)
        
        with pytest.raises(DateValidationError):
            vehicle_manager._validate_vehicle_data(
                vin="1HGBH41JXMN109186",
                owner="Test Owner",
                date_in=one_min_future
            )
    
    def test_one_year_ago_accepted(self, vehicle_manager):
        """Test that dates one year in past are accepted."""
        one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)
        
        result = vehicle_manager._validate_vehicle_data(
            vin="1HGBH41JXMN109186",
            owner="Test Owner",
            date_in=one_year_ago
        )
        
        assert result['valid'] is True
    
    def test_invalid_date_type_rejected(self, vehicle_manager):
        """Test that non-datetime objects are rejected."""
        with pytest.raises(DateValidationError):
            vehicle_manager._validate_vehicle_data(
                vin="1HGBH41JXMN109186",
                owner="Test Owner",
                date_in="2026-01-15"  # String instead of datetime
            )
    
    def test_none_date_handled(self, vehicle_manager):
        """Test that None date is handled (defaults to current)."""
        result = vehicle_manager._validate_vehicle_data(
            vin="1HGBH41JXMN109186",
            owner="Test Owner",
            date_in=None
        )
        
        # Should not raise exception
        assert result['valid'] is True


class TestTimezoneHandling:
    """Test UTC timezone handling (Issue #11)."""
    
    @pytest.fixture
    def vehicle_manager(self, tmp_path):
        import config
        original_db = config.DB_FILE
        config.DB_FILE = str(tmp_path / "test_tz.db")
        vm = VehicleManager()
        yield vm
        config.DB_FILE = original_db
    
    def test_utc_timezone_used(self, vehicle_manager):
        """Test that validation uses UTC timezone."""
        # Create timezone-aware datetime in UTC
        utc_now = datetime.now(timezone.utc)
        
        result = vehicle_manager._validate_vehicle_data(
            vin="1HGBH41JXMN109186",
            owner="Test Owner",
            date_in=utc_now
        )
        
        assert result['valid'] is True
    
    def test_timezone_aware_date_accepted(self, vehicle_manager):
        """Test that timezone-aware dates are handled correctly."""
        # Date in different timezone (should still compare correctly)
        import pytz
        tokyo_tz = pytz.timezone('Asia/Tokyo')
        tokyo_time = datetime.now(tokyo_tz)
        
        # Convert to UTC
        utc_time = tokyo_time.astimezone(timezone.utc)
        
        # Should be accepted as current time
        result = vehicle_manager._validate_vehicle_data(
            vin="1HGBH41JXMN109186",
            owner="Test Owner",
            date_in=utc_time
        )
        
        assert result['valid'] is True
    
    def test_naive_datetime_handled(self, vehicle_manager):
        """Test that naive datetime (no timezone) is handled."""
        # Naive datetime (no timezone info) - use past date to avoid future date issue
        naive_past = datetime.now() - timedelta(days=1)
        
        # Should still work (converted to UTC and treated as valid)
        result = vehicle_manager._validate_vehicle_data(
            vin="1HGBH41JXMN109186",
            owner="Test Owner",
            date_in=naive_past
        )
        
        assert result['valid'] is True


class TestDateValidationIntegration:
    """Integration tests for date validation in add_vehicle."""
    
    @pytest.fixture
    def vehicle_manager(self, tmp_path):
        import config
        original_db = config.DB_FILE
        config.DB_FILE = str(tmp_path / "test_integration.db")
        vm = VehicleManager()
        yield vm
        config.DB_FILE = original_db
    
    def test_add_vehicle_with_future_date_fails(self, vehicle_manager):
        """Test that add_vehicle rejects future dates."""
        future_date = datetime.now(timezone.utc) + timedelta(days=5)
        
        # add_vehicle catches DateValidationError and returns error dict
        result = vehicle_manager.add_vehicle(
            vin="1HGBH41JXMN109186",
            owner="Test Owner",
            vehicle_type="Sedan",
            date_in=future_date,
            location_id=None
        )
        
        assert result['success'] is False
        assert "tương lai" in result['message'].lower() or "future" in result['message'].lower()
    
    def test_add_vehicle_with_valid_date_succeeds(self, vehicle_manager):
        """Test that add_vehicle accepts valid past date."""
        past_date = datetime.now(timezone.utc) - timedelta(days=10)
        
        result = vehicle_manager.add_vehicle(
            vin="1HGBH41JXMN109186",
            owner="Test Owner",
            vehicle_type="Sedan",
            date_in=past_date,
            location_id=None
        )
        
        assert result['success'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
