# -*- coding: utf-8 -*-
import io
import time
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_simulator import *
from database import *
from risk_engine import *
from system_monitor import *


def spacer(lines=1):
    for _ in range(lines):
        st.markdown("<br>", unsafe_allow_html=True)


def compute_sludge_metrics(sludge_grid, pond_size):
    avg = float(np.mean(sludge_grid))
    max_v = float(np.max(sludge_grid))
    critical_pct = float(np.sum(sludge_grid > 1.5) / sludge_grid.size * 100)
    est_volume = float(np.sum(sludge_grid) * (20 / pond_size) * (20 / pond_size))
    return {
        "avg": avg,
        "max": max_v,
        "critical_pct": critical_pct,
        "volume": est_volume,
    }


# ─── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DeepEcho · Water Intelligence",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Reset & base ── */
html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #020b18 0%, #051626 40%, #071f35 70%, #040d1a 100%);
    min-height: 100vh;
}

/* ── Animated background grid ── */
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(0,170,255,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,170,255,0.03) 1px, transparent 1px);
    background-size: 50px 50px;
    pointer-events: none;
    z-index: 0;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #030f1e 0%, #051a2e 100%) !important;
    border-right: 1px solid rgba(0,170,255,0.12) !important;
}

[data-testid="stSidebar"] * {
    color: #a8d4f5 !important;
}

[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stCheckbox label,
[data-testid="stSidebar"] .stNumberInput label {
    color: #7db8e8 !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}

[data-testid="stSidebar"] h3 {
    color: #00aaff !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}

[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
    background: rgba(0,100,180,0.15) !important;
    border: 1px solid rgba(0,170,255,0.2) !important;
    color: #a8d4f5 !important;
    border-radius: 8px !important;
}

/* ── Main content text ── */
h1, h2, h3, h4, p, label, div {
    color: #c8e6ff;
}

/* ── App header ── */
.app-header {
    background: linear-gradient(90deg, rgba(0,170,255,0.08) 0%, rgba(0,70,140,0.05) 100%);
    border: 1px solid rgba(0,170,255,0.15);
    border-radius: 16px;
    padding: 20px 30px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 16px;
    position: relative;
    overflow: hidden;
}

.app-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,170,255,0.6), transparent);
}

.app-header-title {
    font-size: 1.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #00aaff, #00e5ff, #ffffff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    letter-spacing: -0.02em;
}

.app-header-subtitle {
    font-size: 0.82rem;
    color: #5a9fd4;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.05em;
    margin: 0;
}

.live-dot {
    width: 10px;
    height: 10px;
    background: #00ff88;
    border-radius: 50%;
    display: inline-block;
    animation: pulse-dot 1.8s ease-in-out infinite;
    box-shadow: 0 0 8px #00ff88;
    margin-right: 6px;
}

@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.7); }
}

/* ── KPI Cards ── */
.kpi-card {
    background: linear-gradient(135deg, rgba(0,50,100,0.4) 0%, rgba(0,20,50,0.6) 100%);
    border: 1px solid rgba(0,170,255,0.18);
    border-radius: 14px;
    padding: 20px 22px;
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
}

