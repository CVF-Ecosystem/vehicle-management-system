import argparse
import os
from datetime import date, datetime

from reporting.site_event_bundle import build_audit_event_bundle, save_event_bundle_json
from utils import load_config


def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def main() -> int:
    parser = argparse.ArgumentParser(description="Export event bundle (audit logs) để gửi về trung tâm.")
    parser.add_argument("--from", dest="from_date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--to", dest="to_date", required=True, help="YYYY-MM-DD")
    parser.add_argument(
        "--out",
        dest="out_path",
        default=None,
        help="Đường dẫn output .json (mặc định: exports/events_<site>_<from>_<to>.json)",
    )
    parser.add_argument(
        "--audit-db",
        dest="audit_db",
        default=None,
        help="Đường dẫn audit DB (mặc định lấy từ config.AUDIT_DB_FILE)",
    )

    args = parser.parse_args()

    start_date = _parse_date(args.from_date)
    end_date = _parse_date(args.to_date)

    cfg = load_config()
    site_code = cfg.get("Site", "site_code", fallback="SITE_001").strip() or "SITE_001"
    site_instance_id = cfg.get("Site", "site_instance_id", fallback="").strip()
    if not site_instance_id:
        # load_config() should ensure it exists, but keep it safe
        from uuid import uuid4

        site_instance_id = str(uuid4())

    bundle = build_audit_event_bundle(
        start_date,
        end_date,
        site_code=site_code,
        site_instance_id=site_instance_id,
        audit_db_path=args.audit_db,
    )

    out_path = args.out_path
    if not out_path:
        os.makedirs("exports", exist_ok=True)
        out_path = os.path.join(
            "exports",
            f"events_{site_code}_{start_date.isoformat()}_{end_date.isoformat()}.json",
        )

    save_event_bundle_json(bundle, out_path)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
