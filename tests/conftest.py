"""
Pytest configuration and fixtures for Vehicle Management System tests.

This file contains shared fixtures and configuration for all test modules.
"""

import pytest
import os
import sys
import sqlite3
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import random
import string
import hashlib

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# SAFETY: PROTECT PRODUCTION DB DURING TESTS
# =============================================================================


def _resolve_db_path(db_file: str) -> Path:
    """Resolve DB_FILE to an absolute path (repo-root relative if needed)."""
    p = Path(db_file)
    if p.is_absolute():
        return p
    return PROJECT_ROOT / p


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


@pytest.fixture(scope="session", autouse=True)
def protect_production_db(tmp_path_factory):
    """Force tests to use a temp DB and detect accidental writes to the real DB.

    Why:
    - Code uses singleton DB connection (BaseManager) with default config.DB_FILE.
    - If a test (or imported module) triggers BaseManager() without db_path, it may touch the real DB.
    """
    import config

    # Track the real DB file hash (if exists) to detect accidental mutation.
    real_db_path = _resolve_db_path(config.DB_FILE)
    real_db_hash_before = None
    if real_db_path.exists() and real_db_path.is_file():
        try:
            real_db_hash_before = _sha256_file(real_db_path)
        except Exception:
            real_db_hash_before = None

    yield

    # Teardown: detect if real DB was modified during tests.
    if real_db_hash_before is not None and real_db_path.exists() and real_db_path.is_file():
        try:
            real_db_hash_after = _sha256_file(real_db_path)
        except Exception:
            real_db_hash_after = real_db_hash_before

        assert real_db_hash_after == real_db_hash_before, (
            "Production DB file was modified during tests. "
            "This indicates a test accidentally used the real DB. "
            f"Real DB path: {real_db_path}"
        )


@pytest.fixture(autouse=True)
def force_test_db(tmp_path, monkeypatch):
    """Per-test DB isolation.

    Ensures any code path that uses config.DB_FILE will use a temp db under tmp_path.
    This prevents accidental writes to the real DB and avoids cross-test pollution.
    """
    import config

    test_db_path = tmp_path / "pytest_function.db"
    monkeypatch.setattr(config, "DB_FILE", str(test_db_path), raising=False)

    # Reset BaseManager singleton before and after each test.
    try:
        from database.base_manager import BaseManager
        BaseManager._conn = None
        BaseManager._db_path = None
    except Exception:
        pass

    yield

    try:
        from database.base_manager import BaseManager
        BaseManager._conn = None
        BaseManager._db_path = None
    except Exception:
        pass


# =============================================================================
# DATABASE FIXTURES
# =============================================================================

@pytest.fixture(scope="function")
def fresh_db(tmp_path):
    """
    Fixture: DB trống (fresh) - Tạo DB mới với schema nhưng không có dữ liệu.
    
    Yields:
        Path: Đường dẫn tới file DB tạm
    """
    db_path = tmp_path / "test_fresh.db"
    
    from database.base_manager import BaseManager
    
    # Reset singleton connection
    BaseManager._conn = None
    BaseManager._db_path = None
    
    # Initialize schema với db_path cụ thể
    manager = BaseManager(str(db_path))
    
    yield db_path
    
    # Cleanup - reset connection
    BaseManager._conn = None
    BaseManager._db_path = None


