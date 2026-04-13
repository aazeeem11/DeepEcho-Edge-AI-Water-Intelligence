# -*- coding: utf-8 -*-
import time

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_simulator import *
from database import *
from risk_engine import *
from system_monitor import *

st.set_page_config(layout="wide")
st.title("DeepEcho Edge-AI Water Intelligence")

init_db()

# Sidebar controls
st.sidebar.header("System Controls")
mode = st.sidebar.selectbox("Operation Mode", ["Monitoring", "Survey", "Calibration"])

auto_refresh = st.sidebar.checkbox("Auto Refresh", True)

# GPS Configuration
st.sidebar.markdown("---")
st.sidebar.subheader("GPS Location")
gps_lat = st.sidebar.number_input("Latitude", value=16.5062, format="%.6f")
gps_lon = st.sidebar.number_input("Longitude", value=80.6480, format="%.6f")
st.sidebar.caption(f"Center: {gps_lat:.6f}Â°N, {gps_lon:.6f}Â°E")

show_survey_path = st.sidebar.checkbox("Show Survey Path", True)
show_gps_overlay = st.sidebar.checkbox("Show GPS Map", False)

# Generate data
time_offset = time.time() * 0.5  # For animated ripples
X, Y, base, sludge, water_surface = generate_pond_surface(time_offset)
env = generate_environment()
ammonia_df = generate_time_series()

# Generate GPS data
from data_simulator import generate_gps_grid, generate_survey_path
X_local, Y_local, LAT, LON = generate_gps_grid()
survey_x, survey_y, survey_lat, survey_lon = generate_survey_path()

hypoxia = calculate_hypoxia_risk(env)
ammonia_peak = ammonia_df["ammonia"].max()
alert = generate_alert(hypoxia, ammonia_peak)

# Save to DB
insert_measurement(
    {
        "temperature": env["temperature"],
        "turbidity": env["turbidity"],
        "organic_ratio": env["organic_ratio"],
        "hypoxia": hypoxia,
        "ammonia_peak": ammonia_peak,
        "alert": alert,
    }
)

# Status bar
col1, col2, col3, col4 = st.columns(4)
col1.metric("Mode", mode)
DEG = chr(176)
col2.metric("Temperature", f"{env['temperature']:.1f} {DEG}C")
col3.metric("Hypoxia Risk", f"{hypoxia:.2f}")
col4.metric("Alert", alert)

st.markdown("---")

left, right = st.columns([3, 1])

