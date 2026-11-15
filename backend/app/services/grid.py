import math
from typing import List, Tuple
from app.models import GridCell, GridBounds, GridResponse
from app.data.openaq import fetch_delhi_stations
from app.services.aqi import calculate_cpcb_aqi

DELHI_BOUNDS = GridBounds(
    min_lat=28.40,
    max_lat=28.88,
    min_lon=76.84,
    max_lon=77.38
)

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

async def generate_interpolated_grid(resolution_km: float = 2.0) -> Tuple[List[GridCell], str, str]:
    """
    Interpolate station measurements using Inverse Distance Weighting (IDW)
    across the Delhi NCT + Noida corridor bounding box.
    """
    stations, status, as_of = await fetch_delhi_stations()
    valid_stations = [s for s in stations if s.pm25 is not None and s.pm25 > 0]
    
    if not valid_stations:
        # Default baseline
        default_val = 150.0
        aqi, cat, _, _ = calculate_cpcb_aqi(default_val)
        return [GridCell(lat=28.61, lon=77.20, pm25=default_val, aqi=aqi, category=cat)], "snapshot", as_of

    lat_step = resolution_km / 111.0 # ~1 deg lat = 111 km
    lon_step = resolution_km / (111.0 * math.cos(math.radians(28.6)))

    grid_cells: List[GridCell] = []
    
    curr_lat = DELHI_BOUNDS.min_lat
    while curr_lat <= DELHI_BOUNDS.max_lat:
        curr_lon = DELHI_BOUNDS.min_lon
        while curr_lon <= DELHI_BOUNDS.max_lon:
            # IDW calculation
            weights = []
            values = []
            exact_match = None
            
            for st in valid_stations:
                dist = haversine_km(curr_lat, curr_lon, st.lat, st.lon)
                if dist < 0.3: # Near-station priority
                    exact_match = st.pm25
                    break
                w = 1.0 / (dist ** 2.0)
                weights.append(w)
                values.append(st.pm25 * w)
                
            if exact_match is not None:
                cell_pm25 = exact_match
            else:
                total_w = sum(weights)
                cell_pm25 = sum(values) / total_w if total_w > 0 else 120.0

            aqi, cat, _, _ = calculate_cpcb_aqi(cell_pm25)
            grid_cells.append(GridCell(
                lat=round(curr_lat, 3),
                lon=round(curr_lon, 3),
                pm25=round(cell_pm25, 1),
                aqi=aqi,
                category=cat
            ))
            curr_lon += lon_step
        curr_lat += lat_step

    return grid_cells, status, as_of
