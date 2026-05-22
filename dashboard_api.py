"""
Vehicle Management Dashboard — Flask API Server
================================================
Replaces Streamlit with a direct HTML/React UI served by Flask.
Run:  python dashboard_api.py
Open: http://localhost:8502?token=<SESSION_TOKEN>
"""

import os
import secrets
import sqlite3
from datetime import datetime, timedelta
from functools import wraps

import pandas as pd
from flask import Flask, jsonify, request, send_from_directory

# ─── config ─────────────────────────────────────────────────────────────────
APP_VERSION   = os.environ.get("VEHICLE_APP_VERSION", "V1.0 @2026")
DB_FILE       = os.environ.get("VEHICLE_APP_DB_PATH", "vehicle_management_v1.0.db")
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
PORT          = int(os.environ.get("VEHICLE_DASH_PORT", "8502"))

# Session token: injected by WebDashboardManager via env var; new token each run.
SESSION_TOKEN = os.environ.get("VEHICLE_DASH_TOKEN", "")

app = Flask(__name__, static_url_path="")


# ─── auth helpers ─────────────────────────────────────────────────────────────

def _require_token(f):
    """Decorator: enforce Bearer token on API endpoints."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not SESSION_TOKEN:
            # Token not configured — allow (standalone / dev mode)
            return f(*args, **kwargs)
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Unauthorized"}), 401
        token = auth_header[len("Bearer "):]
        if not secrets.compare_digest(token, SESSION_TOKEN):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


@app.after_request
def _add_cors_headers(response):
    """Restrict CORS to localhost only."""
    origin = request.headers.get("Origin", "")
    if origin.startswith("http://localhost") or origin.startswith("http://127.0.0.1"):
        response.headers["Access-Control-Allow-Origin"] = origin
    else:
        response.headers["Access-Control-Allow-Origin"] = "null"
    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    return response

# ─── db helpers ─────────────────────────────────────────────────────────────
def _db_path():
    return DB_FILE if os.path.isabs(DB_FILE) else os.path.join(BASE_DIR, DB_FILE)

def _conn():
    return sqlite3.connect(_db_path(), check_same_thread=False)

def _q(query, params=None):
    conn = _conn()
    try:
        return pd.read_sql_query(query, conn, params=params) if params \
               else pd.read_sql_query(query, conn)
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# ─── date helpers ────────────────────────────────────────────────────────────
def _fmt_vi(s):
    """'YYYY-MM-DD' → 'DD/MM/YYYY'"""
    if not s:
        return ""
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return str(s)

def _parse_vi(s):
    """'DD/MM/YYYY' → 'YYYY-MM-DD'"""
    try:
        return datetime.strptime(str(s).strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
    except Exception:
        return str(s)

def _normalise_date(s):
    """Accept dd/mm/yyyy or yyyy-mm-dd, always return yyyy-mm-dd."""
    s = (s or "").strip()
    return _parse_vi(s) if "/" in s else s

# ─── serve static files ──────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "dashboard.html")

@app.route("/assets/<path:filename>")
def assets(filename):
    return send_from_directory(os.path.join(BASE_DIR, "assets"), filename)

# ─── /api/meta ───────────────────────────────────────────────────────────────
@app.route("/api/meta")
@_require_token
def api_meta():
    df_range = _q("""
        SELECT
            MIN(DATE(date_in))  AS min_date,
            MAX(DATE(date_in))  AS max_in,
            MAX(DATE(date_out)) AS max_out
        FROM vehicles WHERE is_active = 1
    """)
    min_d = max_d = ""
    if not df_range.empty:
        row   = df_range.iloc[0]
        min_d = str(row["min_date"] or "")
        max_d = str(max(str(row["max_in"] or ""), str(row["max_out"] or "")) or "")

    df_owners = _q("""
        SELECT DISTINCT owner FROM vehicles
        WHERE is_active = 1 AND owner IS NOT NULL AND owner != ''
        ORDER BY owner
    """)
    owners = df_owners["owner"].tolist() if not df_owners.empty else []

    return jsonify({
        "dateRange": {"min": _fmt_vi(min_d), "max": _fmt_vi(max_d)},
        "owners":    owners,
        "version":   APP_VERSION,
    })

# ─── /api/data ───────────────────────────────────────────────────────────────
@app.route("/api/data")
@_require_token
def api_data():
    start     = _normalise_date(request.args.get("start", ""))
    end       = _normalise_date(request.args.get("end",   ""))
    owner_sel = request.args.get("owner", "Tất cả")

    if not start:
        start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end:
        end = datetime.now().strftime("%Y-%m-%d")

    # ── KPI ──────────────────────────────────────────────────────────────────
    df_kpi = _q("""
        SELECT
            COUNT(*) AS total_vehicles,
            SUM(CASE WHEN status='IN_STOCK' AND is_active=1 THEN 1 ELSE 0 END) AS in_stock,
            SUM(CASE WHEN status='SHIPPED'  AND is_active=1 THEN 1 ELSE 0 END) AS shipped,
            SUM(CASE WHEN is_active=1
                      AND DATE(date_in) BETWEEN DATE(?) AND DATE(?) THEN 1 ELSE 0 END) AS total_in,
            SUM(CASE WHEN is_active=1 AND date_out IS NOT NULL
                      AND DATE(date_out) BETWEEN DATE(?) AND DATE(?) THEN 1 ELSE 0 END) AS total_out
        FROM vehicles
        WHERE is_active = 1
          AND (
              DATE(date_in) BETWEEN DATE(?) AND DATE(?)
              OR (date_out IS NOT NULL AND DATE(date_out) BETWEEN DATE(?) AND DATE(?))
              OR status = 'IN_STOCK'
          )
    """, (start, end, start, end, start, end, start, end))

    kpi = {"total": 0, "nhap": 0, "xuat": 0, "ton": 0, "daXuat": 0}
    if not df_kpi.empty:
        r = df_kpi.iloc[0]
        kpi = {
            "total":  int(r["total_vehicles"] or 0),
            "nhap":   int(r["total_in"]        or 0),
            "xuat":   int(r["total_out"]       or 0),
            "ton":    int(r["in_stock"]         or 0),
            "daXuat": int(r["shipped"]          or 0),
        }

    # ── OWNERS summary ────────────────────────────────────────────────────────
    df_in = _q("""
        SELECT owner, COUNT(*) AS nhap FROM vehicles
        WHERE is_active=1 AND DATE(date_in) BETWEEN DATE(?) AND DATE(?)
        GROUP BY owner
    """, (start, end))

    df_out = _q("""
        SELECT owner, COUNT(*) AS xuat FROM vehicles
        WHERE is_active=1 AND date_out IS NOT NULL
          AND DATE(date_out) BETWEEN DATE(?) AND DATE(?)
        GROUP BY owner
    """, (start, end))

    df_stock = _q("""
        SELECT owner, COUNT(*) AS ton FROM vehicles
        WHERE is_active=1 AND status='IN_STOCK'
        GROUP BY owner
    """)

    df_ow = df_stock.copy() if not df_stock.empty \
            else pd.DataFrame(columns=["owner", "ton"])
    if not df_in.empty:
        df_ow = df_ow.merge(df_in, on="owner", how="outer")
    else:
        df_ow["nhap"] = 0
    if not df_out.empty:
        df_ow = df_ow.merge(df_out, on="owner", how="outer")
    else:
        df_ow["xuat"] = 0

    df_ow = df_ow.fillna(0)
    for c in ["nhap", "xuat", "ton"]:
        if c not in df_ow.columns:
            df_ow[c] = 0
    df_ow[["nhap", "xuat", "ton"]] = df_ow[["nhap", "xuat", "ton"]].astype(int)
    df_ow = df_ow[df_ow[["nhap", "xuat", "ton"]].sum(axis=1) > 0].copy()
    df_ow = df_ow.rename(columns={"owner": "name"})

    if owner_sel != "Tất cả" and not df_ow.empty:
        df_ow = df_ow[df_ow["name"] == owner_sel]

    owners_list = df_ow[["name", "nhap", "xuat", "ton"]].to_dict(orient="records") \
                  if not df_ow.empty else []

    # ── DAILY trend ───────────────────────────────────────────────────────────
    df_daily = _q("""
        SELECT DATE(date_in) AS dt, 'n' AS tp, COUNT(*) AS cnt
        FROM vehicles
        WHERE is_active=1 AND DATE(date_in) BETWEEN DATE(?) AND DATE(?)
        GROUP BY DATE(date_in)
        UNION ALL
        SELECT DATE(date_out), 'x', COUNT(*)
        FROM vehicles
        WHERE is_active=1 AND date_out IS NOT NULL
          AND DATE(date_out) BETWEEN DATE(?) AND DATE(?)
        GROUP BY DATE(date_out)
        ORDER BY dt
    """, (start, end, start, end))

    daily = []
    if not df_daily.empty:
        df_pv = df_daily.pivot_table(
            index="dt", columns="tp", values="cnt",
            aggfunc="sum", fill_value=0
        ).reset_index().sort_values("dt")
        if "n" not in df_pv.columns: df_pv["n"] = 0
        if "x" not in df_pv.columns: df_pv["x"] = 0
        for _, row in df_pv.iterrows():
            try:
                label = datetime.strptime(str(row["dt"])[:10], "%Y-%m-%d").strftime("%d/%m")
            except Exception:
                label = str(row["dt"])
            daily.append({"d": label, "n": int(row["n"]), "x": int(row["x"])})

    # ── YARD occupancy ────────────────────────────────────────────────────────
    df_yard = _q("""
        SELECT
            l.block AS block,
            SUM(CASE WHEN v.vin IS NOT NULL THEN 1 ELSE 0 END) AS occ,
            COUNT(l.id) AS tot
        FROM locations l
        LEFT JOIN vehicles v
            ON l.id = v.location_id AND v.is_active=1 AND v.status='IN_STOCK'
        WHERE l.block IS NOT NULL
        GROUP BY l.block
        ORDER BY l.block
    """)
    yard = df_yard[["block", "occ", "tot"]].to_dict(orient="records") \
           if not df_yard.empty else []
    for item in yard:
        item["occ"] = int(item["occ"])
        item["tot"] = int(item["tot"])

    # ── LONG STOCK ────────────────────────────────────────────────────────────
    df_ls = _q("""
        SELECT
            v.vin,
            v.owner,
            v.vehicle_type                                            AS type,
            v.date_in,
            CAST(julianday('now') - julianday(v.date_in) AS INTEGER)  AS days,
            COALESCE(l.block, '-')                                    AS blk,
            COALESCE(CAST(l.slot AS TEXT), '-')                       AS slot
        FROM vehicles v
        LEFT JOIN locations l ON v.location_id = l.id
        WHERE v.is_active=1 AND v.status='IN_STOCK'
          AND julianday('now') - julianday(v.date_in) > 5
        ORDER BY days DESC
    """)
    longstock = []
    if not df_ls.empty:
        df_ls["date"] = pd.to_datetime(
            df_ls["date_in"], errors="coerce"
        ).dt.strftime("%d/%m/%Y")
        df_ls["days"] = df_ls["days"].fillna(0).astype(int)
        longstock = df_ls[["vin", "owner", "type", "date", "days", "blk", "slot"]] \
                        .to_dict(orient="records")

    # ── VEHICLE TYPES ─────────────────────────────────────────────────────────
    df_vt = _q("""
        SELECT vehicle_type AS type, COUNT(*) AS count
        FROM vehicles
        WHERE is_active=1 AND status='IN_STOCK'
        GROUP BY vehicle_type
        ORDER BY count DESC
    """)
    vehicle_types = df_vt.to_dict(orient="records") if not df_vt.empty else []
    for item in vehicle_types:
        item["count"] = int(item["count"])

    return jsonify({
        "kpi":          kpi,
        "owners":       owners_list,
        "daily":        daily,
        "yard":         yard,
        "longstock":    longstock,
        "vehicleTypes": vehicle_types,
    })

# ─── main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    db = _db_path()
    if not os.path.exists(db):
        print(f"[WARN] Database not found: {db}")
    print(f"[Dashboard] http://localhost:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
