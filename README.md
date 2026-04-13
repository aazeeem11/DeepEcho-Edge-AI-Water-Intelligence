# DeepEcho Edge-AI Water Intelligence

DeepEcho is a Streamlit dashboard for pond monitoring with simulated sensor signals, 3D sludge/bathymetry visualization, GPS-referenced overlays, and risk alerting.

## Live App

Streamlit deployment: https://deepecho-edge-ai-water-intelligence-11.streamlit.app/

## Overview

This project demonstrates an edge-friendly water intelligence workflow:

- Simulates pond environment and sludge distribution
- Visualizes pond condition in interactive 3D and 2D maps
- Computes hypoxia risk and ammonia-driven alerts
- Stores historical snapshots in local SQLite
- Supports data export and auto-refresh monitoring

## Key Features

- Live dashboard modes: `Monitoring`, `Survey`, `Calibration`
- 3D pond view with selectable visualization:
- `Sludge Depth`
- `Bottom Terrain`
- `Combined`
- GPS center controls and optional survey path overlays
- Hotspot detection for high sludge regions
- Time-series ammonia chart and historical trend logging
- System health indicators (CPU, memory, battery, signal quality)

## Tech Stack

- Python
- Streamlit
- Plotly
- NumPy
- Pandas
- SciPy
- SQLite

## Project Structure

```text
.
├── app.py                # Streamlit entrypoint
├── config.py             # Thresholds and pond/GPS constants
├── data_simulator.py     # Surface/env/GPS/path/hotspot simulation
├── risk_engine.py        # Hypoxia score and alert logic
├── database.py           # SQLite init/insert/load helpers
├── system_monitor.py     # Simulated system health metrics
├── requirements.txt
├── design.md             # Architecture and design notes
└── GPS_INTEGRATION.md    # GPS-specific implementation notes
```

## Local Setup

### 1. Clone

```bash
git clone https://github.com/aazeeem11/DeepEcho-Edge-AI-Water-Intelligence.git
cd DeepEcho-Edge-AI-Water-Intelligence
```

### 2. Create and activate virtual environment

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
streamlit run app.py
```

## Deploy to Streamlit Community Cloud

1. Push this repository to GitHub.
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **Create app**.
4. Select:
- Repository: `aazeeem11/DeepEcho-Edge-AI-Water-Intelligence`
- Branch: `main`
- Main file path: `app.py`
5. Click **Deploy**.

## Data Persistence Notes

- App data is stored in local SQLite file `deepecho.db`.
- On managed cloud platforms, local file persistence may reset on restart/redeploy.
- For production persistence, use a managed external database.

## Current Limitations

- Uses simulated (not live hardware) sensor/GPS feeds
- No authentication or multi-user controls
- SQLite is local-only by default

## Future Improvements

- Integrate real sensor and telemetry ingestion
- Add anomaly detection and forecasting models
- Add user roles and secure remote operations
- Migrate to cloud storage/warehouse for long-term analytics

## License

This project currently has no explicit license file. Add a `LICENSE` if you want to define usage permissions.
