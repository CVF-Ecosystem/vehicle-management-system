"""
Transfer Event Normalization (Phase 3.1)

Detects OUT↔IN vehicle movement events and creates normalized TRANSFER events
to support deduplication in HQ reporting without affecting snapshot bundles.

Matching Rules:
1. OUT: status changes to SHIPPED (has date_out)
2. IN: status = IN_STOCK at different site (has date_in)
3. Time Window: IN within [OUT_time, OUT_time + max_days]
4. Conflict Resolution:
   - Multiple IN: pick earliest
   - Multiple OUT: pick latest (before IN)
5. Chain Transfers: A→B→C supported
6. Idempotent: Re-running doesn't create duplicates
"""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import config


@dataclass
class TransferEvent:
    """Normalized TRANSFER event."""

    vin: str
    from_site: str
    to_site: str
    out_at: str  # ISO datetime
    in_at: str  # ISO datetime
    out_event_uid: str
    in_event_uid: str
    transfer_status: str = "detected"  # "detected" or "confirmed"
    transfer_duration_days: float = 0.0


class TransferNormalizer:
    """Detects and normalizes OUT↔IN events into TRANSFER events."""

    def __init__(self, central_events_db: str, max_days: int = 7):
        """
        Args:
            central_events_db: Path to central_events.db
            max_days: Maximum days between OUT and IN to consider a transfer
        """
        self.db_path = central_events_db
        self.max_days = max_days

    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _is_out_event(self, action: str, payload: Dict[str, Any]) -> bool:
        """Check if event represents a vehicle OUT (SHIPPED)."""
        if action != "UPDATE":
            return False

        new_value = (payload or {}).get("new_value") or {}
        return new_value.get("status") == config.STATUS_SHIPPED and bool(
            new_value.get("date_out")
        )

    def _is_in_event(self, action: str, payload: Dict[str, Any]) -> bool:
        """Check if event represents a vehicle IN (IN_STOCK)."""
        if action != "CREATE":
            return False

        new_value = (payload or {}).get("new_value") or {}
        return new_value.get("status") == config.STATUS_IN_STOCK and bool(
            new_value.get("date_in")
        )

    def _load_payload(self, payload_json: Optional[str]) -> Dict[str, Any]:
        """Parse payload JSON."""
        if not payload_json:
            return {}
        try:
            return json.loads(payload_json)
        except Exception:
            return {}

    def _parse_iso_dt(self, s: str) -> Optional[datetime]:
        """Parse ISO datetime string."""
        if not s:
            return None
        try:
            return datetime.fromisoformat(s)
        except Exception:
            return None

    def _transfer_duration_days(self, out_at: str, in_at: str) -> float:
        """Calculate transfer duration in days."""
        out_dt = self._parse_iso_dt(out_at)
        in_dt = self._parse_iso_dt(in_at)

        if not out_dt or not in_dt:
            return 0.0

        delta = in_dt - out_dt
        return delta.total_seconds() / (24 * 3600)

    def normalize(
        self, period_from: str, period_to: str
    ) -> List[TransferEvent]:
        """
        Scan central_events for OUT↔IN pairs and return matched transfers.

        Args:
            period_from: Start date (YYYY-MM-DD)
            period_to: End date (YYYY-MM-DD)

        Returns:
            List of detected TRANSFER events
        """
        max_delta = timedelta(days=self.max_days)

        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT event_uid, site_code, occurred_at, action, table_name,
                       record_id, payload_json
                FROM central_events
                WHERE table_name = 'vehicles'
                  AND record_id IS NOT NULL AND record_id != ''
                  AND occurred_at >= ? AND occurred_at <= ?
                ORDER BY record_id ASC, occurred_at ASC
                """,
                (period_from, period_to),
            ).fetchall()

        # Group events by VIN
        by_vin: Dict[str, List[Dict[str, Any]]] = {}
        for r in rows:
            vin = (r["record_id"] or "").strip()
            if not vin:
                continue

            by_vin.setdefault(vin, []).append(dict(r))

        transfers: List[TransferEvent] = []

        # For each VIN, find OUT→IN pairs using a sophisticated matching algorithm:
        # - Avoid one OUT matching multiple INs
        # - Avoid one IN matching multiple OUTs
        # - For single OUT + multiple IN: pick earliest IN (closest in time)
        # - For single IN + multiple OUT: pick latest OUT (closest in time)
        for vin, events in by_vin.items():
            used_out_indices: set = set()  # Track which OUT events have been used
            used_in_indices: set = set()   # Track which IN events have been used
            
            # First pass: collect all OUT→IN candidate pairs
            candidates: List[tuple] = []  # (out_idx, in_idx, out_dt, in_dt, time_diff)
            
            for i in range(len(events)):
                e_out = events[i]
                payload_out = self._load_payload(e_out.get("payload_json"))

                if not self._is_out_event(e_out.get("action") or "", payload_out):
                    continue

                out_at = e_out.get("occurred_at") or ""
                out_dt = self._parse_iso_dt(out_at)
                if out_dt is None:
                    continue

                out_site = e_out.get("site_code") or ""

                # Find all valid IN candidates for this OUT
                for j in range(i + 1, len(events)):
                    e_in = events[j]
                    in_site = e_in.get("site_code") or ""

                    # IN must be at different site
                    if in_site == out_site:
                        continue

                    payload_in = self._load_payload(e_in.get("payload_json"))
                    if not self._is_in_event(e_in.get("action") or "", payload_in):
                        continue

                    in_at = e_in.get("occurred_at") or ""
                    in_dt = self._parse_iso_dt(in_at)
                    if in_dt is None:
                        continue

                    # Time constraints
                    if in_dt < out_dt:
                        continue
                    if in_dt - out_dt > max_delta:
                        continue

                    # Valid candidate - store with time difference for sorting
                    time_diff = (in_dt - out_dt).total_seconds()
                    candidates.append((i, j, out_dt, in_dt, time_diff))

            # Second pass: resolve conflicts greedily
            # Sort by: time_diff (shortest transfer) to prioritize best matches
            candidates_sorted = sorted(candidates, key=lambda x: x[4])
            
            for out_idx, in_idx, out_dt, in_dt, time_diff in candidates_sorted:
                # Skip if either OUT or IN already used
                if out_idx in used_out_indices or in_idx in used_in_indices:
                    continue
                
                e_out = events[out_idx]
                e_in = events[in_idx]
                
                out_at = e_out.get("occurred_at") or ""
                in_at = e_in.get("occurred_at") or ""
                out_site = e_out.get("site_code") or ""
                in_site = e_in.get("site_code") or ""

                transfer = TransferEvent(
                    vin=vin,
                    from_site=out_site,
                    to_site=in_site,
                    out_at=out_at,
                    in_at=in_at,
                    out_event_uid=e_out.get("event_uid") or "",
                    in_event_uid=e_in.get("event_uid") or "",
                    transfer_status="detected",
                    transfer_duration_days=self._transfer_duration_days(
                        out_at, in_at
                    ),
                )
                transfers.append(transfer)
                used_out_indices.add(out_idx)
                used_in_indices.add(in_idx)

        return transfers

    def save_transfers_to_db(
        self, transfers: List[TransferEvent], period_from: str, period_to: str
    ) -> int:
        """
        Save normalized TRANSFER events to central_events table (idempotent).

        Args:
            transfers: List of detected transfers
            period_from: Period start (for tracking)
            period_to: Period end (for tracking)

        Returns:
            Number of new TRANSFER events inserted
        """
        if not transfers:
            return 0

        with self._get_conn() as conn:
            inserted = 0

            for t in transfers:
                # Check if this transfer already exists (idempotent)
                existing = conn.execute(
                    """
                    SELECT 1 FROM central_events
                    WHERE action = 'TRANSFER_DETECTED'
                      AND record_id = ?
                      AND payload_json LIKE ?
                    LIMIT 1
                    """,
                    (
                        t.vin,
                        f'%"out_event_uid": "{t.out_event_uid}"%',
                    ),
                ).fetchone()

                if existing:
                    continue  # Already exists, skip

                # Create TRANSFER event
                payload = {
                    "vin": t.vin,
                    "from_site": t.from_site,
                    "to_site": t.to_site,
                    "out_at": t.out_at,
                    "in_at": t.in_at,
                    "out_event_uid": t.out_event_uid,
                    "in_event_uid": t.in_event_uid,
                    "transfer_duration_days": t.transfer_duration_days,
                    "transfer_status": t.transfer_status,
                    "notes": "Auto-normalized TRANSFER event",
                }

                event_uid = f"transfer-{t.vin}-{t.out_at.replace(':', '')}-{t.in_at.replace(':', '')}"

                conn.execute(
                    """
                    INSERT INTO central_events
                    (event_uid, site_code, site_instance_id, bundle_id, event_source,
                     occurred_at, action, table_name, record_id, payload_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_uid,
                        "HQ",  # TRANSFER events marked as HQ-generated
                        "hq-001",
                        "transfer-normalization",
                        "transfer_normalizer",
                        t.out_at,  # Use OUT timestamp as reference
                        "TRANSFER_DETECTED",
                        "vehicles",
                        t.vin,
                        json.dumps(payload),
                    ),
                )
                inserted += 1

            conn.commit()

        return inserted
