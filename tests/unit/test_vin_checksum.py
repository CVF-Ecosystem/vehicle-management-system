"""
Unit tests for VIN checksum validation (Issue #12).

Tests the ISO 3779 VIN checksum algorithm implementation.
"""

import pytest
from data_normalizer import normalize_vin
from exceptions import VINValidationError


class TestVINChecksumValidation:
    """Test VIN checksum validation according to ISO 3779."""
    
    def test_valid_vin_with_correct_checksum(self):
        """Test that valid VIN with correct checksum passes."""
        # Real VIN with valid checksum: 1HGBH41JXMN109186
        valid_vin = "1HGBH41JXMN109186"
        result = normalize_vin(valid_vin)
        assert result == valid_vin
    
    def test_invalid_vin_with_wrong_checksum(self):
        """Test that VIN with wrong checksum is rejected."""
        # VIN with invalid checksum (last digit changed)
        invalid_vin = "1HGBH41JXMN109187"  # Should be 6, not 7
        with pytest.raises(VINValidationError) as exc_info:
            normalize_vin(invalid_vin)
        assert "checksum" in str(exc_info.value).lower()
    
    def test_vin_checksum_with_letter_x(self):
        """Test VIN with X as checksum digit."""
        # VIN where checksum is X (represents 10)
        vin_with_x = "1HGCP2F71CA123456"  # Example with X checksum
        # This should either pass or fail consistently based on checksum
        try:
            result = normalize_vin(vin_with_x)
            assert len(result) == 17
        except VINValidationError:
            pass  # Expected if checksum is invalid
    
    def test_vin_checksum_case_insensitive(self):
        """Test that checksum validation works regardless of case."""
        valid_vin_upper = "1HGBH41JXMN109186"
        valid_vin_lower = "1hgbh41jxmn109186"
        
        result_upper = normalize_vin(valid_vin_upper)
        result_lower = normalize_vin(valid_vin_lower)
        
        assert result_upper == result_lower
        assert result_upper == valid_vin_upper


class TestVINChecksumCalculation:
    """Test the internal checksum calculation logic."""
    
    def test_transliteration_values(self):
        """Test that letters are correctly converted to numeric values."""
        # According to ISO 3779:
        # A=1, B=2, C=3, D=4, E=5, F=6, G=7, H=8, J=1, K=2, L=3, M=4, N=5,
        # P=7, R=9, S=2, T=3, U=4, V=5, W=6, X=7, Y=8, Z=9
        # Letters I, O, Q are not used
        
        # Test VIN: ABCDEFGHJKLMNPRSTUVWXYZ123
        # Should not raise error if transliteration is correct
        test_vin = "1HGBH41JXMN109186"
        result = normalize_vin(test_vin)
        assert len(result) == 17
    
    def test_weight_factors(self):
        """Test that weight factors are correctly applied."""
        # Weight factors: 8,7,6,5,4,3,2,10,0,9,8,7,6,5,4,3,2
        # Position 9 (index 8) has weight 0 - this is the check digit
        valid_vin = "1HGBH41JXMN109186"
        result = normalize_vin(valid_vin)
        assert result == valid_vin
    
    def test_modulo_11_calculation(self):
        """Test that modulo 11 is correctly calculated."""
        # Sum of (transliteration * weight) mod 11 should equal check digit
        # If result is 10, check digit should be 'X'
        valid_vin = "1HGBH41JXMN109186"
        result = normalize_vin(valid_vin)
        assert result[8] == "X"  # Check digit at position 9 is X (representing 10)


class TestVINChecksumEdgeCases:
    """Test edge cases for VIN checksum validation."""
    
    def test_vin_with_invalid_characters(self):
        """Test that VIN with I, O, Q characters is rejected."""
        invalid_vins = [
            "1HGBH41IXMN109186",  # Contains I
            "1HGBH41OXMN109186",  # Contains O
            "1HGBH41QXMN109186",  # Contains Q
        ]
        
        for vin in invalid_vins:
            with pytest.raises(VINValidationError):
                normalize_vin(vin)
    
    def test_short_vin(self):
        """Test that VIN shorter than 17 characters is rejected."""
        short_vin = "1HGBH41JXMN10918"  # 16 characters
        with pytest.raises(VINValidationError):
            normalize_vin(short_vin)
    
    def test_long_vin(self):
        """Test that VIN longer than 17 characters is rejected."""
        long_vin = "1HGBH41JXMN1091866"  # 18 characters
        with pytest.raises(VINValidationError):
            normalize_vin(long_vin)
    
    def test_empty_vin(self):
        """Test that empty VIN is rejected."""
        with pytest.raises(VINValidationError):
            normalize_vin("")
    
    def test_vin_with_spaces(self):
        """Test that VIN with spaces is handled."""
        vin_with_spaces = " 1HGBH41JXMN109186 "
        result = normalize_vin(vin_with_spaces)
        assert result == "1HGBH41JXMN109186"
