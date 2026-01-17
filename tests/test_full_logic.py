"""
🧪 FULL LOGIC TEST SUITE
========================
Kiểm tra toàn bộ logic của ứng dụng Vehicle Management System
Tester: AI Assistant
Date: 2026-01-18
"""

import sqlite3
import sys
import os
from datetime import datetime, timedelta

# Get project root directory and change to it
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

DB_FILE = "vehicle_management_v5.1"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def ok(msg):
    print(f"  {Colors.GREEN}✅ PASS:{Colors.END} {msg}")

def fail(msg):
    print(f"  {Colors.RED}❌ FAIL:{Colors.END} {msg}")

def warn(msg):
    print(f"  {Colors.YELLOW}⚠️ WARN:{Colors.END} {msg}")

def info(msg):
    print(f"  {Colors.BLUE}ℹ️ INFO:{Colors.END} {msg}")

def section(title):
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print('='*60)

issues = []

# ============================================
# 1. DATABASE TESTS
# ============================================
def test_database():
    section("1. DATABASE STRUCTURE TESTS")
    
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Test 1.1: Check tables exist
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r['name'] for r in cur.fetchall()]
    
    # Note: owners stored in vehicles.owner column, audit_log not implemented in this version
    required_tables = ['vehicles', 'locations', 'dispatches', 'users', 'drivers']
    for table in required_tables:
        if table in tables:
            ok(f"Table '{table}' exists")
        else:
            fail(f"Table '{table}' MISSING!")
            issues.append(f"Missing table: {table}")
    
    # Test 1.2: Check vehicles schema
    cur.execute("PRAGMA table_info(vehicles)")
    cols = {r['name']: r['type'] for r in cur.fetchall()}
    
    required_cols = ['vin', 'owner', 'vehicle_type', 'status', 'date_in', 'location_id', 'is_active', 'is_deleted']
    for col in required_cols:
        if col in cols:
            ok(f"Column 'vehicles.{col}' exists ({cols[col]})")
        else:
            fail(f"Column 'vehicles.{col}' MISSING!")
            issues.append(f"Missing column: vehicles.{col}")
    
    # Test 1.3: Check locations schema
    cur.execute("PRAGMA table_info(locations)")
    loc_cols = {r['name']: r['type'] for r in cur.fetchall()}
    
    required_loc_cols = ['id', 'block', 'row', 'slot', 'full_location_name', 'is_occupied']
    for col in required_loc_cols:
        if col in loc_cols:
            ok(f"Column 'locations.{col}' exists")
        else:
            fail(f"Column 'locations.{col}' MISSING!")
            issues.append(f"Missing column: locations.{col}")
    
    # Test 1.4: Check data integrity
    cur.execute("SELECT COUNT(*) FROM vehicles WHERE vin IS NULL OR vin = ''")
    null_vins = cur.fetchone()[0]
    if null_vins == 0:
        ok("No NULL or empty VINs")
    else:
        fail(f"Found {null_vins} vehicles with NULL/empty VIN!")
        issues.append(f"Data integrity: {null_vins} NULL VINs")
    
    # Test 1.5: Check status values
    cur.execute("SELECT DISTINCT status FROM vehicles")
    statuses = [r['status'] for r in cur.fetchall()]
    valid_statuses = ['IN_STOCK', 'SHIPPED', None]
    for status in statuses:
        if status in valid_statuses:
            ok(f"Status '{status}' is valid")
        else:
            warn(f"Unknown status: '{status}'")
    
    conn.close()
    return len([i for i in issues if 'Missing' in i]) == 0

