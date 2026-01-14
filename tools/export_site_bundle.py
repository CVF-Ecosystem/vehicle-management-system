import argparse
import os
from datetime import date, datetime

from api_client import ApiClient
from reporting.site_bundle import build_site_bundle, save_bundle_json
from utils import load_config


def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def main() -> int:
    parser = argparse.ArgumentParser(description="Export site bundle JSON để gửi về trung tâm.")
    parser.add_argument("--from", dest="from_date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--to", dest="to_date", required=True, help="YYYY-MM-DD")
    parser.add_argument(
        "--out",
        dest="out_path",
        default=None,
        help="Đường dẫn output .json (mặc định: exports/bundle_<site>_<from>_<to>.json)",
    )

    args = parser.parse_args()

    start_date = _parse_date(args.from_date)
    end_date = _parse_date(args.to_date)

    cfg = load_config()
    site_code = cfg.get("Site", "site_code", fallback="SITE_001")

    api = ApiClient()
    vehicle_manager = api.vehicle_manager

    bundle = build_site_bundle(vehicle_manager, start_date, end_date, site_code)

    out_path = args.out_path
    if not out_path:
        os.makedirs("exports", exist_ok=True)
        out_path = os.path.join(
            "exports",
            f"bundle_{site_code}_{start_date.isoformat()}_{end_date.isoformat()}.json",
        )

    save_bundle_json(bundle, out_path)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
