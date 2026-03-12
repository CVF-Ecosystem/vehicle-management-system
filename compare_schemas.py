# scripts/compare_schemas.py
import sqlite3
from pprint import pprint

def get_schema(path):
    with sqlite3.connect(path) as conn:
        cur = conn.execute("SELECT sql FROM sqlite_master WHERE type='table'")
        return {row[0].split()[2]: row[0] for row in cur}

v2 = get_schema("vehicle_management_v2.db")
v1 = get_schema("vehicle_management_v1.0.db")

print("Tables only in v2:", set(v2) - set(v1))
print("Tables only in v1:", set(v1) - set(v2))
print("\nDifferences:")
for tbl in set(v2) & set(v1):
    if v2[tbl] != v1[tbl]:
        print(f"\n-- {tbl} --")
        print("v2:", v2[tbl])
        print("v1:", v1[tbl])