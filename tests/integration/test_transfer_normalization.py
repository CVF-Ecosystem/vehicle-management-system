"""
Integration tests for TRANSFER event normalization (Phase 3.1).

These tests verify:
1. OUT↔IN event matching logic
2. Time window constraints
3. Conflict resolution (multiple IN/OUT candidates)
4. Chain transfer detection (A→B→C)
5. Edge cases (malformed, same site, duplicates)
"""

import json
import pytest
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import config
from reporting.central_event_store import CentralEventStore
from reporting.transfer_normalizer import TransferNormalizer, TransferEvent


@pytest.fixture
def central_events_db(tmp_path):
    """Create a temporary central_events.db for testing."""
    db_path = str(tmp_path / "central_events_test.db")
    store = CentralEventStore(db_path)
    yield db_path
    # Cleanup is implicit with tmp_path


def _add_event(
    db_path: str,
    event_uid: str,
    site_code: str,
    occurred_at: str,
    action: str,
    record_id: str,
    payload: dict,
) -> None:
    """Helper to insert an event into central_events table."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        INSERT INTO central_events
        (event_uid, site_code, site_instance_id, bundle_id, event_source,
         occurred_at, action, table_name, record_id, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_uid,
            site_code,
            "site-001",
            "bundle-001",
            "audit",
            occurred_at,
            action,
            "vehicles",
            record_id,
            json.dumps(payload),
        ),
    )
    conn.commit()
    conn.close()


def _out_event_payload(vin: str, from_site: str, date_out: str) -> dict:
    """Generate OUT event payload."""
    return {
        "old_value": {"status": config.STATUS_IN_STOCK, "date_out": None},
        "new_value": {"status": config.STATUS_SHIPPED, "date_out": date_out},
    }


def _in_event_payload(vin: str, date_in: str) -> dict:
    """Generate IN event payload."""
    return {
        "old_value": None,
        "new_value": {"status": config.STATUS_IN_STOCK, "date_in": date_in},
    }


class TestBasicTransferMatching:
    """Test basic OUT→IN matching."""

    def test_basic_out_in_match(self, central_events_db):
        """Simple transfer: Site A OUT → Site B IN within time window."""
        # OUT at site A on 2025-01-10 10:00
        _add_event(
            central_events_db,
            "evt-001",
            "site-a",
            "2025-01-10T10:00:00",
            "UPDATE",
            "VIN001",
            _out_event_payload("VIN001", "site-a", "2025-01-10"),
        )

        # IN at site B on 2025-01-11 15:00 (1 day later, within 7-day window)
        _add_event(
            central_events_db,
            "evt-002",
            "site-b",
            "2025-01-11T15:00:00",
            "CREATE",
            "VIN001",
            _in_event_payload("VIN001", "2025-01-11"),
        )

        normalizer = TransferNormalizer(central_events_db)
        transfers = normalizer.normalize("2025-01-01", "2025-01-31")

        assert len(transfers) == 1
        assert transfers[0].vin == "VIN001"
        assert transfers[0].from_site == "site-a"
        assert transfers[0].to_site == "site-b"
        assert transfers[0].transfer_status == "detected"

    def test_same_site_no_transfer(self, central_events_db):
        """OUT→IN at SAME site should NOT create transfer."""
        # OUT at site A
        _add_event(
            central_events_db,
            "evt-001",
            "site-a",
            "2025-01-10T10:00:00",
            "UPDATE",
            "VIN002",
            _out_event_payload("VIN002", "site-a", "2025-01-10"),
        )

        # IN at SAME site A (should be ignored)
        _add_event(
            central_events_db,
            "evt-002",
            "site-a",  # Same site!
            "2025-01-11T15:00:00",
            "CREATE",
            "VIN002",
            _in_event_payload("VIN002", "2025-01-11"),
        )

        normalizer = TransferNormalizer(central_events_db)
        transfers = normalizer.normalize("2025-01-01", "2025-01-31")

        assert len(transfers) == 0, "Same-site IN/OUT should not create transfer"


class TestTimeWindowConstraints:
    """Test time window (max_days) constraints."""

    def test_within_time_window(self, central_events_db):
        """IN exactly at max_days boundary should match."""
        base = datetime.fromisoformat("2025-01-10T10:00:00")

        _add_event(
            central_events_db,
            "evt-001",
            "site-a",
            base.isoformat(),
            "UPDATE",
            "VIN003",
            _out_event_payload("VIN003", "site-a", "2025-01-10"),
        )

        # Exactly 7 days later
        in_time = base + timedelta(days=7)
        _add_event(
            central_events_db,
            "evt-002",
            "site-b",
            in_time.isoformat(),
            "CREATE",
            "VIN003",
            _in_event_payload("VIN003", "2025-01-17"),
        )

        normalizer = TransferNormalizer(central_events_db, max_days=7)
        transfers = normalizer.normalize("2025-01-01", "2025-01-31")

        assert len(transfers) == 1, "Event at max_days boundary should match"

    def test_exceeds_time_window(self, central_events_db):
        """IN beyond max_days should NOT match."""
        base = datetime.fromisoformat("2025-01-10T10:00:00")

        _add_event(
            central_events_db,
            "evt-001",
            "site-a",
            base.isoformat(),
            "UPDATE",
            "VIN004",
            _out_event_payload("VIN004", "site-a", "2025-01-10"),
        )

        # 8 days later (exceeds 7-day window)
        in_time = base + timedelta(days=8)
        _add_event(
            central_events_db,
            "evt-002",
            "site-b",
            in_time.isoformat(),
            "CREATE",
            "VIN004",
            _in_event_payload("VIN004", "2025-01-18"),
        )

        normalizer = TransferNormalizer(central_events_db, max_days=7)
        transfers = normalizer.normalize("2025-01-01", "2025-01-31")

        assert len(transfers) == 0, "Event beyond max_days should not match"


class TestConflictResolution:
    """Test conflict resolution when multiple candidates exist."""

    def test_multiple_in_pick_earliest(self, central_events_db):
        """Single OUT + 2 IN candidates → pick earliest IN."""
        _add_event(
            central_events_db,
            "evt-001",
            "site-a",
            "2025-01-10T10:00:00",
            "UPDATE",
            "VIN005",
            _out_event_payload("VIN005", "site-a", "2025-01-10"),
        )

        # First IN candidate (site B, 1 day later)
        _add_event(
            central_events_db,
            "evt-002",
            "site-b",
            "2025-01-11T15:00:00",
            "CREATE",
            "VIN005",
            _in_event_payload("VIN005", "2025-01-11"),
        )

        # Second IN candidate (site C, 2 days later)
        _add_event(
            central_events_db,
            "evt-003",
            "site-c",
            "2025-01-12T15:00:00",
            "CREATE",
            "VIN005",
            _in_event_payload("VIN005", "2025-01-12"),
        )

        normalizer = TransferNormalizer(central_events_db)
        transfers = normalizer.normalize("2025-01-01", "2025-01-31")

        assert len(transfers) == 1
        assert transfers[0].to_site == "site-b", "Should pick earliest IN"

    def test_multiple_out_pick_latest(self, central_events_db):
        """Single IN + 2 OUT candidates → pick latest OUT."""
        # First OUT candidate (site A, 2025-01-08)
        _add_event(
            central_events_db,
            "evt-001",
            "site-a",
            "2025-01-08T10:00:00",
            "UPDATE",
            "VIN006",
            _out_event_payload("VIN006", "site-a", "2025-01-08"),
        )

        # Second OUT candidate (site B, 2025-01-10, before IN)
        _add_event(
            central_events_db,
            "evt-002",
            "site-b",
            "2025-01-10T10:00:00",
            "UPDATE",
            "VIN006",
            _out_event_payload("VIN006", "site-b", "2025-01-10"),
        )

        # IN at site C
        _add_event(
            central_events_db,
            "evt-003",
            "site-c",
            "2025-01-11T15:00:00",
            "CREATE",
            "VIN006",
            _in_event_payload("VIN006", "2025-01-11"),
        )

        normalizer = TransferNormalizer(central_events_db)
        transfers = normalizer.normalize("2025-01-01", "2025-01-31")

        assert len(transfers) == 1
        assert transfers[0].from_site == "site-b", "Should pick latest OUT"


class TestChainTransfers:
    """Test chain detection: A→B→C→..."""

    def test_chain_transfer_a_to_b_to_c(self, central_events_db):
        """VIN travels A→B→C. Should create 2 TRANSFER events."""
        # OUT at A
        _add_event(
            central_events_db,
            "evt-001",
            "site-a",
            "2025-01-10T10:00:00",
            "UPDATE",
            "VIN007",
            _out_event_payload("VIN007", "site-a", "2025-01-10"),
        )

        # IN at B, then OUT again
        _add_event(
            central_events_db,
            "evt-002",
            "site-b",
            "2025-01-11T15:00:00",
            "CREATE",
            "VIN007",
            _in_event_payload("VIN007", "2025-01-11"),
        )

        _add_event(
            central_events_db,
            "evt-003",
            "site-b",
            "2025-01-12T10:00:00",
            "UPDATE",
            "VIN007",
            _out_event_payload("VIN007", "site-b", "2025-01-12"),
        )

        # IN at C
        _add_event(
            central_events_db,
            "evt-004",
            "site-c",
            "2025-01-13T15:00:00",
            "CREATE",
            "VIN007",
            _in_event_payload("VIN007", "2025-01-13"),
        )

        normalizer = TransferNormalizer(central_events_db)
        transfers = normalizer.normalize("2025-01-01", "2025-01-31")

        assert len(transfers) == 2, "Should detect A→B and B→C as 2 transfers"
        assert transfers[0].from_site == "site-a" and transfers[0].to_site == "site-b"
        assert transfers[1].from_site == "site-b" and transfers[1].to_site == "site-c"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_events(self, central_events_db):
        """Empty database should return empty results."""
        normalizer = TransferNormalizer(central_events_db)
        transfers = normalizer.normalize("2025-01-01", "2025-01-31")

        assert len(transfers) == 0

    def test_missing_date_out(self, central_events_db):
        """OUT event without date_out should be ignored."""
        _add_event(
            central_events_db,
            "evt-001",
            "site-a",
            "2025-01-10T10:00:00",
            "UPDATE",
            "VIN008",
            {
                "old_value": {"status": config.STATUS_IN_STOCK, "date_out": None},
                "new_value": {"status": config.STATUS_SHIPPED, "date_out": None},  # Missing!
            },
        )

        _add_event(
            central_events_db,
            "evt-002",
            "site-b",
            "2025-01-11T15:00:00",
            "CREATE",
            "VIN008",
            _in_event_payload("VIN008", "2025-01-11"),
        )

        normalizer = TransferNormalizer(central_events_db)
        transfers = normalizer.normalize("2025-01-01", "2025-01-31")

        assert len(transfers) == 0, "OUT without date_out should be ignored"

    def test_missing_date_in(self, central_events_db):
        """IN event without date_in should be ignored."""
        _add_event(
            central_events_db,
            "evt-001",
            "site-a",
            "2025-01-10T10:00:00",
            "UPDATE",
            "VIN009",
            _out_event_payload("VIN009", "site-a", "2025-01-10"),
        )

        _add_event(
            central_events_db,
            "evt-002",
            "site-b",
            "2025-01-11T15:00:00",
            "CREATE",
            "VIN009",
            {
                "old_value": None,
                "new_value": {"status": config.STATUS_IN_STOCK, "date_in": None},  # Missing!
            },
        )

        normalizer = TransferNormalizer(central_events_db)
        transfers = normalizer.normalize("2025-01-01", "2025-01-31")

        assert len(transfers) == 0, "IN without date_in should be ignored"

    def test_in_before_out(self, central_events_db):
        """IN occurring before OUT should be ignored."""
        _add_event(
            central_events_db,
            "evt-002",  # IN happens first
            "site-b",
            "2025-01-10T10:00:00",
            "CREATE",
            "VIN010",
            _in_event_payload("VIN010", "2025-01-10"),
        )

        _add_event(
            central_events_db,
            "evt-001",  # OUT happens later
            "site-a",
            "2025-01-11T15:00:00",
            "UPDATE",
            "VIN010",
            _out_event_payload("VIN010", "site-a", "2025-01-11"),
        )

        normalizer = TransferNormalizer(central_events_db)
        transfers = normalizer.normalize("2025-01-01", "2025-01-31")

        assert len(transfers) == 0, "IN before OUT should be ignored"

    def test_duplicate_transfers_not_created(self, central_events_db):
        """Running normalize twice should not create duplicates."""
        _add_event(
            central_events_db,
            "evt-001",
            "site-a",
            "2025-01-10T10:00:00",
            "UPDATE",
            "VIN011",
            _out_event_payload("VIN011", "site-a", "2025-01-10"),
        )

        _add_event(
            central_events_db,
            "evt-002",
            "site-b",
            "2025-01-11T15:00:00",
            "CREATE",
            "VIN011",
            _in_event_payload("VIN011", "2025-01-11"),
        )

        normalizer = TransferNormalizer(central_events_db)
        transfers1 = normalizer.normalize("2025-01-01", "2025-01-31")
        transfers2 = normalizer.normalize("2025-01-01", "2025-01-31")

        assert len(transfers1) == 1
        assert len(transfers2) == 1, "Second run should not create duplicates (idempotent)"


class TestPerformance:
    """Performance tests."""

    def test_performance_1k_events(self, central_events_db):
        """Normalize 1K events should complete in < 5 seconds."""
        import time

        # Create 500 transfer pairs (1K events total: 500 OUT + 500 IN)
        event_id = 0
        for pair in range(500):
            vin = f"VIN{pair:04d}"
            site_from = f"site-{pair % 5}"
            site_to = f"site-{(pair + 1) % 5}"
            
            # Ensure different site
            if site_to == site_from:
                site_to = f"site-{(pair + 2) % 5}"
            
            # OUT event
            out_date = f"2025-01-{(pair % 20) + 1:02d}"
            _add_event(
                central_events_db,
                f"evt-{event_id:04d}",
                site_from,
                f"{out_date}T{(pair % 24):02d}:00:00",
                "UPDATE",
                vin,
                _out_event_payload(vin, site_from, out_date),
            )
            event_id += 1
            
            # IN event (1-3 days later, always within 7-day window)
            in_days_delta = (pair % 3) + 1
            in_date_day = (pair % 20) + 1 + in_days_delta
            if in_date_day > 28:
                in_date_day = in_date_day - 28
            in_date = f"2025-01-{in_date_day:02d}"
            
            _add_event(
                central_events_db,
                f"evt-{event_id:04d}",
                site_to,
                f"{in_date}T{((pair + 12) % 24):02d}:00:00",
                "CREATE",
                vin,
                _in_event_payload(vin, in_date),
            )
            event_id += 1

        normalizer = TransferNormalizer(central_events_db)
        start = time.time()
        transfers = normalizer.normalize("2025-01-01", "2025-01-31")
        elapsed = time.time() - start

        assert elapsed < 5.0, f"Normalization took {elapsed:.2f}s, expected < 5s"
        assert len(transfers) > 450, f"Should find ~500 transfers, got {len(transfers)}"
