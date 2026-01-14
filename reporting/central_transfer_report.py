import csv
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional

import config


@dataclass
class TransferCandidate:
    vin: str
    from_site: str
    to_site: str
    out_at: str
    in_at: str
    out_event_uid: str
    in_event_uid: str


def _get_conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _parse_iso_dt(s: str) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def _load_payload(payload_json: Optional[str]) -> Dict[str, Any]:
    if not payload_json:
        return {}
    try:
        return json.loads(payload_json)
    except Exception:
        return {}


def _is_vehicle_in_event(action: str, payload: Dict[str, Any]) -> bool:
    if action != "CREATE":
        return False
    new_value = (payload or {}).get("new_value") or {}
    return new_value.get("status") == config.STATUS_IN_STOCK and bool(new_value.get("date_in"))


def _is_vehicle_out_event(action: str, payload: Dict[str, Any]) -> bool:
    if action != "UPDATE":
        return False
    new_value = (payload or {}).get("new_value") or {}
    return new_value.get("status") == config.STATUS_SHIPPED and bool(new_value.get("date_out"))


def find_transfer_candidates(
    central_events_db: str,
    period_from: str,
    period_to: str,
    *,
    max_days: int = 7,
) -> List[TransferCandidate]:
    """Heuristic: VIN shipped at site A then created at site B soon after.

    This is additive (does not change existing reporting). It helps HQ identify
    transfer-like movements to avoid double counting in business reports.
    """

    max_delta = timedelta(days=max_days)

    with _get_conn(central_events_db) as conn:
        rows = conn.execute(
            """
            SELECT event_uid, site_code, occurred_at, action, table_name, record_id, payload_json
            FROM central_events
            WHERE table_name = 'vehicles'
              AND record_id IS NOT NULL AND record_id != ''
              AND occurred_at >= ? AND occurred_at <= ?
            ORDER BY record_id ASC, occurred_at ASC
            """,
            (period_from, period_to),
        ).fetchall()

    by_vin: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        vin = (r["record_id"] or "").strip()
        if not vin:
            continue
        by_vin.setdefault(vin, []).append(dict(r))

    candidates: List[TransferCandidate] = []

    for vin, events in by_vin.items():
        # scan sequentially: OUT followed by IN at different site within threshold
        for i in range(len(events) - 1):
            e_out = events[i]
            payload_out = _load_payload(e_out.get("payload_json"))
            if not _is_vehicle_out_event(e_out.get("action") or "", payload_out):
                continue
            out_at = e_out.get("occurred_at") or ""
            out_dt = _parse_iso_dt(out_at)
            if out_dt is None:
                continue

            for j in range(i + 1, len(events)):
                e_in = events[j]
                if (e_in.get("site_code") or "") == (e_out.get("site_code") or ""):
                    continue
                payload_in = _load_payload(e_in.get("payload_json"))
                if not _is_vehicle_in_event(e_in.get("action") or "", payload_in):
                    continue

                in_at = e_in.get("occurred_at") or ""
                in_dt = _parse_iso_dt(in_at)
                if in_dt is None:
                    continue

                if in_dt < out_dt:
                    continue
                if in_dt - out_dt > max_delta:
                    continue

                candidates.append(
                    TransferCandidate(
                        vin=vin,
                        from_site=(e_out.get("site_code") or ""),
                        to_site=(e_in.get("site_code") or ""),
                        out_at=out_at,
                        in_at=in_at,
                        out_event_uid=e_out.get("event_uid") or "",
                        in_event_uid=e_in.get("event_uid") or "",
                    )
                )
                break

    return candidates


def export_transfer_candidates_csv(candidates: Iterable[TransferCandidate], out_path: str) -> str:
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "vin",
                "from_site",
                "to_site",
                "out_at",
                "in_at",
                "out_event_uid",
                "in_event_uid",
            ],
        )
        writer.writeheader()
        for c in candidates:
            writer.writerow(
                {
                    "vin": c.vin,
                    "from_site": c.from_site,
                    "to_site": c.to_site,
                    "out_at": c.out_at,
                    "in_at": c.in_at,
                    "out_event_uid": c.out_event_uid,
                    "in_event_uid": c.in_event_uid,
                }
            )
    return out_path
