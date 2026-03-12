import sqlite3, os
path=r"D:\UNG DUNG AI\TOOL AI 2026\CVF-Workspace\vehicle-management-system\vehicle_management_v2.db"
print('exists', os.path.exists(path))
if os.path.exists(path):
    conn=sqlite3.connect(path)
    cur=conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print('tables:', [r[0] for r in cur.fetchall()])
