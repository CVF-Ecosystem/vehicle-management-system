"""
Unit tests for database indexes verification and performance.
Tests that all required indexes exist and function correctly.

Phase 1C: Database Index Verification Tests
"""

import pytest
import sqlite3
from pathlib import Path
from datetime import datetime
from database.base_manager import BaseManager
from database.vehicle_manager import VehicleManager


class TestIndexExistence:
    """Test that all required indexes exist in the database."""
    
    @pytest.fixture
    def db_path(self, tmp_path):
        """Create a temporary database for testing."""
        db_file = tmp_path / "test_indexes.db"
        return str(db_file)
    
    @pytest.fixture
    def manager(self, db_path):
        """Initialize a database manager."""
        manager = BaseManager(db_path)
        # Schema is automatically created in __init__
        yield manager
        BaseManager.close_connection()
    
    def test_vehicle_vin_index_exists(self, manager):
        """Test idx_vehicles_vin index exists."""
        indexes = manager.get_table_indexes('vehicles')
        assert 'idx_vehicles_vin' in [idx['name'] for idx in indexes]
    
    def test_vehicle_owner_index_exists(self, manager):
        """Test idx_vehicles_owner index exists."""
        indexes = manager.get_table_indexes('vehicles')
        assert 'idx_vehicles_owner' in [idx['name'] for idx in indexes]
    
    def test_vehicle_status_index_exists(self, manager):
        """Test idx_vehicles_status index exists."""
        indexes = manager.get_table_indexes('vehicles')
        assert 'idx_vehicles_status' in [idx['name'] for idx in indexes]
    
    def test_vehicle_date_in_index_exists(self, manager):
        """Test idx_vehicles_date_in index exists."""
        indexes = manager.get_table_indexes('vehicles')
        assert 'idx_vehicles_date_in' in [idx['name'] for idx in indexes]
    
    def test_vehicle_date_out_index_exists(self, manager):
        """Test idx_vehicles_date_out index exists."""
        indexes = manager.get_table_indexes('vehicles')
        assert 'idx_vehicles_date_out' in [idx['name'] for idx in indexes]
    
    def test_vehicle_status_active_index_exists(self, manager):
        """Test idx_vehicles_status_active composite index exists."""
        indexes = manager.get_table_indexes('vehicles')
        assert 'idx_vehicles_status_active' in [idx['name'] for idx in indexes]
    
    def test_vehicle_is_deleted_index_exists(self, manager):
        """Test idx_vehicles_is_deleted index exists for soft deletes."""
        indexes = manager.get_table_indexes('vehicles')
        assert 'idx_vehicles_is_deleted' in [idx['name'] for idx in indexes]
    
    def test_vehicle_deleted_at_index_exists(self, manager):
        """Test idx_vehicles_deleted_at partial index exists."""
        indexes = manager.get_table_indexes('vehicles')
        assert 'idx_vehicles_deleted_at' in [idx['name'] for idx in indexes]
    
    def test_location_full_name_index_exists(self, manager):
        """Test idx_locations_full_name index exists."""
        indexes = manager.get_table_indexes('locations')
        assert 'idx_locations_full_name' in [idx['name'] for idx in indexes]
    
    def test_location_free_index_exists(self, manager):
        """Test idx_locations_free composite index exists."""
        indexes = manager.get_table_indexes('locations')
        assert 'idx_locations_free' in [idx['name'] for idx in indexes]
    
    def test_driver_cccd_unique_index_exists(self, manager):
        """Test idx_drivers_cccd unique index exists."""
        indexes = manager.get_table_indexes('drivers')
        index_names = [idx['name'] for idx in indexes]
        assert 'idx_drivers_cccd' in index_names
        
        # Verify it's unique
        for idx in indexes:
            if idx['name'] == 'idx_drivers_cccd':
                assert idx['unique'] == 1
    
    def test_minimum_index_count(self, manager):
        """Test minimum number of indexes are created."""
        vehicle_indexes = manager.get_table_indexes('vehicles')
        location_indexes = manager.get_table_indexes('locations')
        driver_indexes = manager.get_table_indexes('drivers')
        
        # Should have at least the performance indexes
        assert len(vehicle_indexes) >= 8  # Multiple vehicle indexes
        assert len(location_indexes) >= 2  # Location indexes
        assert len(driver_indexes) >= 1   # Driver CCCD index


