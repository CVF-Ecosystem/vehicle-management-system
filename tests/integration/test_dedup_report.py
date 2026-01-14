"""
Tests for HQ Deduplication Report (Phase 3.2)
"""

import json
import pytest
import sqlite3
import tempfile
from pathlib import Path

import config
from reporting.central_event_store import CentralEventStore
from reporting.transfer_normalizer import TransferNormalizer
from reporting.central_report_dedup import CentralReportGenerator, VehicleMovement


@pytest.fixture
def setup_dbs():
    """Setup central_report.db and security.db for testing."""
    import atexit
    
    tmpdir = tempfile.mkdtemp()
    central_db = f"{tmpdir}/central_report_test.db"
    security_db = f"{tmpdir}/security_test.db"

    # Create central_report DB schema
    conn = sqlite3.connect(central_db)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS vehicles (
            vin TEXT PRIMARY KEY,
            owner TEXT,
            vehicle_type TEXT,
            latest_site TEXT,
            last_date_in TEXT,
            last_date_out TEXT,
            last_status TEXT
        )
        """
    )

    # Create central_events table (for TRANSFER events)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS central_events (
            event_uid TEXT PRIMARY KEY,
            site_code TEXT,
            site_instance_id TEXT,
            bundle_id TEXT,
            event_source TEXT,
            occurred_at TEXT,
            action TEXT,
            table_name TEXT,
            record_id TEXT,
            payload_json TEXT
        )
        """
    )
    conn.commit()
    conn.close()

    # Create security DB (minimal)
    conn = sqlite3.connect(security_db)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT
        )
        """
    )
    conn.commit()
    conn.close()

    yield central_db, security_db
    
    # Cleanup
    import shutil
    try:
        shutil.rmtree(tmpdir)
    except Exception:
        pass


def _insert_vehicle(
    db_path: str,
    vin: str,
    owner: str,
    vtype: str,
    site: str,
    status: str,
    date_in: str = None,
    date_out: str = None,
) -> None:
    """Insert a vehicle record."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        INSERT OR REPLACE INTO vehicles
        (vin, owner, vehicle_type, latest_site, last_status, last_date_in, last_date_out)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (vin, owner, vtype, site, status, date_in, date_out),
    )
    conn.commit()
    conn.close()


