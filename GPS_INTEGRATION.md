# GPS Integration for Pond Mapping

## Overview
The DeepEcho system now includes full GPS integration for georeferenced pond mapping, enabling real-world coordinate tracking and location-based analysis.

## Key Features

### 1. GPS Coordinate System
- **Center Point Configuration**: Set pond center coordinates (default: Andhra Pradesh, India)
  - Latitude: 16.5062°N
  - Longitude: 80.6480°E
- **Automatic Conversion**: Local meter coordinates automatically converted to GPS lat/lon
- **Accurate Mapping**: Uses proper geodetic calculations accounting for latitude

### 2. Survey Path Planning
- **Zigzag Pattern**: Systematic coverage pattern for drone/boat surveys
- **GPS Tracking**: Complete survey path with GPS coordinates
- **Visual Overlay**: Cyan dotted line showing planned survey route
- **Efficient Coverage**: Optimized path for complete pond scanning

### 3. Hotspot GPS Tagging
- **Automatic Detection**: Critical sludge zones identified and GPS-tagged
- **Precise Coordinates**: Each hotspot has exact lat/lon coordinates
- **Exportable Data**: GPS coordinates available for navigation devices
- **Severity Classification**: Critical/High severity with location data

### 4. GPS Map View
- **2D Overlay Map**: Top-down view with GPS coordinates on axes
- **Sludge Heatmap**: Color-coded sludge distribution on GPS grid
- **Interactive Markers**: Click hotspots to see GPS coordinates
- **Survey Path Display**: Shows planned/completed survey routes

### 5. Data Export
- **GPS Coordinates Table**: Exportable hotspot locations
- **Navigation Ready**: Coordinates formatted for GPS devices
- **Integration Ready**: Data compatible with GIS systems

## How GPS Integration Works

### During Pond Mapping:

1. **Initial Setup**
   - Configure pond center GPS coordinates in sidebar
   - Set pond dimensions (default: 20m x 20m)
   - System calculates GPS grid for entire pond

2. **Survey Mode**
   - Enable "Show Survey Path" to see planned route
   - Drone/boat follows cyan path for systematic coverage
   - Each measurement point has GPS coordinates

3. **Data Collection**
   - Depth sensors collect bathymetry data
   - Each data point tagged with GPS coordinates
   - Real-time sludge mapping with location data

4. **Hotspot Identification**
   - System identifies critical sludge zones
   - Each hotspot automatically GPS-tagged
   - Red star markers show exact locations

5. **GPS Map View**
   - Toggle "Show GPS Map" in sidebar
   - View 2D map with lat/lon axes
   - Export coordinates for field navigation

## Use Cases

### Field Navigation
- Navigate to specific hotspots using GPS coordinates
- Plan cleaning operations based on GPS locations
- Track multiple ponds with unique GPS identifiers

### Multi-Pond Management
- Each pond has unique GPS center point
- Compare sludge patterns across different locations
- Regional analysis of multiple farms

### Integration with External Systems
- Export GPS data to GIS software
- Import into farm management systems
- Share locations with cleaning crews

### Regulatory Compliance
- Document exact locations of problem areas
- Provide GPS-verified monitoring data
- Track remediation progress by location

## Technical Details

### Coordinate Conversion
```python
# Meters to GPS conversion
lat_offset = y_meters / 111320  # meters per degree latitude
lon_offset = x_meters / (111320 * cos(latitude))  # adjusted for latitude
```

### Survey Path Algorithm
- Zigzag pattern for efficient coverage
- 8 parallel passes across pond
- Alternating directions for continuous path
- ~50 measurement points per survey

### Accuracy
- GPS precision: ±0.000001° (~0.1 meters)
- Suitable for pond-scale mapping
- Compatible with consumer GPS devices

## Configuration

Edit `config.py` to customize:
```python
GPS_CENTER_LAT = 16.5062  # Your pond latitude
GPS_CENTER_LON = 80.6480  # Your pond longitude
POND_WIDTH_METERS = 20    # Pond width
POND_LENGTH_METERS = 20   # Pond length
```

## Future Enhancements
- Real-time GPS tracking from drone/boat
- Historical GPS track playback
- Multi-pond GPS database
- Automatic pond boundary detection
- Integration with satellite imagery
