import json
import os
import sqlite3
import hashlib
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import config

DateLike = Union[date, datetime]


def _as_datetime_start(d: DateLike) -> datetime:
    if isinstance(d, datetime):
        return d
    return datetime.combine(d, time.min)


def _as_datetime_end(d: DateLike) -> datetime:
    if isinstance(d, datetime):
        return d
    return datetime.combine(d, time.max)


def _json_load_maybe(value: Optional[str]) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if not isinstance(value, str):
        return value
    if not value:
        return None
    try:
        return json.loads(value)
    except Exception:
        return value


def _make_event_uid(site_instance_id: str, audit_id: int, created_at: str, action: str, table_name: str, record_id: str) -> str:
    payload = {
        "site_instance_id": site_instance_id,
        "audit_id": audit_id,
        "created_at": created_at,
        "action": action,
        "table_name": table_name,
        "record_id": record_id,
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    return f"evt_{digest}"


@dataclass
class SiteEventBundle:
    bundle_id: str
    site_code: str
    site_instance_id: str
    exported_at: str
    period_from: str
    period_to: str
    events: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": 1,
            "bundle_id": self.bundle_id,
            "site_code": self.site_code,
            "site_instance_id": self.site_instance_id,
            "exported_at": self.exported_at,
            "period": {"from": self.period_from, "to": self.period_to},
            "source": {"type": "audit_logs"},
            "events": self.events,
        }


def build_audit_event_bundle(
    start: DateLike,
    end: DateLike,
    *,
    site_code: str,
    site_instance_id: str,
    audit_db_path: Optional[str] = None,
) -> SiteEventBundle:
    db_path = audit_db_path or getattr(config, "AUDIT_DB_FILE", None) or config.DB_FILE

    start_dt = _as_datetime_start(start)
    end_dt = _as_datetime_end(end)

    start_iso = start_dt.isoformat()
    end_iso = end_dt.isoformat()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, user_id, username, action, table_name, record_id,
                   old_value, new_value, details, created_at
            FROM audit_logs
            WHERE created_at >= ? AND created_at <= ?
            ORDER BY created_at ASC, id ASC
            """,
            (start_iso, end_iso),
        )

        events: List[Dict[str, Any]] = []
        for r in cur.fetchall():
            audit_id = int(r["id"]) if r["id"] is not None else 0
            created_at = str(r["created_at"])
            action = str(r["action"] or "")
            table_name = str(r["table_name"] or "")
            record_id = str(r["record_id"] or "")

            event_uid = _make_event_uid(site_instance_id, audit_id, created_at, action, table_name, record_id)

            events.append(
                {
                    "event_uid": event_uid,
                    "event_source": "audit_logs",
                    "audit_id": audit_id,
                    "occurred_at": created_at,
                    "user_id": r["user_id"],
                    "username": r["username"],
                    "action": action,
                    "table_name": table_name,
                    "record_id": record_id,
                    "old_value": _json_load_maybe(r["old_value"]),
                    "new_value": _json_load_maybe(r["new_value"]),
                    "details": _json_load_maybe(r["details"]),
                }
            )

        return SiteEventBundle(
            bundle_id=str(uuid4()),
            site_code=site_code,
            site_instance_id=site_instance_id,
            exported_at=datetime.now().isoformat(),
            period_from=start_dt.date().isoformat(),
            period_to=end_dt.date().isoformat(),
            events=events,
        )
    finally:
        conn.close()


def save_event_bundle_json(bundle: SiteEventBundle, output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(bundle.to_dict(), f, ensure_ascii=False, indent=2)
    return output_path
