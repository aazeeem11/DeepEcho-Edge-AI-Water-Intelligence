import numpy as np
import pandas as pd

from config import MAX_SLUDGE, POND_SIZE, GPS_CENTER_LAT, GPS_CENTER_LON, POND_WIDTH_METERS, POND_LENGTH_METERS, METERS_PER_DEGREE_LAT


def meters_to_gps(x_meters, y_meters, center_lat, center_lon):
    """Convert local meter coordinates to GPS lat/lon"""
    # Calculate meters per degree longitude at this latitude
    meters_per_degree_lon = METERS_PER_DEGREE_LAT * np.cos(np.radians(center_lat))
    
    # Convert offsets from center
    lat_offset = y_meters / METERS_PER_DEGREE_LAT
    lon_offset = x_meters / meters_per_degree_lon
    
    latitude = center_lat + lat_offset
    longitude = center_lon + lon_offset
    
    return latitude, longitude


def generate_gps_grid():
    """Generate GPS coordinates for pond grid"""
    # Local coordinates in meters (centered at 0,0)
    x_local = np.linspace(-POND_LENGTH_METERS/2, POND_LENGTH_METERS/2, POND_SIZE)
    y_local = np.linspace(-POND_WIDTH_METERS/2, POND_WIDTH_METERS/2, POND_SIZE)
    X_local, Y_local = np.meshgrid(x_local, y_local)
    
    # Convert to GPS coordinates
    LAT, LON = meters_to_gps(X_local, Y_local, GPS_CENTER_LAT, GPS_CENTER_LON)
    
    return X_local, Y_local, LAT, LON


