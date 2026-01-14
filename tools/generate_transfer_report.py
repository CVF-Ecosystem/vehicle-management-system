import argparse
import os
from datetime import datetime

from reporting.central_transfer_report import export_transfer_candidates_csv, find_transfer_candidates


def _parse_date(s: str) -> str:
    return datetime.strptime(s, "%Y-%m-%d").date().isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Xuất danh sách VIN nghi là chuyển bãi (heuristic) từ central_events.db."
    )
    parser.add_argument("--from", dest="from_date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--to", dest="to_date", required=True, help="YYYY-MM-DD")
    parser.add_argument(
        "--db",
        default=os.path.join("config", "central_events.db"),
        help="Đường dẫn DB events trung tâm (mặc định: config/central_events.db)",
    )
    parser.add_argument(
        "--max-days",
        type=int,
        default=7,
        help="Khoảng ngày tối đa giữa OUT->IN để coi là chuyển bãi (mặc định: 7)",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Đường dẫn file CSV output (mặc định: reports/transfers_<from>_<to>.csv)",
    )

    args = parser.parse_args()

    period_from = _parse_date(args.from_date)
    period_to = _parse_date(args.to_date)

    candidates = find_transfer_candidates(args.db, period_from, period_to, max_days=args.max_days)

    out_path = args.out
    if not out_path:
        os.makedirs("reports", exist_ok=True)
        out_path = os.path.join("reports", f"transfers_{period_from}_{period_to}.csv")

    export_transfer_candidates_csv(candidates, out_path)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
