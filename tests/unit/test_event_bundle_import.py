import json

from reporting.central_event_store import CentralEventStore


def test_import_event_bundle_idempotent(tmp_path):
    db_path = tmp_path / "central_events.db"
    store = CentralEventStore(str(db_path))

    bundle = {
        "schema_version": 1,
        "bundle_id": "bundle_1",
        "site_code": "SITE_A",
        "site_instance_id": "instance_a",
        "exported_at": "2025-01-01T00:00:00",
        "period": {"from": "2025-01-01", "to": "2025-01-02"},
        "source": {"type": "audit_logs"},
        "events": [
            {
                "event_uid": "evt_1",
                "event_source": "audit_logs",
                "audit_id": 1,
                "occurred_at": "2025-01-01T08:00:00",
                "user_id": 1,
                "username": "admin",
                "action": "CREATE",
                "table_name": "vehicles",
                "record_id": "VIN001",
                "old_value": None,
                "new_value": {"status": "IN_STOCK", "date_in": "2025-01-01T08:00:00"},
                "details": None,
            },
            {
                "event_uid": "evt_2",
                "event_source": "audit_logs",
                "audit_id": 2,
                "occurred_at": "2025-01-02T09:00:00",
                "user_id": 1,
                "username": "admin",
                "action": "UPDATE",
                "table_name": "vehicles",
                "record_id": "VIN001",
                "old_value": None,
                "new_value": {"status": "SHIPPED", "date_out": "2025-01-02T09:00:00"},
                "details": None,
            },
        ],
    }

    r1 = store.import_event_bundle(bundle)
    assert r1.success is True
    assert r1.inserted == 2

    r2 = store.import_event_bundle(bundle)
    assert r2.success is True
    assert r2.inserted == 0


def test_import_event_bundle_file(tmp_path):
    db_path = tmp_path / "central_events.db"
    store = CentralEventStore(str(db_path))

    bundle_path = tmp_path / "events.json"
    bundle_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "bundle_id": "bundle_2",
                "site_code": "SITE_B",
                "site_instance_id": "instance_b",
                "exported_at": "2025-01-01T00:00:00",
                "period": {"from": "2025-01-01", "to": "2025-01-01"},
                "source": {"type": "audit_logs"},
                "events": [
                    {
                        "event_uid": "evt_3",
                        "event_source": "audit_logs",
                        "audit_id": 3,
                        "occurred_at": "2025-01-01T10:00:00",
                        "user_id": 1,
                        "username": "admin",
                        "action": "CREATE",
                        "table_name": "vehicles",
                        "record_id": "VIN002",
                        "old_value": None,
                        "new_value": {"status": "IN_STOCK", "date_in": "2025-01-01T10:00:00"},
                        "details": None,
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    r = store.import_event_bundle_file(str(bundle_path))
    assert r.success is True
    assert r.inserted == 1