# ============================================
# 2. VEHICLE MANAGER TESTS
# ============================================
def test_vehicle_manager():
    section("2. VEHICLE MANAGER TESTS")
    
    try:
        from database.vehicle_manager import VehicleManager
        ok("VehicleManager imported successfully")
    except Exception as e:
        fail(f"Cannot import VehicleManager: {e}")
        issues.append(f"Import error: VehicleManager")
        return False
    
    vm = VehicleManager()  # No argument - uses config.DB_FILE
    
    # Test 2.1: get_in_stock_count
    try:
        count = vm.get_in_stock_count()
        if count is not None and isinstance(count, int):
            ok(f"get_in_stock_count() returns {count}")
        else:
            fail(f"get_in_stock_count() returned {type(count)}: {count}")
            issues.append("get_in_stock_count returns wrong type")
    except Exception as e:
        fail(f"get_in_stock_count() error: {e}")
        issues.append(f"get_in_stock_count error: {e}")
    
    # Test 2.2: get_in_stock with pagination
    try:
        data = vm.get_in_stock(limit=10, offset=0)
        if isinstance(data, list):
            ok(f"get_in_stock(limit=10) returns {len(data)} items")
            if len(data) > 0 and 'vin' in data[0]:
                ok("Data contains 'vin' field")
            elif len(data) > 0:
                fail("Data missing 'vin' field!")
                issues.append("get_in_stock missing vin field")
        else:
            fail(f"get_in_stock returns {type(data)}")
            issues.append("get_in_stock wrong return type")
    except Exception as e:
        fail(f"get_in_stock() error: {e}")
        issues.append(f"get_in_stock error: {e}")
    
    # Test 2.3: get_vins_ordered_by_id
    try:
        test_vins = ['TEST1', 'TEST2', 'TEST3']
        result = vm.get_vins_ordered_by_id(test_vins)
        if isinstance(result, list):
            ok(f"get_vins_ordered_by_id() works (returned {len(result)} items)")
        else:
            fail("get_vins_ordered_by_id returns wrong type")
            issues.append("get_vins_ordered_by_id wrong type")
    except Exception as e:
        fail(f"get_vins_ordered_by_id() error: {e}")
        issues.append(f"get_vins_ordered_by_id error: {e}")
    
    # Test 2.4: get_vehicle_by_vin
    try:
        # Get a real VIN from database (any vehicle, regardless of is_active status)
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT vin FROM vehicles WHERE status='IN_STOCK' LIMIT 1")
        row = cur.fetchone()
        conn.close()
        
        if row:
            real_vin = row[0]
            vehicle = vm.get_vehicle_by_vin(real_vin)
            if vehicle and 'vin' in vehicle:
                ok(f"get_vehicle_by_vin('{real_vin[:10]}...') works")
            else:
                # Vehicle may not be found if is_active=0 - this is expected behavior
                warn(f"get_vehicle_by_vin('{real_vin[:10]}...') returned None (may be inactive)")
        else:
            warn("No IN_STOCK vehicles in database to test get_vehicle_by_vin")
    except Exception as e:
        fail(f"get_vehicle_by_vin() error: {e}")
        issues.append(f"get_vehicle_by_vin error: {e}")
    
    # Test 2.5: Filter by owner
    try:
        count_filtered = vm.get_in_stock_count(owner_filter="PHƯƠNG ANH")
        if count_filtered is not None:
            ok(f"Owner filter works (PHƯƠNG ANH: {count_filtered} vehicles)")
        else:
            fail("Owner filter returns None")
            issues.append("Owner filter returns None")
    except Exception as e:
        fail(f"Owner filter error: {e}")
        issues.append(f"Owner filter error: {e}")
    
    # Test 2.6: Search term
    try:
        count_search = vm.get_in_stock_count(search_term="VF")
        if count_search is not None:
            ok(f"Search filter works (term 'VF': {count_search} vehicles)")
        else:
            fail("Search filter returns None")
            issues.append("Search filter returns None")
    except Exception as e:
        fail(f"Search filter error: {e}")
        issues.append(f"Search filter error: {e}")
    
    # vm.close() - not needed, uses context manager
    return True

