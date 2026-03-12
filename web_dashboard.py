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
import os
from config import APP_VERSION_DISPLAY

# ============================================
# CONFIGURATION
# ============================================
DB_FILE = "vehicle_management_v1.0.db"
PAGE_TITLE = "🚗 Vehicle Management Dashboard"
PAGE_ICON = "🚗"

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
    
    # Header
    col_title, col_version = st.columns([4, 1])
    with col_title:
        st.title("🚗 Vehicle Management Dashboard")
    with col_version:
        st.markdown(f"<div style='text-align:right; padding-top:20px; color:#666;'></div>", unsafe_allow_html=True)
    
    st.divider()
    
    # Sidebar filters
    with st.sidebar:
        st.markdown("### 🔧 Bộ lọc dữ liệu")
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
    
    # Show current filter period
    st.markdown(f"<div style='text-align:center; padding:5px; background:#f0f2f6; border-radius:5px; margin-bottom:10px;'>"
                f"📅 <b>Từ {start_display} đến {end_display}</b></div>", unsafe_allow_html=True)
    
    # ==========================================
    # KEY METRICS ROW
    # ==========================================
    stats = get_summary_stats(start_str, end_str)
    
    if stats is not None:
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                label="📦 Tổng xe (toàn bộ)",
                value=f"{int(stats['total_vehicles']):,}"
            )
        
        with col2:
            st.metric(
                label="📥 Nhập trong kỳ",
                value=f"{int(stats['total_in_period']):,}"
            )
        
        with col3:
            st.metric(
                label="📤 Xuất trong kỳ",
                value=f"{int(stats['total_out_period']):,}"
            )
        
        with col4:
            st.metric(
                label="🏢 Đang tồn kho",
                value=f"{int(stats['in_stock']):,}"
            )
        
        with col5:
            st.metric(
                label="🚛 Đã xuất (tổng)",
                value=f"{int(stats['shipped']):,}"
            )
    
    st.divider()
    
    # ==========================================
    # MAIN TABS
    # ==========================================
    main_tab1, main_tab2 = st.tabs(["📊 Dashboard", "🗺️ Bản đồ bãi xe"])
    
    with main_tab1:
        # Get data
        df_summary = get_summary_by_owner_period(start_str, end_str)
        
        # Apply owner filter
        if selected_owner != "Tất cả" and not df_summary.empty:
            df_summary = df_summary[df_summary['owner'] == selected_owner]
        
        # ==========================================
        # CHARTS ROW
        # ==========================================
        col_left, col_right = st.columns([3, 2])
        
        with col_left:
            st.markdown("#### 📊 Chủ hàng")
            
            if not df_summary.empty:
                # Create grouped bar chart
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    name='Nhập',
                    x=df_summary['owner'],
                    y=df_summary['total_in'],
                    marker_color='#3498db',
                    text=df_summary['total_in'],
                    textposition='outside'
                ))
                
                fig.add_trace(go.Bar(
                    name='Xuất',
                    x=df_summary['owner'],
                    y=df_summary['total_out'],
                    marker_color='#e74c3c',
                    text=df_summary['total_out'],
                    textposition='outside'
                ))
                
                fig.add_trace(go.Bar(
                    name='Tồn',
                    x=df_summary['owner'],
                    y=df_summary['stock'],
                    marker_color='#2ecc71',
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
                    height=400,
                    margin=dict(l=40, r=40, t=60, b=40),
                    yaxis=dict(
                        tickmode='linear',
                        tick0=0,
                        dtick=max(1, int(max_val / 5)) if max_val > 5 else 1,
                        rangemode='tozero',
                        range=[0, max_val * 1.2] if max_val > 0 else [0, 10]
                    ),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                
                fig.update_xaxes(tickangle=0 if len(df_summary) <= 5 else 45)
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📭 Không có dữ liệu trong khoảng thời gian này")
        
        with col_right:
            st.markdown("#### 🥧 Tỷ lệ tồn kho theo Chủ hàng")
            
            df_owners = get_vehicles_by_owner(start_str, end_str)
            
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
                    color_discrete_sequence=px.colors.qualitative.Set3
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
                    height=400,
                    margin=dict(l=20, r=20, t=40, b=80)
                )
                
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("📭 Không có xe tồn kho")
        
        st.divider()
        
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
        
        st.markdown(f"#### {chart_title}")
        
        df_daily = get_daily_inbound_outbound(start_str, end_str)
        
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
                    marker_color='#3498db',
                    text=df_pivot['Nhập'].apply(lambda x: str(int(x)) if x > 0 else ''),
                    textposition='outside'
                ))
                
                fig_ts.add_trace(go.Bar(
                    name='Xuất',
                    x=df_pivot['period_label'],
                    y=df_pivot['Xuất'],
                    marker_color='#e74c3c',
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
                    fillcolor='rgba(52, 152, 219, 0.3)',
                    line=dict(color='#3498db', width=2),
                    marker=dict(size=6)
                ))
                
                fig_ts.add_trace(go.Scatter(
                    name='Xuất',
                    x=df_pivot['period_label'],
                    y=df_pivot['Xuất'],
                    mode='lines+markers',
                    fill='tozeroy',
                    fillcolor='rgba(231, 76, 60, 0.3)',
                    line=dict(color='#e74c3c', width=2),
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
                'height': 400,
                'margin': dict(l=40, r=40, t=60, b=60),
                'xaxis': dict(
                    type='category',
                    tickangle=45 if len(df_pivot) > 10 else 0
                ),
                'yaxis': dict(
                    rangemode='tozero',
                    range=[0, max_val * 1.2] if max_val > 0 else [0, 10]
                ),
                'plot_bgcolor': 'rgba(0,0,0,0)',
                'paper_bgcolor': 'rgba(0,0,0,0)',
                'hovermode': 'x unified'
            }
            
            if barmode:
                layout_opts['barmode'] = barmode
            
            fig_ts.update_layout(**layout_opts)
            
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
            st.markdown("##### ⚠️ Danh sách xe tồn bãi quá 5 ngày")
            
            df_long_stock = get_long_stock_vehicles(5)
            
            if not df_long_stock.empty:
                df_long_stock['date_in'] = pd.to_datetime(df_long_stock['date_in']).dt.strftime('%d/%m/%Y')
                
                st.dataframe(
                    df_long_stock,
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
                
                st.warning(f"⚠️ Có **{len(df_long_stock)}** xe tồn quá 5 ngày cần kiểm tra")
            else:
                st.success("✅ Không có xe nào tồn quá 5 ngày")
        
        with tab2:
            st.markdown("##### 📋 Bảng tổng hợp theo Chủ hàng")
            
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
            st.markdown("##### 🚗 Thống kê đang tồn")
            
            df_types = get_vehicle_types()
            
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
                        height=300
                    )
                
                with col_t2:
                    max_count = df_types['count'].max()
                    
                    fig_types = px.bar(
                        df_types,
                        x='vehicle_type',
                        y='count',
                        color='count',
                        color_continuous_scale='Blues',
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
                    fig_types.update_traces(textposition='outside')
                    st.plotly_chart(fig_types, use_container_width=True)
            else:
                st.info("📭 Không có dữ liệu loại xe")
    
    # ==========================================
    # YARD MAP TAB
    # ==========================================
    with main_tab2:
        st.markdown("#### 🗺️ Bản đồ bãi xe")
        st.caption("Tổng quan vị trí xe trong bãi theo từng Block")
        
        df_yard = get_yard_occupancy()
        
        if not df_yard.empty:
            # Summary metrics
            col_y1, col_y2, col_y3 = st.columns(3)
            total_occupied = int(df_yard['occupied'].sum())
            total_slots = int(df_yard['total_slots'].sum())
            total_blocks = len(df_yard)
            
            with col_y1:
                st.metric("🚗 Xe trong bãi", f"{total_occupied:,}")
            with col_y2:
                st.metric("📍 Tổng vị trí", f"{total_slots:,}")
            with col_y3:
                occupancy_rate = (total_occupied / total_slots * 100) if total_slots > 0 else 0
                st.metric("📊 Tỷ lệ lấp đầy", f"{occupancy_rate:.1f}%")
            
            st.divider()
            
            # Bar chart - full width
            max_occupied = int(df_yard['occupied'].max())
            
            fig_yard = go.Figure()
            
            fig_yard.add_trace(go.Bar(
                x=df_yard['block'],
                y=df_yard['occupied'],
                marker_color='#3498db',
                text=df_yard['occupied'].astype(int),
                textposition='outside',
                name='Số xe'
            ))
            
            fig_yard.update_layout(
                xaxis_title="Block",
                yaxis_title="Số xe",
                showlegend=False,
                height=450,
                margin=dict(l=40, r=40, t=40, b=40),
                yaxis=dict(
                    tickmode='linear',
                    tick0=0,
                    dtick=max(1, int(max_occupied / 5)) if max_occupied > 5 else 1,
                    rangemode='tozero',
                    range=[0, max_occupied * 1.2] if max_occupied > 0 else [0, 10]
                ),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig_yard, use_container_width=True)
            
            # Detail table
            st.divider()
            st.markdown("##### 📋 Chi tiết xe trong bãi")
            
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
