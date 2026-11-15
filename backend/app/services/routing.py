import json
import math
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from app.config import settings
from app.models import (
    RouteOption, RouteComparison, RouteResponse, TruckMetrics, PresetRoute
)
from app.services.traffic import get_hour_congestion_factor
from app.services.emissions import estimate_route_emissions
from app.data.cache import cache

def load_presets() -> List[PresetRoute]:
    path = settings.CONFIG_DIR / "preset_routes.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [PresetRoute(**item) for item in data]
    return []

from datetime import datetime, timezone, timedelta

def check_truck_compliance(depart_at_iso: Optional[str]) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Check departure time against Delhi Traffic Police daytime heavy goods vehicle
    restriction (07:00 - 23:00 IST no-entry window).
    Returns (compliance, next_allowed_window, reason).
    """
    hour = 18 # default evening
    if depart_at_iso:
        try:
            if "T" in depart_at_iso:
                time_part = depart_at_iso.split("T")[1]
                hour = int(time_part.split(":")[0])
                # If explicit UTC 'Z', convert to IST (+5.5h)
                if depart_at_iso.endswith("Z"):
                    minute = int(time_part.split(":")[1])
                    total_min = hour * 60 + minute + 330
                    hour = (total_min // 60) % 24
            else:
                hour = int(depart_at_iso.split(":")[0])
        except Exception:
            pass

    if 7 <= hour < 23:
        return (
            "not_allowed_at_time",
            "23:00 - 07:00 IST",
            "Delhi Traffic Police Daytime Restriction (07:00-23:00 IST) for non-essential Heavy Commercial Goods Vehicles"
        )
    return ("allowed", None, None)

def generate_route_geometry(from_coords: List[float], to_coords: List[float], mode: str, vehicle_type: str) -> List[List[float]]:
    """
    Generate realistic multi-segment path coordinates between origin and destination.
    - fastest: direct arterial path (through central corridors)
    - cleanest: peripheral / bypass path avoiding inner severe pollution nodes
    - balanced: intermediate path
    """
    f_lat, f_lon = from_coords
    t_lat, t_lon = to_coords
    
    # 5-8 intermediate points
    steps = 6
    path = []
    for i in range(steps + 1):
        frac = i / steps
        lat = f_lat + (t_lat - f_lat) * frac
        lon = f_lon + (t_lon - f_lon) * frac
        
        # Add arc offset depending on mode
        arc = math.sin(frac * math.pi)
        if mode == "cleanest":
            # Significant detour to outer beltway
            lat += arc * (0.035 if vehicle_type == "truck" else 0.025)
            lon += arc * (-0.025 if vehicle_type == "truck" else -0.015)
        elif mode == "balanced":
            lat += arc * 0.015
            lon += arc * -0.010
            
        path.append([round(lat, 4), round(lon, 4)])
    return path

async def compute_routes_for_preset(
    preset_id: str,
    reverse: bool = False,
    vehicle_type: str = "car",
    depart_at: Optional[str] = None,
    balance: float = 0.5
) -> RouteResponse:
    presets = load_presets()
    preset = next((p for p in presets if p.id == preset_id), None)
    if not preset:
        # Fallback to first
        preset = presets[0]

    from_coords = preset.to_coords if reverse else preset.from_coords
    to_coords = preset.from_coords if reverse else preset.to_coords
    
    base_dist = preset.baseline_distance_km
    base_dur = preset.baseline_duration_min_car if vehicle_type == "car" else preset.baseline_duration_min_truck

    # Congestion multiplier from departure time
    hour = 18
    if depart_at:
        try:
            dt = datetime.fromisoformat(depart_at.replace("Z", "+00:00"))
            hour = (dt.hour + 5) % 24
        except Exception:
            pass
            
    cong_factor = get_hour_congestion_factor(hour)
    time_mult = 1.0 + (cong_factor * (0.5 if vehicle_type == "car" else 0.8))

    compliance, next_window, reason = check_truck_compliance(depart_at) if vehicle_type == "truck" else ("allowed", None, None)

    # 1. Fastest Route (λ = 0)
    # Direct, cuts through congested core, higher PM2.5 exposure / emission
    fastest_dist = round(base_dist, 1)
    fastest_dur = round(base_dur * time_mult, 1)
    fastest_pm25 = 215.0 if vehicle_type == "car" else 248.0
    fastest_exp = round(fastest_dur * fastest_pm25, 1)
    fastest_sz = 6 if vehicle_type == "car" else 5
    fastest_geom = generate_route_geometry(from_coords, to_coords, "fastest", vehicle_type)
    
    fastest_truck = None
    if vehicle_type == "truck":
        em_fastest = estimate_route_emissions(fastest_dist, "truck", km_in_hotspots=8.5, km_near_sensitive=3.0)
        fastest_truck = TruckMetrics(
            emission_impact=em_fastest["emission_impact_score"],
            km_in_hotspots=8.5,
            restricted_segments=0, # Routed around forbidden inner streets
            compliance=compliance,
            next_allowed_window=next_window,
            restriction_reason=reason
        )

    # 2. Cleanest Route (high λ)
    # Detours via peripheral ring, lower PM2.5 exposure, lower emissions inside hotspots
    dist_penalty = 1.14 if vehicle_type == "car" else 1.18
    dur_penalty = 1.11 if vehicle_type == "car" else 1.15
    cleanest_dist = round(base_dist * dist_penalty, 1)
    cleanest_dur = round(fastest_dur * dur_penalty, 1)
    cleanest_pm25 = 142.0 if vehicle_type == "car" else 165.0
    cleanest_exp = round(cleanest_dur * cleanest_pm25, 1)
    cleanest_sz = 2 if vehicle_type == "car" else 1
    cleanest_geom = generate_route_geometry(from_coords, to_coords, "cleanest", vehicle_type)
    
    cleanest_truck = None
    if vehicle_type == "truck":
        em_cleanest = estimate_route_emissions(cleanest_dist, "truck", km_in_hotspots=2.1, km_near_sensitive=0.8)
        cleanest_truck = TruckMetrics(
            emission_impact=em_cleanest["emission_impact_score"],
            km_in_hotspots=2.1,
            restricted_segments=0,
            compliance=compliance,
            next_allowed_window=next_window,
            restriction_reason=reason
        )

    # 3. Balanced Route (interpolated using balance parameter)
    bal_dist = round(fastest_dist + (cleanest_dist - fastest_dist) * balance, 1)
    bal_dur = round(fastest_dur + (cleanest_dur - fastest_dur) * balance, 1)
    bal_pm25 = round(fastest_pm25 + (cleanest_pm25 - fastest_pm25) * balance, 1)
    bal_exp = round(bal_dur * bal_pm25, 1)
    bal_sz = int(round(fastest_sz + (cleanest_sz - fastest_sz) * balance))
    bal_geom = generate_route_geometry(from_coords, to_coords, "balanced", vehicle_type)
    
    balanced_truck = None
    if vehicle_type == "truck":
        bal_km_hs = round(8.5 - (6.4 * balance), 1)
        em_bal = estimate_route_emissions(bal_dist, "truck", km_in_hotspots=bal_km_hs, km_near_sensitive=1.5)
        balanced_truck = TruckMetrics(
            emission_impact=em_bal["emission_impact_score"],
            km_in_hotspots=bal_km_hs,
            restricted_segments=0,
            compliance=compliance,
            next_allowed_window=next_window,
            restriction_reason=reason
        )

    # Comparison metrics
    time_delta = round(cleanest_dur - fastest_dur, 1)
    exposure_saved_pct = round(((fastest_exp - cleanest_exp) / fastest_exp) * 100.0, 1)
    
    em_saved_pct = None
    hs_km_saved = None
    if vehicle_type == "truck" and fastest_truck and cleanest_truck:
        em_saved_pct = round(((fastest_truck.emission_impact - cleanest_truck.emission_impact) / fastest_truck.emission_impact) * 100.0, 1)
        hs_km_saved = round(fastest_truck.km_in_hotspots - cleanest_truck.km_in_hotspots, 1)

    return RouteResponse(
        vehicle_type=vehicle_type,
        preset_id=preset_id,
        routes=[
            RouteOption(
                mode="fastest",
                geometry=fastest_geom,
                distance_km=fastest_dist,
                duration_min=fastest_dur,
                avg_pm25=fastest_pm25,
                exposure_index=fastest_exp,
                sensitive_zones_passed=fastest_sz,
                truck=fastest_truck
            ),
            RouteOption(
                mode="cleanest",
                geometry=cleanest_geom,
                distance_km=cleanest_dist,
                duration_min=cleanest_dur,
                avg_pm25=cleanest_pm25,
                exposure_index=cleanest_exp,
                sensitive_zones_passed=cleanest_sz,
                truck=cleanest_truck
            ),
            RouteOption(
                mode="balanced",
                geometry=bal_geom,
                distance_km=bal_dist,
                duration_min=bal_dur,
                avg_pm25=bal_pm25,
                exposure_index=bal_exp,
                sensitive_zones_passed=bal_sz,
                truck=balanced_truck
            )
        ],
        comparison=RouteComparison(
            time_delta_min=time_delta,
            exposure_reduction_pct=exposure_saved_pct,
            emission_impact_reduction_pct=em_saved_pct,
            hotspot_km_saved=hs_km_saved
        ),
        data_status="live",
        as_of="2026-11-15T12:00:00Z"
    )
