# DeepEcho Dashboard Design

## Overview
DeepEcho is a Streamlit dashboard for monitoring a rural pond with simulated sensor data, sludge mapping, and GPS-referenced visualization. The app generates synthetic bathymetry and environmental metrics, computes risk alerts, persists measurements to a local SQLite database, and renders 3D/2D visual analytics with Plotly.

## Goals
- Provide an operator-friendly dashboard for pond health and sludge accumulation.
- Visualize spatial data in 3D with optional GPS overlays.
- Track time-series trends and export data for analysis.
- Keep the stack lightweight and runnable on a local edge device.

## Non-Goals
- Real-time hardware sensor integration (currently simulated).
- Multi-user authentication or remote access control.
- Production-grade data warehousing or cloud telemetry.

## Architecture

### Runtime Flow
1. Initialize Streamlit page and SQLite database.
2. Collect operator controls from the sidebar (mode, auto-refresh, GPS toggles).
3. Generate simulated pond surface, environment, and ammonia forecast.
4. Compute hypoxia risk and alert level.
5. Persist measurement snapshot to SQLite.
6. Render visualizations and system health metrics.
7. Optionally export history and auto-refresh UI.

### Components
- UI layer: Streamlit app for layout, interactivity, and metrics.
- Simulation layer: Generates bathymetry, sludge distribution, GPS grid, and time-series data.
- Risk layer: Computes hypoxia risk and alert states.
- Persistence layer: Stores measurement snapshots in SQLite.
- Visualization layer: Plotly 3D surface, 2D GPS contour map, time-series charts.

## Modules

### app.py
- Entry point and Streamlit UI layout.
- Calls simulation functions and risk calculations.
- Persists a measurement to SQLite each run.
- Renders: 3D bathymetry, GPS overlay map, gauges, and time series.
- Auto-refresh loop using Streamlit rerun.

### config.py
- Central configuration for pond size, thresholds, and GPS defaults.
- Defines hypoxia and ammonia warning/critical thresholds.

### data_simulator.py
- Generates pond surface, sludge patterns, and water surface ripples.
- Builds GPS grid and zigzag survey path.
- Detects sludge hotspots with GPS tagging.
- Provides environment and ammonia time-series simulation.

### risk_engine.py
- Calculates hypoxia risk using weighted factors.
- Produces alert status based on hypoxia and ammonia thresholds.

### database.py
- SQLite schema for measurement snapshots.
- Inserts and loads historical data.

### system_monitor.py
- Produces randomized system health metrics.

## Data Model

### Measurement Record
Stored in SQLite table `measurements`:
- timestamp (ISO string)
- temperature (float)
- turbidity (float)
- organic_ratio (float)
- hypoxia (float)
- ammonia_peak (float)
- alert (text)

## Key UI States
- Operation Mode: Monitoring / Survey / Calibration.
- Auto Refresh: re-runs the app every update interval.
- GPS Location: editable center coordinates.
- Survey Path toggle: shows zigzag path in 3D and 2D views.
- GPS Map toggle: enables 2D contour map with lat/lon axes.
- Visualization Mode: Sludge Depth / Bottom Terrain / Combined.

## Visualization Details

### 3D Bathymetry
- Surface uses Plotly `Surface` with color scales for sludge depth.
- Optional water surface layer with transparency.
- Hotspots rendered as 3D markers with severity labels.
- Survey path rendered as cyan dotted 3D line.

### 2D GPS Overlay
- Contour heatmap of sludge depth with lat/lon axes.
- Hotspot markers and survey path overlay.
- Hotspot table in expandable view.

### Risk and Health
- Hypoxia gauge with normalized range 0-1.
- System health displayed as progress bars.

## Thresholds and Risk
- Hypoxia risk is weighted: organic ratio (0.5), temperature (0.3), turbidity (0.2).
- Alert is NORMAL, WARNING, or CRITICAL depending on hypoxia and ammonia thresholds.

## Persistence and Export
- Each run inserts a snapshot into SQLite.
- Historical trend chart uses `load_history()`.
- Export button writes `deepecho_export.csv` in the working directory.

## Dependencies
- streamlit
- plotly
- numpy
- pandas
- sqlalchemy (not currently used directly)
- scipy (used for hotspot labeling)

## Constraints and Assumptions
- Data is simulated; no sensor or GPS hardware integration.
- SQLite database is local to the app directory.
- Auto-refresh inserts a new record every cycle.
- GPS conversion assumes flat-earth approximation based on latitude.

## Future Extensions
- Replace simulators with sensor ingestion services.
- Add user authentication and role-based access.
- Persist data to a cloud datastore.
- Expose API endpoints for mobile and GIS clients.
- Add anomaly detection and historical forecasting.
