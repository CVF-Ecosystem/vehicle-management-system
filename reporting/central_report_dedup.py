"""
HQ Report with Deduplication Support (Phase 3.2)

Generates enhanced central reports with optional deduplication of inter-site transfers.
Maintains backward compatibility with existing snapshot reports.
"""

import csv
import sqlite3
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import config


@dataclass
class VehicleMovement:
    """Vehicle movement record."""

    vin: str
    date_in: Optional[str]
    date_out: Optional[str]
    site_code: str
    owner: Optional[str]
    vehicle_type: Optional[str]
    status: str
    transfer_status: str = "normal"  # "normal" | "internal_transfer_out" | "internal_transfer_in"


@dataclass
class TransferSummaryRow:
    """Summary row for transfer reconciliation."""

    vin: str
    from_site: str
    to_site: str
    out_date: str
    in_date: str
    transfer_days: float
    reconcile_status: str = "reconciled"


class CentralReportGenerator:
    """Generate HQ reports with optional deduplication."""

    def __init__(self, central_db: str, security_db: str, enable_dedup: bool = True):
        """
        Args:
            central_db: central_report.db path
            security_db: security.db path (for user info)
            enable_dedup: Enable deduplication of transfers
        """
        self.central_db = central_db
        self.security_db = security_db
        self.enable_dedup = enable_dedup

    def _get_conn(self, db_path: str) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _load_transfers(self, period_from: str, period_to: str) -> Dict[str, Tuple[str, str]]:
        """Load TRANSFER events for period. Returns {vin: (out_site, in_site)}."""
        transfers = {}

        with self._get_conn(self.central_db) as conn:
            rows = conn.execute(
                """
                SELECT record_id, payload_json FROM central_events
                WHERE action = 'TRANSFER_DETECTED'
                  AND table_name = 'vehicles'
                  AND occurred_at >= ? AND occurred_at <= ?
                """,
                (period_from, period_to),
            ).fetchall()

        for row in rows:
            vin = row["record_id"]
            try:
                payload = json.loads(row["payload_json"] or "{}")
                from_site = payload.get("from_site", "")
                to_site = payload.get("to_site", "")
                if from_site and to_site:
                    transfers[vin] = (from_site, to_site)
            except Exception:
                pass

        return transfers

    def get_vehicles(self, period_from: str, period_to: str) -> List[VehicleMovement]:
        """Get all vehicles with movement info for period."""
        transfers = self._load_transfers(period_from, period_to) if self.enable_dedup else {}

        vehicles = []
        with self._get_conn(self.central_db) as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT
                    vin, owner, vehicle_type, latest_site,
                    last_date_in, last_date_out, last_status
                FROM vehicles
                ORDER BY vin
                """
            ).fetchall()

        for row in rows:
            vin = row["vin"]
            date_in = row["last_date_in"]
            date_out = row["last_date_out"]
            site = row["latest_site"]
            owner = row["owner"]
            vehicle_type = row["vehicle_type"]
            status = row["last_status"] or config.STATUS_IN_STOCK

            # Determine transfer status
            transfer_status = "normal"
            if vin in transfers:
                from_site, to_site = transfers[vin]
                if site == from_site:
                    transfer_status = "internal_transfer_out"
                elif site == to_site:
                    transfer_status = "internal_transfer_in"

            vehicles.append(
                VehicleMovement(
                    vin=vin,
                    date_in=date_in,
                    date_out=date_out,
                    site_code=site,
                    owner=owner,
                    vehicle_type=vehicle_type,
                    status=status,
                    transfer_status=transfer_status,
                )
            )

        return vehicles

    def get_site_summary(
        self, period_from: str, period_to: str
    ) -> Dict[str, Dict[str, int]]:
        """
        Get summary by site.

        Returns:
        {
          'site_a': {
            'imported': 10,
            'exported': 8,
            'ending_stock': 45,
            'transfers_in': 3,    # New transfers in (when dedup enabled)
            'transfers_out': 2    # New transfers out (when dedup enabled)
          },
          ...
        }
        """
        vehicles = self.get_vehicles(period_from, period_to)
        transfers = self._load_transfers(period_from, period_to) if self.enable_dedup else {}

        summary: Dict[str, Dict[str, int]] = {}

        for vehicle in vehicles:
            site = vehicle.site_code
            if site not in summary:
                summary[site] = {
                    "imported": 0,
                    "exported": 0,
                    "ending_stock": 0,
                    "transfers_in": 0,
                    "transfers_out": 0,
                    "internal_transfer_in": 0,
                    "internal_transfer_out": 0,
                }

            summary[site]["ending_stock"] += 1

            # Count movements based on transfer status
            if vehicle.date_in:
                if vehicle.transfer_status == "internal_transfer_in":
                    summary[site]["transfers_in"] += 1
                    summary[site]["internal_transfer_in"] += 1
                else:
                    summary[site]["imported"] += 1

            if vehicle.date_out:
                if vehicle.transfer_status == "internal_transfer_out":
                    summary[site]["transfers_out"] += 1
                    summary[site]["internal_transfer_out"] += 1
                else:
                    summary[site]["exported"] += 1

        return summary

    def export_vehicle_movement_csv(
        self, period_from: str, period_to: str, out_path: str
    ) -> str:
        """Export detailed vehicle movement report (with transfer status)."""
        vehicles = self.get_vehicles(period_from, period_to)

        with open(out_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "vin",
                "owner",
                "vehicle_type",
                "site_code",
                "status",
                "date_in",
                "date_out",
                "transfer_status",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for v in vehicles:
                writer.writerow(asdict(v))

        return out_path

    def export_site_summary_csv(
        self, period_from: str, period_to: str, out_path: str
    ) -> str:
        """Export site summary with dedup info."""
        summary = self.get_site_summary(period_from, period_to)

        with open(out_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "site_code",
                "imported",
                "exported",
                "transfers_in",
                "transfers_out",
                "internal_transfer_in",
                "internal_transfer_out",
                "ending_stock",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for site_code in sorted(summary.keys()):
                row = {"site_code": site_code, **summary[site_code]}
                writer.writerow(row)

        return out_path

    def export_transfer_summary_csv(
        self, period_from: str, period_to: str, out_path: str
    ) -> str:
        """Export transfer reconciliation summary."""
        transfers = self._load_transfers(period_from, period_to)

        # Load transfer details from central_events
        transfer_details = []
        with self._get_conn(self.central_db) as conn:
            rows = conn.execute(
                """
                SELECT record_id, payload_json, occurred_at FROM central_events
                WHERE action = 'TRANSFER_DETECTED'
                  AND table_name = 'vehicles'
                  AND occurred_at >= ? AND occurred_at <= ?
                ORDER BY record_id
                """,
                (period_from, period_to),
            ).fetchall()

        for row in rows:
            vin = row["record_id"]
            try:
                payload = json.loads(row["payload_json"] or "{}")
                summary_row = TransferSummaryRow(
                    vin=vin,
                    from_site=payload.get("from_site", ""),
                    to_site=payload.get("to_site", ""),
                    out_date=payload.get("out_at", "").split("T")[0],
                    in_date=payload.get("in_at", "").split("T")[0],
                    transfer_days=payload.get("transfer_duration_days", 0),
                    reconcile_status="reconciled",
                )
                transfer_details.append(summary_row)
            except Exception:
                pass

        # Export
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "vin",
                "from_site",
                "to_site",
                "out_date",
                "in_date",
                "transfer_days",
                "reconcile_status",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for row in transfer_details:
                writer.writerow(asdict(row))

        return out_path

    def export_consolidated_report(
        self, period_from: str, period_to: str, out_dir: str
    ) -> Dict[str, str]:
        """
        Generate all reports together.

        Returns: dict of {report_type: file_path}
        """
        import os

        os.makedirs(out_dir, exist_ok=True)

        reports = {}

        # 1. Vehicle movement report
        movement_path = os.path.join(
            out_dir, f"vehicles_movement_{period_from}_{period_to}.csv"
        )
        self.export_vehicle_movement_csv(period_from, period_to, movement_path)
        reports["vehicle_movement"] = movement_path

        # 2. Site summary report
        summary_path = os.path.join(out_dir, f"sites_summary_{period_from}_{period_to}.csv")
        self.export_site_summary_csv(period_from, period_to, summary_path)
        reports["site_summary"] = summary_path

        # 3. Transfer summary report (only if transfers exist)
        transfers = self._load_transfers(period_from, period_to)
        if transfers:
            transfer_path = os.path.join(
                out_dir, f"transfers_reconciled_{period_from}_{period_to}.csv"
            )
            self.export_transfer_summary_csv(period_from, period_to, transfer_path)
            reports["transfer_summary"] = transfer_path

        return reports
