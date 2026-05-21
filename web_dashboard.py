"""
🌐 Vehicle Management System - Web Dashboard
=============================================
Interactive dashboard using Streamlit + Plotly
Run: streamlit run web_dashboard.py
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from html import escape
from io import BytesIO
import os

# Lấy version từ biến môi trường (được truyền vào bởi WebDashboardManager khi chạy từ exe)
# Fallback về chuỗi tĩnh nếu chạy độc lập
APP_VERSION_DISPLAY = os.environ.get('VEHICLE_APP_VERSION', 'V1.0 @2026')

# ============================================
# CONFIGURATION
# ============================================
DB_FILE = os.environ.get('VEHICLE_APP_DB_PATH', "vehicle_management_v1.0.db")
PAGE_TITLE = "🚗 Vehicle Management Dashboard"
PAGE_ICON = "🚗"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_FILE = os.path.join(BASE_DIR, "assets", "Logo.jpg")
COLORS = {
    "in": "#3b82f6",
    "out": "#ef4444",
    "stock": "#10b981",
    "total": "#7c3aed",
    "done": "#f59e0b",
    "text": "#0f172a",
    "muted": "#64748b",
}

# ============================================
# DATABASE CONNECTION
# ============================================
def get_connection():
    """Create a fresh database connection (no cache to always get latest data)."""
    if not os.path.exists(DB_FILE):
        st.error(f"❌ Database file not found: {DB_FILE}")
        st.stop()
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def run_query(query, params=None):
    """Execute a query and return results as DataFrame."""
    conn = get_connection()
    try:
        if params:
            return pd.read_sql_query(query, conn, params=params)
        return pd.read_sql_query(query, conn)
    except Exception as e:
        st.error(f"Query error: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# ============================================
# DATA QUERIES
# ============================================
def get_summary_stats(start_date=None, end_date=None):
    """Get overall statistics with optional date filter."""
    if start_date and end_date:
        query = """
            SELECT 
                COUNT(*) as total_vehicles,
                SUM(CASE WHEN status = 'IN_STOCK' AND is_active = 1 THEN 1 ELSE 0 END) as in_stock,
                SUM(CASE WHEN status = 'SHIPPED' AND is_active = 1 THEN 1 ELSE 0 END) as shipped,
                SUM(CASE WHEN is_active = 1 AND DATE(date_in) BETWEEN DATE(?) AND DATE(?) THEN 1 ELSE 0 END) as total_in_period,
                SUM(CASE WHEN is_active = 1 AND date_out IS NOT NULL AND DATE(date_out) BETWEEN DATE(?) AND DATE(?) THEN 1 ELSE 0 END) as total_out_period
            FROM vehicles
            WHERE is_active = 1 AND (
                DATE(date_in) BETWEEN DATE(?) AND DATE(?)
                OR (date_out IS NOT NULL AND DATE(date_out) BETWEEN DATE(?) AND DATE(?))
                OR status = 'IN_STOCK'
            )
        """
        df = run_query(query, (start_date, end_date, start_date, end_date, start_date, end_date, start_date, end_date))
    else:
        query = """
            SELECT 
                COUNT(*) as total_vehicles,
                SUM(CASE WHEN status = 'IN_STOCK' AND is_active = 1 THEN 1 ELSE 0 END) as in_stock,
                SUM(CASE WHEN status = 'SHIPPED' AND is_active = 1 THEN 1 ELSE 0 END) as shipped,
                0 as total_in_period,
                0 as total_out_period
            FROM vehicles
        """
        df = run_query(query)
    return df.iloc[0] if not df.empty else None

def get_date_range_from_db():
    """Get min and max dates from database."""
    query = """
        SELECT 
            MIN(DATE(date_in)) as min_date,
            MAX(DATE(date_in)) as max_date_in,
            MAX(DATE(date_out)) as max_date_out
        FROM vehicles
        WHERE is_active = 1
    """
    df = run_query(query)
    if not df.empty:
        min_date = df.iloc[0]['min_date']
        max_in = df.iloc[0]['max_date_in']
        max_out = df.iloc[0]['max_date_out']
        max_date = max(max_in or '', max_out or '') or max_in
        return min_date, max_date
    return None, None

def get_vehicles_by_owner(start_date=None, end_date=None):
    """Get vehicle count by owner with optional date filter."""
    if start_date and end_date:
        query = """
            SELECT owner, 
                   COUNT(*) as total,
                   SUM(CASE WHEN status = 'IN_STOCK' THEN 1 ELSE 0 END) as in_stock,
                   SUM(CASE WHEN status = 'SHIPPED' THEN 1 ELSE 0 END) as shipped,
                   SUM(CASE WHEN DATE(date_in) BETWEEN DATE(?) AND DATE(?) THEN 1 ELSE 0 END) as in_period,
                   SUM(CASE WHEN date_out IS NOT NULL AND DATE(date_out) BETWEEN DATE(?) AND DATE(?) THEN 1 ELSE 0 END) as out_period
            FROM vehicles 
            WHERE is_active = 1 AND owner IS NOT NULL AND owner != ''
              AND (
                DATE(date_in) BETWEEN DATE(?) AND DATE(?)
                OR (date_out IS NOT NULL AND DATE(date_out) BETWEEN DATE(?) AND DATE(?))
                OR status = 'IN_STOCK'
              )
            GROUP BY owner
            ORDER BY total DESC
        """
        return run_query(query, (start_date, end_date, start_date, end_date, start_date, end_date, start_date, end_date))
    else:
        query = """
            SELECT owner, 
                   COUNT(*) as total,
                   SUM(CASE WHEN status = 'IN_STOCK' THEN 1 ELSE 0 END) as in_stock,
                   SUM(CASE WHEN status = 'SHIPPED' THEN 1 ELSE 0 END) as shipped
            FROM vehicles 
            WHERE is_active = 1 AND owner IS NOT NULL AND owner != ''
            GROUP BY owner
            ORDER BY total DESC
        """
        return run_query(query)

def get_daily_inbound_outbound(start_date, end_date):
    """Get daily inbound/outbound statistics."""
    query = """
        SELECT 
            DATE(date_in) as date,
            'Nhập' as type,
            COUNT(*) as count
        FROM vehicles 
        WHERE is_active = 1 
          AND DATE(date_in) BETWEEN DATE(?) AND DATE(?)
        GROUP BY DATE(date_in)
        
        UNION ALL
        
        SELECT 
            DATE(date_out) as date,
            'Xuất' as type,
            COUNT(*) as count
        FROM vehicles 
        WHERE is_active = 1 
          AND date_out IS NOT NULL
          AND DATE(date_out) BETWEEN DATE(?) AND DATE(?)
        GROUP BY DATE(date_out)
        ORDER BY date
    """
    return run_query(query, (start_date, end_date, start_date, end_date))

def get_summary_by_owner_period(start_date, end_date):
    """Get summary report by owner for a specific period."""
    query_in = """
        SELECT owner, COUNT(*) as total_in
        FROM vehicles 
        WHERE is_active = 1 AND DATE(date_in) BETWEEN DATE(?) AND DATE(?)
        GROUP BY owner
    """
    query_out = """
        SELECT owner, COUNT(*) as total_out
        FROM vehicles 
        WHERE is_active = 1 AND date_out IS NOT NULL AND DATE(date_out) BETWEEN DATE(?) AND DATE(?)
        GROUP BY owner
    """
    query_stock = """
        SELECT owner, COUNT(*) as stock
        FROM vehicles 
        WHERE is_active = 1 AND status = 'IN_STOCK'
        GROUP BY owner
    """
    
    df_in = run_query(query_in, (start_date, end_date))
    df_out = run_query(query_out, (start_date, end_date))
    df_stock = run_query(query_stock)
    
    # Merge dataframes
    if df_in.empty and df_out.empty and df_stock.empty:
        return pd.DataFrame()
    
    # Start with stock as base
    df = df_stock.copy() if not df_stock.empty else pd.DataFrame(columns=['owner', 'stock'])
    
    if not df_in.empty:
        df = df.merge(df_in, on='owner', how='outer')
    else:
        df['total_in'] = 0
        
    if not df_out.empty:
        df = df.merge(df_out, on='owner', how='outer')
    else:
        df['total_out'] = 0
    
    df = df.fillna(0)
    
    # Ensure columns exist
    for col in ['total_in', 'total_out', 'stock']:
        if col not in df.columns:
            df[col] = 0
    
    df[['total_in', 'total_out', 'stock']] = df[['total_in', 'total_out', 'stock']].astype(int)
    
    return df[df[['total_in', 'total_out', 'stock']].sum(axis=1) > 0]

def get_vehicle_types():
    """Get vehicle count by type."""
    query = """
        SELECT vehicle_type, COUNT(*) as count
        FROM vehicles 
        WHERE is_active = 1 AND status = 'IN_STOCK'
        GROUP BY vehicle_type
        ORDER BY count DESC
    """
    return run_query(query)

def get_long_stock_vehicles(days=5):
    """Get vehicles that have been in stock for more than X days."""
    query = f"""
        SELECT 
            v.vin, 
            v.owner, 
            v.vehicle_type, 
            v.date_in,
            CAST(julianday('now') - julianday(v.date_in) AS INTEGER) as days_in_stock,
            COALESCE(l.block, '-') as block,
            COALESCE(CAST(l.slot AS TEXT), '-') as slot
        FROM vehicles v
        LEFT JOIN locations l ON v.location_id = l.id
        WHERE v.is_active = 1 
          AND v.status = 'IN_STOCK'
          AND julianday('now') - julianday(v.date_in) > {days}
        ORDER BY days_in_stock DESC
    """
    return run_query(query)

def get_owners_list():
    """Get list of all owners."""
    query = """
        SELECT DISTINCT owner 
        FROM vehicles 
        WHERE is_active = 1 AND owner IS NOT NULL AND owner != ''
        ORDER BY owner
    """
    df = run_query(query)
    return df['owner'].tolist() if not df.empty else []

def get_yard_occupancy():
    """Get yard occupancy by block from locations table."""
    query = """
        SELECT 
            l.block as block, 
            SUM(CASE WHEN v.vin IS NOT NULL THEN 1 ELSE 0 END) as occupied,
            COUNT(l.id) as total_slots
        FROM locations l
        LEFT JOIN vehicles v ON l.id = v.location_id AND v.is_active = 1 AND v.status = 'IN_STOCK'
        WHERE l.block IS NOT NULL
        GROUP BY l.block
        ORDER BY l.block
    """
    return run_query(query)

def get_yard_detail():
    """Get detailed yard map with all locations."""
    query = """
        SELECT 
            l.block,
            CAST(l.slot AS TEXT) as slot,
            l.is_occupied,
            COALESCE(v.vin, '') as vin,
            COALESCE(v.owner, '') as owner,
            COALESCE(v.vehicle_type, '') as vehicle_type
        FROM locations l
        LEFT JOIN vehicles v ON l.id = v.location_id AND v.is_active = 1 AND v.status = 'IN_STOCK'
        ORDER BY l.block, l.slot
    """
    return run_query(query)

def fmt_number(value):
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "0"

def safe_int(value):
    try:
        if pd.isna(value):
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0

def fmt_kpi_value(value):
    if isinstance(value, str):
        return escape(value)
    return fmt_number(value)

def inject_design_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
        html, body, [class*="css"], .stApp {
            font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        .stApp {
            background: #f0f3fb;
        }
        .main .block-container {
            padding: 1rem 1.7rem 1.4rem;
            max-width: 100%;
        }
        [data-testid="stHeader"] {
            background: rgba(240, 243, 251, 0.88);
            backdrop-filter: blur(10px);
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(175deg, #0c1d46 0%, #142d5a 55%, #1a3a6b 100%);
            border-right: 1px solid rgba(255, 255, 255, 0.09);
        }
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] div {
            color: rgba(255, 255, 255, 0.88);
        }
        [data-testid="stSidebar"] small,
        [data-testid="stSidebar"] .stCaptionContainer,
        [data-testid="stSidebar"] .stMarkdown p {
            color: rgba(255, 255, 255, 0.62);
        }
        [data-testid="stSidebar"] hr {
            border-color: rgba(255, 255, 255, 0.09);
            margin: 0.75rem 0;
        }
        [data-testid="stSidebar"] .stButton button {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.13);
            border-radius: 8px;
            color: rgba(255, 255, 255, 0.74);
            transition: all .15s ease;
        }
        [data-testid="stSidebar"] .stButton button:hover {
            background: rgba(59, 130, 246, 0.28);
            border-color: rgba(96, 165, 250, 0.7);
            color: #93c5fd;
        }
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: #ffffff;
            border: 1px solid #e4e9f2;
            border-radius: 14px;
            box-shadow: 0 2px 8px rgba(15, 23, 42, .07), 0 1px 3px rgba(15, 23, 42, .04);
        }
        .vm-sidebar-brand {
            display: flex;
            align-items: center;
            gap: 11px;
            padding: 4px 0 10px;
        }
        .vm-sidebar-logo {
            width: 42px;
            height: 42px;
            border-radius: 9px;
            background: #fff;
            padding: 3px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 8px rgba(0, 0, 0, .2);
            font-size: 20px;
        }
        .vm-sidebar-title {
            color: #fff;
            font-weight: 700;
            font-size: 13.5px;
            line-height: 1.2;
        }
        .vm-sidebar-subtitle {
            color: rgba(255, 255, 255, .38);
            font-size: 10px;
            letter-spacing: .07em;
            margin-top: 2px;
        }
        .vm-topbar {
            background: #fff;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 14px 18px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 14px;
            box-shadow: 0 2px 10px rgba(15, 23, 42, .06);
            margin-bottom: 16px;
        }
        .vm-topbar h1 {
            font-size: 21px;
            font-weight: 800;
            color: #0f172a;
            letter-spacing: -0.01em;
            margin: 0;
            padding: 0;
        }
        .vm-topbar p {
            font-size: 12.5px;
            color: #94a3b8;
            margin: 3px 0 0;
        }
        .vm-topbar-actions {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 10px;
            flex-wrap: wrap;
        }
        .vm-chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            border-radius: 8px;
            padding: 7px 13px;
            font-size: 12.5px;
            font-weight: 600;
            white-space: nowrap;
        }
        .vm-chip-blue {
            background: #f0f9ff;
            border: 1px solid #bae6fd;
            color: #0369a1;
        }
        .vm-chip-gray {
            background: #f1f5f9;
            border: 1px solid #e2e8f0;
            color: #64748b;
        }
        .vm-live-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #10b981;
            display: inline-block;
        }
        .vm-section {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 4px 0 12px;
        }
        .vm-section-bar {
            width: 3px;
            height: 24px;
            border-radius: 2px;
            background: linear-gradient(180deg, #3b82f6, #7c3aed);
        }
        .vm-section-title {
            font-size: 13.5px;
            font-weight: 700;
            color: #0f172a;
            display: flex;
            gap: 6px;
            align-items: center;
        }
        .vm-section-sub {
            font-size: 11.5px;
            color: #94a3b8;
            margin-top: 1px;
        }
        .vm-kpi {
            background: #fff;
            border: 1px solid #e4e9f2;
            border-left: 3px solid var(--accent);
            border-radius: 14px;
            padding: 16px 18px;
            min-height: 128px;
            position: relative;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(15, 23, 42, .07), 0 1px 3px rgba(15, 23, 42, .04);
            transition: transform .22s cubic-bezier(.34, 1.56, .64, 1), box-shadow .22s ease;
        }
        .vm-kpi:hover {
            transform: translateY(-3px) scale(1.015);
            box-shadow: 0 14px 32px rgba(15, 23, 42, .12), 0 4px 12px rgba(15, 23, 42, .08);
        }
        .vm-kpi-watermark {
            position: absolute;
            top: -14px;
            right: -10px;
            font-size: 48px;
            opacity: .04;
        }
        .vm-kpi-head {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            margin-bottom: 11px;
        }
        .vm-kpi-title {
            font-size: 11.5px;
            font-weight: 500;
            color: #64748b;
            line-height: 1.4;
            padding-right: 4px;
        }
        .vm-kpi-icon {
            width: 31px;
            height: 31px;
            border-radius: 8px;
            background: var(--icon-bg);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 15px;
            flex-shrink: 0;
        }
        .vm-kpi-value {
            font-size: 28px;
            font-weight: 800;
            color: #0f172a;
            letter-spacing: -0.03em;
            line-height: 1;
        }
        .vm-kpi-sub {
            font-size: 11px;
            color: #94a3b8;
            margin-top: 5px;
        }
        .vm-card-title {
            font-size: 15px;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 2px;
        }
        .vm-card-subtitle {
            font-size: 12px;
            color: #94a3b8;
            margin-bottom: 12px;
        }
        .vm-alert {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 9px 13px;
            background: #fff7ed;
            border: 1px solid #fed7aa;
            border-radius: 9px;
            margin-bottom: 14px;
            font-size: 12.5px;
            color: #92400e;
        }
        .vm-yard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 12px;
        }
        .vm-yard-card {
            border: 1.5px solid var(--yard-border);
            border-radius: 11px;
            padding: 16px;
            background: var(--yard-bg);
        }
        .vm-yard-name {
            font-size: 13px;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 10px;
        }
        .vm-yard-track {
            height: 7px;
            background: #f1f5f9;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 9px;
        }
        .vm-yard-fill {
            height: 100%;
            width: var(--pct);
            background: var(--yard-color);
            border-radius: 4px;
        }
        .vm-yard-meta {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
        }
        .vm-yard-count {
            color: #64748b;
        }
        .vm-yard-pct {
            font-weight: 700;
            color: var(--yard-color);
        }
        .stDownloadButton button {
            background: #16a34a;
            border: 1px solid #15803d;
            color: #fff;
            border-radius: 8px;
            font-size: 12.5px;
            font-weight: 600;
            box-shadow: 0 1px 4px rgba(22, 163, 74, .28);
            transition: all .15s ease;
        }
        .stDownloadButton button:hover {
            background: #15803d;
            border-color: #15803d;
            color: #fff;
            transform: translateY(-1px);
            box-shadow: 0 4px 14px rgba(22, 163, 74, .45);
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 0;
            border-bottom: 2px solid #e2e8f0;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 0;
            padding: 10px 22px;
            color: #64748b;
            font-weight: 500;
        }
        .stTabs [aria-selected="true"] {
            color: #2563eb;
            font-weight: 700;
            border-bottom: 2px solid #2563eb;
        }
        h1, h2, h3 {
            color: #0f172a;
        }
        </style>
    """, unsafe_allow_html=True)