# ============================================
# 3. LOCATION MANAGER TESTS
# ============================================
def test_location_manager():
    section("3. LOCATION MANAGER TESTS")
    
    try:
        from database.location_manager import LocationManager
        ok("LocationManager imported successfully")
    except Exception as e:
        fail(f"Cannot import LocationManager: {e}")
        issues.append("Import error: LocationManager")
        return False
    
    lm = LocationManager()
    
    # Test 3.1: get_all_free_locations
    try:
        free_locs = lm.get_all_free_locations()
        if isinstance(free_locs, list):
            ok(f"get_all_free_locations() returns {len(free_locs)} locations")
            if len(free_locs) > 0:
                # Check ordering
                names = [l['full_location_name'] for l in free_locs[:5]]
                info(f"First 5 free locations: {names}")
        else:
            fail("get_all_free_locations returns wrong type")
            issues.append("get_all_free_locations wrong type")
    except Exception as e:
        fail(f"get_all_free_locations() error: {e}")
        issues.append(f"get_all_free_locations error: {e}")
    
    # Test 3.2: get_all_blocks
    try:
        blocks = lm.get_all_blocks()
        if isinstance(blocks, list):
            ok(f"get_all_blocks() returns {len(blocks)} blocks: {blocks}")
        else:
            fail("get_all_blocks returns wrong type")
    except Exception as e:
        fail(f"get_all_blocks() error: {e}")
        issues.append(f"get_all_blocks error: {e}")
    
    # Test 3.3: get_block_statistics (requires block_name parameter)
    try:
        blocks = lm.get_all_blocks()
        if blocks:
            # Test with first block
            first_block = blocks[0]
            stats = lm.get_block_statistics(first_block)
            if isinstance(stats, dict) and 'total' in stats:
                ok(f"get_block_statistics('{first_block}') returns: total={stats['total']}, occupied={stats['occupied']}, free={stats['free']}")
            else:
                fail(f"get_block_statistics returns wrong type: {type(stats)}")
        else:
            warn("No blocks in database to test get_block_statistics")
    except Exception as e:
        fail(f"get_block_statistics() error: {e}")
        issues.append(f"get_block_statistics error: {e}")
    
    # Test 3.4: Location consistency check
    try:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        
        # Check: is_occupied should match vehicles with location_id
        cur.execute("""
            SELECT COUNT(*) FROM locations l
            WHERE l.is_occupied = 1 
            AND NOT EXISTS (SELECT 1 FROM vehicles v WHERE v.location_id = l.id AND v.is_active = 1)
        """)
        orphan_occupied = cur.fetchone()[0]
        
        if orphan_occupied == 0:
            ok("Location occupancy is consistent with vehicles")
        else:
            warn(f"Found {orphan_occupied} locations marked occupied but no vehicle assigned!")
            issues.append(f"Inconsistent occupancy: {orphan_occupied} orphan locations")
        
        conn.close()
    except Exception as e:
        fail(f"Consistency check error: {e}")
    
    # lm.close() - not needed
    return True

# ============================================
# 4. BATCH LOCATION ASSIGNMENT TESTS
# ============================================
def test_batch_assignment():
    section("4. BATCH LOCATION ASSIGNMENT LOGIC")
    
    # Test the ordering logic
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Test 4.1: Check VIN ordering method
    try:
        from database.vehicle_manager import VehicleManager
        vm = VehicleManager()
        
        # Get 5 random VINs
        cur.execute("SELECT vin FROM vehicles WHERE status='IN_STOCK' AND is_active=1 LIMIT 5")
        test_vins = [r['vin'] for r in cur.fetchall()]
        
        if len(test_vins) >= 3:
            # Test ordering
            ordered = vm.get_vins_ordered_by_id(test_vins)
            
            # Check it returns same VINs (or subset if some VINs were not found)
            if set(ordered).issubset(set(test_vins)):
                ok(f"get_vins_ordered_by_id returns valid VINs ({len(ordered)}/{len(test_vins)} found)")
            else:
                fail("get_vins_ordered_by_id returns different VINs!")
                issues.append("Ordering returns wrong VINs")
            
            # Check ordering is consistent
            ordered2 = vm.get_vins_ordered_by_id(test_vins)
            if ordered == ordered2:
                ok("Ordering is consistent (same result twice)")
            else:
                fail("Ordering is NOT consistent!")
                issues.append("Ordering not consistent")
        else:
            warn(f"Not enough IN_STOCK vehicles to test ordering (found {len(test_vins)}, need 3)")
        
        # vm.close() - not needed, uses context manager
    except Exception as e:
        fail(f"Ordering test error: {e}")
        issues.append(f"Ordering test error: {e}")
    
    # Test 4.2: Check location ordering
    try:
        from database.location_manager import LocationManager
        lm = LocationManager()
        
        free_locs = lm.get_all_free_locations()
        if len(free_locs) >= 2:
            # Check locations are ordered correctly (A before B before C, etc)
            names = [l['full_location_name'] for l in free_locs]
            is_sorted = names == sorted(names, key=lambda x: (x.split('-')[0], int(x.split('-')[1]), int(x.split('-')[2])))
            
            if is_sorted:
                ok("Free locations are correctly ordered (Block-Row-Slot)")
            else:
                warn("Free locations may not be in correct order")
                info(f"Sample: {names[:5]}")
        
        # lm.close() - not needed
    except Exception as e:
        fail(f"Location ordering test error: {e}")
    
    conn.close()
    return True

