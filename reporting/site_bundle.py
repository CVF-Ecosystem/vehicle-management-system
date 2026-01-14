import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

import config

DateLike = Union[datetime, date]


def _to_iso_date(d: DateLike) -> str:
    # Keep consistent with existing code: dates are compared as ISO strings in SQLite.
    if isinstance(d, datetime):
        return d.date().isoformat()
    return d.isoformat()


def get_site_code(app_config) -> str:
    """Get site_code from config.ini (loaded via utils.load_config())."""
    try:
        code = app_config.get("Site", "site_code", fallback="SITE_001").strip()
        return code or "SITE_001"
    except Exception:
        return "SITE_001"


@dataclass
class SiteBundle:
    bundle_id: str
    site_code: str
    exported_at: str
    period_from: str
    period_to: str
    summary_overall: Dict[str, int]
    summary_by_owner: List[Dict[str, Any]]
    vehicles_in: List[Dict[str, Any]]
    vehicles_out: List[Dict[str, Any]]
    stock_snapshot: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": 1,
            "bundle_id": self.bundle_id,
            "site_code": self.site_code,
            "exported_at": self.exported_at,
            "period": {"from": self.period_from, "to": self.period_to},
            "summary_overall": self.summary_overall,
            "summary_by_owner": self.summary_by_owner,
            "vehicles_in": self.vehicles_in,
            "vehicles_out": self.vehicles_out,
            "stock_snapshot": self.stock_snapshot,
        }


def build_site_bundle(
    vehicle_manager,
    start_date: DateLike,
    end_date: DateLike,
    site_code: str,
) -> SiteBundle:
    """Build an export bundle for a single site.

    The bundle is designed to be merged centrally (idempotent by bundle_id).
    """
    period_from = _to_iso_date(start_date)
    period_to = _to_iso_date(end_date)

    conn = vehicle_manager.conn
    if not isinstance(conn, sqlite3.Connection):
        raise RuntimeError("vehicle_manager.conn is not a sqlite3.Connection")

    cur = conn.cursor()

    # Overall summary (site-level)
    cur.execute(
        """
        SELECT
            (SELECT COUNT(vin) FROM vehicles WHERE is_active = 1 AND date_in BETWEEN ? AND ?) AS total_in,
            (SELECT COUNT(vin) FROM vehicles WHERE is_active = 1 AND date_out BETWEEN ? AND ?) AS total_out,
            (SELECT COUNT(vin) FROM vehicles WHERE is_active = 1 AND date_in <= ? AND (date_out IS NULL OR date_out > ?)) AS stock
        """,
        (period_from, period_to, period_from, period_to, period_to, period_to),
    )
    row = cur.fetchone()
    summary_overall = {
        "total_in": int(row[0] or 0),
        "total_out": int(row[1] or 0),
        "stock": int(row[2] or 0),
    }

    # Owner summary uses existing method (keeps business logic consistent)
    summary_by_owner = vehicle_manager.get_summary_report_data(start_date, end_date)

    # Vehicles IN during period
    cur.execute(
        """
        SELECT vin, owner, vehicle_type, date_in
        FROM vehicles
        WHERE is_active = 1 AND date_in BETWEEN ? AND ?
        ORDER BY date_in ASC
        """,
        (period_from, period_to),
    )
    vehicles_in = [dict(r) for r in cur.fetchall()]

    # Vehicles OUT during period
    cur.execute(
        """
        SELECT vin, owner, vehicle_type, date_out
        FROM vehicles
        WHERE is_active = 1 AND date_out BETWEEN ? AND ?
        ORDER BY date_out ASC
        """,
        (period_from, period_to),
    )
    vehicles_out = [dict(r) for r in cur.fetchall()]

    # Stock snapshot at export time
    cur.execute(
        """
        SELECT v.vin, v.owner, v.vehicle_type, v.date_in,
               l.full_location_name, l.block
        FROM vehicles v
        LEFT JOIN locations l ON v.location_id = l.id
        WHERE v.is_active = 1 AND v.status = ?
        ORDER BY v.date_in DESC
        """,
        (config.STATUS_IN_STOCK,),
    )
    stock_snapshot = []
    for r in cur.fetchall():
        d = dict(r)
        stock_snapshot.append(
            {
                "vin": d.get("vin"),
                "owner": d.get("owner"),
                "vehicle_type": d.get("vehicle_type"),
                "date_in": d.get("date_in"),
                "full_location_name": d.get("full_location_name") or "",
                "block": d.get("block") or "",
            }
        )

    return SiteBundle(
        bundle_id=str(uuid4()),
        site_code=site_code,
        exported_at=datetime.now().isoformat(),
        period_from=period_from,
        period_to=period_to,
        summary_overall=summary_overall,
        summary_by_owner=summary_by_owner,
        vehicles_in=vehicles_in,
        vehicles_out=vehicles_out,
        stock_snapshot=stock_snapshot,
    )


def save_bundle_json(bundle: SiteBundle, output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(bundle.to_dict(), f, ensure_ascii=False, indent=2)
    return output_path