def _insert_transfer_event(
    db_path: str,
    vin: str,
    from_site: str,
    to_site: str,
    out_at: str,
    in_at: str,
    transfer_days: float,
) -> None:
    """Insert a TRANSFER_DETECTED event."""
    conn = sqlite3.connect(db_path)
    payload = {
        "vin": vin,
        "from_site": from_site,
        "to_site": to_site,
        "out_at": out_at,
        "in_at": in_at,
        "transfer_duration_days": transfer_days,
        "transfer_status": "detected",
    }
    conn.execute(
        """
        INSERT INTO central_events
        (event_uid, site_code, site_instance_id, bundle_id, event_source,
         occurred_at, action, table_name, record_id, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"transfer-{vin}",
            "HQ",
            "hq-001",
            "transfer-norm",
            "transfer_normalizer",
            out_at,
            "TRANSFER_DETECTED",
            "vehicles",
            vin,
            json.dumps(payload),
        ),
    )
    conn.commit()
    conn.close()


class TestBasicDedup:
    """Test basic deduplication logic."""

    def test_vehicle_classification_normal(self, setup_dbs):
        """Vehicle without transfer = normal status."""
        central_db, security_db = setup_dbs

        _insert_vehicle(central_db, "VIN001", "Owner A", "Sedan", "site-a", "IN_STOCK")

        gen = CentralReportGenerator(central_db, security_db, enable_dedup=True)
        vehicles = gen.get_vehicles("2025-01-01", "2025-01-31")

        assert len(vehicles) == 1
        assert vehicles[0].vin == "VIN001"
        assert vehicles[0].transfer_status == "normal"

    def test_vehicle_classification_transfer_out(self, setup_dbs):
        """Vehicle that was transferred out."""
        central_db, security_db = setup_dbs

        # Vehicle is at site-a (where it was transferred OUT from)
        _insert_vehicle(central_db, "VIN002", "Owner B", "SUV", "site-a", "IN_STOCK")
        _insert_transfer_event(
            central_db, "VIN002", "site-a", "site-b", "2025-01-10T10:00:00", "2025-01-11T15:00:00", 1.2
        )

        gen = CentralReportGenerator(central_db, security_db, enable_dedup=True)
        vehicles = gen.get_vehicles("2025-01-01", "2025-01-31")

        assert len(vehicles) == 1
        assert vehicles[0].transfer_status == "internal_transfer_out"

    def test_vehicle_classification_transfer_in(self, setup_dbs):
        """Vehicle that was transferred in."""
        central_db, security_db = setup_dbs

        # Vehicle is at site-b (where it was transferred IN to)
        _insert_vehicle(central_db, "VIN003", "Owner C", "Truck", "site-b", "IN_STOCK")
        _insert_transfer_event(
            central_db, "VIN003", "site-a", "site-b", "2025-01-10T10:00:00", "2025-01-11T15:00:00", 1.2
        )

        gen = CentralReportGenerator(central_db, security_db, enable_dedup=True)
        vehicles = gen.get_vehicles("2025-01-01", "2025-01-31")

        assert len(vehicles) == 1
        assert vehicles[0].transfer_status == "internal_transfer_in"


class TestSiteSummary:
    """Test site summary with deduplication."""

    def test_summary_without_dedup(self, setup_dbs):
        """Summary without dedup = normal counting."""
        central_db, security_db = setup_dbs

        # 10 vehicles at site-a, all with "imported" status
        for i in range(10):
            _insert_vehicle(
                central_db, f"VIN{i:03d}", "Owner", "Sedan", "site-a", config.STATUS_IN_STOCK
            )

        gen = CentralReportGenerator(central_db, security_db, enable_dedup=False)
        summary = gen.get_site_summary("2025-01-01", "2025-01-31")

        assert "site-a" in summary
        assert summary["site-a"]["ending_stock"] == 10

    def test_summary_with_transfers(self, setup_dbs):
        """Summary with transfers properly categorized."""
        central_db, security_db = setup_dbs

        # 5 vehicles at site-a (not transferred)
        for i in range(5):
            _insert_vehicle(central_db, f"VIN{i:03d}", "Owner", "Sedan", "site-a", "IN_STOCK")

        # 3 vehicles with transfer events defined
        for i in range(3):
            vin = f"VINA{i:02d}"
            # Insert at site-a with date_out (indicates it left)
            _insert_vehicle(
                central_db,
                vin,
                "Owner",
                "Sedan",
                "site-a",
                "IN_STOCK",
                date_out="2025-01-10T10:00:00",
            )
            # Create transfer event
            _insert_transfer_event(
                central_db, vin, "site-a", "site-b", "2025-01-10T10:00:00", "2025-01-11T15:00:00", 1.2
            )

        gen = CentralReportGenerator(central_db, security_db, enable_dedup=True)
        summary = gen.get_site_summary("2025-01-01", "2025-01-31")

        # Site A: 5 local + 3 transferred out = 8 total
        assert summary["site-a"]["ending_stock"] == 8
        assert summary["site-a"]["transfers_out"] == 3


class TestReportExport:
    """Test report export functionality."""

    def test_export_vehicle_movement_csv(self, setup_dbs):
        """Export vehicle movement CSV with transfer status."""
        central_db, security_db = setup_dbs

        _insert_vehicle(central_db, "VIN001", "Owner A", "Sedan", "site-a", "IN_STOCK")
        _insert_transfer_event(
            central_db, "VIN001", "site-a", "site-b", "2025-01-10T10:00:00", "2025-01-11T15:00:00", 1.2
        )

        gen = CentralReportGenerator(central_db, security_db, enable_dedup=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = f"{tmpdir}/movement.csv"
            gen.export_vehicle_movement_csv("2025-01-01", "2025-01-31", out_path)

            assert Path(out_path).exists()
            with open(out_path, "r") as f:
                lines = f.readlines()
                assert len(lines) == 2  # header + 1 vehicle
                assert "transfer_status" in lines[0]
                assert "internal_transfer_out" in lines[1]

    def test_export_site_summary_csv(self, setup_dbs):
        """Export site summary CSV."""
        central_db, security_db = setup_dbs

        _insert_vehicle(central_db, "VIN001", "Owner", "Sedan", "site-a", "IN_STOCK")
        _insert_vehicle(central_db, "VIN002", "Owner", "Sedan", "site-b", "IN_STOCK")

        gen = CentralReportGenerator(central_db, security_db, enable_dedup=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = f"{tmpdir}/summary.csv"
            gen.export_site_summary_csv("2025-01-01", "2025-01-31", out_path)

            assert Path(out_path).exists()
            with open(out_path, "r") as f:
                lines = f.readlines()
                assert len(lines) == 3  # header + 2 sites

    def test_export_transfer_summary_csv(self, setup_dbs):
        """Export transfer summary CSV."""
        central_db, security_db = setup_dbs

        _insert_transfer_event(
            central_db, "VIN001", "site-a", "site-b", "2025-01-10T10:00:00", "2025-01-11T15:00:00", 1.2
        )
        _insert_transfer_event(
            central_db, "VIN002", "site-b", "site-c", "2025-01-15T10:00:00", "2025-01-16T15:00:00", 1.2
        )

        gen = CentralReportGenerator(central_db, security_db, enable_dedup=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = f"{tmpdir}/transfers.csv"
            gen.export_transfer_summary_csv("2025-01-01", "2025-01-31", out_path)

            assert Path(out_path).exists()
            with open(out_path, "r") as f:
                lines = f.readlines()
                assert len(lines) == 3  # header + 2 transfers

    def test_export_consolidated_report(self, setup_dbs):
        """Export all reports together."""
        central_db, security_db = setup_dbs

        # Create test data
        _insert_vehicle(central_db, "VIN001", "Owner", "Sedan", "site-a", "IN_STOCK")
        _insert_vehicle(central_db, "VIN002", "Owner", "Sedan", "site-b", "IN_STOCK")
        _insert_transfer_event(
            central_db, "VIN001", "site-a", "site-b", "2025-01-10T10:00:00", "2025-01-11T15:00:00", 1.2
        )

        gen = CentralReportGenerator(central_db, security_db, enable_dedup=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            reports = gen.export_consolidated_report("2025-01-01", "2025-01-31", tmpdir)

            assert "vehicle_movement" in reports
            assert "site_summary" in reports
            assert "transfer_summary" in reports
            assert Path(reports["vehicle_movement"]).exists()
            assert Path(reports["site_summary"]).exists()
            assert Path(reports["transfer_summary"]).exists()