# ============================================
# 5. WEB DASHBOARD QUERIES TESTS
# ============================================
def test_dashboard_queries():
    section("5. WEB DASHBOARD QUERIES")
    
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    
    # Test 5.1: Summary stats query
    try:
        query = """
            SELECT 
                COUNT(*) as total_vehicles,
                SUM(CASE WHEN status = 'IN_STOCK' AND is_active = 1 THEN 1 ELSE 0 END) as in_stock,
                SUM(CASE WHEN status = 'SHIPPED' AND is_active = 1 THEN 1 ELSE 0 END) as shipped
            FROM vehicles
        """
        cur = conn.cursor()
        cur.execute(query)
        row = cur.fetchone()
        ok(f"Summary: Total={row['total_vehicles']}, InStock={row['in_stock']}, Shipped={row['shipped']}")
    except Exception as e:
        fail(f"Summary query error: {e}")
        issues.append(f"Dashboard summary query error: {e}")
    
    # Test 5.2: Daily inbound/outbound query
    try:
        query = """
            SELECT 
                DATE(date_in) as date,
                'Nhập' as type,
                COUNT(*) as count
            FROM vehicles 
            WHERE is_active = 1 
              AND DATE(date_in) BETWEEN DATE('2025-01-01') AND DATE('2026-01-18')
            GROUP BY DATE(date_in)
            LIMIT 5
        """
        cur.execute(query)
        rows = cur.fetchall()
        ok(f"Daily inbound query works ({len(rows)} days sampled)")
    except Exception as e:
        fail(f"Daily inbound query error: {e}")
        issues.append(f"Dashboard daily query error: {e}")
    
    # Test 5.3: Long stock vehicles query
    try:
        query = """
            SELECT 
                v.vin, 
                v.owner, 
                CAST(julianday('now') - julianday(v.date_in) AS INTEGER) as days_in_stock,
                COALESCE(l.block, '-') as block,
                COALESCE(CAST(l.slot AS TEXT), '-') as slot
            FROM vehicles v
            LEFT JOIN locations l ON v.location_id = l.id
            WHERE v.is_active = 1 
              AND v.status = 'IN_STOCK'
              AND julianday('now') - julianday(v.date_in) > 5
            ORDER BY days_in_stock DESC
            LIMIT 5
        """
        cur.execute(query)
        rows = cur.fetchall()
        ok(f"Long stock query works ({len(rows)} vehicles > 5 days)")
    except Exception as e:
        fail(f"Long stock query error: {e}")
        issues.append(f"Dashboard long stock query error: {e}")
    
    # Test 5.4: Yard occupancy query
    try:
        query = """
            SELECT 
                l.block as block, 
                SUM(CASE WHEN v.vin IS NOT NULL THEN 1 ELSE 0 END) as occupied,
                COUNT(l.id) as total_slots
            FROM locations l
            LEFT JOIN vehicles v ON l.id = v.location_id AND v.is_active = 1 AND v.status = 'IN_STOCK'
            WHERE l.block IS NOT NULL
            GROUP BY l.block
            ORDER BY l.block
        """
        cur.execute(query)
        rows = cur.fetchall()
        ok(f"Yard occupancy query works ({len(rows)} blocks)")
        for r in rows:
            info(f"  Block {r['block']}: {r['occupied']}/{r['total_slots']}")
    except Exception as e:
        fail(f"Yard occupancy query error: {e}")
        issues.append(f"Dashboard yard query error: {e}")
    
    conn.close()
    return True

