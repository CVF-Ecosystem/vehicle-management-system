"""
tools/generate_owner_map.py
----------------------------
Chạy 1 lần để tự động sinh owner_map.json từ database đã được normalize đúng.

Cách dùng:
    python tools/generate_owner_map.py
    python tools/generate_owner_map.py --db path/to/other.db

Script sẽ:
1. Đọc tất cả tên chủ hàng duy nhất từ DB
2. Với mỗi tên canonical, tự sinh các biến thể (no diacritics, no space, lowercase...)
3. Merge vào config/owner_map.json hiện có (không xóa entries cũ)
4. In ra report các mapping mới được thêm
"""

import argparse
import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import unidecode
except ImportError:
    print("[ERROR] Cài thư viện: pip install unidecode")
    sys.exit(1)

from config import DB_FILE, OWNER_MAP_FILE


def _sanitize(text: str) -> str:
    text = text.strip()
    text = re.sub(r'\s*[/\\]\s*', '/', text)
    text = ' '.join(text.split())
    return text.upper()


def _generate_variants(canonical: str) -> list[str]:
    """Tự sinh các biến thể thường gặp của một tên canonical."""
    variants = set()
    lower = canonical.lower()
    ascii_ver = unidecode.unidecode(lower)

    # Cơ bản
    variants.add(lower)
    variants.add(ascii_ver)
    variants.add(lower.replace(' ', ''))
    variants.add(ascii_ver.replace(' ', ''))

    # Với composite A/B → thêm biến thể từng phần
    if '/' in canonical:
        parts = [p.strip() for p in canonical.split('/')]
        for p in parts:
            p_lower = p.lower()
            p_ascii = unidecode.unidecode(p_lower)
            variants.add(p_lower)
            variants.add(p_ascii)
            variants.add(p_lower.replace(' ', ''))
            variants.add(p_ascii.replace(' ', ''))

    # Loại bỏ variant trùng với canonical (tránh self-loop)
    canonical_lower = canonical.lower()
    variants.discard(canonical_lower)
    variants.discard(canonical)

    return sorted(variants)


def load_owners_from_db(db_path: str) -> list[str]:
    if not os.path.exists(db_path):
        print(f"[ERROR] Không tìm thấy database: {db_path}")
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT owner
        FROM vehicles
        WHERE owner IS NOT NULL AND owner != ''
        ORDER BY owner
    """)
    owners = [row[0] for row in cur.fetchall()]
    conn.close()
    return owners


def load_owner_map(path: str) -> dict:
    if not os.path.exists(path):
        return {"_comment": "Owner name normalization map - Chuan hoa ten chu hang"}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARNING] Không đọc được {path}: {e}")
        return {}


def save_owner_map(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def main():
    parser = argparse.ArgumentParser(description='Generate owner_map.json from database')
    parser.add_argument('--db', default=DB_FILE, help='Đường dẫn đến database tốt (đã normalize đúng)')
    parser.add_argument('--output', default=OWNER_MAP_FILE, help='Đường dẫn file owner_map.json output')
    parser.add_argument('--dry-run', action='store_true', help='Chỉ in kết quả, không ghi file')
    args = parser.parse_args()

    print(f"[INFO] Đọc owners từ: {args.db}")
    raw_owners = load_owners_from_db(args.db)
    print(f"[INFO] Tìm thấy {len(raw_owners)} owner duy nhất trong DB")

    # Sanitize để lấy canonical
    canonicals = []
    for owner in raw_owners:
        canonical = _sanitize(owner)
        if canonical:
            canonicals.append(canonical)
    canonicals = sorted(set(canonicals))
    print(f"[INFO] {len(canonicals)} canonical names sau sanitize")

    # Load map hiện có
    owner_map = load_owner_map(args.output)
    existing_keys = set(k for k in owner_map if not k.startswith('_'))

    added = 0
    for canonical in canonicals:
        # Thêm self-mapping (lowercase → canonical) để phonetic match tìm thấy
        key = canonical.lower()
        if key not in owner_map:
            owner_map[key] = canonical
            added += 1

        # Sinh và thêm các biến thể
        for variant in _generate_variants(canonical):
            if variant and variant not in owner_map:
                # Chỉ thêm nếu variant chưa có mapping khác
                owner_map[variant] = canonical
                added += 1

    print(f"\n[RESULT] Thêm {added} entries mới vào owner_map")
    print(f"[RESULT] Tổng số entries: {len(owner_map)}")

    if args.dry_run:
        print("\n[DRY RUN] Không ghi file. Mẫu entries mới:")
        new_entries = {k: v for k, v in owner_map.items()
                       if k not in existing_keys and not k.startswith('_')}
        for k, v in list(new_entries.items())[:20]:
            print(f"  '{k}' → '{v}'")
        if len(new_entries) > 20:
            print(f"  ... và {len(new_entries) - 20} entries nữa")
    else:
        save_owner_map(args.output, owner_map)
        print(f"[DONE] Đã lưu vào: {args.output}")
        print("\nBước tiếp theo:")
        print("  1. Xóa file config/owner_normalization_cache.json (để force re-normalize)")
        print("  2. Copy DB cũ vào thay DB hiện tại")
        print("  3. Khởi động lại app — normalization sẽ tự chạy")


if __name__ == '__main__':
    main()
