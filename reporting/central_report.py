import sqlite3
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class CentralPeriodReport:
    period_from: str
    period_to: str
    bundles_count: int

    overall_total_in: int
    overall_total_out: int
    overall_stock_end: int

    per_site_rows: List[Dict]
    per_owner_rows: List[Dict]


def _get_conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _select_bundle_rows(conn: sqlite3.Connection, period_from: str, period_to: str):
    return conn.execute(
        """
        SELECT bundle_id, site_code, exported_at, period_from, period_to
        FROM central_bundles
        WHERE period_from >= ? AND period_to <= ?
        ORDER BY site_code ASC, period_to ASC, exported_at ASC
        """,
        (period_from, period_to),
    ).fetchall()


def build_central_period_report(db_path: str, period_from: str, period_to: str) -> CentralPeriodReport:
    with _get_conn(db_path) as conn:
        bundle_rows = _select_bundle_rows(conn, period_from, period_to)
        if not bundle_rows:
            raise ValueError("Không có bundle nào trong khoảng thời gian đã chọn")

        bundle_ids = [r["bundle_id"] for r in bundle_rows]

        # Totals by site for movements during period (sum across bundles in range)
        per_site_totals = conn.execute(
            f"""
            SELECT b.site_code AS site_code,
                   SUM(o.total_in) AS total_in,
                   SUM(o.total_out) AS total_out,
                   COUNT(1) AS bundles_count
            FROM central_bundles b
            JOIN central_summary_overall o ON o.bundle_id = b.bundle_id
            WHERE b.bundle_id IN ({','.join(['?'] * len(bundle_ids))})
            GROUP BY b.site_code
            ORDER BY b.site_code ASC
            """,
            bundle_ids,
        ).fetchall()

        # Latest bundle per site (for stock_end)
        latest_bundle_by_site: Dict[str, str] = {}
        last_period_to_by_site: Dict[str, str] = {}
        last_exported_at_by_site: Dict[str, str] = {}
        for r in bundle_rows:
            site = r["site_code"]
            bundle_id = r["bundle_id"]
            period_to_val = r["period_to"]
            exported_at = r["exported_at"]

            if site not in latest_bundle_by_site:
                latest_bundle_by_site[site] = bundle_id
                last_period_to_by_site[site] = period_to_val
                last_exported_at_by_site[site] = exported_at
            else:
                cur_period_to = last_period_to_by_site[site]
                cur_exported_at = last_exported_at_by_site[site]
                # pick max(period_to, exported_at)
                if (period_to_val, exported_at) > (cur_period_to, cur_exported_at):
                    latest_bundle_by_site[site] = bundle_id
                    last_period_to_by_site[site] = period_to_val
                    last_exported_at_by_site[site] = exported_at

        # Stock end per site from latest bundle
        per_site_stock_end: Dict[str, int] = {}
        for site, bundle_id in latest_bundle_by_site.items():
            row = conn.execute(
                "SELECT stock FROM central_summary_overall WHERE bundle_id = ?",
                (bundle_id,),
            ).fetchone()
            per_site_stock_end[site] = int(row[0] if row else 0)

        per_site_rows: List[Dict] = []
        overall_total_in = 0
        overall_total_out = 0
        overall_stock_end = 0

        for r in per_site_totals:
            site = r["site_code"]
            total_in = int(r["total_in"] or 0)
            total_out = int(r["total_out"] or 0)
            bundles_count_site = int(r["bundles_count"] or 0)
            stock_end = int(per_site_stock_end.get(site, 0))
            per_site_rows.append(
                {
                    "site_code": site,
                    "total_in": total_in,
                    "total_out": total_out,
                    "stock_end": stock_end,
                    "bundles_count": bundles_count_site,
                    "last_period_to": last_period_to_by_site.get(site, ""),
                }
            )
            overall_total_in += total_in
            overall_total_out += total_out
            overall_stock_end += stock_end

        # Owner totals (movement totals during period)
        per_owner_totals = conn.execute(
            f"""
            SELECT COALESCE(owner, '') AS owner,
                   SUM(total_in) AS total_in,
                   SUM(total_out) AS total_out
            FROM central_summary_owner
            WHERE bundle_id IN ({','.join(['?'] * len(bundle_ids))})
            GROUP BY COALESCE(owner, '')
            ORDER BY owner ASC
            """,
            bundle_ids,
        ).fetchall()

        # Owner stock end (sum across sites' latest bundle)
        latest_bundle_ids = list(latest_bundle_by_site.values())
        owner_stock_end_rows = conn.execute(
            f"""
            SELECT COALESCE(owner, '') AS owner,
                   SUM(stock) AS stock_end
            FROM central_summary_owner
            WHERE bundle_id IN ({','.join(['?'] * len(latest_bundle_ids))})
            GROUP BY COALESCE(owner, '')
            ORDER BY owner ASC
            """,
            latest_bundle_ids,
        ).fetchall()
        owner_stock_end_map = {r["owner"]: int(r["stock_end"] or 0) for r in owner_stock_end_rows}

        per_owner_rows: List[Dict] = []
        for r in per_owner_totals:
            owner = (r["owner"] or "").strip()
            if not owner:
                continue
            per_owner_rows.append(
                {
                    "owner": owner,
                    "total_in": int(r["total_in"] or 0),
                    "total_out": int(r["total_out"] or 0),
                    "stock_end": int(owner_stock_end_map.get(owner, 0)),
                }
            )

        return CentralPeriodReport(
            period_from=period_from,
            period_to=period_to,
            bundles_count=len(bundle_ids),
            overall_total_in=overall_total_in,
            overall_total_out=overall_total_out,
            overall_stock_end=overall_stock_end,
            per_site_rows=per_site_rows,
            per_owner_rows=per_owner_rows,
        )
