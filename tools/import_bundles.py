import argparse
import glob
import os
import sys

from reporting.central_store import CentralStore


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import các site bundle JSON vào central_report.db (idempotent theo bundle_id)."
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Đường dẫn file .json hoặc pattern glob (vd: exports/*.json)",
    )
    parser.add_argument(
        "--db",
        default=os.path.join("config", "central_report.db"),
        help="Đường dẫn central sqlite db (mặc định: config/central_report.db)",
    )

    args = parser.parse_args()

    files = []
    for p in args.paths:
        matched = glob.glob(p)
        if matched:
            files.extend(matched)
        elif os.path.isfile(p):
            files.append(p)

    files = sorted(set(files))
    if not files:
        print("Không tìm thấy file bundle để import.")
        return 2

    store = CentralStore(args.db)

    ok = 0
    skipped = 0
    failed = 0

    for path in files:
        result = store.import_bundle_file(path)
        if result.success:
            if result.inserted == 0:
                skipped += 1
                status = "SKIP"
            else:
                ok += 1
                status = "OK"
        else:
            failed += 1
            status = "FAIL"

        print(f"[{status}] {os.path.basename(path)} -> {result.message}")

    print(f"Tổng: OK={ok} SKIP={skipped} FAIL={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
