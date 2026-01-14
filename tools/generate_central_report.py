import argparse
import os
from datetime import datetime

from report_generators.central_excel_report import generate_central_excel_report
from reporting.central_report import build_central_period_report


def _parse_date(s: str) -> str:
    # keep ISO YYYY-MM-DD
    return datetime.strptime(s, "%Y-%m-%d").date().isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Xuất báo cáo tổng hợp từ DB trung tâm (central_report.db) theo thời gian."
    )
    parser.add_argument("--from", dest="from_date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--to", dest="to_date", required=True, help="YYYY-MM-DD")
    parser.add_argument(
        "--db",
        default=os.path.join("config", "central_report.db"),
        help="Đường dẫn DB trung tâm (mặc định: config/central_report.db)",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Đường dẫn file Excel output (mặc định: reports/central_<from>_<to>.xlsx)",
    )

    args = parser.parse_args()

    period_from = _parse_date(args.from_date)
    period_to = _parse_date(args.to_date)

    report = build_central_period_report(args.db, period_from, period_to)

    out_path = args.out
    if not out_path:
        os.makedirs("reports", exist_ok=True)
        out_path = os.path.join("reports", f"central_{period_from}_{period_to}.xlsx")

    result = generate_central_excel_report(
        out_path,
        period_from=report.period_from,
        period_to=report.period_to,
        overall={
            "total_in": report.overall_total_in,
            "total_out": report.overall_total_out,
            "stock_end": report.overall_stock_end,
            "bundles_count": report.bundles_count,
        },
        per_site_rows=report.per_site_rows,
        per_owner_rows=report.per_owner_rows,
    )

    if result.get("success"):
        print(out_path)
        return 0

    print(result.get("message") or "Lỗi xuất báo cáo")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