# 3D map
with left:
    st.subheader("3D Pond Bathymetry & Sludge Analysis")
    
    # Visualization mode selector
    viz_mode = st.radio("View Mode", ["Sludge Depth", "Bottom Terrain", "Combined"], horizontal=True)
    
    if viz_mode == "Sludge Depth":
        # Sludge thickness visualization
        surface = go.Surface(
            x=X, 
            y=Y, 
            z=base - sludge,
            surfacecolor=sludge,
            colorscale=[
                [0, '#F5DEB3'],      # Wheat (clean)
                [0.2, '#DEB887'],    # Burlywood
                [0.4, '#D2691E'],    # Chocolate
                [0.6, '#A0522D'],    # Sienna
                [0.8, '#8B4513'],    # Saddle brown
                [1, '#654321']       # Dark brown (heavy sludge)
            ],
            colorbar=dict(
                title="Sludge<br>Depth (m)",
                x=1.02
            ),
            contours=dict(
                z=dict(
                    show=True,
                    usecolormap=False,
                    color='white',
                    width=2,
                    project=dict(z=True)
                )
            ),
            lighting=dict(
                ambient=0.5,
                diffuse=0.8,
                specular=0.4,
                roughness=0.5,
                fresnel=0.3
            ),
            lightposition=dict(x=50, y=50, z=150)
        )
        
        # Add water surface
        water = go.Surface(
            x=X, y=Y, z=water_surface,
            opacity=0.25,
            colorscale=[[0, 'rgba(100,150,200,0.3)'], [1, 'rgba(100,150,200,0.3)']],
            showscale=False,
            name='Water Surface',
            hoverinfo='skip'
        )
        
        # Identify and mark sludge hotspots
        from data_simulator import get_sludge_hotspots
        hotspots = get_sludge_hotspots(X, Y, sludge)
        
        if hotspots:
            hotspot_x = [h['x'] for h in hotspots]
            hotspot_y = [h['y'] for h in hotspots]
            hotspot_z = [base[np.argmin(np.abs(X[0] - h['x'])), np.argmin(np.abs(Y[:, 0] - h['y']))] for h in hotspots]
            hotspot_text = [f"Hotspot: {h['severity']}<br>Sludge: {h['z']:.2f}m<br>GPS: {h['lat']:.6f}Â°N, {h['lon']:.6f}Â°E" for h in hotspots]
            
            markers = go.Scatter3d(
                x=hotspot_x, y=hotspot_y, z=hotspot_z,
                mode='markers+text',
                marker=dict(size=10, color='red', symbol='diamond', 
                           line=dict(color='yellow', width=2)),
                text=['âš '] * len(hotspots),
                textposition='top center',
                textfont=dict(size=20, color='red'),
                hovertext=hotspot_text,
                hoverinfo='text',
                name='Critical Zones'
            )
            
            # Add survey path if enabled
            if show_survey_path:
                survey_path = go.Scatter3d(
                    x=survey_x + 10, y=survey_y + 10, 
                    z=[np.max(base) + 0.5] * len(survey_x),
                    mode='lines',
                    line=dict(color='cyan', width=3, dash='dot'),
                    name='Survey Path',
                    hoverinfo='skip'
                )
                fig = go.Figure(data=[surface, water, markers, survey_path])
            else:
                fig = go.Figure(data=[surface, water, markers])
        else:
            if show_survey_path:
                survey_path = go.Scatter3d(
                    x=survey_x + 10, y=survey_y + 10, 
                    z=[np.max(base) + 0.5] * len(survey_x),
                    mode='lines',
                    line=dict(color='cyan', width=3, dash='dot'),
                    name='Survey Path',
                    hoverinfo='skip'
                )
                fig = go.Figure(data=[surface, water, survey_path])
            else:
                fig = go.Figure(data=[surface, water])
            
    elif viz_mode == "Bottom Terrain":
        # Bottom terrain without sludge
        surface = go.Surface(
            x=X, y=Y, z=base,
            colorscale='earth',
            colorbar=dict(title="Elevation<br>(m)"),
            contours=dict(
                z=dict(show=True, usecolormap=True, 
                      highlightcolor="white", project=dict(z=True))
            ),
            lighting=dict(ambient=0.6, diffuse=0.8, specular=0.3)
        )
        fig = go.Figure(data=[surface])
        
    else:  # Combined view
        # Bottom terrain
        terrain = go.Surface(
            x=X, y=Y, z=base,
            colorscale='earth',
            opacity=0.7,
            showscale=False,
            name='Bottom'
        )
        
        # Sludge layer
        sludge_layer = go.Surface(
            x=X, y=Y, z=base - sludge,
            surfacecolor=sludge,
            colorscale=[
                [0, 'rgba(245,222,179,0.8)'],
                [0.5, 'rgba(210,105,30,0.8)'],
                [1, 'rgba(101,67,33,0.9)']
            ],
            colorbar=dict(title="Sludge<br>(m)"),
            name='Sludge'
        )
        
        # Water surface
        water = go.Surface(
            x=X, y=Y, z=water_surface,
            opacity=0.2,
            colorscale=[[0, 'rgba(100,150,200,0.2)'], [1, 'rgba(100,150,200,0.2)']],
            showscale=False,
            name='Water'
        )
        
        fig = go.Figure(data=[terrain, sludge_layer, water])
    
    # Enhanced layout
    fig.update_layout(
        height=550,
        scene=dict(
            xaxis=dict(
                title='Length (m)',
                backgroundcolor="rgb(200, 220, 230)",
                gridcolor="white",
                showbackground=True
            ),
            yaxis=dict(
                title='Width (m)',
                backgroundcolor="rgb(200, 220, 230)",
                gridcolor="white",
                showbackground=True
            ),
            zaxis=dict(
                title='Depth (m)',
                backgroundcolor="rgb(230, 230, 250)",
                gridcolor="white",
                showbackground=True
            ),
            camera=dict(
                eye=dict(x=1.6, y=1.6, z=1.2),
                center=dict(x=0, y=0, z=-0.1)
            ),
            aspectmode='manual',
            aspectratio=dict(x=1, y=1, z=0.4)
        ),
        margin=dict(l=0, r=0, t=30, b=0),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Enhanced statistics
    avg_sludge = np.mean(sludge)
    max_sludge_depth = np.max(sludge)
    critical_area = np.sum(sludge > 1.5) / sludge.size * 100
    total_volume = np.sum(sludge) * (20/POND_SIZE) * (20/POND_SIZE)  # Approximate volume
    
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Avg Sludge", f"{avg_sludge:.2f}m", delta=f"{(avg_sludge-1.2):.2f}m")
    col_b.metric("Max Depth", f"{max_sludge_depth:.2f}m")
    col_c.metric("Critical Area", f"{critical_area:.1f}%", 
                 delta="High" if critical_area > 30 else "Normal",
                 delta_color="inverse")
    col_d.metric("Est. Volume", f"{total_volume:.1f}mÂ³")
    
    # GPS Overlay Map
    if show_gps_overlay:
        st.markdown("---")
        st.subheader("ðŸ“ GPS-Referenced Map View")
        
        # Create 2D GPS map with sludge overlay
        gps_fig = go.Figure()
        
        # Sludge heatmap on GPS coordinates
        gps_fig.add_trace(go.Contour(
            x=LON[0, :],
            y=LAT[:, 0],
            z=sludge,
            colorscale=[
                [0, '#F5DEB3'],
                [0.5, '#D2691E'],
                [1, '#654321']
            ],
            colorbar=dict(title="Sludge<br>Depth (m)"),
            contours=dict(
                showlabels=True,
                labelfont=dict(size=10, color='white')
            )
        ))
        
        # Add survey path
        if show_survey_path:
            gps_fig.add_trace(go.Scatter(
                x=survey_lon,
                y=survey_lat,
                mode='lines+markers',
                line=dict(color='cyan', width=2),
                marker=dict(size=4, color='cyan'),
                name='Survey Path'
            ))
        
        # Add hotspot markers
        hotspots = get_sludge_hotspots(X, Y, sludge)
        if hotspots:
            gps_fig.add_trace(go.Scatter(
                x=[h['lon'] for h in hotspots],
                y=[h['lat'] for h in hotspots],
                mode='markers+text',
                marker=dict(size=15, color='red', symbol='star', 
                           line=dict(color='yellow', width=2)),
                text=['âš '] * len(hotspots),
                textposition='top center',
                textfont=dict(size=16, color='red'),
                hovertext=[f"{h['severity']}<br>{h['lat']:.6f}Â°N<br>{h['lon']:.6f}Â°E" for h in hotspots],
                name='Hotspots'
            ))
        
        gps_fig.update_layout(
            xaxis_title="Longitude (Â°E)",
            yaxis_title="Latitude (Â°N)",
            height=400,
            hovermode='closest',
            showlegend=True
        )
        
        st.plotly_chart(gps_fig, use_container_width=True)
        
        # GPS Data Table
        with st.expander("ðŸ“Š GPS Hotspot Coordinates"):
            if hotspots:
                gps_data = pd.DataFrame([
                    {
                        'Severity': h['severity'],
                        'Latitude': f"{h['lat']:.6f}Â°N",
                        'Longitude': f"{h['lon']:.6f}Â°E",
                        'Sludge Depth': f"{h['z']:.2f}m"
                    } for h in hotspots
                ])
                st.dataframe(gps_data, use_container_width=True)
            else:
                st.info("No critical hotspots detected")

# Risk + health
with right:
    st.subheader("Risk Gauge")
    gauge = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=hypoxia,
            title={"text": "Hypoxia"},
            gauge={"axis": {"range": [0, 1]}},
        )
    )
    st.plotly_chart(gauge, use_container_width=True)

    st.subheader("System Health")
    health = get_system_health()
    for k, v in health.items():
        st.progress(int(v), text=f"{k.upper()}: {v:.1f}%")