@pytest.fixture(scope="function")
def sample_db(tmp_path):
    """
    Fixture: DB mẫu nhỏ - Có 50-200 xe với đủ trạng thái.
    
    Trạng thái bao gồm:
    - inbound: Xe vừa nhập
    - in_stock: Xe đang tồn
    - dispatched: Xe đã xuất
    - archived: Xe đã lưu trữ
    
    Yields:
        tuple: (db_path, test_data_summary)
    """
    db_path = tmp_path / "test_sample.db"
    
    from database.base_manager import BaseManager
    
    # Reset singleton
    BaseManager._conn = None
    BaseManager._db_path = None
    
    manager = BaseManager(str(db_path))
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create sample data
    test_data = {
        "vehicles": [],
        "drivers": [],
        "transport_vehicles": [],
        "locations": [],
        "dispatches": []
    }
    
    # Create locations first - phù hợp với schema thực tế
    locations = [
        ("A", "1", 1, "A-1-1"), ("A", "1", 2, "A-1-2"), ("A", "2", 1, "A-2-1"), ("A", "2", 2, "A-2-2"),
        ("B", "1", 1, "B-1-1"), ("B", "1", 2, "B-1-2"), ("B", "2", 1, "B-2-1"), ("B", "2", 2, "B-2-2"),
        ("C", "1", 1, "C-1-1"), ("C", "1", 2, "C-1-2"), ("C", "2", 1, "C-2-1"), ("C", "2", 2, "C-2-2"),
    ]
    for block, row, slot, full_name in locations:
        cursor.execute(
            "INSERT INTO locations (block, row, slot, full_location_name, is_occupied) VALUES (?, ?, ?, ?, 0)",
            (block, row, slot, full_name)
        )
        test_data["locations"].append({
            "id": cursor.lastrowid,
            "block": block,
            "row": row,
            "slot": slot,
            "full_location_name": full_name
        })
    
    # Create drivers
    drivers = ["Nguyễn Văn A", "Trần Văn B", "Lê Văn C", "Phạm Văn D"]
    for name in drivers:
        phone = f"09{random.randint(10000000, 99999999)}"
        cursor.execute(
            "INSERT INTO drivers (name, phone) VALUES (?, ?)",
            (name, phone)
        )
        test_data["drivers"].append({"id": cursor.lastrowid, "name": name})
    
    # Create transport vehicles - phù hợp với schema (license_plate không phải plate_number)
    transport_vehicles = ["51C-12345", "51C-67890", "51H-11111", "51H-22222"]
    for plate in transport_vehicles:
        cursor.execute(
            "INSERT INTO transport_vehicles (license_plate) VALUES (?)",
            (plate,)
        )
        test_data["transport_vehicles"].append({"id": cursor.lastrowid, "license_plate": plate})
    
    # Create vehicles with different statuses
    owners = ["THACO", "TOYOTA VN", "HYUNDAI VN", "FORD VN", "HONDA VN"]
    vehicle_types = ["Sedan", "SUV", "Pickup", "Hatchback", "MPV"]
    statuses = ["in_stock", "in_stock", "in_stock", "dispatched", "archived"]  # Distribution
    
    base_date = datetime.now() - timedelta(days=30)
    
    for i in range(100):  # Create 100 vehicles
        # Generate VIN
        vin = ''.join(random.choices(string.ascii_uppercase + string.digits, k=17))
        
        owner = random.choice(owners)
        v_type = random.choice(vehicle_types)
        status = random.choice(statuses)
        
        date_in = (base_date + timedelta(days=random.randint(0, 25))).strftime("%Y-%m-%d")
        
        # Determine date_out and dispatch based on status
        date_out = None
        dispatch_id = None
        location_id = None
        
        if status == "in_stock":
            # Assign a location
            available_loc = random.choice(test_data["locations"])
            location_id = available_loc["id"]
        elif status == "dispatched":
            date_out = (datetime.strptime(date_in, "%Y-%m-%d") + timedelta(days=random.randint(1, 5))).strftime("%Y-%m-%d")
        elif status == "archived":
            date_out = (datetime.strptime(date_in, "%Y-%m-%d") + timedelta(days=random.randint(1, 10))).strftime("%Y-%m-%d")
        
        cursor.execute("""
            INSERT INTO vehicles (vin, owner, vehicle_type, status, date_in, date_out, location_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (vin, owner, v_type, status, date_in, date_out, location_id))
        
        test_data["vehicles"].append({
            "id": cursor.lastrowid,
            "vin": vin,
            "owner": owner,
            "status": status
        })
    
    conn.commit()
    conn.close()
    
    # Summary
    summary = {
        "total_vehicles": len(test_data["vehicles"]),
        "in_stock": len([v for v in test_data["vehicles"] if v["status"] == "in_stock"]),
        "dispatched": len([v for v in test_data["vehicles"] if v["status"] == "dispatched"]),
        "archived": len([v for v in test_data["vehicles"] if v["status"] == "archived"]),
        "locations": len(test_data["locations"]),
        "drivers": len(test_data["drivers"]),
    }
    
    yield db_path, summary
    
    # Cleanup
    BaseManager._conn = None
    BaseManager._db_path = None


@pytest.fixture(scope="function")
def edge_case_db(tmp_path):
    """
    Fixture: DB edge cases - Dữ liệu biên và bất thường.
    
    Bao gồm:
    - VIN trùng
    - Owner có dấu/không dấu
    - Ngày rỗng/sai format
    - Ký tự đặc biệt
    
    Yields:
        tuple: (db_path, edge_cases_info)
    """
    db_path = tmp_path / "test_edge_cases.db"
    
    from database.base_manager import BaseManager
    
    # Reset singleton
    BaseManager._conn = None
    BaseManager._db_path = None
    
    manager = BaseManager(str(db_path))
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    edge_cases = []
    
    # Case 1: VIN với độ dài khác nhau
    vins_varied = [
        ("ABC123", "VIN quá ngắn"),
        ("12345678901234567", "VIN đúng 17 ký tự"),
        ("123456789012345678901234567890", "VIN quá dài"),
        ("", "VIN rỗng"),
    ]
    
    for vin, desc in vins_varied:
        try:
            cursor.execute(
                "INSERT INTO vehicles (vin, owner, status, date_in) VALUES (?, ?, ?, ?)",
                (vin, "Test Owner", "in_stock", "2024-01-01")
            )
            edge_cases.append({"type": "vin_length", "value": vin, "desc": desc, "inserted": True})
        except Exception as e:
            edge_cases.append({"type": "vin_length", "value": vin, "desc": desc, "inserted": False, "error": str(e)})
    
    # Case 2: Owner với dấu tiếng Việt
    owners_vietnamese = [
        "Công ty THACO",
        "CÔNG TY TOYOTA VIỆT NAM",
        "Nguyễn Văn Ả",
        "Lê Thị Ô",
    ]
    
    for owner in owners_vietnamese:
        vin = ''.join(random.choices(string.ascii_uppercase + string.digits, k=17))
        cursor.execute(
            "INSERT INTO vehicles (vin, owner, status, date_in) VALUES (?, ?, ?, ?)",
            (vin, owner, "in_stock", "2024-01-01")
        )
        edge_cases.append({"type": "vietnamese_owner", "value": owner, "inserted": True})
    
    # Case 3: Ký tự đặc biệt
    special_chars = [
        "Owner's Company",  # Apostrophe
        "Owner \"Quoted\"",  # Quotes
        "Owner; DROP TABLE;",  # SQL injection attempt
        "Owner\nNewline",  # Newline
        "Owner\tTab",  # Tab
    ]
    
    for owner in special_chars:
        vin = ''.join(random.choices(string.ascii_uppercase + string.digits, k=17))
        try:
            cursor.execute(
                "INSERT INTO vehicles (vin, owner, status, date_in) VALUES (?, ?, ?, ?)",
                (vin, owner, "in_stock", "2024-01-01")
            )
            edge_cases.append({"type": "special_char", "value": owner, "inserted": True})
        except Exception as e:
            edge_cases.append({"type": "special_char", "value": owner, "inserted": False, "error": str(e)})
    
    # Case 4: Date edge cases
    dates_edge = [
        ("2024-01-01", "Date chuẩn"),
        ("01-01-2024", "Date format khác"),
        ("2024/01/01", "Date với slash"),
        ("", "Date rỗng"),
        (None, "Date NULL"),
        ("invalid-date", "Date không hợp lệ"),
    ]
    
    for date_val, desc in dates_edge:
        vin = ''.join(random.choices(string.ascii_uppercase + string.digits, k=17))
        try:
            cursor.execute(
                "INSERT INTO vehicles (vin, owner, status, date_in) VALUES (?, ?, ?, ?)",
                (vin, "Date Test Owner", "in_stock", date_val)
            )
            edge_cases.append({"type": "date_format", "value": date_val, "desc": desc, "inserted": True})
        except Exception as e:
            edge_cases.append({"type": "date_format", "value": date_val, "desc": desc, "inserted": False, "error": str(e)})
    
    conn.commit()
    conn.close()
    
    yield db_path, edge_cases
    
    # Cleanup
    BaseManager._conn = None
    BaseManager._db_path = None


# =============================================================================
# UTILITY FIXTURES
# =============================================================================

@pytest.fixture
def mock_config(tmp_path, monkeypatch):
    """
    Fixture: Mock config với đường dẫn tạm.
    """
    # Create temp config
    config_path = tmp_path / "config.ini"
    config_path.write_text("""
[Settings]
language = vi
theme = dark

[Database]
path = test.db
    """)
    
    return config_path


@pytest.fixture
def sample_vin_list():
    """
    Fixture: Danh sách VIN mẫu để test.
    """
    return [
        # Valid VINs (17 characters)
        "1HGBH41JXMN109186",
        "JM1BK32F781234567",
        "WVWZZZ3CZWE123456",
        # Invalid VINs
        "INVALID",
        "12345",
        "1HGBH41JXMN10918",  # 16 chars
        "1HGBH41JXMN1091860",  # 18 chars
        "",  # Empty
        "1HGBH41JXIN109186",  # Contains I
        "1HGBH41JXON109186",  # Contains O
        "1HGBH41JXQN109186",  # Contains Q
    ]


@pytest.fixture
def sample_owner_list():
    """
    Fixture: Danh sách Owner mẫu để test normalization.
    """
    return [
        # Raw -> Expected normalized
        ("thaco", "THACO"),
        ("THACO", "THACO"),
        ("Thaco Truong Hai", "THACO"),
        ("toyota vn", "TOYOTA VN"),
        ("TOYOTA VIETNAM", "TOYOTA VN"),
        ("hyundai thanh cong", "HYUNDAI TC"),
        ("", ""),
        ("  spaced  ", "SPACED"),
    ]


# =============================================================================
# TEST MARKERS
# =============================================================================

def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "smoke: Quick smoke tests (select with '-m smoke')"
    )
    config.addinivalue_line(
        "markers", "regression: Full regression tests (select with '-m regression')"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer to run"
    )
    config.addinivalue_line(
        "markers", "db: Tests that require database"
    )
    config.addinivalue_line(
        "markers", "ui: Tests that require UI components"
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def generate_random_vin() -> str:
    """Generate a random valid VIN (17 characters, no I/O/Q)."""
    valid_chars = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"
    return ''.join(random.choices(valid_chars, k=17))


def generate_test_vehicle_data(count: int = 1) -> list:
    """Generate test vehicle data."""
    owners = ["THACO", "TOYOTA VN", "HYUNDAI TC", "FORD VN"]
    types = ["Sedan", "SUV", "Pickup", "Hatchback"]
    
    vehicles = []
    for _ in range(count):
        vehicles.append({
            "vin": generate_random_vin(),
            "owner": random.choice(owners),
            "vehicle_type": random.choice(types),
            "date_in": datetime.now().strftime("%Y-%m-%d"),
            "status": "in_stock"
        })
    
    return vehicles if count > 1 else vehicles[0]
