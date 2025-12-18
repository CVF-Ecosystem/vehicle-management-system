# tests/unit/test_soft_delete.py
"""Unit tests for soft delete functionality in VehicleManager."""
import pytest
import tempfile
import os
from datetime import datetime, timezone

from database.vehicle_manager import VehicleManager


class TestSoftDelete:
    """Tests for soft_delete_vehicle method."""
    
    @pytest.fixture
    def vm_with_vehicle(self, tmp_path, monkeypatch):
        """Create VehicleManager with a test vehicle."""
        db_path = tmp_path / "test.db"
        monkeypatch.setattr("config.DB_FILE", str(db_path))
        
        vm = VehicleManager()
        # Add a test vehicle - use valid VIN (no I, O, Q)
        result = vm.add_vehicle(
            vin="1HGBH41JXMN109186",  # Valid 17-char VIN
            owner="Test Owner",
            vehicle_type="Sedan",
            date_in=datetime.now(timezone.utc),
            location_id=None
        )
        assert result["success"], f"Failed to add test vehicle: {result['message']}"
        yield vm
    
    def test_soft_delete_success(self, vm_with_vehicle):
        """Test successful soft delete."""
        vm = vm_with_vehicle
        
        result = vm.soft_delete_vehicle(
            vin="1HGBH41JXMN109186",
            deleted_by="admin",
            delete_reason="Test deletion"
        )
        
        assert result["success"]
        
        # Verify vehicle is marked as deleted
        vehicle = vm.get_vehicle_by_vin("1HGBH41JXMN109186")
        assert vehicle is not None
        assert vehicle["is_deleted"] == 1
        assert vehicle["is_active"] == 0
        assert vehicle["deleted_by"] == "admin"
        assert vehicle["delete_reason"] == "Test deletion"
        assert vehicle["deleted_at"] is not None
    
    def test_soft_delete_nonexistent_vin(self, vm_with_vehicle):
        """Test soft delete with non-existent VIN."""
        vm = vm_with_vehicle
        
        result = vm.soft_delete_vehicle(
            vin="ZZZZZZZZZ12345",  # Non-existent
            deleted_by="admin"
        )
        
        assert not result["success"]
        assert "Không tìm thấy" in result["message"]
    
    def test_soft_delete_already_deleted(self, vm_with_vehicle):
        """Test soft deleting an already deleted vehicle."""
        vm = vm_with_vehicle
        
        # First delete
        vm.soft_delete_vehicle(vin="1HGBH41JXMN109186", deleted_by="admin")
        
        # Try to delete again
        result = vm.soft_delete_vehicle(
            vin="1HGBH41JXMN109186",
            deleted_by="admin"
        )
        
        assert not result["success"]
        assert "đã bị xóa" in result["message"] or "Không tìm thấy" in result["message"]


class TestRestoreDeleted:
    """Tests for restore_deleted_vehicle method."""
    
    @pytest.fixture
    def vm_with_deleted_vehicle(self, tmp_path, monkeypatch):
        """Create VehicleManager with a soft-deleted vehicle."""
        db_path = tmp_path / "test.db"
        monkeypatch.setattr("config.DB_FILE", str(db_path))
        
        vm = VehicleManager()
        vm.add_vehicle(
            vin="2HGBH41JXMN109186",  # Valid VIN
            owner="Test Owner",
            vehicle_type="SUV",
            date_in=datetime.now(timezone.utc),
            location_id=None
        )
        vm.soft_delete_vehicle(
            vin="2HGBH41JXMN109186",
            deleted_by="admin",
            delete_reason="Initial deletion"
        )
        yield vm
    
    def test_restore_success(self, vm_with_deleted_vehicle):
        """Test successful restore."""
        vm = vm_with_deleted_vehicle
        
        result = vm.restore_deleted_vehicle(
            vin="2HGBH41JXMN109186",
            restored_by="manager"
        )
        
        assert result["success"]
        
        # Verify vehicle is restored
        vehicle = vm.get_vehicle_by_vin("2HGBH41JXMN109186")
        assert vehicle["is_deleted"] == 0
        assert vehicle["is_active"] == 1
        assert vehicle["deleted_at"] is None
        assert vehicle["deleted_by"] is None
    
    def test_restore_nonexistent(self, vm_with_deleted_vehicle):
        """Test restoring non-existent deleted vehicle."""
        vm = vm_with_deleted_vehicle
        
        result = vm.restore_deleted_vehicle(
            vin="ZZZZZZZZZ12345",  # Non-existent
            restored_by="manager"
        )
        
        assert not result["success"]
        assert "Không tìm thấy" in result["message"]
    
    def test_restore_active_vehicle(self, tmp_path, monkeypatch):
        """Test restoring an active (not deleted) vehicle."""
        db_path = tmp_path / "test.db"
        monkeypatch.setattr("config.DB_FILE", str(db_path))
        
        vm = VehicleManager()
        vm.add_vehicle(
            vin="3HGBH41JXMN109186",  # Valid VIN
            owner="Active Owner",
            vehicle_type="Truck",
            date_in=datetime.now(timezone.utc),
            location_id=None
        )
        
        result = vm.restore_deleted_vehicle(
            vin="3HGBH41JXMN109186",
            restored_by="manager"
        )
        
        assert not result["success"]