# Ammonia forecast
st.markdown("---")
st.subheader("Ammonia Forecast")

fig2 = px.line(ammonia_df, x="hour", y="ammonia")
fig2.add_hline(y=2.0, line_dash="dash")
st.plotly_chart(fig2, use_container_width=True)

# Historical trends
st.markdown("---")
st.subheader("Historical Trends")

history = load_history()

if not history.empty:
    fig3 = px.line(history, x="timestamp", y="hypoxia")
    st.plotly_chart(fig3, use_container_width=True)

    st.dataframe(history.tail(10))

# Auto-generated treatment plan using live values
st.markdown("---")
st.subheader("Treatment Action Plan")

ammonia_peak_now = float(ammonia_df["ammonia"].max())
sludge_critical_area = np.sum(sludge > 1.5) / sludge.size * 100
sludge_avg_now = float(np.mean(sludge))
temp_now = float(env["temperature"])
hypoxia_now = float(hypoxia)

if alert == "CRITICAL":
    aeration_base_hours = 4.0
elif alert == "WARNING":
    aeration_base_hours = 2.0
else:
    aeration_base_hours = 0.5

heat_stress_bonus_hours = max(0.0, (temp_now - 30.0) * 0.3)
aeration_extra_hours = round(aeration_base_hours + heat_stress_bonus_hours, 1)

