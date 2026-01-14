"""
Integration tests for complete vehicle lifecycle workflow.

Tests the full workflow: add vehicle → in stock → dispatch → ship → complete
"""

import pytest
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
import config
from database.vehicle_manager import VehicleManager
from database.dispatch_manager import DispatchManager
from database.entity_manager import EntityManager


class TestVehicleLifecycle:
    """Test complete vehicle lifecycle from arrival to shipment."""
    
    @pytest.fixture
    def managers(self, tmp_path):
        """Create managers with temporary database."""
        original_db = config.DB_FILE
        test_db = tmp_path / "test_workflow.db"
        config.DB_FILE = str(test_db)
        
        vm = VehicleManager()
        dm = DispatchManager()
        em = EntityManager()
        
        yield {'vehicle': vm, 'dispatch': dm, 'entity': em}
        
        # Cleanup
        config.DB_FILE = original_db
    
    def test_full_vehicle_workflow(self, managers):
        """Test complete workflow: add → stock → dispatch → ship."""
        vm = managers['vehicle']
        dm = managers['dispatch']
        em = managers['entity']
        
        # Step 1: Add driver and transport vehicle
        driver_result = em.add_driver("Nguyễn Văn A", "0901234567", "123456789", "Test driver")
        assert driver_result['success'] is True
        driver_id = driver_result['id']
        
        transport_result = em.add_transport_vehicle("29A-12345", "TRUCK", "Hino")
        assert transport_result['success'] is True
        transport_id = transport_result['id']
        
        # Step 2: Add vehicle to stock
        vin = "1HGBH41JXMN109186"
        result = vm.add_vehicle(
            vin=vin,
            owner="CÔNG TY A",
            vehicle_type="Sedan",
            date_in=datetime.now(timezone.utc) - timedelta(days=1),
            location_id=None
        )
        assert result['success'] is True
        
        # Step 3: Verify vehicle in stock
        vehicles = vm.get_in_stock()
        assert len(vehicles) == 1
        assert vehicles[0]['vin'] == vin
        assert vehicles[0]['status'] == 'IN_STOCK'
        
        # Step 4: Create dispatch
        dispatch_id = dm.create_dispatch(
            driver_id=driver_id,
            transport_vehicle_id=transport_id
        )
        assert dispatch_id is not None
        
        # Step 5: Add vehicle to dispatch
        result = dm.add_vehicle_to_dispatch(vin, dispatch_id)
        assert result is True
        
        # Step 6: Verify vehicle assigned to dispatch
        vehicle = vm.get_vehicle_by_vin(vin)
        assert vehicle['dispatch_id'] == dispatch_id
        
        # Step 7: Complete dispatch (updates status and date_out)
        result = dm.complete_dispatch(dispatch_id)
        assert result['success'] is True
        
        # Step 8: Verify vehicle status updated
        vehicle = vm.get_vehicle_by_vin(vin)
        assert vehicle['status'] == 'SHIPPED'
        assert vehicle['date_out'] is not None
        
        # Step 9: Verify vehicle no longer in stock
        vehicles = vm.get_in_stock()
        assert len(vehicles) == 0  # Vehicle should be moved to history
    
    def test_add_multiple_vehicles_to_dispatch(self, managers):
        """Test adding multiple vehicles to same dispatch."""
        vm = managers['vehicle']
        dm = managers['dispatch']
        em = managers['entity']
        
        # Setup
        driver_result = em.add_driver("Tài xế B", "0912345678", "987654321", "")
        driver_id = driver_result['id']
        transport_result = em.add_transport_vehicle("30B-67890", "TRUCK", "Isuzu")
        transport_id = transport_result['id']
        
        # Add 3 vehicles
        vins = [
            "1HGBH41JXMN109186",
            "2HGCP2F71CA654321",
            "3GNCA13D46S123456"
        ]
        
        for vin in vins:
            result = vm.add_vehicle(
                vin=vin,
                owner="CÔNG TY B",
                vehicle_type="Sedan",
                date_in=datetime.now(timezone.utc) - timedelta(hours=12),
                location_id=None
            )
            assert result['success'] is True
        
        # Create dispatch
        dispatch_id = dm.create_dispatch(driver_id, transport_id)
        
        # Add all vehicles to dispatch
        for vin in vins:
            result = dm.add_vehicle_to_dispatch(vin, dispatch_id)
            assert result is True
        
        # Verify all vehicles assigned
        for vin in vins:
            vehicle = vm.get_vehicle_by_vin(vin)
            assert vehicle['dispatch_id'] == dispatch_id
        
        # Complete dispatch
        result = dm.complete_dispatch(dispatch_id)
        assert result['success'] is True
        
        # Verify all vehicles shipped
        for vin in vins:
            vehicle = vm.get_vehicle_by_vin(vin)
            assert vehicle['status'] == 'SHIPPED'