class TestListDeleted:
    """Tests for list_deleted_vehicles method."""
    
    @pytest.fixture
    def vm_with_multiple_deleted(self, tmp_path, monkeypatch):
        """Create VehicleManager with multiple deleted vehicles."""
        db_path = tmp_path / "test.db"
        monkeypatch.setattr("config.DB_FILE", str(db_path))
        
        vm = VehicleManager()
        
        # Add and delete multiple vehicles - use short valid VINs
        test_vins = ["DEL001", "DEL002", "DEL003", "DEL004", "DEL005"]
        for i, vin in enumerate(test_vins):
            vm.add_vehicle(
                vin=vin,
                owner=f"Owner{i}",
                vehicle_type="Sedan",
                date_in=datetime.now(timezone.utc),
                location_id=None
            )
            vm.soft_delete_vehicle(
                vin=vin,
                deleted_by="admin",
                delete_reason=f"Reason {i}"
            )
        
        yield vm
    
    def test_list_all_deleted(self, vm_with_multiple_deleted):
        """Test listing all deleted vehicles."""
        vm = vm_with_multiple_deleted
        
        deleted = vm.list_deleted_vehicles()
        
        assert len(deleted) == 5
        for v in deleted:
            assert v["is_deleted"] == 1
    
    def test_list_deleted_with_limit(self, vm_with_multiple_deleted):
        """Test listing deleted vehicles with limit."""
        vm = vm_with_multiple_deleted
        
        deleted = vm.list_deleted_vehicles(limit=3)
        
        assert len(deleted) == 3
    
    def test_list_deleted_with_offset(self, vm_with_multiple_deleted):
        """Test listing deleted vehicles with offset."""
        vm = vm_with_multiple_deleted
        
        all_deleted = vm.list_deleted_vehicles()
        offset_deleted = vm.list_deleted_vehicles(offset=2)
        
        assert len(offset_deleted) == 3
    
    def test_list_deleted_with_search(self, vm_with_multiple_deleted):
        """Test searching deleted vehicles."""
        vm = vm_with_multiple_deleted
        
        deleted = vm.list_deleted_vehicles(search_term="DEL003")
        
        assert len(deleted) == 1
        assert deleted[0]["vin"] == "DEL003"
    
    def test_count_deleted(self, vm_with_multiple_deleted):
        """Test counting deleted vehicles."""
        vm = vm_with_multiple_deleted
        
        count = vm.count_deleted_vehicles()
        
        assert count == 5


