#!/usr/bin/env python3
"""
tools/export_translations_json.py
===================================
Xuất translations.py thành file JSON để dễ chỉnh sửa bởi non-developer.

Usage:
    python tools/export_translations_json.py
    python tools/export_translations_json.py --output config/translations.json

Output: config/translations.json
"""

import sys
import os
import json
import argparse

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


def main():
    parser = argparse.ArgumentParser(description="Xuất translations sang JSON")
    parser.add_argument(
        "--output", "-o",
        default=os.path.join(PROJECT_ROOT, "config", "translations.json"),
        help="Đường dẫn file JSON output"
    )
    args = parser.parse_args()

    from translations import translations

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(translations, f, ensure_ascii=False, indent=2, sort_keys=True)

    print(f"[OK] Đã xuất {len(translations)} keys sang: {args.output}")
    print(f"     Bạn có thể chỉnh sửa file JSON này và import lại bằng:")
    print(f"     python tools/import_translations_json.py --input {args.output}")


if __name__ == "__main__":
    main()