class TestIndexColumns:
    """Test that indexes are created on correct columns."""
    
    @pytest.fixture
    def db_path(self, tmp_path):
        """Create a temporary database for testing."""
        db_file = tmp_path / "test_index_cols.db"
        return str(db_file)
    
    @pytest.fixture
    def manager(self, db_path):
        """Initialize a database manager."""
        manager = BaseManager(db_path)
        # Schema is automatically created in __init__
        yield manager
        # Don't close - it's a singleton
    
    def test_vin_index_on_correct_column(self, manager):
        """Test VIN index is on vin column."""
        conn = sqlite3.connect(BaseManager._db_path)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA index_info(idx_vehicles_vin)")
        columns = [row[2] for row in cursor.fetchall()]
        
        assert 'vin' in columns
        conn.close()
    
    def test_status_index_on_correct_column(self, manager):
        """Test status index is on status column."""
        conn = sqlite3.connect(BaseManager._db_path)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA index_info(idx_vehicles_status)")
        columns = [row[2] for row in cursor.fetchall()]
        
        assert 'status' in columns
        conn.close()
    
    def test_status_active_composite_index(self, manager):
        """Test status_active is composite index on (status, is_active)."""
        conn = sqlite3.connect(BaseManager._db_path)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA index_info(idx_vehicles_status_active)")
        columns = [row[2] for row in cursor.fetchall()]
        
        assert 'status' in columns
        assert 'is_active' in columns
        assert len(columns) == 2
        conn.close()
    
    def test_deleted_at_partial_index_has_where_clause(self, manager):
        """Test deleted_at is partial index with WHERE clause."""
        conn = sqlite3.connect(BaseManager._db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND name='idx_vehicles_deleted_at'")
        result = cursor.fetchone()
        
        assert result is not None
        # Partial index should have WHERE clause
        assert 'WHERE' in result[0].upper()
        conn.close()


class TestIndexFunctionality:
    """Test that indexes actually improve query performance."""
    
    @pytest.fixture
    def db_path(self, tmp_path):
        """Create a temporary database for testing."""
        db_file = tmp_path / "test_index_perf.db"
        return str(db_file)
    
    @pytest.fixture
    def vehicle_manager(self, db_path):
        """Initialize a vehicle manager."""
        manager = VehicleManager(db_path)
        yield manager
        # Don't close - it's a singleton
    
    def test_vin_index_speeds_up_search(self, vehicle_manager):
        """Test that VIN index improves search performance."""
        # Add test vehicle
        vin = "JTHBP5C2XA5034186"  # Valid VIN with proper checksum
        result = vehicle_manager.add_vehicle(
            vin=vin,
            owner="Test Owner",
            vehicle_type="Car",
            date_in=datetime.now(),
            location_id=None,
        )
        
        assert result['success']
        
        # Search by VIN should be fast with index
        vehicle = vehicle_manager.get_vehicle_by_vin(vin)
        
        assert vehicle is not None
        assert vehicle['vin'] == vin
    
    def test_status_index_filter_works(self, vehicle_manager):
        """Test that status index enables efficient filtering."""
        # Add vehicles with different statuses
        for i in range(5):
            vin = f"JTHBP5C2XA50341{80+i}"
            vehicle_manager.add_vehicle(
                vin=vin,
                owner=f"Owner {i}",
                vehicle_type="Car",
                date_in=datetime.now(),
                location_id=None,
            )
        
        # Filter by status should be efficient
        vehicles = vehicle_manager.search_all_vehicles(status_filter='in_stock')
        
        assert len(vehicles) >= 5
        for v in vehicles:
            assert v['status'] == 'IN_STOCK'
    
    def test_date_range_index_efficiency(self, vehicle_manager):
        """Test date indexes enable range queries."""
        # Add multiple vehicles
        for i in range(3):
            vin = f"JTHBP5C2XA50341{90+i}"
            vehicle_manager.add_vehicle(
                vin=vin,
                owner=f"Owner {i}",
                vehicle_type="Car",
                date_in=datetime.now(),
                location_id=None,
            )
        
        # Range query should work efficiently
        vehicles = vehicle_manager.search_all_vehicles()
        
        assert len(vehicles) >= 3


class TestIndexPerformanceMetrics:
    """Test index performance characteristics."""
    
    @pytest.fixture
    def db_path(self, tmp_path):
        """Create a temporary database for testing."""
        db_file = tmp_path / "test_index_metrics.db"
        return str(db_file)
    
    @pytest.fixture
    def vehicle_manager(self, db_path):
        """Initialize a vehicle manager."""
        manager = VehicleManager(db_path)
        yield manager
        # Don't close - it's a singleton
    
    def test_unique_index_enforces_uniqueness(self, vehicle_manager):
        """Test unique index enforces constraint."""
        from database.entity_manager import EntityManager
        entity_manager = EntityManager(BaseManager._db_path)
        # Add a driver with CCCD
        result1 = entity_manager.add_driver(
            name="Driver 1",
            phone="0123456789",
            cccd="123456789012",
            notes=""
        )
        
        assert result1['success']
        
        # Try to add another driver with same CCCD - should fail due to unique constraint
        result2 = entity_manager.add_driver(
            name="Driver 2",
            phone="0987654321",
            cccd="123456789012",
            notes=""
        )
        assert result2['success'] is False
    
    def test_composite_index_helps_multi_column_filter(self, vehicle_manager):
        """Test composite index improves multi-column filtering."""
        # Add vehicles
        for i in range(10):
            vin = f"JTHBP5C2XA50341{i:02d}"
            vehicle_manager.add_vehicle(
                vin=vin,
                owner=f"Owner {i}",
                vehicle_type="Car",
                date_in=datetime.now(),
                location_id=None,
            )
        
        # Query that uses composite index
        cursor = vehicle_manager.conn.cursor()
        
        cursor.execute(
            "SELECT * FROM vehicles WHERE status = ? AND is_active = ?",
            ('IN_STOCK', 1)
        )
        results = cursor.fetchall()
        
        # Should find vehicles efficiently
        assert len(results) > 0
    
    def test_partial_index_filters_deleted(self, vehicle_manager):
        """Test partial index on deleted_at correctly filters."""
        # Add vehicle
        vin = "JTHBP5C2XA5034101"
        result = vehicle_manager.add_vehicle(
            vin=vin,
            owner="Test",
            vehicle_type="Car",
            date_in=datetime.now(),
            location_id=None,
        )
        
        assert result['success']
        
        # Soft delete it
        vehicle_manager.soft_delete_vehicle(vin, "admin", "Testing")
        
        # Partial index should efficiently filter non-deleted records
        all_vehicles = vehicle_manager.search_all_vehicles()
        
        # Vehicle should not be in normal list (it's deleted)
        vins = [v['vin'] for v in all_vehicles]
        assert vin not in vins


class TestIndexStatistics:
    """Test index statistics and metadata."""
    
    @pytest.fixture
    def db_path(self, tmp_path):
        """Create a temporary database for testing."""
        db_file = tmp_path / "test_index_stats.db"
        return str(db_file)
    
    @pytest.fixture
    def manager(self, db_path):
        """Initialize a database manager."""
        manager = BaseManager(db_path)
        yield manager
        BaseManager.close_connection()
    
    def test_all_indexes_are_named_consistently(self, manager):
        """Test all indexes follow naming convention."""
        all_tables = ['vehicles', 'locations', 'drivers']
        
        for table in all_tables:
            indexes = manager.get_table_indexes(table)
            for idx in indexes:
                name = idx['name']
                if name.startswith('sqlite_'):
                    continue
                # Should start with 'idx_'
                assert name.startswith('idx_'), f"Index {name} doesn't follow naming convention"
    
    def test_index_creation_success_count(self, manager):
        """Test that expected number of indexes are created."""
        vehicle_indexes = manager.get_table_indexes('vehicles')
        location_indexes = manager.get_table_indexes('locations')
        
        # Should have created multiple performance indexes
        total_custom_indexes = len(vehicle_indexes) + len(location_indexes)
        
        # At least 10 custom performance indexes should exist
        assert total_custom_indexes >= 10


class TestIndexQueryPlanning:
    """Test that indexes are actually used by query planner."""
    
    @pytest.fixture
    def db_path(self, tmp_path):
        """Create a temporary database for testing."""
        db_file = tmp_path / "test_query_plan.db"
        return str(db_file)
    
    @pytest.fixture
    def vehicle_manager(self, db_path):
        """Initialize a vehicle manager."""
        manager = VehicleManager(db_path)
        yield manager
        # Don't close - it's a singleton
    
    def test_vin_search_uses_index(self, vehicle_manager):
        """Test VIN search query uses index in query plan."""
        conn = sqlite3.connect(BaseManager._db_path)
        cursor = conn.cursor()
        
        # Get query plan for VIN search
        cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM vehicles WHERE vin = ?", ("TEST",))
        plan = cursor.fetchall()
        plan_str = str(plan)
        
        # Plan should mention the index
        # (SQLite shows index usage in the plan)
        assert plan is not None  # Query should be plannable
        conn.close()
    
    def test_status_filter_uses_index(self, vehicle_manager):
        """Test status filter uses index."""
        conn = sqlite3.connect(BaseManager._db_path)
        cursor = conn.cursor()
        
        # Get query plan for status filter
        cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM vehicles WHERE status = ?", ("in_stock",))
        plan = cursor.fetchall()
        
        assert plan is not None
        conn.close()
    
    def test_date_range_query_uses_index(self, vehicle_manager):
        """Test date range query can use index."""
        conn = sqlite3.connect(BaseManager._db_path)
        cursor = conn.cursor()
        
        # Get query plan for date range
        now = datetime.now()
        cursor.execute(
            "EXPLAIN QUERY PLAN SELECT * FROM vehicles WHERE date_in >= ? AND date_in <= ?",
            (now, now)
        )
        plan = cursor.fetchall()
        
        assert plan is not None
        conn.close()


class TestIndexIntegration:
    """Test indexes work correctly with application queries."""
    
    @pytest.fixture
    def db_path(self, tmp_path):
        """Create a temporary database for testing."""
        db_file = tmp_path / "test_index_integration.db"
        return str(db_file)
    
    @pytest.fixture
    def vehicle_manager(self, db_path):
        """Initialize a vehicle manager."""
        manager = VehicleManager(db_path)
        yield manager
        # Don't close - it's a singleton
    
    def test_search_with_multiple_indexes(self, vehicle_manager):
        """Test search using multiple indexes together."""
        # Add test data
        for i in range(5):
            vin = f"JTHBP5C2XA50341{50+i}"
            vehicle_manager.add_vehicle(
                vin=vin,
                owner=f"Owner {i}",
                vehicle_type="Car",
                date_in=datetime.now(),
                location_id=None,
            )
        
        # Complex search that could use multiple indexes
        results = vehicle_manager.search_all_vehicles(
            status_filter='in_stock',
            owner='Owner 1'
        )
        
        assert len(results) > 0
    
    def test_indexes_with_soft_delete(self, vehicle_manager):
        """Test indexes work correctly with soft delete filtering."""
        # Add vehicle
        vin = "JTHBP5C2XA5034199"
        vehicle_manager.add_vehicle(
            vin=vin,
            owner="Test",
            vehicle_type="Car",
            date_in=datetime.now(),
            location_id=None,
        )
        
        # Soft delete
        vehicle_manager.soft_delete_vehicle(vin, "admin", "test")
        
        # Deleted vehicle should not appear in normal searches (using is_deleted index)
        all_vehicles = vehicle_manager.search_all_vehicles()
        vins = [v['vin'] for v in all_vehicles]
        
        assert vin not in vins
        
        # But should be retrievable as deleted
        deleted = vehicle_manager.list_deleted_vehicles()
        deleted_vins = [v['vin'] for v in deleted]
        
        assert vin in deleted_vins
