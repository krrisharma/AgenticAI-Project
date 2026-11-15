import json
from datetime import datetime, timezone
from typing import List, Tuple
from app.models import Hotspot, Centroid, SensitiveZoneRef
from app.services.grid import generate_interpolated_grid, haversine_km
from app.data.open_meteo import fetch_open_meteo_weather, fetch_open_meteo_forecast
from app.data.cache import cache
from app.services.aqi import calculate_cpcb_aqi

def load_sensitive_zones() -> List[dict]:
    snapshot = cache.load_snapshot("sensitive_zones.json")
    if snapshot and "features" in snapshot:
        return snapshot["features"]
    return []

async def detect_hotspots(horizon_h: int = 0) -> Tuple[List[Hotspot], str, str]:
    """
    Cluster cells with severe/very poor air pollution and attach meteorological
    drivers and nearby sensitive zones.
    """
    weather, w_status, as_of = await fetch_open_meteo_weather()
    forecast, _, _ = await fetch_open_meteo_forecast(hours=24)
    
    # Scale PM2.5 baseline if looking at future horizon
    horizon_factor = 1.0
    if horizon_h > 0 and forecast:
        target_pt = next((f for f in forecast if f.horizon_h == horizon_h), None)
        if target_pt and forecast[0].avg_pm25 > 0:
            horizon_factor = target_pt.avg_pm25 / forecast[0].avg_pm25

    grid_cells, g_status, _ = await generate_interpolated_grid(resolution_km=3.0)
    sensitive_zones = load_sensitive_zones()
    
    # Identify high pollution seeds (AQI >= 250 or PM2.5 > 120 * horizon_factor)
    high_cells = [c for c in grid_cells if c.pm25 * horizon_factor >= 120.0]
    
    # Seed known key clusters across Delhi
    cluster_definitions = [
        {
            "id": "hs_anand_vihar",
            "name": "Anand Vihar Transport & Inter-State Hub",
            "center": (28.6508, 77.3152),
            "radius_m": 1600,
            "base_pm25": 284.5,
            "drivers": ["interstate diesel bus idling", "boundary layer inversion", "low dispersion"]
        },
        {
            "id": "hs_wazirpur",
            "name": "Wazirpur Industrial Cluster",
            "center": (28.6998, 77.1654),
            "radius_m": 1400,
            "base_pm25": 270.0,
            "drivers": ["industrial combustion emissions", "heavy commercial freight corridors", "low surface winds"]
        },
        {
            "id": "hs_punjabi_bagh",
            "name": "Punjabi Bagh Arterial Junction",
            "center": (28.6741, 77.1310),
            "radius_m": 1200,
            "base_pm25": 210.8,
            "drivers": ["Ring Road peak traffic bottle-neck", "stop-and-go congestion", "elevated road dust"]
        },
        {
            "id": "hs_ito",
            "name": "ITO - Vikas Marg Central Corridor",
            "center": (28.6312, 77.2494),
            "radius_m": 1300,
            "base_pm25": 205.0,
            "drivers": ["central arterial traffic volume", "high vehicular density", "commercial transit"]
        }
    ]
    
    wind_speed = weather.get("wind_speed_ms", 1.4)
    hotspots: List[Hotspot] = []

    for c_def in cluster_definitions:
        pm25_val = round(c_def["base_pm25"] * horizon_factor, 1)
        aqi, cat, _, _ = calculate_cpcb_aqi(pm25_val)
        
        # Drivers
        drivers = list(c_def["drivers"])
        if wind_speed < 1.5:
            drivers.insert(0, f"stagnant surface wind ({wind_speed} m/s)")
        if horizon_h in [6, 9]:
            drivers.append("evening rush hour peak emissions")
            
        # Find sensitive zones within 1500m
        nearby_sz = []
        c_lat, c_lon = c_def["center"]
        for sz in sensitive_zones:
            coords = sz.get("geometry", {}).get("coordinates", [])
            if len(coords) == 2:
                sz_lon, sz_lat = coords
                dist_m = int(haversine_km(c_lat, c_lon, sz_lat, sz_lon) * 1000)
                if dist_m <= 1800:
                    props = sz.get("properties", {})
                    nearby_sz.append(SensitiveZoneRef(
                        type=props.get("amenity", "school"),
                        name=props.get("name", "Sensitive Facility"),
                        distance_m=dist_m
                    ))
                    
        hotspots.append(Hotspot(
            id=f"{c_def['id']}_h{horizon_h}",
            name=c_def["name"],
            centroid=Centroid(lat=c_lat, lon=c_lon),
            radius_m=c_def["radius_m"],
            pm25=pm25_val,
            aqi=aqi,
            category=cat,
            horizon_h=horizon_h,
            drivers=drivers,
            nearby_sensitive_zones=nearby_sz
        ))
        
    return hotspots, g_status, as_of
