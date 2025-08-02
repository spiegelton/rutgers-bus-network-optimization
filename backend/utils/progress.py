import math
import numpy as np

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def bearing(lat1, lon1, lat2, lon2):
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(dlon))
    return (math.degrees(math.atan2(x, y)) + 360) % 360

def compute_progress(bus_lat, bus_lon, bus_course, polyline):
    # Convert polyline into radians once
    poly_rad = [(math.radians(lat), math.radians(lon)) for lat, lon in polyline]

    min_error = float('inf')
    best_proj = None
    best_cumulative = None

    # Precompute cumulative distances
    cumulative = [0]
    for i in range(1, len(poly_rad)):
        cumulative.append(
            cumulative[-1] + haversine(
                poly_rad[i-1][0], poly_rad[i-1][1],
                poly_rad[i][0], poly_rad[i][1]
            )
        )
    total_length = cumulative[-1]

    bus_lat_rad = math.radians(bus_lat)
    bus_lon_rad = math.radians(bus_lon)

    for i in range(len(poly_rad) - 1):
        (lat1, lon1) = poly_rad[i]
        (lat2, lon2) = poly_rad[i+1]

        # Calculate segment vector
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        if dlat == 0 and dlon == 0:
            continue  # skip identical points

        # Project bus onto segment
        t = ((bus_lat_rad - lat1) * dlat + (bus_lon_rad - lon1) * dlon) / (dlat**2 + dlon**2)
        t = max(0, min(1, t))
        proj_lat = lat1 + t * dlat
        proj_lon = lon1 + t * dlon

        # How far off is projection
        error = haversine(bus_lat_rad, bus_lon_rad, proj_lat, proj_lon)

        # Check direction consistency
        seg_bearing = bearing(lat1, lon1, lat2, lon2)
        heading_diff = min(abs(seg_bearing - bus_course), 360 - abs(seg_bearing - bus_course))

        if heading_diff > 60:  # threshold degrees (you can tune this)
            continue  # skip wrong direction segments

        if error < min_error:
            min_error = error
            best_proj = (proj_lat, proj_lon)
            best_cumulative = cumulative[i] + t * (cumulative[i+1] - cumulative[i])

    if best_proj is None:
        return 0.0  # fallback in bad case

    progress = best_cumulative / total_length
    return max(0.0, min(1.0, progress))


def compute_progress_no_heading(lat, lon, polyline):
    poly_rad = [(math.radians(lat), math.radians(lon)) for lat, lon in polyline]

    min_error = float('inf')
    best_cumulative = None

    # Precompute cumulative distances
    cumulative = [0]
    for i in range(1, len(poly_rad)):
        cumulative.append(
            cumulative[-1] + haversine(
                poly_rad[i-1][0], poly_rad[i-1][1],
                poly_rad[i][0], poly_rad[i][1]
            )
        )
    total_length = cumulative[-1]

    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)

    for i in range(len(poly_rad) - 1):
        (lat1, lon1) = poly_rad[i]
        (lat2, lon2) = poly_rad[i+1]

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        if dlat == 0 and dlon == 0:
            continue

        t = ((lat_rad - lat1) * dlat + (lon_rad - lon1) * dlon) / (dlat**2 + dlon**2)
        t = max(0, min(1, t))
        proj_lat = lat1 + t * dlat
        proj_lon = lon1 + t * dlon

        error = haversine(lat_rad, lon_rad, proj_lat, proj_lon)

        if error < min_error:
            min_error = error
            best_cumulative = cumulative[i] + t * (cumulative[i+1] - cumulative[i])

    if best_cumulative is None:
        return 0.0

    return max(0.0, min(1.0, best_cumulative / total_length))