class TestHardDelete:
    """Tests for hard_delete_vehicle method."""
    
    @pytest.fixture
    def vm_with_deleted_vehicle(self, tmp_path, monkeypatch):
        """Create VehicleManager with a soft-deleted vehicle."""
        db_path = tmp_path / "test.db"
        monkeypatch.setattr("config.DB_FILE", str(db_path))
        
        vm = VehicleManager()
        vm.add_vehicle(
            vin="HARD001",  # Valid short VIN
            owner="Delete Owner",
            vehicle_type="Van",
            date_in=datetime.now(timezone.utc),
            location_id=None
        )
        vm.soft_delete_vehicle(
            vin="HARD001",
            deleted_by="admin",
            delete_reason="Prepare for hard delete"
        )
        yield vm
    
    def test_hard_delete_success(self, vm_with_deleted_vehicle):
        """Test successful hard delete."""
        vm = vm_with_deleted_vehicle
        
        result = vm.hard_delete_vehicle(
            vin="HARD001",
            deleted_by="superadmin",
            delete_reason="Permanent removal"
        )
        
        assert result["success"]
        
        # Verify vehicle is completely removed from vehicles table
        vehicle = vm.get_vehicle_by_vin("HARD001")
        assert vehicle is None
        
        # Verify record exists in archive
        archived = vm.get_archived_deleted_vehicles()
        assert len(archived) == 1
        assert archived[0]["vin"] == "HARD001"
        assert archived[0]["deleted_by"] == "superadmin"
    
    def test_hard_delete_active_vehicle_fails(self, tmp_path, monkeypatch):
        """Test hard delete on active vehicle fails."""
        db_path = tmp_path / "test.db"
        monkeypatch.setattr("config.DB_FILE", str(db_path))
        
        vm = VehicleManager()
        vm.add_vehicle(
            vin="ACTVE001",  # Valid VIN
            owner="Active Owner",
            vehicle_type="Pickup",
            date_in=datetime.now(timezone.utc),
            location_id=None
        )
        
        result = vm.hard_delete_vehicle(
            vin="ACTVE001",
            deleted_by="admin"
        )
        
        assert not result["success"]
        assert "soft delete" in result["message"].lower() or "đã xóa" in result["message"]
    
    def test_hard_delete_nonexistent(self, vm_with_deleted_vehicle):
        """Test hard delete on non-existent vehicle."""
        vm = vm_with_deleted_vehicle
        
        result = vm.hard_delete_vehicle(
            vin="ZZZZZZZZZ12345",
            deleted_by="admin"
        )
        
        assert not result["success"]
    
    def test_archived_record_contains_full_data(self, tmp_path, monkeypatch):
        """Test that archived record contains full vehicle data as JSON."""
        import json
        
        db_path = tmp_path / "test.db"
        monkeypatch.setattr("config.DB_FILE", str(db_path))
        
        vm = VehicleManager()
        vm.add_vehicle(
            vin="ARCH001",
            owner="Archive Owner",
            vehicle_type="Van",
            date_in=datetime.now(timezone.utc),
            location_id=None
        )
        vm.soft_delete_vehicle(vin="ARCH001", deleted_by="admin")
        vm.hard_delete_vehicle(
            vin="ARCH001",
            deleted_by="admin",
            delete_reason="Archive test"
        )
        
        archived = vm.get_archived_deleted_vehicles()
        record = archived[0]
        
        # Verify full_record_json contains complete data
        full_record = json.loads(record["full_record_json"])
        assert full_record["vin"] == "ARCH001"
        assert full_record["owner"] == "ARCHIVE OWNER"  # Normalized
        assert full_record["vehicle_type"] == "VAN"  # Normalized to uppercase


class TestSoftDeleteEdgeCases:
    """Edge case tests for soft delete functionality."""
    
    def test_deleted_vehicle_not_in_stock_list(self, tmp_path, monkeypatch):
        """Test that deleted vehicles don't appear in stock list."""
        db_path = tmp_path / "test.db"
        monkeypatch.setattr("config.DB_FILE", str(db_path))
        
        vm = VehicleManager()
        
        # Add two vehicles (valid VINs - no I, O, Q)
        vm.add_vehicle(
            vin="STCK001",  # Valid VIN - no O
            owner="Stock Owner",
            vehicle_type="Sedan",
            date_in=datetime.now(timezone.utc),
            location_id=None
        )
        vm.add_vehicle(
            vin="DELET001",  # Valid VIN
            owner="Delete Owner",
            vehicle_type="SUV",
            date_in=datetime.now(timezone.utc),
            location_id=None
        )
        
        # Delete one
        vm.soft_delete_vehicle(vin="DELET001", deleted_by="admin")
        
        # Check stock list
        stock = vm.get_in_stock()
        vins = [v["vin"] for v in stock]
        
        assert "STCK001" in vins
        assert "DELET001" not in vins