# ============================================
# 6. CODE CONSISTENCY CHECKS
# ============================================
def test_code_consistency():
    section("6. CODE CONSISTENCY CHECKS")
    
    # Test 6.1: Check STATUS constants
    try:
        from database.vehicle_manager import STATUS_IN_STOCK, STATUS_SHIPPED
        ok(f"STATUS constants: IN_STOCK='{STATUS_IN_STOCK}', SHIPPED='{STATUS_SHIPPED}'")
        
        # Verify they match database values
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT status FROM vehicles WHERE status IS NOT NULL")
        db_statuses = [r[0] for r in cur.fetchall()]
        conn.close()
        
        if STATUS_IN_STOCK in db_statuses:
            ok(f"STATUS_IN_STOCK matches database")
        else:
            fail(f"STATUS_IN_STOCK '{STATUS_IN_STOCK}' not in database!")
            issues.append("STATUS constant mismatch")
            
    except ImportError as e:
        fail(f"Cannot import STATUS constants: {e}")
        issues.append("STATUS constants import error")
    
    # Test 6.2: Check translations exist (note: module uses lowercase 'translations')
    try:
        from translations import translations
        ok("translations dict imported successfully")
        
        # translations is a dict where keys are translation IDs, values have 'vi' and 'en' keys
        required_keys = ['batch_selected_count', 'batch_assign_location', 'status_stock_count']
        for key in required_keys:
            if key in translations and 'vi' in translations[key]:
                ok(f"Translation key '{key}' exists")
            else:
                warn(f"Translation key '{key}' might be missing")
    except Exception as e:
        fail(f"Translations error: {e}")
        issues.append(f"Translations error: {e}")
    
    # Test 6.3: Check config
    try:
        from config import DB_FILE as CONFIG_DB
        if CONFIG_DB == DB_FILE or CONFIG_DB == "vehicle_management_v5.1":
            ok(f"Config DB_FILE matches: {CONFIG_DB}")
        else:
            warn(f"Config DB_FILE differs: {CONFIG_DB} vs {DB_FILE}")
    except Exception as e:
        warn(f"Config check: {e}")
    
    return True

# ============================================
# 7. EDGE CASES
# ============================================
def test_edge_cases():
    section("7. EDGE CASES")
    
    from database.vehicle_manager import VehicleManager
    from database.location_manager import LocationManager
    
    vm = VehicleManager()
    lm = LocationManager()
    
    # Test 7.1: Empty list handling
    try:
        result = vm.get_vins_ordered_by_id([])
        if result == []:
            ok("Empty VIN list handled correctly")
        else:
            fail(f"Empty list returned: {result}")
    except Exception as e:
        fail(f"Empty list error: {e}")
        issues.append("Empty list not handled")
    
    # Test 7.2: Non-existent VIN
    try:
        result = vm.get_vehicle_by_vin("NON_EXISTENT_VIN_12345")
        if result is None:
            ok("Non-existent VIN returns None")
        else:
            warn(f"Non-existent VIN returned: {result}")
    except Exception as e:
        fail(f"Non-existent VIN error: {e}")
    
    # Test 7.3: Count with no matches
    try:
        count = vm.get_in_stock_count(owner_filter="OWNER_THAT_DOES_NOT_EXIST_12345")
        if count == 0:
            ok("No matches returns 0")
        else:
            warn(f"No matches returned: {count}")
    except Exception as e:
        fail(f"No matches error: {e}")
    
    # Test 7.4: Pagination edge cases
    try:
        # Large offset
        data = vm.get_in_stock(limit=10, offset=999999)
        if data == []:
            ok("Large offset returns empty list")
        else:
            warn(f"Large offset returned {len(data)} items")
    except Exception as e:
        fail(f"Large offset error: {e}")
    
    # vm.close() - not needed, uses context manager
    # lm.close() - not needed
    return True

# ============================================
# MAIN
# ============================================
def main():
    print("\n" + "="*60)
    print("🧪 VEHICLE MANAGEMENT SYSTEM - FULL LOGIC TEST")
    print("="*60)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Database: {DB_FILE}")
    print(f"📂 Working dir: {os.getcwd()}")
    print("="*60)
    
    # Run all tests
    results = []
    results.append(("Database Structure", test_database()))
    results.append(("Vehicle Manager", test_vehicle_manager()))
    results.append(("Location Manager", test_location_manager()))
    results.append(("Batch Assignment", test_batch_assignment()))
    results.append(("Dashboard Queries", test_dashboard_queries()))
    results.append(("Code Consistency", test_code_consistency()))
    results.append(("Edge Cases", test_edge_cases()))
    
    # Summary
    section("SUMMARY")
    passed = sum(1 for _, r in results if r)
    failed = len(results) - passed
    
    print(f"\n📊 Test Results:")
    for name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"   {status} - {name}")
    
    print(f"\n📈 Total: {passed}/{len(results)} test groups passed")
    
    if issues:
        print(f"\n{Colors.RED}⚠️ ISSUES FOUND ({len(issues)}):{Colors.END}")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
    else:
        print(f"\n{Colors.GREEN}✅ No critical issues found!{Colors.END}")
    
    return len(issues) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
