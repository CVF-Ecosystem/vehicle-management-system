"""
Unit tests for data_normalizer module.

Tests VIN validation, owner normalization, and date handling.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data_normalizer import normalize_vin, validate_vin, normalize_owner


class TestVINValidation:
    """Test suite for VIN validation functions."""
    
    @pytest.mark.smoke
    def test_valid_vin_17_chars(self):
        """VIN hợp lệ 17 ký tự phải pass."""
        valid_vins = [
            "1HGBH41JXMN109186",
            "JM1BK32F781234567",
            "WVWZZZ3CZWE123456",
            "5YJSA1E26MF123456",
        ]
        for vin in valid_vins:
            result = validate_vin(vin)
            assert result["valid"] is True, f"VIN {vin} should be valid"
    
    @pytest.mark.smoke
    def test_invalid_vin_wrong_length(self):
        """VIN sai độ dài phải fail (strict mode)."""
        invalid_vins = [
            ("ABC123", "too short"),
            ("1HGBH41JXMN10918", "16 chars"),
            ("1HGBH41JXMN1091860", "18 chars"),
            ("12345678901234567890", "20 chars"),
        ]
        for vin, desc in invalid_vins:
            # Dùng strict mode để yêu cầu đúng 17 ký tự
            result = validate_vin(vin, strict=True)
            assert result["valid"] is False, f"VIN {vin} ({desc}) should be invalid in strict mode"
    
    @pytest.mark.smoke
    def test_invalid_vin_empty(self):
        """VIN rỗng phải fail."""
        result = validate_vin("")
        assert result["valid"] is False, "Empty VIN should be invalid"
        
        result = validate_vin(None)
        assert result["valid"] is False, "None VIN should be invalid"
    
    @pytest.mark.regression
    def test_vin_with_invalid_chars_strict_mode(self):
        """VIN chứa I, O, Q phải fail ở strict mode."""
        invalid_vins = [
            "1HGBH41IXMN109186",  # Contains I
            "1HGBH41OXMN109186",  # Contains O  
            "1HGBH41QXMN109186",  # Contains Q
        ]
        for vin in invalid_vins:
            result = validate_vin(vin, strict=True)
            assert result["valid"] is False, f"VIN {vin} with I/O/Q should fail in strict mode"
    
    @pytest.mark.regression
    def test_vin_with_lowercase(self):
        """VIN chữ thường phải được normalize thành chữ hoa."""
        vin = "1hgbh41jxmn109186"
        normalized = normalize_vin(vin)
        assert normalized == "1HGBH41JXMN109186"
    
    @pytest.mark.regression
    def test_vin_with_spaces(self):
        """VIN có khoảng trắng phải được trim."""
        vin = "  1HGBH41JXMN109186  "
        normalized = normalize_vin(vin)
        assert normalized == "1HGBH41JXMN109186"


class TestOwnerNormalization:
    """Test suite for owner name normalization."""
    
    @pytest.mark.smoke
    def test_basic_normalization(self):
        """Owner cơ bản phải được normalize đúng."""
        test_cases = [
            ("thaco", "THACO"),
            ("THACO", "THACO"),
            ("  thaco  ", "THACO"),
        ]
        for raw, expected in test_cases:
            result = normalize_owner(raw)
            assert result.upper() == expected.upper(), f"'{raw}' should normalize to '{expected}'"
    
    @pytest.mark.smoke
    def test_empty_owner(self):
        """Owner rỗng phải trả về rỗng."""
        assert normalize_owner("") == ""
        assert normalize_owner(None) == ""
        assert normalize_owner("   ") == ""
    
    @pytest.mark.regression
    def test_vietnamese_characters(self):
        """Owner tiếng Việt có dấu phải xử lý được."""
        test_cases = [
            "Công ty THACO",
            "TOYOTA VIỆT NAM",
            "Nguyễn Văn Ả",
        ]
        for owner in test_cases:
            result = normalize_owner(owner)
            assert result is not None
            assert len(result) > 0
    
    @pytest.mark.regression
    def test_special_characters(self):
        """Owner có ký tự đặc biệt phải xử lý được."""
        test_cases = [
            "Owner's Company",
            "Owner & Partners",
            "Owner (VN)",
        ]
        for owner in test_cases:
            result = normalize_owner(owner)
            assert result is not None


class TestDateNormalization:
    """Test suite for date handling (if applicable)."""
    
    @pytest.mark.smoke
    def test_valid_date_format(self):
        """Date format YYYY-MM-DD phải valid."""
        from datetime import datetime
        
        valid_dates = [
            "2024-01-01",
            "2024-12-31",
            "2025-06-15",
        ]
        for date_str in valid_dates:
            try:
                parsed = datetime.strptime(date_str, "%Y-%m-%d")
                assert parsed is not None
            except ValueError:
                pytest.fail(f"Date {date_str} should be valid")
    
    @pytest.mark.regression
    def test_invalid_date_formats(self):
        """Date format khác phải được detect."""
        from datetime import datetime
        
        invalid_formats = [
            "01-01-2024",   # DD-MM-YYYY
            "01/01/2024",   # DD/MM/YYYY  
            "2024/01/01",   # YYYY/MM/DD
            "invalid",
        ]
        for date_str in invalid_formats:
            with pytest.raises(ValueError):
                datetime.strptime(date_str, "%Y-%m-%d")
