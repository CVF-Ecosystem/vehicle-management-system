import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class ImportResult:
    success: bool
    message: str
    bundle_id: Optional[str] = None
    inserted: int = 0


class CentralStore:
    """Central SQLite store for merged multi-site bundles."""

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
                CREATE TABLE IF NOT EXISTS central_bundles (
                    bundle_id TEXT PRIMARY KEY,
                    site_code TEXT NOT NULL,
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
                CREATE INDEX IF NOT EXISTS idx_central_bundles_period
                ON central_bundles(period_from, period_to)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_central_bundles_site
                ON central_bundles(site_code)
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS central_summary_overall (
                    bundle_id TEXT NOT NULL,
                    total_in INTEGER NOT NULL,
                    total_out INTEGER NOT NULL,
                    stock INTEGER NOT NULL,
                    FOREIGN KEY(bundle_id) REFERENCES central_bundles(bundle_id)
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS central_summary_owner (
                    bundle_id TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    total_in INTEGER NOT NULL,
                    total_out INTEGER NOT NULL,
                    stock INTEGER NOT NULL,
                    FOREIGN KEY(bundle_id) REFERENCES central_bundles(bundle_id)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_central_owner_owner
                ON central_summary_owner(owner)
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS central_vehicles_in (
                    bundle_id TEXT NOT NULL,
                    vin TEXT NOT NULL,
                    owner TEXT,
                    vehicle_type TEXT,
                    date_in TEXT,
                    FOREIGN KEY(bundle_id) REFERENCES central_bundles(bundle_id)
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS central_vehicles_out (
                    bundle_id TEXT NOT NULL,
                    vin TEXT NOT NULL,
                    owner TEXT,
                    vehicle_type TEXT,
                    date_out TEXT,
                    FOREIGN KEY(bundle_id) REFERENCES central_bundles(bundle_id)
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS central_stock_snapshot (
                    bundle_id TEXT NOT NULL,
                    vin TEXT NOT NULL,
                    owner TEXT,
                    vehicle_type TEXT,
                    date_in TEXT,
                    full_location_name TEXT,
                    block TEXT,
                    FOREIGN KEY(bundle_id) REFERENCES central_bundles(bundle_id)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_central_stock_vin
                ON central_stock_snapshot(vin)
                """
            )

            conn.commit()

    def import_bundle_file(self, json_path: str) -> ImportResult:
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                bundle = json.load(f)
        except Exception as e:
            return ImportResult(False, f"Không đọc được file bundle: {e}")

        return self.import_bundle(bundle, source_file=os.path.basename(json_path))

    def import_bundle(self, bundle: Dict[str, Any], source_file: Optional[str] = None) -> ImportResult:
        try:
            schema_version = bundle.get("schema_version")
            if schema_version != 1:
                return ImportResult(False, f"schema_version không hỗ trợ: {schema_version}")

            bundle_id = bundle.get("bundle_id")
            site_code = bundle.get("site_code")
            exported_at = bundle.get("exported_at")
            period = bundle.get("period") or {}
            period_from = period.get("from")
            period_to = period.get("to")

            if not bundle_id or not site_code or not exported_at or not period_from or not period_to:
                return ImportResult(False, "Bundle thiếu thông tin bắt buộc (bundle_id/site_code/exported_at/period)")

            imported_at = datetime.now().isoformat()

            with self._get_conn() as conn:
                # Idempotency: skip if bundle_id already imported
                existing = conn.execute(
                    "SELECT bundle_id FROM central_bundles WHERE bundle_id = ?",
                    (bundle_id,),
                ).fetchone()
                if existing:
                    return ImportResult(True, "Bundle đã được import trước đó (skip)", bundle_id=bundle_id, inserted=0)

                conn.execute(
                    """
                    INSERT INTO central_bundles (bundle_id, site_code, exported_at, period_from, period_to, imported_at, source_file)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (bundle_id, site_code, exported_at, period_from, period_to, imported_at, source_file),
                )

                overall = bundle.get("summary_overall") or {}
                conn.execute(
                    """
                    INSERT INTO central_summary_overall (bundle_id, total_in, total_out, stock)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        bundle_id,
                        int(overall.get("total_in") or 0),
                        int(overall.get("total_out") or 0),
                        int(overall.get("stock") or 0),
                    ),
                )

                owner_rows = bundle.get("summary_by_owner") or []
                for r in owner_rows:
                    conn.execute(
                        """
                        INSERT INTO central_summary_owner (bundle_id, owner, total_in, total_out, stock)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            bundle_id,
                            str(r.get("owner") or "").strip(),
                            int(r.get("total_in") or 0),
                            int(r.get("total_out") or 0),
                            int(r.get("stock") or 0),
                        ),
                    )

                in_rows = bundle.get("vehicles_in") or []
                for r in in_rows:
                    conn.execute(
                        """
                        INSERT INTO central_vehicles_in (bundle_id, vin, owner, vehicle_type, date_in)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            bundle_id,
                            str(r.get("vin") or "").strip(),
                            r.get("owner"),
                            r.get("vehicle_type"),
                            r.get("date_in"),
                        ),
                    )

                out_rows = bundle.get("vehicles_out") or []
                for r in out_rows:
                    conn.execute(
                        """
                        INSERT INTO central_vehicles_out (bundle_id, vin, owner, vehicle_type, date_out)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            bundle_id,
                            str(r.get("vin") or "").strip(),
                            r.get("owner"),
                            r.get("vehicle_type"),
                            r.get("date_out"),
                        ),
                    )

                stock_rows = bundle.get("stock_snapshot") or []
                for r in stock_rows:
                    conn.execute(
                        """
                        INSERT INTO central_stock_snapshot
                        (bundle_id, vin, owner, vehicle_type, date_in, full_location_name, block)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            bundle_id,
                            str(r.get("vin") or "").strip(),
                            r.get("owner"),
                            r.get("vehicle_type"),
                            r.get("date_in"),
                            r.get("full_location_name"),
                            r.get("block"),
                        ),
                    )

                conn.commit()

            inserted = 1
            return ImportResult(True, "Import bundle thành công", bundle_id=bundle_id, inserted=inserted)

        except Exception as e:
            return ImportResult(False, f"Lỗi import bundle: {e}")