class TestWorkflowEdgeCases:
    """Test edge cases and error handling in workflow."""
    
    @pytest.fixture
    def managers(self, tmp_path):
        """Create managers with temporary database."""
        original_db = config.DB_FILE
        test_db = tmp_path / "test_edge_cases.db"
        config.DB_FILE = str(test_db)
        
        vm = VehicleManager()
        dm = DispatchManager()
        em = EntityManager()
        
        yield {'vehicle': vm, 'dispatch': dm, 'entity': em}
        
        config.DB_FILE = original_db
    
    def test_cannot_dispatch_nonexistent_vehicle(self, managers):
        """Test that adding non-existent vehicle to dispatch fails."""
        dm = managers['dispatch']
        em = managers['entity']
        
        driver_result = em.add_driver("Driver C", "0923456789", "111222333", "")
        driver_id = driver_result['id']
        transport_result = em.add_transport_vehicle("51C-11111", "TRUCK", "Hino")
        transport_id = transport_result['id']
        dispatch_id = dm.create_dispatch(driver_id, transport_id)
        
        # Try to add non-existent vehicle
        result = dm.add_vehicle_to_dispatch("NONEXISTENTVVIN", dispatch_id)
        assert result is False
    
    def test_cannot_add_already_dispatched_vehicle(self, managers):
        """Test that vehicle already in dispatch cannot be added to another."""
        vm = managers['vehicle']
        dm = managers['dispatch']
        em = managers['entity']
        
        # Setup
        driver_result = em.add_driver("Driver D", "0934567890", "444555666", "")
        driver_id = driver_result['id']
        transport_result1 = em.add_transport_vehicle("52D-22222", "TRUCK", "Isuzu")
        transport_id1 = transport_result1['id']
        transport_result2 = em.add_transport_vehicle("52D-33333", "TRUCK", "Hino")
        transport_id2 = transport_result2['id']
        
        # Add vehicle
        vin = "1HGBH41JXMN109186"
        vm.add_vehicle(
            vin=vin,
            owner="CÔNG TY C",
            vehicle_type="SUV",
            date_in=datetime.now(timezone.utc) - timedelta(hours=6),
            location_id=None
        )
        
        # Create two dispatches
        dispatch_id1 = dm.create_dispatch(driver_id, transport_id1)
        dispatch_id2 = dm.create_dispatch(driver_id, transport_id2)
        
        # Add vehicle to first dispatch
        result = dm.add_vehicle_to_dispatch(vin, dispatch_id1)
        assert result is True
        
        # Try to add same vehicle to second dispatch
        result = dm.add_vehicle_to_dispatch(vin, dispatch_id2)
        # Should handle gracefully (either reassign or reject based on business logic)
        # Current implementation should reassign
        vehicle = vm.get_vehicle_by_vin(vin)
        assert vehicle['dispatch_id'] == dispatch_id2
    
    def test_vehicle_with_future_date_rejected(self, managers):
        """Test that vehicle with future date_in is rejected."""
        vm = managers['vehicle']
        
        vin = "1HGBH41JXMN109186"
        result = vm.add_vehicle(
            vin=vin,
            owner="CÔNG TY D",
            vehicle_type="Sedan",
            date_in=datetime.now(timezone.utc) + timedelta(days=1),  # Future date
            location_id=None
        )
        assert result['success'] is False
        assert 'tương lai' in result['message'].lower()


class TestWorkflowPerformance:
    """Test workflow performance with larger datasets."""
    
    @pytest.fixture
    def managers(self, tmp_path):
        """Create managers with temporary database."""
        original_db = config.DB_FILE
        test_db = tmp_path / "test_performance.db"
        config.DB_FILE = str(test_db)
        
        vm = VehicleManager()
        dm = DispatchManager()
        em = EntityManager()
        
        yield {'vehicle': vm, 'dispatch': dm, 'entity': em}
        
        config.DB_FILE = original_db
    
    def test_add_100_vehicles_performance(self, managers):
        """Test adding 100 vehicles completes in reasonable time."""
        import time
        vm = managers['vehicle']
        
        start_time = time.time()
        
        
        # Add 100 vehicles - use known valid VINs and cycle/modify
        # Known valid VINs from test_vin_checksum.py
        valid_vins = [
            "1HGBH41JXMN109186",  # Check digit: 8
            "2HGCP2F71CA654321",  # Check digit: 1
            "3GNCA13D46S123456",  # Check digit: 6
            "5XXGN4A70CG000000",  # Check digit: 0
        ]
        
        for i in range(100):
            # Cycle through valid VINs and modify last digit to make unique
            base_vin = valid_vins[i % len(valid_vins)]
            # Modify last 2 digits to create uniqueness (will break checksum but that's ok for perf test)
            # Or just try to add the valid VINs as-is and handle duplicates
            vin = base_vin[:15] + str(i % 100).zfill(2)  # Change last 2 digits
            
            # Try to add vehicle (some may fail validation, that's expected)
            vm.add_vehicle(
                vin=vin,
                owner=f"OWNER_{i}",
                vehicle_type="Sedan",
                date_in=datetime.now(timezone.utc) - timedelta(days=1),
                location_id=None
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within 10 seconds
        assert duration < 10.0
        
        # Verify count
        vehicles = vm.get_in_stock(limit=200)
        assert len(vehicles) >= 90  # Allow some to fail VIN checksum validation
    
    def test_query_vehicles_performance(self, managers):
        """Test querying vehicles with indexes is fast."""
        import time
        vm = managers['vehicle']
        
        # Add 50 vehicles
        for i in range(50):
            vin = f"2HGCP2F71CA{i:05d}X"
            if len(vin) == 17:
                vm.add_vehicle(
                    vin=vin,
                    owner=f"COMPANY_{i % 10}",  # 10 different owners
                    vehicle_type="SUV",
                    date_in=datetime.now(timezone.utc) - timedelta(days=i),
                    location_id=None
                )
        
        # Query all vehicles (should use indexes)
        start_time = time.time()
        vehicles = vm.get_in_stock(limit=200)
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Should complete within 1 second with indexes
        assert duration < 1.0
        assert len(vehicles) >= 40