def render_section_header(icon, title, subtitle):
    st.markdown(
        f"""
        <div class="vm-section">
            <div class="vm-section-bar"></div>
            <div>
                <div class="vm-section-title"><span>{icon}</span><span>{escape(title)}</span></div>
                <div class="vm-section-sub">{escape(subtitle)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_kpi_card(title, value, icon, color, icon_bg, subtitle):
    st.markdown(
        f"""
        <div class="vm-kpi" style="--accent:{color};--icon-bg:{icon_bg};">
            <div class="vm-kpi-watermark">{icon}</div>
            <div class="vm-kpi-head">
                <div class="vm-kpi-title">{escape(title)}</div>
                <div class="vm-kpi-icon">{icon}</div>
            </div>
            <div class="vm-kpi-value">{fmt_kpi_value(value)}</div>
            <div class="vm-kpi-sub">{escape(subtitle)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def apply_plotly_style(fig, height=320, legend_top=True):
    legend = dict(
        orientation="h",
        yanchor="bottom",
        y=1.02 if legend_top else -0.22,
        xanchor="center",
        x=0.5,
        font=dict(size=12, color=COLORS["muted"])
    )
    fig.update_layout(
        font=dict(family="Inter, Arial, sans-serif", color=COLORS["text"]),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=height,
        margin=dict(l=36, r=28, t=42, b=54),
        legend=legend,
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="Inter")
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor="#e2e8f0", tickfont=dict(color=COLORS["muted"], size=11))
    fig.update_yaxes(showgrid=True, gridcolor="#f1f5f9", zeroline=False, tickfont=dict(color="#94a3b8", size=11))
    return fig

def build_excel_report(stats, df_summary, df_daily, df_types, df_long_stock, df_yard, start_display, end_display):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        if stats is not None:
            pd.DataFrame([{
                "Từ ngày": start_display,
                "Đến ngày": end_display,
                "Tổng xe (toàn bộ)": safe_int(stats["total_vehicles"]),
                "Nhập trong kỳ": safe_int(stats["total_in_period"]),
                "Xuất trong kỳ": safe_int(stats["total_out_period"]),
                "Đang tồn kho": safe_int(stats["in_stock"]),
                "Đã xuất (tổng)": safe_int(stats["shipped"]),
            }]).to_excel(writer, sheet_name="KPI Tổng quan", index=False)
        if not df_summary.empty:
            df_summary.rename(columns={
                "owner": "Chủ hàng",
                "total_in": "Nhập trong kỳ",
                "total_out": "Xuất trong kỳ",
                "stock": "Tồn hiện tại",
            }).to_excel(writer, sheet_name="Theo Chủ hàng", index=False)
        if not df_daily.empty:
            df_export_daily = df_daily.copy()
            df_export_daily["date"] = pd.to_datetime(df_export_daily["date"], errors="coerce").dt.strftime("%d/%m/%Y")
            df_export_daily.rename(columns={
                "date": "Ngày",
                "type": "Loại",
                "count": "Số lượng",
            }).to_excel(writer, sheet_name="Biến động", index=False)
        if not df_types.empty:
            df_types.rename(columns={
                "vehicle_type": "Loại xe",
                "count": "Số lượng đang tồn",
            }).to_excel(writer, sheet_name="Theo loại xe", index=False)
        if not df_long_stock.empty:
            df_export_long = df_long_stock.copy()
            df_export_long["date_in"] = pd.to_datetime(df_export_long["date_in"], errors="coerce").dt.strftime("%d/%m/%Y")
            df_export_long.rename(columns={
                "vin": "Số khung (VIN)",
                "owner": "Chủ hàng",
                "vehicle_type": "Loại xe",
                "date_in": "Ngày nhập",
                "days_in_stock": "Số ngày tồn",
                "block": "Block",
                "slot": "Vị trí",
            }).to_excel(writer, sheet_name="Xe tồn lâu", index=False)
        if not df_yard.empty:
            df_yard.rename(columns={
                "block": "Block",
                "occupied": "Đang chiếm dụng",
                "total_slots": "Tổng vị trí",
            }).to_excel(writer, sheet_name="Bản đồ bãi", index=False)
    output.seek(0)
    return output.getvalue()

def render_yard_fill_cards(df_yard):
    cards = []
    for _, row in df_yard.iterrows():
        occupied = int(row["occupied"] or 0)
        total = int(row["total_slots"] or 0)
        pct = round((occupied / total * 100) if total > 0 else 0)
        color = COLORS["out"] if pct >= 75 else (COLORS["done"] if pct >= 55 else COLORS["stock"])
        cards.append(
            f"""
            <div class="vm-yard-card" style="--yard-color:{color};--yard-border:{color}30;--yard-bg:{color}07;--pct:{pct}%;">
                <div class="vm-yard-name">{escape(str(row["block"]))}</div>
                <div class="vm-yard-track"><div class="vm-yard-fill"></div></div>
                <div class="vm-yard-meta">
                    <span class="vm-yard-count">{fmt_number(occupied)} / {fmt_number(total)} xe</span>
                    <span class="vm-yard-pct">{pct}%</span>
                </div>
            </div>
            """
        )
    st.markdown(f"<div class='vm-yard-grid'>{''.join(cards)}</div>", unsafe_allow_html=True)

# ============================================
# STREAMLIT APP
# ============================================
def main():
    # Page config
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for professional look
    st.markdown("""
        <style>
        /* Main container */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        
        /* Metrics styling */
        div[data-testid="metric-container"] {
            background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
            border: 1px solid #e0e0e0;
            padding: 15px 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        div[data-testid="metric-container"] > div {
            font-size: 0.9rem;
        }
        
        div[data-testid="metric-container"] label {
            font-weight: 600;
            color: #333;
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 10px 20px;
            border-radius: 8px 8px 0 0;
            font-weight: 500;
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1e3a5f 0%, #2d5a87 100%);
        }
        
        [data-testid="stSidebar"] .stMarkdown {
            color: white;
        }
        
        /* Headers */
        h1, h2, h3 {
            color: #1e3a5f;
        }
        
        /* Divider */
        hr {
            margin: 1rem 0;
            border-color: #e0e0e0;
        }
        </style>
    """, unsafe_allow_html=True)
    inject_design_css()
    
    # Header
    header_placeholder = st.empty()
    
    # Sidebar filters
    with st.sidebar:
        if os.path.exists(LOGO_FILE):
            brand_logo, brand_text = st.columns([1, 3])
            with brand_logo:
                st.image(LOGO_FILE, width=46)
            with brand_text:
                st.markdown(
                    """
                    <div class="vm-sidebar-title">Vehicle Management</div>
                    <div class="vm-sidebar-subtitle">CSG SAIGON PORT · SINCE 1863</div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.markdown(
                """
                <div class="vm-sidebar-brand">
                    <div class="vm-sidebar-logo">🚗</div>
                    <div>
                        <div class="vm-sidebar-title">Vehicle Management</div>
                        <div class="vm-sidebar-subtitle">CSG SAIGON PORT · SINCE 1863</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        st.divider()
        
        # Get date range from database
        db_min_date, db_max_date = get_date_range_from_db()
        
        # Initialize session state for dates FIRST (use different keys than widget keys)
        if 'filter_start' not in st.session_state:
            st.session_state['filter_start'] = (datetime.now() - timedelta(days=30)).date()
        if 'filter_end' not in st.session_state:
            st.session_state['filter_end'] = datetime.now().date()
        
        # Quick date range buttons
        st.markdown("**⚡ Lọc nhanh**")
        quick_col1, quick_col2 = st.columns(2)
        with quick_col1:
            if st.button("7 ngày", use_container_width=True):
                st.session_state['filter_start'] = (datetime.now() - timedelta(days=7)).date()
                st.session_state['filter_end'] = datetime.now().date()
                st.rerun()
            if st.button("90 ngày", use_container_width=True):
                st.session_state['filter_start'] = (datetime.now() - timedelta(days=90)).date()
                st.session_state['filter_end'] = datetime.now().date()
                st.rerun()
        with quick_col2:
            if st.button("30 ngày", use_container_width=True):
                st.session_state['filter_start'] = (datetime.now() - timedelta(days=30)).date()
                st.session_state['filter_end'] = datetime.now().date()
                st.rerun()
            if st.button("Tất cả", use_container_width=True):
                if db_min_date:
                    st.session_state['filter_start'] = datetime.strptime(db_min_date, "%Y-%m-%d").date()
                else:
                    st.session_state['filter_start'] = (datetime.now() - timedelta(days=365)).date()
                st.session_state['filter_end'] = datetime.now().date()
                st.rerun()
        
        st.divider()
        
        # Date range picker
        st.markdown("**📅 Khoảng thời gian**")
        
        start_date = st.date_input(
            "Từ ngày",
            value=st.session_state['filter_start'],
            format="DD/MM/YYYY"
        )
        end_date = st.date_input(
            "Đến ngày",
            value=st.session_state['filter_end'],
            format="DD/MM/YYYY"
        )
        
        # Update session state when user changes date picker
        st.session_state['filter_start'] = start_date
        st.session_state['filter_end'] = end_date
        
        # Show database date range info - format dd/mm/yyyy
        if db_min_date and db_max_date:
            min_fmt = datetime.strptime(db_min_date, "%Y-%m-%d").strftime("%d/%m/%Y")
            max_fmt = datetime.strptime(db_max_date, "%Y-%m-%d").strftime("%d/%m/%Y")
            st.caption(f"📊 Dữ liệu từ: {min_fmt} đến {max_fmt}")
        
        st.divider()
        
        # Owner filter
        st.markdown("**👤 Chủ hàng**")
        owners = get_owners_list()
        selected_owner = st.selectbox(
            "Chủ hàng",
            ["Tất cả"] + owners,
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # Refresh button
        if st.button("🔄 Làm mới dữ liệu", use_container_width=True, type="primary"):
            st.rerun()
        
        st.divider()
        st.caption("💡 Dữ liệu realtime từ database")
        st.caption(f"🕐 {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}")
    
    # Convert dates to string for SQL
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    # Format dates for display (Vietnamese format)
    start_display = start_date.strftime("%d/%m/%Y")
    end_display = end_date.strftime("%d/%m/%Y")

    stats = get_summary_stats(start_str, end_str)
    df_summary_base = get_summary_by_owner_period(start_str, end_str)
    df_summary = df_summary_base.copy()
    if selected_owner != "Tất cả" and not df_summary.empty:
        df_summary = df_summary[df_summary['owner'] == selected_owner]
    df_owners = get_vehicles_by_owner(start_str, end_str)
    df_daily = get_daily_inbound_outbound(start_str, end_str)
    df_long_stock = get_long_stock_vehicles(5)
    df_types = get_vehicle_types()
    df_yard = get_yard_occupancy()
    excel_data = build_excel_report(
        stats,
        df_summary,
        df_daily,
        df_types,
        df_long_stock,
        df_yard,
        start_display,
        end_display
    )

    with header_placeholder.container():
        head_left, head_right = st.columns([5, 1])
        with head_left:
            st.markdown(
                f"""
                <div class="vm-topbar">
                    <div>
                        <h1>Vehicle Management Dashboard</h1>
                        <p>Hệ thống quản lý phương tiện · Cảng Tân Thuận – CSG Saigon Port</p>
                    </div>
                    <div class="vm-topbar-actions">
                        <div class="vm-chip vm-chip-blue">📅 Từ {start_display} đến {end_display}</div>
                        <div class="vm-chip vm-chip-gray"><span class="vm-live-dot"></span>Realtime</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with head_right:
            st.download_button(
                "⬇️ Xuất Excel",
                data=excel_data,
                file_name=f"BaoCao_VehicleManagement_{datetime.now().strftime('%d-%m-%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    
    # Show current filter period
    render_section_header("📊", "Chỉ số tổng quan", "Tổng hợp số liệu trong kỳ báo cáo đã chọn")
    
    # ==========================================
    # KEY METRICS ROW
    # ==========================================
    if stats is not None:
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            render_kpi_card("Tổng xe (toàn bộ)", stats['total_vehicles'], "🚗", COLORS["total"], "#f5f3ff", "Tất cả thời gian")
        
        with col2:
            render_kpi_card("Nhập trong kỳ", stats['total_in_period'], "📥", COLORS["in"], "#eff6ff", "Xe nhập trong kỳ")
        
        with col3:
            render_kpi_card("Xuất trong kỳ", stats['total_out_period'], "📤", COLORS["out"], "#fff1f2", "Xe xuất trong kỳ")
        
        with col4:
            render_kpi_card("Đang tồn kho", stats['in_stock'], "🏭", COLORS["stock"], "#ecfdf5", "Xe hiện trong bãi")
        
        with col5:
            render_kpi_card("Đã xuất (tổng)", stats['shipped'], "🚛", COLORS["done"], "#fffbeb", "Tổng xe đã giao")
    
    # ==========================================
    # MAIN TABS
    # ==========================================
    main_tab1, main_tab2 = st.tabs(["📊 Dashboard Tổng Quan", "🗺️ Bản đồ bãi xe"])
    
    with main_tab1:
        # Get data
        render_section_header("📈", "Phân tích theo Chủ hàng", "Số lượng nhập / xuất / tồn · Tỷ lệ tồn kho hiện tại")
        
        # ==========================================
        # CHARTS ROW
        # ==========================================
        col_left, col_right = st.columns([3, 2])
        
        with col_left:
            st.markdown(
                """
                <div class="vm-card-title">📊 Số lượng xe theo Chủ hàng</div>
                <div class="vm-card-subtitle">Phân tích nhập / xuất / tồn trong kỳ theo từng chủ hàng</div>
                """,
                unsafe_allow_html=True
            )
            
            if not df_summary.empty:
                # Create grouped bar chart
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    name='Nhập',
                    x=df_summary['owner'],
                    y=df_summary['total_in'],
                    marker_color=COLORS["in"],
                    text=df_summary['total_in'],
                    textposition='outside'
                ))
                
                fig.add_trace(go.Bar(
                    name='Xuất',
                    x=df_summary['owner'],
                    y=df_summary['total_out'],
                    marker_color=COLORS["out"],
                    text=df_summary['total_out'],
                    textposition='outside'
                ))
                
                fig.add_trace(go.Bar(
                    name='Tồn',
                    x=df_summary['owner'],
                    y=df_summary['stock'],
                    marker_color=COLORS["stock"],
                    text=df_summary['stock'],
                    textposition='outside'
                ))
                
                max_val = max(df_summary[['total_in', 'total_out', 'stock']].max())
                
                fig.update_layout(
                    barmode='group',
                    xaxis_title="",
                    yaxis_title="Số lượng xe",
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="center",
                        x=0.5
                    ),
                    yaxis=dict(
                        tickmode='linear',
                        tick0=0,
                        dtick=max(1, int(max_val / 5)) if max_val > 5 else 1,
                        rangemode='tozero',
                        range=[0, max_val * 1.2] if max_val > 0 else [0, 10]
                    )
                )
                apply_plotly_style(fig, height=360)
                
                fig.update_xaxes(tickangle=0 if len(df_summary) <= 5 else 45)
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📭 Không có dữ liệu trong khoảng thời gian này")
        
        with col_right:
            st.markdown(
                """
                <div class="vm-card-title">🥧 Tỷ lệ tồn kho theo Chủ hàng</div>
                <div class="vm-card-subtitle">Phân bố xe đang trong bãi</div>
                """,
                unsafe_allow_html=True
            )
            
            if not df_owners.empty and df_owners['in_stock'].sum() > 0:
                df_pie = df_owners[df_owners['in_stock'] > 0].copy()
                
                # Limit to top 10
                if len(df_pie) > 10:
                    others = df_pie.iloc[10:]['in_stock'].sum()
                    df_pie = df_pie.head(10)
                    df_pie = pd.concat([df_pie, pd.DataFrame({'owner': ['Khác'], 'in_stock': [others]})])
                
                fig_pie = px.pie(
                    df_pie,
                    values='in_stock',
                    names='owner',
                    hole=0.4,
                    color_discrete_sequence=[COLORS["stock"], COLORS["in"], COLORS["done"], COLORS["total"], COLORS["out"], "#06b6d4", "#ec4899"]
                )
                
                fig_pie.update_traces(
                    textposition='inside',
                    textinfo='percent+value',
                    textfont_size=11
                )
                fig_pie.update_layout(
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.3,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=10)
                    ),
                    margin=dict(l=20, r=20, t=40, b=80)
                )
                apply_plotly_style(fig_pie, height=360, legend_top=False)
                
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("📭 Không có xe tồn kho")
        
        st.divider()
        render_section_header("📋", "Biến động & Chi tiết dữ liệu", "Biến động nhập xuất theo ngày · Bảng phân tích chi tiết")
        
        # ==========================================
        # TIME SERIES CHART - Auto aggregate based on date range
        # ==========================================
        
        # Calculate number of days in range
        days_in_range = (end_date - start_date).days
        
        # Choose aggregation level based on date range
        if days_in_range <= 30:
            agg_level = "day"
            chart_title = "📈 Biến động theo ngày"
        elif days_in_range <= 90:
            agg_level = "week"
            chart_title = "📈 Biến động theo tuần"
        else:
            agg_level = "month"
            chart_title = "📈 Biến động theo tháng"
        
        st.markdown(f"<div class='vm-card-title'>{chart_title}</div>", unsafe_allow_html=True)
        
        if not df_daily.empty and len(df_daily) > 0:
            # Convert date column
            df_daily['date'] = pd.to_datetime(df_daily['date'])
            
            # Aggregate based on level
            if agg_level == "week":
                df_daily['period'] = df_daily['date'].dt.to_period('W').apply(lambda x: x.start_time)
                df_daily['period_label'] = df_daily['date'].dt.to_period('W').apply(
                    lambda x: f"T{x.week}\n{x.start_time.strftime('%d/%m')}"
                )
            elif agg_level == "month":
                df_daily['period'] = df_daily['date'].dt.to_period('M').apply(lambda x: x.start_time)
                df_daily['period_label'] = df_daily['date'].dt.strftime('%m/%Y')
            else:
                df_daily['period'] = df_daily['date']
                df_daily['period_label'] = df_daily['date'].dt.strftime('%d/%m')
            
            # Pivot and aggregate
            df_pivot = df_daily.pivot_table(
                index=['period', 'period_label'],
                columns='type',
                values='count',
                aggfunc='sum',
                fill_value=0
            ).reset_index()
            
            df_pivot = df_pivot.sort_values('period')
            
            # Ensure columns exist
            if 'Nhập' not in df_pivot.columns:
                df_pivot['Nhập'] = 0
            if 'Xuất' not in df_pivot.columns:
                df_pivot['Xuất'] = 0
            
            fig_ts = go.Figure()
            
            # Use different chart types based on data density
            if agg_level == "day" and len(df_pivot) <= 30:
                # Bar chart for daily data (up to 30 days)
                fig_ts.add_trace(go.Bar(
                    name='Nhập',
                    x=df_pivot['period_label'],
                    y=df_pivot['Nhập'],
                    marker_color=COLORS["in"],
                    text=df_pivot['Nhập'].apply(lambda x: str(int(x)) if x > 0 else ''),
                    textposition='outside'
                ))
                
                fig_ts.add_trace(go.Bar(
                    name='Xuất',
                    x=df_pivot['period_label'],
                    y=df_pivot['Xuất'],
                    marker_color=COLORS["out"],
                    text=df_pivot['Xuất'].apply(lambda x: str(int(x)) if x > 0 else ''),
                    textposition='outside'
                ))
                barmode = 'group'
            else:
                # Area chart for weekly/monthly aggregation
                fig_ts.add_trace(go.Scatter(
                    name='Nhập',
                    x=df_pivot['period_label'],
                    y=df_pivot['Nhập'],
                    mode='lines+markers',
                    fill='tozeroy',
                    fillcolor='rgba(59, 130, 246, 0.18)',
                    line=dict(color=COLORS["in"], width=2),
                    marker=dict(size=6)
                ))
                
                fig_ts.add_trace(go.Scatter(
                    name='Xuất',
                    x=df_pivot['period_label'],
                    y=df_pivot['Xuất'],
                    mode='lines+markers',
                    fill='tozeroy',
                    fillcolor='rgba(239, 68, 68, 0.18)',
                    line=dict(color=COLORS["out"], width=2),
                    marker=dict(size=6)
                ))
                barmode = None
            
            max_val = max(df_pivot[['Nhập', 'Xuất']].max()) if len(df_pivot) > 0 else 10
            
            layout_opts = {
                'xaxis_title': "Tuần" if agg_level == "week" else ("Tháng" if agg_level == "month" else "Ngày"),
                'yaxis_title': "Số lượng xe",
                'legend': dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5
                ),
                'xaxis': dict(
                    type='category',
                    tickangle=45 if len(df_pivot) > 10 else 0
                ),
                'yaxis': dict(
                    rangemode='tozero',
                    range=[0, max_val * 1.2] if max_val > 0 else [0, 10]
                ),
                'hovermode': 'x unified'
            }
            
            if barmode:
                layout_opts['barmode'] = barmode
            
            fig_ts.update_layout(**layout_opts)
            apply_plotly_style(fig_ts, height=320)
            
            st.plotly_chart(fig_ts, use_container_width=True)
            
            # Show aggregation info
            st.caption(f"📊 Hiển thị {len(df_pivot)} {'ngày' if agg_level == 'day' else ('tuần' if agg_level == 'week' else 'tháng')} | Tổng nhập: {int(df_pivot['Nhập'].sum())} | Tổng xuất: {int(df_pivot['Xuất'].sum())}")
        else:
            st.info("📭 Không có dữ liệu biến động trong khoảng thời gian này")
        
        st.divider()
        
        # ==========================================
        # DATA TABLES
        # ==========================================
        tab1, tab2, tab3 = st.tabs(["⚠️ Xe tồn lâu (>5 ngày)", "📋 Chi tiết theo Chủ hàng", "🚗 Theo loại xe"])
        
        with tab1:
            st.markdown("<div class='vm-card-title'>⚠️ Danh sách xe tồn bãi quá 5 ngày</div>", unsafe_allow_html=True)
            
            if not df_long_stock.empty:
                st.markdown(
                    f"<div class='vm-alert'>⚠️ Có <b>{len(df_long_stock)}</b> xe tồn bãi quá 5 ngày — cần kiểm tra và xử lý</div>",
                    unsafe_allow_html=True
                )
                df_long_stock_display = df_long_stock.copy()
                df_long_stock_display['date_in'] = pd.to_datetime(df_long_stock_display['date_in']).dt.strftime('%d/%m/%Y')
                
                st.dataframe(
                    df_long_stock_display,
                    column_config={
                        "vin": st.column_config.TextColumn("Số khung (VIN)", width="large"),
                        "owner": "Chủ hàng",
                        "vehicle_type": "Loại xe",
                        "date_in": "Ngày nhập",
                        "days_in_stock": st.column_config.NumberColumn(
                            "Số ngày",
                            format="%d",
                            help="Số ngày xe đã nằm trong bãi"
                        ),
                        "block": "Block",
                        "slot": "Vị trí"
                    },
                    hide_index=True,
                    use_container_width=True,
                    height=400
                )
            else:
                st.success("✅ Không có xe nào tồn quá 5 ngày")
        
        with tab2:
            st.markdown("<div class='vm-card-title'>📋 Bảng tổng hợp theo Chủ hàng</div>", unsafe_allow_html=True)
            
            if not df_summary.empty:
                df_display = df_summary.copy()
                
                # Add totals row
                totals = pd.DataFrame({
                    'owner': ['📊 TỔNG CỘNG'],
                    'total_in': [df_display['total_in'].sum()],
                    'total_out': [df_display['total_out'].sum()],
                    'stock': [df_display['stock'].sum()]
                })
                df_display = pd.concat([df_display, totals], ignore_index=True)
                
                st.dataframe(
                    df_display,
                    column_config={
                        "owner": st.column_config.TextColumn("Chủ hàng", width="medium"),
                        "total_in": st.column_config.NumberColumn("Nhập trong kỳ", format="%d"),
                        "total_out": st.column_config.NumberColumn("Xuất trong kỳ", format="%d"),
                        "stock": st.column_config.NumberColumn("Tồn hiện tại", format="%d")
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("📭 Không có dữ liệu")
        
        with tab3:
            st.markdown("<div class='vm-card-title'>🚗 Thống kê đang tồn theo loại xe</div>", unsafe_allow_html=True)
            
            if not df_types.empty:
                col_t1, col_t2 = st.columns([1, 2])
                
                with col_t1:
                    st.dataframe(
                        df_types,
                        column_config={
                            "vehicle_type": "Loại xe",
                            "count": st.column_config.NumberColumn("Số lượng", format="%d")
                        },
                        hide_index=True,
                        use_container_width=True,
                        height=len(df_types) * 35 + 38
                    )
                
                with col_t2:
                    max_count = df_types['count'].max()
                    
                    fig_types = px.bar(
                        df_types,
                        x='vehicle_type',
                        y='count',
                        color_discrete_sequence=[COLORS["stock"]],
                        text='count'
                    )
                    fig_types.update_layout(
                        xaxis_title="",
                        yaxis_title="Số lượng",
                        showlegend=False,
                        coloraxis_showscale=False,
                        height=300,
                        margin=dict(l=40, r=40, t=20, b=40),
                        yaxis=dict(
                            tickmode='linear',
                            tick0=0,
                            dtick=max(1, int(max_count / 5)) if max_count > 5 else 1,
                            rangemode='tozero'
                        )
                    )
                    apply_plotly_style(fig_types, height=340)
                    fig_types.update_traces(textposition='outside')
                    st.plotly_chart(fig_types, use_container_width=True)
            else:
                st.info("📭 Không có dữ liệu loại xe")
    
    # ==========================================
    # YARD MAP TAB
    # ==========================================
    with main_tab2:
        render_section_header("🗺️", "Bản đồ bãi xe", "Tình trạng chiếm dụng và tỷ lệ lấp đầy từng khu vực")
        
        if not df_yard.empty:
            # Summary metrics
            col_y1, col_y2, col_y3 = st.columns(3)
            total_occupied = int(df_yard['occupied'].sum())
            total_slots = int(df_yard['total_slots'].sum())
            occupancy_rate = (total_occupied / total_slots * 100) if total_slots > 0 else 0
            
            with col_y1:
                render_kpi_card("Xe trong bãi", total_occupied, "🚗", COLORS["in"], "#eff6ff", "Tổng xe có vị trí")
            with col_y2:
                render_kpi_card("Tổng vị trí", total_slots, "📍", COLORS["total"], "#f5f3ff", "Tổng slot trong bãi")
            with col_y3:
                render_kpi_card("Tỷ lệ lấp đầy", f"{occupancy_rate:.1f}%", "📊", COLORS["stock"], "#ecfdf5", "Phần trăm chiếm dụng")
            
            st.divider()
            
            st.markdown(
                """
                <div class="vm-card-title">📊 Tình trạng chiếm dụng theo Block</div>
                <div class="vm-card-subtitle">So sánh số xe đang chiếm dụng và tổng vị trí theo từng Block</div>
                """,
                unsafe_allow_html=True
            )
            max_slots = int(df_yard[['occupied', 'total_slots']].max().max())
            
            fig_yard = go.Figure()
            
            fig_yard.add_trace(go.Bar(
                x=df_yard['block'],
                y=df_yard['occupied'],
                marker_color=COLORS["in"],
                text=df_yard['occupied'].astype(int),
                textposition='outside',
                name='Đang chiếm dụng'
            ))
            fig_yard.add_trace(go.Bar(
                x=df_yard['block'],
                y=df_yard['total_slots'],
                marker_color='#e8edf5',
                text=df_yard['total_slots'].astype(int),
                textposition='outside',
                name='Tổng vị trí'
            ))
            
            fig_yard.update_layout(
                xaxis_title="Block",
                yaxis_title="Số xe",
                barmode='group',
                yaxis=dict(
                    tickmode='linear',
                    tick0=0,
                    dtick=max(1, int(max_slots / 5)) if max_slots > 5 else 1,
                    rangemode='tozero',
                    range=[0, max_slots * 1.2] if max_slots > 0 else [0, 10]
                )
            )
            apply_plotly_style(fig_yard, height=360)
            
            st.plotly_chart(fig_yard, use_container_width=True)

            st.markdown(
                """
                <div class="vm-card-title">🗺️ Bản đồ bãi – Tỷ lệ lấp đầy từng Block</div>
                <div class="vm-card-subtitle">Màu đỏ ≥ 75%, vàng ≥ 55%, xanh &lt; 55%</div>
                """,
                unsafe_allow_html=True
            )
            render_yard_fill_cards(df_yard)
            
            # Detail table
            st.divider()
            st.markdown("<div class='vm-card-title'>📋 Chi tiết xe trong bãi</div>", unsafe_allow_html=True)
            
            df_detail = get_yard_detail()
            if not df_detail.empty:
                df_occupied = df_detail[df_detail['vin'] != ''].copy()
                if not df_occupied.empty:
                    st.dataframe(
                        df_occupied,
                        column_config={
                            "block": "Block",
                            "slot": "Vị trí",
                            "vin": st.column_config.TextColumn("Số khung (VIN)", width="large"),
                            "owner": "Chủ hàng",
                            "vehicle_type": "Loại xe"
                        },
                        hide_index=True,
                        use_container_width=True,
                        height=400
                    )
                else:
                    st.info("📭 Không có xe nào trong bãi có vị trí")
        else:
            st.info("📭 Chưa thiết lập bản đồ bãi. Vui lòng thiết lập trong ứng dụng chính.")
    
    # Footer
    st.divider()
    st.markdown(
        f"<div style='text-align:center; color:#888; font-size:0.85rem;'>"
        f"🚗 <b>Vehicle Management System {APP_VERSION_DISPLAY}</b> | Tiền - Cảng Tân Thuận"
        f"</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