def generate_survey_path(num_points=50):
    """Generate GPS survey path for drone/boat mapping"""
    # Zigzag pattern for systematic coverage
    path_x = []
    path_y = []
    
    y_lines = np.linspace(-POND_WIDTH_METERS/2, POND_WIDTH_METERS/2, 8)
    
    for i, y in enumerate(y_lines):
        if i % 2 == 0:
            x_line = np.linspace(-POND_LENGTH_METERS/2, POND_LENGTH_METERS/2, num_points//8)
        else:
            x_line = np.linspace(POND_LENGTH_METERS/2, -POND_LENGTH_METERS/2, num_points//8)
        
        path_x.extend(x_line)
        path_y.extend([y] * len(x_line))
    
    path_x = np.array(path_x)
    path_y = np.array(path_y)
    
    # Convert to GPS
    path_lat, path_lon = meters_to_gps(path_x, path_y, GPS_CENTER_LAT, GPS_CENTER_LON)
    
    return path_x, path_y, path_lat, path_lon


def generate_pond_surface(time_offset=0):
    """Generate realistic rural Indian pond surface with irregular shape and sludge accumulation"""
    x = np.linspace(0, 20, POND_SIZE)
    y = np.linspace(0, 20, POND_SIZE)
    X, Y = np.meshgrid(x, y)
    
    # Create irregular pond base (natural depression with varying depth)
    center_x, center_y = 10, 10
    dist_from_center = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
    
    # Irregular bowl shape with asymmetry (typical of rural ponds)
    base = 8 - 0.15 * dist_from_center + 0.3 * np.sin(X * 0.5) + 0.2 * np.cos(Y * 0.7)
    base += 0.4 * np.sin(X * 0.3 + Y * 0.4)  # Natural undulations
    
    # Add rocky/uneven bottom texture
    texture = 0.15 * np.sin(X * 2.5) * np.cos(Y * 2.3)
    base += texture
    
    # ===== REALISTIC IRREGULAR SLUDGE PATTERNS =====
    
    # Start with zero sludge
    sludge = np.zeros_like(X)
    
    # 1. Random irregular patches (like organic matter clusters)
    num_patches = np.random.randint(15, 25)  # Many small irregular patches
    for _ in range(num_patches):
        # Random center
        cx = np.random.uniform(2, 18)
        cy = np.random.uniform(2, 18)
        
        # Irregular shape (not circular)
        stretch_x = np.random.uniform(0.5, 2.5)
        stretch_y = np.random.uniform(0.5, 2.5)
        rotation = np.random.uniform(0, np.pi)
        
        # Rotate coordinates
        X_rot = (X - cx) * np.cos(rotation) - (Y - cy) * np.sin(rotation)
        Y_rot = (X - cx) * np.sin(rotation) + (Y - cy) * np.cos(rotation)
        
        # Irregular patch with random intensity
        intensity = np.random.uniform(0.3, 1.8)
        size = np.random.uniform(1.5, 4.0)
        patch = intensity * np.exp(-((X_rot/stretch_x)**2 + (Y_rot/stretch_y)**2) / size)
        
        sludge += patch
    
    # 2. Streaky patterns (like algae blooms or sediment flows)
    num_streaks = np.random.randint(5, 10)
    for _ in range(num_streaks):
        angle = np.random.uniform(0, 2*np.pi)
        offset = np.random.uniform(-5, 5)
        width = np.random.uniform(0.3, 1.2)
        intensity = np.random.uniform(0.2, 1.0)
        
        # Create streak along a direction
        streak_coord = X * np.cos(angle) + Y * np.sin(angle) + offset
        streak = intensity * np.exp(-(streak_coord**2) / (2 * width**2))
        
        # Make streak patchy (not continuous)
        streak_mask = np.random.random(X.shape) > 0.4
        sludge += streak * streak_mask
    
    # 3. Feeding zone accumulation (concentrated but irregular)
    feeding_centers = [(10, 10), (7, 8), (13, 12)]  # Multiple feeding spots
    for fx, fy in feeding_centers:
        # Irregular feeding zone
        dist_feed = np.sqrt((X - fx)**2 + (Y - fy)**2)
        feeding = 1.2 * np.exp(-dist_feed / 3)
        
        # Make it patchy
        feeding_noise = np.random.random(X.shape)
        feeding = feeding * (feeding_noise > 0.3)
        
        sludge += feeding
    
    # 4. Edge/bank runoff (irregular deposits near edges)
    edge_mask = (dist_from_center > 7) & (dist_from_center < 10)
    edge_sludge = np.random.uniform(0, 1.5, X.shape) * edge_mask
    
    # Make edge deposits very patchy
    edge_pattern = (np.random.random(X.shape) > 0.6)
    sludge += edge_sludge * edge_pattern
    
    # 5. Random scattered debris/organic matter
    debris_mask = np.random.random(X.shape) > 0.85  # Sparse random points
    debris_intensity = np.random.uniform(0.5, 2.0, X.shape)
    sludge += debris_mask * debris_intensity
    
    # 6. Perlin-like noise for natural variation
    # Create multi-scale noise
    for scale in [0.5, 1.0, 2.0, 4.0]:
        noise_x = np.sin(X * scale + np.random.random() * 10) * np.cos(Y * scale + np.random.random() * 10)
        noise_y = np.sin(X * scale * 1.3 + np.random.random() * 10) * np.cos(Y * scale * 0.7 + np.random.random() * 10)
        combined_noise = (noise_x + noise_y) * 0.15 / scale
        sludge += combined_noise
    
    # 7. Create "holes" - areas with no sludge (cleaned or naturally clear)
    num_holes = np.random.randint(3, 8)
    for _ in range(num_holes):
        hx = np.random.uniform(3, 17)
        hy = np.random.uniform(3, 17)
        hole_size = np.random.uniform(1.5, 3.5)
        hole_dist = np.sqrt((X - hx)**2 + (Y - hy)**2)
        hole_mask = hole_dist < hole_size
        sludge[hole_mask] *= np.random.uniform(0, 0.3)  # Reduce sludge in holes
    
    # 8. Add sharp boundaries (like sludge fronts)
    threshold_mask = sludge > np.percentile(sludge, 60)
    sludge[threshold_mask] *= np.random.uniform(1.2, 1.5)
    
    # Clip to realistic range
    sludge = np.clip(sludge, 0, MAX_SLUDGE)
    
    # Make it even more patchy by zeroing out low values randomly
    low_sludge_mask = (sludge < 0.3) & (np.random.random(X.shape) > 0.5)
    sludge[low_sludge_mask] = 0
    
    # Add shallow areas (typical near edges)
    shallow_mask = dist_from_center > 8
    base = np.where(shallow_mask, base + 1.5, base)
    
    # Water surface with subtle ripples (animated)
    water_surface = base + 0.05 * np.sin(X * 2 + time_offset) * np.cos(Y * 2 - time_offset)
    
    return X, Y, base, sludge, water_surface


def get_sludge_hotspots(X, Y, sludge, threshold=1.5):
    """Identify critical sludge accumulation zones"""
    hotspots = []
    mask = sludge > threshold
    
    if np.any(mask):
        # Find local maxima
        from scipy import ndimage
        labeled, num_features = ndimage.label(mask)
        
        for i in range(1, min(num_features + 1, 6)):  # Limit to top 5 hotspots
            region = labeled == i
            if np.sum(region) > 3:  # Minimum size
                y_idx, x_idx = np.where(region)
                center_y, center_x = np.mean(y_idx), np.mean(x_idx)
                max_sludge = np.max(sludge[region])
                
                # Convert to local meters (X, Y are in 0-20 range)
                x_meters = (X[int(center_y), int(center_x)] - 10)
                y_meters = (Y[int(center_y), int(center_x)] - 10)
                
                # Convert to GPS
                lat, lon = meters_to_gps(x_meters, y_meters, GPS_CENTER_LAT, GPS_CENTER_LON)
                
                hotspots.append({
                    'x': X[int(center_y), int(center_x)],
                    'y': Y[int(center_y), int(center_x)],
                    'z': max_sludge,
                    'lat': lat,
                    'lon': lon,
                    'severity': 'Critical' if max_sludge > 2.0 else 'High'
                })
    
    return hotspots


def generate_environment():
    return {
        "temperature": np.random.uniform(20, 35),
        "turbidity": np.random.uniform(10, 80),
        "organic_ratio": np.random.uniform(0.3, 0.9),
    }


def generate_time_series(length=24):
    hours = list(range(length))
    ammonia = np.clip(np.random.normal(1.2, 0.4, length), 0, 3)
    return pd.DataFrame({"hour": hours, "ammonia": ammonia})
