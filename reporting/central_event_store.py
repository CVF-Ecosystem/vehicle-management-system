import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class ImportResult:
    success: bool
    message: str
    bundle_id: Optional[str] = None
    inserted: int = 0


class CentralEventStore:
    """Central SQLite store for merged multi-site event bundles (append-only)."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._ensure_schema()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS central_event_bundles (
                    bundle_id TEXT PRIMARY KEY,
                    site_code TEXT NOT NULL,
                    site_instance_id TEXT NOT NULL,
                    exported_at TEXT NOT NULL,
                    period_from TEXT NOT NULL,
                    period_to TEXT NOT NULL,
                    imported_at TEXT NOT NULL,
                    source_file TEXT
                )
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_central_event_bundles_period
                ON central_event_bundles(period_from, period_to)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_central_event_bundles_site
                ON central_event_bundles(site_code)
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS central_events (
                    event_uid TEXT PRIMARY KEY,
                    site_code TEXT NOT NULL,
                    site_instance_id TEXT NOT NULL,
                    bundle_id TEXT NOT NULL,
                    event_source TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    action TEXT,
                    table_name TEXT,
                    record_id TEXT,
                    username TEXT,
                    user_id INTEGER,
                    payload_json TEXT,
                    FOREIGN KEY(bundle_id) REFERENCES central_event_bundles(bundle_id)
                )
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_central_events_occurred
                ON central_events(occurred_at)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_central_events_site
                ON central_events(site_code, occurred_at)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_central_events_record
                ON central_events(table_name, record_id)
                """
            )

    def import_event_bundle_file(self, file_path: str) -> ImportResult:
        with open(file_path, "r", encoding="utf-8") as f:
            bundle = json.load(f)
        return self.import_event_bundle(bundle, source_file=file_path)

    def import_event_bundle(self, bundle: Dict[str, Any], source_file: Optional[str] = None) -> ImportResult:
        try:
            schema_version = int(bundle.get("schema_version") or 0)
            if schema_version != 1:
                return ImportResult(False, f"Unsupported schema_version={schema_version}")

            bundle_id = bundle.get("bundle_id")
            site_code = bundle.get("site_code")
            site_instance_id = bundle.get("site_instance_id")
            exported_at = bundle.get("exported_at")
            period = bundle.get("period") or {}
            period_from = period.get("from")
            period_to = period.get("to")
            events = bundle.get("events") or []

            if not bundle_id or not site_code or not site_instance_id or not exported_at or not period_from or not period_to:
                return ImportResult(False, "Bundle thiếu thông tin bắt buộc")

            imported_at = datetime.now().isoformat()
            inserted = 0

            with self._get_conn() as conn:
                # Bundle idempotency
                cur = conn.cursor()
                cur.execute("SELECT bundle_id FROM central_event_bundles WHERE bundle_id = ?", (bundle_id,))
                exists = cur.fetchone() is not None
                if not exists:
                    conn.execute(
                        """
                        INSERT INTO central_event_bundles (bundle_id, site_code, site_instance_id, exported_at, period_from, period_to, imported_at, source_file)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (bundle_id, site_code, site_instance_id, exported_at, period_from, period_to, imported_at, source_file),
                    )

                for ev in events:
                    event_uid = ev.get("event_uid")
                    if not event_uid:
                        continue

                    payload = {
                        "event_source": ev.get("event_source"),
                        "audit_id": ev.get("audit_id"),
                        "old_value": ev.get("old_value"),
                        "new_value": ev.get("new_value"),
                        "details": ev.get("details"),
                    }

                    cur.execute(
                        """
                        INSERT OR IGNORE INTO central_events (
                            event_uid, site_code, site_instance_id, bundle_id,
                            event_source, occurred_at, action, table_name, record_id,
                            username, user_id, payload_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            event_uid,
                            site_code,
                            site_instance_id,
                            bundle_id,
                            ev.get("event_source") or "audit_logs",
                            ev.get("occurred_at") or "",
                            ev.get("action"),
                            ev.get("table_name"),
                            ev.get("record_id"),
                            ev.get("username"),
                            ev.get("user_id"),
                            json.dumps(payload, ensure_ascii=False),
                        ),
                    )
                    if cur.rowcount > 0:
                        inserted += 1

            return ImportResult(True, "Import event bundle thành công", bundle_id=bundle_id, inserted=inserted)
        except Exception as e:
            return ImportResult(False, f"Import failed: {e}")