.kpi-card::after {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px; height: 100%;
    background: linear-gradient(180deg, #00aaff, #0044aa);
    border-radius: 3px 0 0 3px;
}

.kpi-card.warning::after { background: linear-gradient(180deg, #ffaa00, #ff5500); }
.kpi-card.critical::after { background: linear-gradient(180deg, #ff3333, #aa0000); }
.kpi-card.success::after { background: linear-gradient(180deg, #00ff88, #00aa44); }

.kpi-label {
    font-size: 0.72rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #4a9fd4;
    font-weight: 600;
    margin-bottom: 8px;
}

.kpi-value {
    font-size: 1.9rem;
    font-weight: 700;
    color: #e8f4ff;
    font-family: 'JetBrains Mono', monospace;
    line-height: 1;
}

.kpi-delta {
    font-size: 0.78rem;
    color: #5ab8a0;
    margin-top: 6px;
    font-family: 'JetBrains Mono', monospace;
}

.kpi-icon {
    position: absolute;
    top: 16px; right: 18px;
    font-size: 1.6rem;
    opacity: 0.3;
}

/* ── Section headers ── */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 20px 0 14px 0;
    padding-bottom: 10px;
    border-bottom: 1px solid rgba(0,170,255,0.12);
}

.section-title {
    font-size: 1.0rem;
    font-weight: 600;
    color: #a8d4f5;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.section-badge {
    background: rgba(0,170,255,0.1);
    border: 1px solid rgba(0,170,255,0.25);
    color: #00aaff;
    font-size: 0.68rem;
    padding: 2px 8px;
    border-radius: 20px;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 500;
    letter-spacing: 0.05em;
}

/* ── Alert banner ── */
.alert-banner {
    border-radius: 12px;
    padding: 14px 20px;
    font-weight: 600;
    font-size: 0.9rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    text-align: center;
    position: relative;
    overflow: hidden;
}

.alert-critical {
    background: linear-gradient(90deg, rgba(180,0,0,0.3), rgba(255,50,50,0.15), rgba(180,0,0,0.3));
    border: 1px solid rgba(255,50,50,0.4);
    color: #ff6666;
    animation: shimmer 2s ease-in-out infinite;
}

.alert-warning {
    background: linear-gradient(90deg, rgba(140,80,0,0.3), rgba(255,160,0,0.15), rgba(140,80,0,0.3));
    border: 1px solid rgba(255,160,0,0.4);
    color: #ffcc44;
}

.alert-normal {
    background: linear-gradient(90deg, rgba(0,100,50,0.3), rgba(0,200,100,0.12), rgba(0,100,50,0.3));
    border: 1px solid rgba(0,200,100,0.3);
    color: #44ffaa;
}

@keyframes shimmer {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

/* ── Panel glass card ── */
.glass-panel {
    background: rgba(5,25,50,0.5);
    border: 1px solid rgba(0,170,255,0.12);
    border-radius: 16px;
    padding: 22px;
    backdrop-filter: blur(12px);
    margin-bottom: 16px;
}

/* ── Progress bars ── */
.health-bar-wrapper {
    margin-bottom: 14px;
}

.health-bar-label {
    display: flex;
    justify-content: space-between;
    font-size: 0.75rem;
    color: #5a9fd4;
    font-family: 'JetBrains Mono', monospace;
    margin-bottom: 5px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

.health-bar-track {
    height: 6px;
    background: rgba(0,80,160,0.2);
    border-radius: 6px;
    overflow: hidden;
}

.health-bar-fill {
    height: 100%;
    border-radius: 6px;
    transition: width 1s ease;
}

/* ── Metrics override ── */
[data-testid="stMetric"] {
    background: rgba(0,30,60,0.4) !important;
    border: 1px solid rgba(0,170,255,0.12) !important;
    border-radius: 12px !important;
    padding: 14px 16px !important;
}

[data-testid="stMetricLabel"] {
    color: #4a9fd4 !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    font-weight: 600 !important;
}

[data-testid="stMetricValue"] {
    color: #e8f4ff !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.5rem !important;
    font-weight: 700 !important;
}

[data-testid="stMetricDelta"] {
    font-size: 0.78rem !important;
}

/* ── Plotly chart backgrounds ── */
.js-plotly-plot {
    border-radius: 12px;
    overflow: hidden;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(0,170,255,0.12) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, rgba(0,100,200,0.4), rgba(0,60,140,0.6)) !important;
    border: 1px solid rgba(0,170,255,0.3) !important;
    color: #a8d4f5 !important;
    border-radius: 10px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    font-size: 0.8rem !important;
    padding: 10px 24px !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, rgba(0,140,255,0.5), rgba(0,80,180,0.7)) !important;
    border-color: rgba(0,200,255,0.5) !important;
    color: #ffffff !important;
    box-shadow: 0 0 20px rgba(0,150,255,0.2) !important;
}

/* ── Radio ── */
.stRadio > div {
    gap: 8px !important;
}

.stRadio > div > label {
    background: rgba(0,40,80,0.4) !important;
    border: 1px solid rgba(0,170,255,0.15) !important;
    border-radius: 8px !important;
    padding: 6px 14px !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    font-size: 0.82rem !important;
    color: #7db8e8 !important;
}

.stRadio > div > label:has(input:checked) {
    background: rgba(0,100,200,0.3) !important;
    border-color: rgba(0,170,255,0.5) !important;
    color: #00aaff !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(0,20,45,0.6) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid rgba(0,170,255,0.1) !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 8px !important;
    color: #5a9fd4 !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}

.stTabs [aria-selected="true"] {
    background: rgba(0,100,200,0.3) !important;
    color: #00aaff !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: rgba(0,30,65,0.4) !important;
    border: 1px solid rgba(0,170,255,0.12) !important;
    border-radius: 10px !important;
    color: #7db8e8 !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
}

/* ── Divider ── */
hr {
    border-color: rgba(0,170,255,0.1) !important;
    margin: 24px 0 !important;
}

/* ── Sidebar logo area ── */
.sidebar-logo {
    text-align: center;
    padding: 8px 0 20px 0;
    border-bottom: 1px solid rgba(0,170,255,0.1);
    margin-bottom: 20px;
}

.sidebar-logo-text {
    font-size: 1.2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #00aaff, #00e5ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.01em;
}

.sidebar-logo-sub {
    font-size: 0.68rem;
    color: #3a6d9a !important;
    letter-spacing: 0.15em;
    text-transform: uppercase;
}

/* ── Sidebar number input ── */
[data-testid="stSidebar"] [data-testid="stNumberInput"] input {
    background: rgba(0,60,120,0.2) !important;
    border: 1px solid rgba(0,170,255,0.2) !important;
    color: #a8d4f5 !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
}

/* ── Treatment table ── */
.treatment-row {
    background: rgba(0,30,65,0.5);
    border: 1px solid rgba(0,170,255,0.1);
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 14px;
    transition: border-color 0.2s ease;
}

.treatment-row:hover {
    border-color: rgba(0,170,255,0.3);
}

.treatment-action {
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #00aaff;
    min-width: 140px;
}

.treatment-rec {
    font-size: 0.88rem;
    color: #c8e6ff;
    flex: 1;
}

.treatment-timeline {
    font-size: 0.72rem;
    color: #4a9fd4;
    font-family: 'JetBrains Mono', monospace;
    background: rgba(0,100,200,0.12);
    border: 1px solid rgba(0,170,255,0.15);
    padding: 3px 10px;
    border-radius: 20px;
    white-space: nowrap;
}

.reason-code {
    font-size: 0.68rem;
    font-family: 'JetBrains Mono', monospace;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 600;
    white-space: nowrap;
}

.rc-ok { background: rgba(0,200,100,0.12); color: #00cc66; border: 1px solid rgba(0,200,100,0.2); }
.rc-warn { background: rgba(255,160,0,0.12); color: #ffaa00; border: 1px solid rgba(255,160,0,0.25); }
.rc-crit { background: rgba(255,50,50,0.12); color: #ff4444; border: 1px solid rgba(255,50,50,0.25); }

/* ── Glow effects for specific cards ── */
.glow-blue { box-shadow: 0 0 30px rgba(0,100,200,0.08); }

/* ── Caption ── */
.custom-caption {
    font-size: 0.72rem;
    color: #3a6d9a;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.04em;
    margin-top: 8px;
    padding: 10px 14px;
    background: rgba(0,20,45,0.4);
    border-left: 2px solid rgba(0,170,255,0.2);
    border-radius: 0 6px 6px 0;
}
</style>
""", unsafe_allow_html=True)

# ─── Init ───────────────────────────────────────────────────────────────────
init_db()

# ─── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <div class="sidebar-logo-text">🌊 DeepEcho</div>
        <div class="sidebar-logo-sub">Edge-AI · Water Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### ⚙ System Controls")
    mode = st.selectbox("Operation Mode", ["Monitoring", "Survey", "Calibration"])
    auto_refresh = st.checkbox("Auto Refresh (2s)", True)

    st.markdown("---")
    st.markdown("### 📍 GPS Location")
    gps_lat = st.number_input("Latitude", value=16.5062, format="%.6f")
    gps_lon = st.number_input("Longitude", value=80.6480, format="%.6f")
    st.markdown(f"""<div style="font-size:0.72rem;color:#3a7a9a;font-family:'JetBrains Mono',monospace;padding:6px 0;">
        📌 {gps_lat:.6f}°N · {gps_lon:.6f}°E</div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🗺 Display Options")
    show_survey_path = st.checkbox("Show Survey Path", True)
    show_gps_overlay = st.checkbox("Show GPS Map", False)

    st.markdown("---")
    st.markdown("""<div style="font-size:0.68rem;color:#2a5a7a;font-family:'JetBrains Mono',monospace;line-height:1.8;">
    v2.1.0 · build 20240612<br>
    Sensor sync: <span style="color:#00ff88;">ONLINE</span><br>
    DB: <span style="color:#00ff88;">CONNECTED</span><br>
    Edge AI: <span style="color:#00aaff;">ACTIVE</span>
    </div>""", unsafe_allow_html=True)

# ─── Data generation ────────────────────────────────────────────────────────
time_offset = time.time() * 0.5
X, Y, base, sludge, water_surface = generate_pond_surface(time_offset)
env = generate_environment()
ammonia_df = generate_time_series()

from data_simulator import generate_gps_grid, generate_survey_path, get_sludge_hotspots
X_local, Y_local, LAT, LON = generate_gps_grid()
survey_x, survey_y, survey_lat, survey_lon = generate_survey_path()
hotspots = get_sludge_hotspots(X, Y, sludge)

hypoxia = calculate_hypoxia_risk(env)
ammonia_peak = ammonia_df["ammonia"].max()
alert = generate_alert(hypoxia, ammonia_peak)

insert_measurement({
    "temperature": env["temperature"],
    "turbidity": env["turbidity"],
    "organic_ratio": env["organic_ratio"],
    "hypoxia": hypoxia,
    "ammonia_peak": ammonia_peak,
    "alert": alert,
})

DEG = chr(176)
sludge_metrics = compute_sludge_metrics(sludge, POND_SIZE)
avg_sludge = sludge_metrics["avg"]
max_sludge = sludge_metrics["max"]
critical_area = sludge_metrics["critical_pct"]
total_volume = sludge_metrics["volume"]

# ─── App header ─────────────────────────────────────────────────────────────
alert_color = {"CRITICAL": "#ff4444", "WARNING": "#ffaa00", "NORMAL": "#00ff88"}.get(alert, "#00ff88")
st.markdown(f"""
<div class="app-header">
    <div>
        <div class="app-header-title">🌊 DeepEcho Water Intelligence</div>
        <div class="app-header-subtitle">
            <span class="live-dot"></span>
            LIVE · {mode.upper()} MODE · {gps_lat:.4f}°N {gps_lon:.4f}°E
        </div>
    </div>
    <div style="margin-left:auto;text-align:right;">
        <div style="font-size:0.7rem;color:#3a6d9a;font-family:'JetBrains Mono',monospace;letter-spacing:0.08em;">SYSTEM ALERT</div>
        <div style="font-size:1.3rem;font-weight:700;color:{alert_color};font-family:'JetBrains Mono',monospace;letter-spacing:0.1em;">{alert}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── KPI Row ─────────────────────────────────────────────────────────────────
kpi_cols = st.columns(6)

def kpi_card(col, icon, label, value, sub, card_class=""):
    col.markdown(f"""
    <div class="kpi-card {card_class}">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-delta">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

kpi_card(kpi_cols[0], "🌡", "Temperature", f"{env['temperature']:.1f}°C", f"Turbidity {env['turbidity']:.1f} NTU")
kpi_card(kpi_cols[1], "💧", "Hypoxia Risk", f"{hypoxia:.3f}",
         "HIGH RISK" if hypoxia > HYPOXIA_CRITICAL else ("MODERATE" if hypoxia > HYPOXIA_WARNING else "NORMAL"),
         "critical" if hypoxia > HYPOXIA_CRITICAL else ("warning" if hypoxia > HYPOXIA_WARNING else "success"))
kpi_card(kpi_cols[2], "⚗", "Ammonia Peak", f"{ammonia_peak:.2f}",
         "mg/L · " + ("CRITICAL" if ammonia_peak > AMMONIA_CRITICAL else ("WARNING" if ammonia_peak > AMMONIA_WARNING else "OK")),
         "critical" if ammonia_peak > AMMONIA_CRITICAL else ("warning" if ammonia_peak > AMMONIA_WARNING else "success"))
kpi_card(kpi_cols[3], "📊", "Avg Sludge", f"{avg_sludge:.2f}m", f"Δ {avg_sludge-1.2:+.2f}m vs baseline",
         "warning" if avg_sludge > 1.2 else "success")
kpi_card(kpi_cols[4], "⚠", "Critical Area", f"{critical_area:.1f}%", "Sludge depth > 1.5m",
         "critical" if critical_area > 30 else ("warning" if critical_area > 15 else "success"))
kpi_card(kpi_cols[5], "📦", "Est. Volume", f"{total_volume:.1f}m³", "Accumulated sludge")

spacer()

# ─── Main layout ────────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 1], gap="medium")

# ─── 3D Map Panel ─────────────────────────────────────────────────────────
with col_left:
    st.markdown("""<div class="section-header">
        <div class="section-title">🗺 3D Pond Bathymetry & Sludge Analysis</div>
        <div class="section-badge">REAL-TIME</div>
    </div>""", unsafe_allow_html=True)

    viz_mode = st.radio("View Mode", ["Sludge Depth", "Bottom Terrain", "Combined"], horizontal=True)

    PLOTLY_LAYOUT = dict(
        paper_bgcolor='rgba(2,10,22,0)',
        plot_bgcolor='rgba(2,10,22,0)',
        font=dict(family='Space Grotesk', color='#7db8e8', size=11),
        height=520,
        margin=dict(l=0, r=0, t=20, b=0),
        showlegend=False,
        scene=dict(
            xaxis=dict(title=dict(text='Length (m)', font=dict(color='#4a9fd4')),
                       backgroundcolor="rgba(0,20,50,0.6)",
                       gridcolor="rgba(0,100,200,0.15)", showbackground=True,
                       tickfont=dict(color='#4a9fd4')),
            yaxis=dict(title=dict(text='Width (m)', font=dict(color='#4a9fd4')),
                       backgroundcolor="rgba(0,20,50,0.6)",
                       gridcolor="rgba(0,100,200,0.15)", showbackground=True,
                       tickfont=dict(color='#4a9fd4')),
            zaxis=dict(title=dict(text='Depth (m)', font=dict(color='#4a9fd4')),
                       backgroundcolor="rgba(0,10,35,0.6)",
                       gridcolor="rgba(0,80,180,0.12)", showbackground=True,
                       tickfont=dict(color='#4a9fd4')),
            camera=dict(eye=dict(x=1.6, y=1.6, z=1.2), center=dict(x=0, y=0, z=-0.1)),
            aspectmode='manual',
            aspectratio=dict(x=1, y=1, z=0.4),
            bgcolor='rgba(2,10,22,0.8)'
        ),
    )

    if viz_mode == "Sludge Depth":
        surface = go.Surface(
            x=X, y=Y, z=base - sludge,
            surfacecolor=sludge,
            colorscale=[[0,'#1a3a5c'],[0.2,'#8B6914'],[0.4,'#C8891A'],
                        [0.6,'#A0522D'],[0.8,'#7B3B1A'],[1,'#4a1a00']],
            colorbar=dict(title=dict(text="Sludge (m)", font=dict(color='#7db8e8', size=11)),
                          tickfont=dict(color='#7db8e8'), x=1.0, thickness=12,
                          bgcolor='rgba(0,10,25,0.5)', bordercolor='rgba(0,170,255,0.2)'),
            contours=dict(z=dict(show=True, usecolormap=False, color='rgba(255,255,255,0.15)',
                                 width=1, project=dict(z=True))),
            lighting=dict(ambient=0.5, diffuse=0.8, specular=0.6, roughness=0.4, fresnel=0.5),
            lightposition=dict(x=50, y=50, z=200),
            hovertemplate='<b>X:</b> %{x:.1f}m<br><b>Y:</b> %{y:.1f}m<br><b>Sludge:</b> %{surfacecolor:.2f}m<extra></extra>'
        )
        water = go.Surface(
            x=X, y=Y, z=water_surface,
            opacity=0.18,
            colorscale=[[0,'rgba(0,120,200,0.4)'],[1,'rgba(0,160,255,0.4)']],
            showscale=False, hoverinfo='skip',
            lighting=dict(ambient=0.3, diffuse=0.5, specular=0.9, fresnel=0.9)
        )
        data_traces = [surface, water]
        if hotspots:
            hx = [h['x'] for h in hotspots]
            hy = [h['y'] for h in hotspots]
            hz = [base[np.argmin(np.abs(X[0]-h['x'])), np.argmin(np.abs(Y[:,0]-h['y']))] for h in hotspots]
            markers = go.Scatter3d(
                x=hx, y=hy, z=hz, mode='markers+text',
                marker=dict(size=12, color='#ff3333', symbol='diamond',
                            line=dict(color='#ffdd00', width=2),
                            opacity=0.9),
                text=['⚠'] * len(hotspots), textposition='top center',
                textfont=dict(size=18, color='#ff4444'),
                hovertext=[f"<b>{h['severity']}</b><br>Sludge: {h['z']:.2f}m<br>{h['lat']:.6f}°N, {h['lon']:.6f}°E" for h in hotspots],
                hoverinfo='text', name='Critical Zones'
            )
            data_traces.append(markers)
        if show_survey_path:
            sp = go.Scatter3d(
                x=survey_x+10, y=survey_y+10,
                z=[np.max(base)+0.5]*len(survey_x),
                mode='lines', line=dict(color='#00e5ff', width=3, dash='dot'),
                name='Survey Path', hoverinfo='skip'
            )
            data_traces.append(sp)
        fig = go.Figure(data=data_traces)

    elif viz_mode == "Bottom Terrain":
        surface = go.Surface(
            x=X, y=Y, z=base,
            colorscale=[[0,'#0a1a30'],[0.3,'#1a3a60'],[0.6,'#2a6090'],[1,'#4a90c0']],
            colorbar=dict(title=dict(text="Elevation (m)", font=dict(color='#7db8e8')),
                          tickfont=dict(color='#7db8e8'), x=1.0, thickness=12),
            contours=dict(z=dict(show=True, usecolormap=True,
                                 highlightcolor="rgba(0,200,255,0.4)", project=dict(z=True))),
            lighting=dict(ambient=0.55, diffuse=0.85, specular=0.4)
        )
        fig = go.Figure(data=[surface])

    else:
        terrain = go.Surface(x=X, y=Y, z=base,
            colorscale=[[0,'#0a1525'],[1,'#1a4060']], opacity=0.65, showscale=False)
        sludge_layer = go.Surface(x=X, y=Y, z=base-sludge, surfacecolor=sludge,
            colorscale=[[0,'rgba(40,100,160,0.8)'],[0.5,'rgba(180,90,20,0.85)'],[1,'rgba(80,30,5,0.9)']],
            colorbar=dict(title=dict(text="Sludge (m)", font=dict(color='#7db8e8')),
                          tickfont=dict(color='#7db8e8'), x=1.0, thickness=12))
        water = go.Surface(x=X, y=Y, z=water_surface, opacity=0.15,
            colorscale=[[0,'rgba(0,120,220,0.2)'],[1,'rgba(0,180,255,0.2)']], showscale=False)
        fig = go.Figure(data=[terrain, sludge_layer, water])

    fig.update_layout(**PLOTLY_LAYOUT)
    st.plotly_chart(fig, width='stretch', config=dict(displayModeBar=True,
        modeBarButtonsToRemove=['sendDataToCloud'], displaylogo=False))

    # Sludge metrics strip
    m1, m2, m3, m4 = st.columns(4)
    delta_color = "normal" if avg_sludge <= 1.2 else "inverse"
    m1.metric("Avg Sludge Depth", f"{avg_sludge:.2f} m", f"{avg_sludge-1.2:+.2f}m vs baseline", delta_color=delta_color)
    m2.metric("Max Sludge Depth", f"{max_sludge:.2f} m")
    m3.metric("Critical Area (>1.5m)", f"{critical_area:.1f}%",
              "High" if critical_area > 30 else "Normal", delta_color="inverse" if critical_area > 30 else "off")
    m4.metric("Est. Sludge Volume", f"{total_volume:.1f} m³")

    # GPS Overlay
    if show_gps_overlay:
        st.markdown("""<div class="section-header" style="margin-top:24px;">
            <div class="section-title">📍 GPS-Referenced Map</div>
            <div class="section-badge">WGS-84</div>
        </div>""", unsafe_allow_html=True)
        gps_fig = go.Figure()
        gps_fig.add_trace(go.Contour(
            x=LON[0,:], y=LAT[:,0], z=sludge,
            colorscale=[[0,'#1a3a5c'],[0.5,'#C8891A'],[1,'#4a1a00']],
            colorbar=dict(title=dict(text="Sludge (m)", font=dict(color='#7db8e8')),
                          tickfont=dict(color='#7db8e8')),
            contours=dict(showlabels=True, labelfont=dict(size=9, color='rgba(255,255,255,0.6)'))
        ))
        if show_survey_path:
            gps_fig.add_trace(go.Scatter(
                x=survey_lon, y=survey_lat, mode='lines+markers',
                line=dict(color='#00e5ff', width=2), marker=dict(size=4, color='#00e5ff'),
                name='Survey Path'
            ))
        if hotspots:
            gps_fig.add_trace(go.Scatter(
                x=[h['lon'] for h in hotspots], y=[h['lat'] for h in hotspots],
                mode='markers+text',
                marker=dict(size=14, color='#ff3333', symbol='star',
                            line=dict(color='#ffdd00', width=2)),
                text=['⚠']*len(hotspots), textposition='top center',
                textfont=dict(size=14, color='#ff4444'),
                hovertext=[f"<b>{h['severity']}</b><br>{h['lat']:.6f}°N<br>{h['lon']:.6f}°E" for h in hotspots],
                name='Hotspots'
            ))
        gps_fig.update_layout(
            paper_bgcolor='rgba(2,10,22,0)', plot_bgcolor='rgba(0,15,35,0.5)',
            font=dict(family='Space Grotesk', color='#7db8e8'),
            xaxis=dict(title='Longitude (°E)', gridcolor='rgba(0,100,200,0.12)',
                       zerolinecolor='rgba(0,100,200,0.2)'),
            yaxis=dict(title='Latitude (°N)', gridcolor='rgba(0,100,200,0.12)',
                       zerolinecolor='rgba(0,100,200,0.2)'),
            height=360, hovermode='closest',
            legend=dict(bgcolor='rgba(0,20,50,0.7)', bordercolor='rgba(0,170,255,0.2)',
                        borderwidth=1, font=dict(color='#7db8e8'))
        )
        st.plotly_chart(gps_fig, width='stretch')
        with st.expander("📊 GPS Hotspot Coordinates"):
            if hotspots:
                gps_df = pd.DataFrame([{
                    'Severity': h['severity'],
                    'Latitude': f"{h['lat']:.6f}°N",
                    'Longitude': f"{h['lon']:.6f}°E",
                    'Sludge Depth': f"{h['z']:.2f}m"
                } for h in hotspots])
                st.dataframe(gps_df, width='stretch', hide_index=True)
            else:
                st.info("No critical hotspots detected")

# ─── Right Panel ─────────────────────────────────────────────────────────────
with col_right:
    # Hypoxia gauge
    st.markdown("""<div class="section-header">
        <div class="section-title">⚡ Risk Gauge</div>
    </div>""", unsafe_allow_html=True)

    gauge_color = "#ff3333" if hypoxia > HYPOXIA_CRITICAL else ("#ffaa00" if hypoxia > HYPOXIA_WARNING else "#00cc66")
    gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=hypoxia,
        delta=dict(reference=HYPOXIA_WARNING, valueformat='.3f',
                   increasing=dict(color='#ff4444'), decreasing=dict(color='#00cc66')),
        title=dict(text="Hypoxia Risk Index", font=dict(color='#7db8e8', size=12, family='Space Grotesk')),
        number=dict(font=dict(color=gauge_color, size=36, family='JetBrains Mono'), valueformat='.3f'),
        gauge=dict(
            axis=dict(range=[0, 1], tickwidth=1, tickcolor='rgba(0,170,255,0.4)',
                      tickfont=dict(color='#4a9fd4', size=9)),
            bar=dict(color=gauge_color, thickness=0.25),
            bgcolor='rgba(0,20,50,0.4)',
            borderwidth=1, bordercolor='rgba(0,170,255,0.2)',
            steps=[
                dict(range=[0, HYPOXIA_WARNING], color='rgba(0,150,80,0.15)'),
                dict(range=[HYPOXIA_WARNING, HYPOXIA_CRITICAL], color='rgba(200,120,0,0.15)'),
                dict(range=[HYPOXIA_CRITICAL, 1], color='rgba(200,30,30,0.15)')
            ],
            threshold=dict(line=dict(color='rgba(255,200,0,0.7)', width=2),
                           thickness=0.75, value=HYPOXIA_CRITICAL)
        )
    ))
    gauge.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', font=dict(family='Space Grotesk'),
        height=220, margin=dict(l=10, r=10, t=30, b=5)
    )
    st.plotly_chart(gauge, width='stretch')

    # Ammonia mini gauge
    st.markdown("""<div class="section-header">
        <div class="section-title">⚗ Ammonia Level</div>
    </div>""", unsafe_allow_html=True)
    amm_color = "#ff3333" if ammonia_peak > AMMONIA_CRITICAL else ("#ffaa00" if ammonia_peak > AMMONIA_WARNING else "#00cc66")
    amm_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=ammonia_peak,
        title=dict(text="Peak (mg/L)", font=dict(color='#7db8e8', size=11, family='Space Grotesk')),
        number=dict(font=dict(color=amm_color, size=28, family='JetBrains Mono'), valueformat='.2f',
                    suffix=' mg/L'),
        gauge=dict(
            axis=dict(range=[0, max(5, ammonia_peak*1.4)],
                      tickfont=dict(color='#4a9fd4', size=9)),
            bar=dict(color=amm_color, thickness=0.25),
            bgcolor='rgba(0,20,50,0.4)', borderwidth=1,
            bordercolor='rgba(0,170,255,0.2)',
            steps=[
                dict(range=[0, AMMONIA_WARNING], color='rgba(0,150,80,0.15)'),
                dict(range=[AMMONIA_WARNING, AMMONIA_CRITICAL], color='rgba(200,120,0,0.15)'),
                dict(range=[AMMONIA_CRITICAL, max(5, ammonia_peak*1.4)], color='rgba(200,30,30,0.15)')
            ],
        )
    ))
    amm_gauge.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', font=dict(family='Space Grotesk'),
        height=180, margin=dict(l=10, r=10, t=25, b=5)
    )
    st.plotly_chart(amm_gauge, width='stretch')

# ─── Water Quality + System Health Row ─────────────────────────────────────
spacer()
aux_left, aux_right = st.columns([2, 1], gap="medium")

# Normalise each parameter to 0-1 where 1.0 = at its safe threshold
TEMP_THRESHOLD    = 32.0
TURB_THRESHOLD    = 50.0
HYPOXIA_THRESH    = float(HYPOXIA_CRITICAL)
AMMONIA_THRESH    = float(AMMONIA_CRITICAL)
ORGANIC_THRESHOLD = 0.5
SLUDGE_THRESHOLD  = 1.5

radar_params = ["Temperature", "Turbidity", "Hypoxia", "Ammonia", "Organic\nRatio", "Sludge\nDepth"]
raw_vals     = [env["temperature"], env["turbidity"], hypoxia, ammonia_peak,
                env["organic_ratio"], avg_sludge]
thresholds   = [TEMP_THRESHOLD, TURB_THRESHOLD, HYPOXIA_THRESH,
                AMMONIA_THRESH, ORGANIC_THRESHOLD, SLUDGE_THRESHOLD]

with aux_left:
    st.markdown("""<div class="section-header">
        <div class="section-title">🕸 Water Quality Radar</div>
        <div class="section-badge">VS THRESHOLD</div>
    </div>""", unsafe_allow_html=True)

    norm_vals        = [min(v / t, 1.4) for v, t in zip(raw_vals, thresholds)]
    norm_vals_closed = norm_vals + [norm_vals[0]]
    thresh_closed    = [1.0] * len(radar_params) + [1.0]
    params_closed    = radar_params + [radar_params[0]]

    max_norm = max(norm_vals)
    if max_norm >= 1.0:
        fill_color, line_color, marker_color = "rgba(255,50,50,0.15)", "#ff4444", "#ff4444"
    elif max_norm >= 0.75:
        fill_color, line_color, marker_color = "rgba(255,170,0,0.13)", "#ffaa00", "#ffaa00"
    else:
        fill_color, line_color, marker_color = "rgba(0,200,120,0.12)", "#00cc66", "#00cc66"

    radar_fig = go.Figure()
    radar_fig.add_trace(go.Scatterpolar(
        r=thresh_closed, theta=params_closed, mode='lines',
        line=dict(color='rgba(255,200,0,0.35)', width=1.5, dash='dot'),
        name='Safe Threshold', hoverinfo='skip',
    ))
    radar_fig.add_trace(go.Scatterpolar(
        r=norm_vals_closed, theta=params_closed,
        mode='lines+markers', fill='toself', fillcolor=fill_color,
        line=dict(color=line_color, width=2),
        marker=dict(color=marker_color, size=6, line=dict(color='rgba(0,0,0,0.4)', width=1)),
        name='Current Reading',
        hovertemplate='<b>%{theta}</b><br>Score: %{r:.2f}× threshold<extra></extra>',
    ))
    radar_fig.update_layout(
        polar=dict(
            bgcolor='rgba(0,15,35,0.6)',
            angularaxis=dict(tickfont=dict(size=9, color='#5a9fd4', family='Space Grotesk'),
                             linecolor='rgba(0,170,255,0.12)', gridcolor='rgba(0,100,200,0.12)'),
            radialaxis=dict(range=[0, 1.4],
                            tickvals=[0.25, 0.5, 0.75, 1.0, 1.25],
                            ticktext=['25%', '50%', '75%', '100%', '125%'],
                            tickfont=dict(size=8, color='#3a6d9a', family='JetBrains Mono'),
                            gridcolor='rgba(0,100,200,0.1)', linecolor='rgba(0,170,255,0.1)', angle=90),
        ),
        paper_bgcolor='rgba(0,0,0,0)', font=dict(family='Space Grotesk', color='#7db8e8'),
        height=280, margin=dict(l=30, r=30, t=10, b=10), showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=-0.12, xanchor='center', x=0.5,
                    font=dict(size=9, color='#5a9fd4'), bgcolor='rgba(0,0,0,0)'),
    )
    st.plotly_chart(radar_fig, width='stretch', config=dict(displayModeBar=False))

    # Per-param status pills below the radar
    pill_cols = st.columns(3)
    param_labels = ["Temp", "Turbidity", "Hypoxia", "Ammonia", "Organic", "Sludge"]
    param_units  = ["°C", "NTU", "", "mg/L", "", "m"]
    for i, (label, raw, thresh, unit) in enumerate(zip(param_labels, raw_vals, thresholds, param_units)):
        ratio = raw / thresh
        pct   = ratio * 100
        if ratio >= 1.0:
            bg, fg = "rgba(255,50,50,0.15)", "#ff4444"
        elif ratio >= 0.75:
            bg, fg = "rgba(255,160,0,0.15)", "#ffaa00"
        else:
            bg, fg = "rgba(0,180,90,0.12)", "#00cc66"
        pill_cols[i % 3].markdown(f"""
        <div style="background:{bg};border:1px solid {fg}44;border-radius:8px;
                    padding:6px 8px;margin-bottom:6px;text-align:center;">
            <div style="font-size:0.65rem;color:#4a9fd4;letter-spacing:0.08em;
                        text-transform:uppercase;font-weight:600;">{label}</div>
            <div style="font-size:0.92rem;color:{fg};font-family:'JetBrains Mono',monospace;
                        font-weight:700;line-height:1.2;">{raw:.2f}<span style="font-size:0.6rem;color:#3a6d9a;"> {unit}</span></div>
            <div style="font-size:0.62rem;color:{fg};opacity:0.8;">{pct:.0f}% of limit</div>
        </div>
        """, unsafe_allow_html=True)

with aux_right:
    st.markdown("""<div class="section-header">
        <div class="section-title">🖥 System Health</div>
    </div>""", unsafe_allow_html=True)
    health = get_system_health()
    for k, v in health.items():
        bar_color = "#ff4444" if v < 40 else ("#ffaa00" if v < 70 else "#00cc66")
        st.markdown(f"""
        <div class="health-bar-wrapper">
            <div class="health-bar-label">
                <span>{k.upper()}</span>
                <span style="color:{bar_color}">{v:.1f}%</span>
            </div>
            <div class="health-bar-track">
                <div class="health-bar-fill" style="width:{v}%;background:linear-gradient(90deg,{bar_color}88,{bar_color});"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ─── Tabs: Forecast + History ─────────────────────────────────────────────
spacer()
tab1, tab2, tab3 = st.tabs(["📈  Ammonia Forecast", "📉  Historical Trends", "🗃  Raw Data"])

LINE_LAYOUT = dict(
    paper_bgcolor='rgba(2,10,22,0)', plot_bgcolor='rgba(0,15,35,0.5)',
    font=dict(family='Space Grotesk', color='#7db8e8', size=11),
    height=300, margin=dict(l=10, r=10, t=20, b=10),
    xaxis=dict(gridcolor='rgba(0,100,200,0.1)', zerolinecolor='rgba(0,100,200,0.2)',
               showline=True, linecolor='rgba(0,170,255,0.2)'),
    yaxis=dict(gridcolor='rgba(0,100,200,0.1)', zerolinecolor='rgba(0,100,200,0.2)',
               showline=True, linecolor='rgba(0,170,255,0.2)'),
    hovermode='x unified',
)

with tab1:
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=ammonia_df["hour"], y=ammonia_df["ammonia"],
        mode='lines', name='Ammonia',
        line=dict(color='#00aaff', width=2.5, shape='spline'),
        fill='tozeroy', fillcolor='rgba(0,120,220,0.08)',
        hovertemplate='Hour %{x}<br><b>Ammonia: %{y:.2f} mg/L</b><extra></extra>'
    ))
    fig2.add_hline(y=AMMONIA_WARNING, line_dash="dot", line_color="rgba(255,170,0,0.5)",
                   annotation_text=f"  Warning ({AMMONIA_WARNING})",
                   annotation_font=dict(color="#ffaa00", size=10))
    fig2.add_hline(y=AMMONIA_CRITICAL, line_dash="dot", line_color="rgba(255,60,60,0.5)",
                   annotation_text=f"  Critical ({AMMONIA_CRITICAL})",
                   annotation_font=dict(color="#ff4444", size=10))
    fig2.update_layout(**LINE_LAYOUT, xaxis_title="Hour", yaxis_title="Ammonia (mg/L)")
    st.plotly_chart(fig2, width='stretch')

with tab2:
    history = load_history()
    if not history.empty:
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=history["timestamp"], y=history["hypoxia"],
            mode='lines', name='Hypoxia Risk',
            line=dict(color='#00e5ff', width=2, shape='spline'),
            fill='tozeroy', fillcolor='rgba(0,200,255,0.06)',
            hovertemplate='%{x}<br><b>Hypoxia: %{y:.4f}</b><extra></extra>'
        ))
        if "ammonia_peak" in history.columns:
            fig3.add_trace(go.Scatter(
                x=history["timestamp"], y=history["ammonia_peak"],
                mode='lines', name='Ammonia Peak',
                line=dict(color='#ffaa00', width=1.5, dash='dash'),
                hovertemplate='%{x}<br><b>Ammonia: %{y:.2f} mg/L</b><extra></extra>',
                yaxis='y2'
            ))
        fig3.update_layout(
            **LINE_LAYOUT,
            yaxis2=dict(title='Ammonia (mg/L)', overlaying='y', side='right',
                        gridcolor='rgba(0,0,0,0)', tickfont=dict(color='#ffaa00')),
            legend=dict(bgcolor='rgba(0,20,50,0.7)', bordercolor='rgba(0,170,255,0.2)',
                        borderwidth=1, font=dict(color='#7db8e8'))
        )
        st.plotly_chart(fig3, width='stretch')
    else:
        st.info("No historical data yet. Data accumulates as the dashboard runs.")

with tab3:
    if not history.empty:
        st.dataframe(
            history.tail(20).style.format({
                'hypoxia': '{:.4f}',
                'ammonia_peak': '{:.2f}',
                'temperature': '{:.1f}',
                'turbidity': '{:.1f}',
            }),
            width='stretch', hide_index=True
        )
    else:
        st.info("No historical records yet.")

# ─── Treatment Plan ──────────────────────────────────────────────────────────
spacer()
st.markdown("""<div class="section-header">
    <div class="section-title">🧪 AI Treatment Action Plan</div>
    <div class="section-badge">AUTO-GENERATED</div>
</div>""", unsafe_allow_html=True)

ammonia_peak_now = float(ammonia_peak)
sludge_critical_area = critical_area
sludge_avg_now = avg_sludge
temp_now = float(env["temperature"])
hypoxia_now = float(hypoxia)

aeration_base_hours = 4.0 if alert=="CRITICAL" else (2.0 if alert=="WARNING" else 0.5)
heat_stress_bonus = max(0.0, (temp_now-30.0)*0.3)
aeration_extra = round(aeration_base_hours + heat_stress_bonus, 1)

if ammonia_peak_now > AMMONIA_CRITICAL:
    water_ex = int(min(35, 20 + min(15, (ammonia_peak_now-AMMONIA_CRITICAL)*10)))
elif ammonia_peak_now > AMMONIA_WARNING:
    water_ex = int(min(35, 10 + min(10, (ammonia_peak_now-AMMONIA_WARNING)*8)))
else:
    water_ex = 0
if sludge_critical_area > 30: water_ex = int(min(35, water_ex + 5))

feed_red = 30 if (alert=="CRITICAL" or ammonia_peak_now > AMMONIA_CRITICAL) else (15 if (alert=="WARNING" or ammonia_peak_now > AMMONIA_WARNING) else 0)
desilt = int(round(sludge_critical_area)) if sludge_critical_area > 30 else (15 if sludge_avg_now > 1.2 else 0)
retest = 4 if alert=="CRITICAL" else (8 if alert=="WARNING" else 24)

def rc_class(code):
    if "CRIT" in code or "HIGH" in code: return "rc-crit"
    if "WARN" in code: return "rc-warn"
    return "rc-ok"

plan = [
    ("💧", "Water Exchange",
     f"{water_ex}% partial exchange now" if water_ex > 0 else "No exchange required",
     "Immediate (0-2h)" if water_ex > 0 else "Monitor (24h)",
     f"AMM_{'CRIT' if ammonia_peak_now > AMMONIA_CRITICAL else ('WARN' if ammonia_peak_now > AMMONIA_WARNING else 'OK')}",
     f"Ammonia {ammonia_peak_now:.2f} mg/L"),
    ("🌬", "Aeration Boost",
     f"+{aeration_extra:.1f} hours/day extra aeration",
     "Immediate & next 24h",
     f"HYP_{'CRIT' if hypoxia_now > HYPOXIA_CRITICAL else ('WARN' if hypoxia_now > HYPOXIA_WARNING else 'OK')}",
     f"Hypoxia {hypoxia_now:.3f}, Temp {temp_now:.1f}°C"),
    ("🐟", "Feed Adjustment",
     f"Reduce feed by {feed_red}%" if feed_red > 0 else "No change to feed schedule",
     "Today (0-24h)",
     f"FEED_{'REDUCE' if feed_red > 0 else 'NORMAL'}",
     f"Alert: {alert}"),
    ("🪣", "Desilting Priority",
     f"Desilt top {desilt}% hotspot area" if desilt > 0 else "No urgent desilting needed",
     "This week (1-7 days)",
     f"SLG_{'HIGH' if desilt > 0 else 'OK'}",
     f"Critical area {sludge_critical_area:.1f}%"),
    ("🔁", "Retest Interval",
     f"Recheck every {retest} hours",
     "Recurring",
     f"MONITOR_{alert}",
     "Based on current risk state"),
]

for icon, action, rec, timeline, code, basis in plan:
    cls = rc_class(code)
    st.markdown(f"""
    <div class="treatment-row">
        <div style="font-size:1.3rem">{icon}</div>
        <div class="treatment-action">{action}</div>
        <div class="treatment-rec">{rec}<br>
            <span style="font-size:0.72rem;color:#3a7a9a;font-family:'JetBrains Mono',monospace;">▸ {basis}</span>
        </div>
        <div class="treatment-timeline">{timeline}</div>
        <div class="reason-code {cls}">{code}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""<div class="custom-caption">
⏱ Execution windows: Immediate = 0–2h &nbsp;|&nbsp; Today = 24h &nbsp;|&nbsp; This week = 1–7 days
&nbsp;&nbsp;·&nbsp;&nbsp; Reason codes derived from live sensor readings
</div>""", unsafe_allow_html=True)

# ─── Export ─────────────────────────────────────────────────────────────────
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable, KeepTogether)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def generate_pdf_report():
    """Build a styled DeepEcho PDF report and return bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=16*mm, bottomMargin=16*mm,
    )

    # ── Colour palette ──────────────────────────────────────────────────────
    NAVY      = colors.HexColor("#020b18")
    BLUE_MID  = colors.HexColor("#00aaff")
    BLUE_DIM  = colors.HexColor("#185FA5")
    STEEL     = colors.HexColor("#1a3a5c")
    SILVER    = colors.HexColor("#a8d4f5")
    MUTED     = colors.HexColor("#5a9fd4")
    C_OK      = colors.HexColor("#00cc66")
    C_WARN    = colors.HexColor("#ffaa00")
    C_CRIT    = colors.HexColor("#ff4444")
    WHITE     = colors.white
    LIGHT_ROW = colors.HexColor("#0d2236")
    DARK_ROW  = colors.HexColor("#071624")

    def alert_color(a):
        return C_CRIT if a == "CRITICAL" else (C_WARN if a == "WARNING" else C_OK)

    # ── Styles ───────────────────────────────────────────────────────────────
    base = getSampleStyleSheet()

    def sty(name, **kw):
        return ParagraphStyle(name, **kw)

    S_TITLE = sty("Title2", fontSize=22, textColor=BLUE_MID, leading=28,
                  alignment=TA_CENTER, fontName="Helvetica-Bold", spaceAfter=2)
    S_SUB   = sty("Sub",   fontSize=9,  textColor=MUTED, alignment=TA_CENTER,
                  fontName="Helvetica", spaceAfter=8)
    S_H1    = sty("H1",    fontSize=11, textColor=BLUE_MID, fontName="Helvetica-Bold",
                  spaceBefore=10, spaceAfter=4)
    S_H2    = sty("H2",    fontSize=9,  textColor=SILVER, fontName="Helvetica-Bold",
                  spaceBefore=6, spaceAfter=3)
    S_BODY  = sty("Body",  fontSize=8,  textColor=SILVER, fontName="Helvetica",
                  leading=12)
    S_SMALL = sty("Small", fontSize=7,  textColor=MUTED,  fontName="Helvetica",
                  leading=10, alignment=TA_CENTER)
    S_ALERT = sty("Alert", fontSize=13, textColor=alert_color(alert),
                  fontName="Helvetica-Bold", alignment=TA_CENTER, spaceBefore=4)
    S_FOOT  = sty("Foot",  fontSize=7,  textColor=MUTED, alignment=TA_CENTER,
                  fontName="Helvetica")

    def hr():
        return HRFlowable(width="100%", thickness=0.5,
                          color=BLUE_DIM, spaceAfter=6, spaceBefore=6)

    def section(title):
        return [Spacer(1, 4), Paragraph(title.upper(), S_H1), hr()]

    # ── Helper: coloured cell paragraph ─────────────────────────────────────
    def cp(text, c=WHITE, bold=False, size=8, align=TA_LEFT):
        fn = "Helvetica-Bold" if bold else "Helvetica"
        return Paragraph(str(text),
                         sty(f"cp{id(text)}", fontSize=size, textColor=c,
                             fontName=fn, leading=size+3, alignment=align))

    # ── Common table style ───────────────────────────────────────────────────
    def base_ts(header_bg=STEEL):
        return TableStyle([
            ("BACKGROUND",  (0, 0), (-1,  0), header_bg),
            ("TEXTCOLOR",   (0, 0), (-1,  0), BLUE_MID),
            ("FONTNAME",    (0, 0), (-1,  0), "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1,  0), 8),
            ("ALIGN",       (0, 0), (-1,  0), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [DARK_ROW, LIGHT_ROW]),
            ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",    (0, 1), (-1, -1), 8),
            ("TEXTCOLOR",   (0, 1), (-1, -1), SILVER),
            ("GRID",        (0, 0), (-1, -1), 0.3, colors.HexColor("#0d2a44")),
            ("LEFTPADDING",  (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING",   (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 0), (0, 0), [STEEL]),
        ])

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    W = A4[0] - 36*mm   # usable width

    story = []

    # ── Cover block ──────────────────────────────────────────────────────────
    cover = Table(
        [[cp("DEEPECHO", BLUE_MID, bold=True, size=24, align=TA_CENTER)],
         [cp("Edge-AI Water Intelligence  ·  Pond Monitoring Report", MUTED, size=9, align=TA_CENTER)],
         [cp(f"Generated: {now_str}   |   GPS: {gps_lat:.6f}°N  {gps_lon:.6f}°E",
             MUTED, size=8, align=TA_CENTER)]],
        colWidths=[W],
    )
    cover.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), NAVY),
        ("BOX",          (0, 0), (-1, -1), 1.2, BLUE_MID),
        ("TOPPADDING",   (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 10),
        ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(cover)
    story.append(Spacer(1, 6))

    # Alert banner
    a_col = alert_color(alert)
    banner = Table(
        [[cp(f"SYSTEM STATUS: {alert}", a_col, bold=True, size=13, align=TA_CENTER)]],
        colWidths=[W],
    )
    banner.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), NAVY),
        ("BOX",          (0,0),(-1,-1), 1.5, a_col),
        ("TOPPADDING",   (0,0),(-1,-1), 8),
        ("BOTTOMPADDING",(0,0),(-1,-1), 8),
    ]))
    story.append(banner)
    story.append(Spacer(1, 10))

    # ── 1. Live Sensor Snapshot ───────────────────────────────────────────────
    story += section("1. Live Sensor Snapshot")

    snap_data = [
        [cp("Parameter", BLUE_MID, bold=True), cp("Value", BLUE_MID, bold=True),
         cp("Threshold", BLUE_MID, bold=True), cp("Status", BLUE_MID, bold=True)],
    ]
    snap_rows = [
        ("Temperature",   f"{env['temperature']:.1f} degC",  "< 32.0 degC",
         env['temperature'] / 32.0),
        ("Turbidity",     f"{env['turbidity']:.1f} NTU",     "< 50.0 NTU",
         env['turbidity'] / 50.0),
        ("Hypoxia Risk",  f"{hypoxia:.4f}",                  f"< {HYPOXIA_CRITICAL}",
         hypoxia / HYPOXIA_CRITICAL),
        ("Ammonia Peak",  f"{ammonia_peak:.2f} mg/L",        f"< {AMMONIA_CRITICAL} mg/L",
         ammonia_peak / AMMONIA_CRITICAL),
        ("Organic Ratio", f"{env['organic_ratio']:.3f}",     "< 0.50",
         env['organic_ratio'] / 0.5),
        ("Avg Sludge",    f"{avg_sludge:.2f} m", "< 1.50 m",
         avg_sludge / 1.5),
    ]
    for param, val, thresh, ratio in snap_rows:
        if ratio >= 1.0:
            sc, sl = C_CRIT, "CRITICAL"
        elif ratio >= 0.75:
            sc, sl = C_WARN, "WARNING"
        else:
            sc, sl = C_OK, "OK"
        snap_data.append([
            cp(param, SILVER), cp(val, WHITE, bold=True),
            cp(thresh, MUTED), cp(sl, sc, bold=True, align=TA_CENTER),
        ])

    snap_t = Table(snap_data, colWidths=[W*0.32, W*0.22, W*0.26, W*0.20])
    snap_ts = base_ts()
    snap_ts.add("ALIGN", (1, 1), (2, -1), "CENTER")
    snap_ts.add("ALIGN", (3, 1), (3, -1), "CENTER")
    snap_t.setStyle(snap_ts)
    story.append(snap_t)

    # ── 2. Sludge Analysis ────────────────────────────────────────────────────
    story += section("2. Sludge Analysis")

    avg_sl   = avg_sludge
    max_sl   = max_sludge
    crit_pct = critical_area
    vol      = total_volume

    sludge_data = [
        [cp("Metric", BLUE_MID, bold=True), cp("Value", BLUE_MID, bold=True),
         cp("Assessment", BLUE_MID, bold=True)],
        [cp("Average depth",        SILVER), cp(f"{avg_sl:.2f} m", WHITE, bold=True),
         cp("Elevated" if avg_sl > 1.2 else "Normal",
            C_WARN if avg_sl > 1.2 else C_OK)],
        [cp("Maximum depth",        SILVER), cp(f"{max_sl:.2f} m", WHITE, bold=True),
         cp("—", MUTED)],
        [cp("Critical area (>1.5m)",SILVER), cp(f"{crit_pct:.1f}%", WHITE, bold=True),
         cp("High" if crit_pct > 30 else "Moderate" if crit_pct > 15 else "Normal",
            C_CRIT if crit_pct > 30 else C_WARN if crit_pct > 15 else C_OK)],
        [cp("Estimated volume",     SILVER), cp(f"{vol:.1f} m3",  WHITE, bold=True),
         cp("—", MUTED)],
    ]
    sl_t = Table(sludge_data, colWidths=[W*0.38, W*0.28, W*0.34])
    sl_t.setStyle(base_ts())
    story.append(sl_t)

    # ── 3. Treatment Action Plan ──────────────────────────────────────────────
    story += section("3. Treatment Action Plan")

    plan_data = [
        [cp("Action", BLUE_MID, bold=True), cp("Recommendation", BLUE_MID, bold=True),
         cp("Timeline", BLUE_MID, bold=True), cp("Code", BLUE_MID, bold=True)],
    ]
    for _icon, action, rec, timeline, code, _basis in plan:
        if "CRIT" in code or "HIGH" in code:
            cc = C_CRIT
        elif "WARN" in code:
            cc = C_WARN
        else:
            cc = C_OK
        plan_data.append([
            cp(action, SILVER, bold=True),
            cp(rec,    WHITE),
            cp(timeline, MUTED, size=7),
            cp(code,   cc, size=7, align=TA_CENTER),
        ])

    plan_t = Table(plan_data, colWidths=[W*0.22, W*0.40, W*0.22, W*0.16])
    plan_t.setStyle(base_ts())
    story.append(plan_t)

    # ── 4. Historical Summary (last 10 rows) ──────────────────────────────────
    history = load_history()
    if not history.empty:
        story += section("4. Recent Historical Readings (last 10)")
        tail = history.tail(10).copy()
        # Build header
        cols_show = [c for c in ["timestamp","temperature","turbidity",
                                  "hypoxia","ammonia_peak","alert"] if c in tail.columns]
        col_labels = {"timestamp":"Timestamp","temperature":"Temp (C)",
                      "turbidity":"Turb (NTU)","hypoxia":"Hypoxia",
                      "ammonia_peak":"Ammonia","alert":"Alert"}
        hist_data = [[cp(col_labels.get(c, c), BLUE_MID, bold=True) for c in cols_show]]
        for _, row in tail.iterrows():
            hist_row = []
            for c in cols_show:
                val = row[c]
                if c == "alert":
                    tc = alert_color(str(val))
                    hist_row.append(cp(str(val), tc, bold=True, size=7, align=TA_CENTER))
                elif c == "timestamp":
                    hist_row.append(cp(str(val)[:19], MUTED, size=7))
                elif isinstance(val, float):
                    hist_row.append(cp(f"{val:.3f}", SILVER, size=8))
                else:
                    hist_row.append(cp(str(val), SILVER, size=8))
            hist_data.append(hist_row)

        n = len(cols_show)
        hist_t = Table(hist_data, colWidths=[W/n]*n)
        hist_t.setStyle(base_ts())
        story.append(hist_t)

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 14))
    story.append(hr())
    story.append(Paragraph(
        f"DeepEcho Edge-AI Water Intelligence  ·  Report generated {now_str}  ·  "
        f"Pond location {gps_lat:.6f}N {gps_lon:.6f}E  ·  Mode: {mode}",
        S_FOOT,
    ))

    doc.build(story)
    buf.seek(0)
    return buf.read()


st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""<div class="section-header">
    <div class="section-title">📤 Export</div>
</div>""", unsafe_allow_html=True)

exp_col1, exp_col2, exp_col3 = st.columns([1, 1, 4])

with exp_col1:
    with st.spinner("Building PDF…"):
        pdf_bytes = generate_pdf_report()
    st.download_button(
        label="📄 Download PDF Report",
        data=pdf_bytes,
        file_name=f"deepecho_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mime="application/pdf",
        width='stretch',
    )

with exp_col2:
    history_exp = load_history()
    csv_bytes = history_exp.to_csv(index=False).encode()
    st.download_button(
        label="📊 Download CSV Data",
        data=csv_bytes,
        file_name=f"deepecho_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        width='stretch',
    )

# ─── Auto refresh ────────────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(2)
    st.rerun()
