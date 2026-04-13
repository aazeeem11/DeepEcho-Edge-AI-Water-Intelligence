# DeepEcho Edge-AI Water Intelligence

DeepEcho is a Streamlit dashboard for pond health monitoring with simulated telemetry, 3D sludge visualization, GPS-referenced mapping, risk scoring, historical logging, and report export.

## What The App Does

- Simulates pond bathymetry, sludge accumulation, and environmental readings
- Calculates hypoxia risk and alert state (`NORMAL`, `WARNING`, `CRITICAL`)
- Visualizes pond state in:
1. 3D bathymetry/sludge map
2. Optional GPS-referenced 2D contour map
3. Gauges, radar, and trend charts
- Detects sludge hotspots and tags them with GPS coordinates
- Stores measurements in local SQLite (`deepecho.db`)
- Exports:
1. PDF report (`reportlab`)
2. CSV history

## Dashboard Sections

- Sidebar controls
1. Operation mode (`Monitoring`, `Survey`, `Calibration`)
2. Auto refresh toggle (2s)
3. GPS center inputs
4. Display toggles for survey path and GPS map
- KPI cards: temperature, hypoxia, ammonia, sludge stats
- Main visual row:
1. 3D pond view (`Sludge Depth`, `Bottom Terrain`, `Combined`)
2. Risk and ammonia gauges
- Secondary row:
1. Water quality radar
2. System health bars
- Tabs:
1. Ammonia forecast
2. Historical trends
3. Raw history table
- AI treatment action plan
- Export buttons (PDF and CSV)

## Tech Stack

- Python
- Streamlit
- Plotly
- NumPy
- Pandas
- SciPy
- SQLite
- ReportLab

## Repository Structure

```text
app.py                     Streamlit app entrypoint and UI
config.py                  Global config, thresholds, GPS defaults
data_simulator.py          Pond/sludge/environment/GPS simulation
risk_engine.py             Hypoxia risk + alert logic
database.py                SQLite init/insert/load helpers
system_monitor.py          Simulated device health metrics
requirements.txt           Python dependencies
README.md                  Project documentation
design.md                  Architecture/design notes
GPS_INTEGRATION.md         GPS implementation details
Untitled40 (1).ipynb       Notebook/prototype notes
deepecho.db                Local SQLite database (runtime data)
*.h5 / *_quant.tflite      Model artifacts currently stored in repo
DeepEcho_Presentation.pptx Presentation asset
incubation_Report (1).pdf  Document asset
```

## Local Setup

1. Clone the repository:

```bash
git clone https://github.com/aazeeem11/DeepEcho-Edge-AI-Water-Intelligence.git
cd DeepEcho-Edge-AI-Water-Intelligence
```

2. Create and activate a virtual environment:

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

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run:

```bash
streamlit run app.py
```

Default local URL is typically `http://localhost:8501`.

## Configuration

Update `config.py` for thresholds and pond/GPS defaults:

- Pond size/grid and sludge cap
- Hypoxia and ammonia warning/critical thresholds
- GPS center and pond dimensions in meters

## Data And Persistence

- Runtime inserts one measurement per app rerun into SQLite table `measurements`
- Database file: `deepecho.db` in project root
- On ephemeral hosting, local DB may reset on restart/redeploy

## Exports

- PDF report includes:
1. Snapshot metrics
2. Sludge analysis
3. Treatment plan
4. Recent history
- CSV export contains all stored measurement rows

## Troubleshooting

- `ModuleNotFoundError: No module named 'reportlab'`
1. Run `pip install -r requirements.txt`
- Port already in use (`8501`)
1. Stop old Streamlit process, or run `streamlit run app.py --server.port 8502`
- Empty/short history
1. Let app run with auto-refresh enabled to accumulate rows

## Current Limitations

- Inputs are simulated, not live hardware telemetry
- No authentication or role-based access
- Local SQLite only (no managed production backend)

## License

No license file is currently included. Add a `LICENSE` file to define usage terms.