if ammonia_peak_now > AMMONIA_CRITICAL:
    water_exchange_pct = 20 + min(15, (ammonia_peak_now - AMMONIA_CRITICAL) * 10)
elif ammonia_peak_now > AMMONIA_WARNING:
    water_exchange_pct = 10 + min(10, (ammonia_peak_now - AMMONIA_WARNING) * 8)
else:
    water_exchange_pct = 0

if sludge_critical_area > 30:
    water_exchange_pct += 5

water_exchange_pct = int(min(35, round(water_exchange_pct)))

if alert == "CRITICAL" or ammonia_peak_now > AMMONIA_CRITICAL:
    feed_reduction_pct = 30
elif alert == "WARNING" or ammonia_peak_now > AMMONIA_WARNING:
    feed_reduction_pct = 15
else:
    feed_reduction_pct = 0

if sludge_critical_area > 30:
    desilting_target_pct = int(round(sludge_critical_area))
elif sludge_avg_now > 1.2:
    desilting_target_pct = 15
else:
    desilting_target_pct = 0

if alert == "CRITICAL":
    retest_interval_hours = 4
elif alert == "WARNING":
    retest_interval_hours = 8
else:
    retest_interval_hours = 24

plan_rows = [
    {
        "Action": "Water exchange",
        "Exact recommendation": (
            f"{water_exchange_pct}% partial exchange now"
            if water_exchange_pct > 0
            else "No immediate exchange required"
        ),
        "Timeline": "Immediate (0-2h)" if water_exchange_pct > 0 else "Monitor (24h)",
        "Target outcome": (
            f"Bring next ammonia reading below {AMMONIA_WARNING:.1f} mg/L within 24h"
            if water_exchange_pct > 0
            else f"Keep ammonia below {AMMONIA_WARNING:.1f} mg/L"
        ),
        "Reason code": (
            "AMM_CRIT"
            if ammonia_peak_now > AMMONIA_CRITICAL
            else ("AMM_WARN" if ammonia_peak_now > AMMONIA_WARNING else "AMM_OK")
        ),
        "Live basis": f"Ammonia peak {ammonia_peak_now:.2f} mg/L",
    },
    {
        "Action": "Aeration increase",
        "Exact recommendation": f"+{aeration_extra_hours:.1f} hours/day",
        "Timeline": "Immediate and next 24h",
        "Target outcome": f"Reduce hypoxia risk to < {HYPOXIA_WARNING:.2f}",
        "Reason code": (
            "HYP_CRIT"
            if hypoxia_now > HYPOXIA_CRITICAL
            else ("HYP_WARN" if hypoxia_now > HYPOXIA_WARNING else "HYP_OK")
        ),
        "Live basis": f"Hypoxia {hypoxia_now:.2f}, Temp {temp_now:.1f} {DEG}C",
    },
    {
        "Action": "Feed adjustment",
        "Exact recommendation": (
            f"Reduce feed by {feed_reduction_pct}% for next 24h"
            if feed_reduction_pct > 0
            else "Keep feed schedule unchanged"
        ),
        "Timeline": "Today (0-24h)",
        "Target outcome": "Lower organic load and stabilize ammonia trend",
        "Reason code": "FEED_REDUCE" if feed_reduction_pct > 0 else "FEED_NORMAL",
        "Live basis": f"Alert level {alert}",
    },
    {
        "Action": "Desilting priority",
        "Exact recommendation": (
            f"Desilt top {desilting_target_pct}% hotspot area this week"
            if desilting_target_pct > 0
            else "No urgent desilting needed now"
        ),
        "Timeline": "This week (1-7 days)",
        "Target outcome": "Reduce critical sludge area below 20%",
        "Reason code": "SLG_HIGH" if desilting_target_pct > 0 else "SLG_OK",
        "Live basis": f"Critical sludge area {sludge_critical_area:.1f}%",
    },
    {
        "Action": "Retest interval",
        "Exact recommendation": f"Recheck key parameters every {retest_interval_hours} hours",
        "Timeline": "Recurring",
        "Target outcome": "Detect deterioration early and adjust plan quickly",
        "Reason code": f"MONITOR_{alert}",
        "Live basis": "Based on current risk state",
    },
]

st.dataframe(pd.DataFrame(plan_rows), use_container_width=True, hide_index=True)

st.caption(
    "Execution windows: Immediate = 0-2h, Today = 24h, This week = 1-7 days. "
    "Reason codes explain why each action is triggered from live sensor values."
)

# Export data
if st.button("Export Data"):
    history.to_csv("deepecho_export.csv", index=False)
    st.success("Data exported!")

# Auto refresh
if auto_refresh:
    time.sleep(2)
    st.rerun()

