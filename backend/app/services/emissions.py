import yaml
from pathlib import Path
from typing import Dict, Any
from app.config import settings

def load_emission_config() -> dict:
    path = settings.CONFIG_DIR / "emission_factors.yaml"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}

EMISSION_CONFIG = load_emission_config()

def estimate_route_emissions(
    distance_km: float,
    vehicle_type: str = "car",
    km_in_hotspots: float = 0.0,
    km_near_sensitive: float = 0.0
) -> Dict[str, Any]:
    """
    Compute estimated vehicular emissions (PM2.5, NO2, CO2) based on vehicle class
    and sensitive hotspot exposure multipliers.
    All figures are explicitly labelled as ESTIMATES.
    """
    v_conf = EMISSION_CONFIG.get("vehicles", {}).get(vehicle_type, {})
    multipliers = EMISSION_CONFIG.get("zone_multipliers", {})
    
    pm25_factor = v_conf.get("pm25_g_per_km", 0.045 if vehicle_type == "car" else 0.480)
    no2_factor = v_conf.get("no2_g_per_km", 0.380 if vehicle_type == "car" else 4.250)
    co2_factor = v_conf.get("co2_g_per_km", 142.0 if vehicle_type == "car" else 780.0)
    
    hotspot_mult = multipliers.get("hotspot", 2.2)
    sensitive_mult = multipliers.get("sensitive_zone_buffer", 1.8)
    
    # Regular km
    reg_km = max(0.0, distance_km - km_in_hotspots - km_near_sensitive)
    
    # Emission impact score: weighted emission released inside sensitive areas
    impact_score = (
        (reg_km * pm25_factor * 1.0) +
        (km_in_hotspots * pm25_factor * hotspot_mult) +
        (km_near_sensitive * pm25_factor * sensitive_mult)
    )
    
    total_pm25_g = distance_km * pm25_factor
    total_no2_g = distance_km * no2_factor
    total_co2_kg = (distance_km * co2_factor) / 1000.0

    return {
        "is_estimate": True,
        "source": EMISSION_CONFIG.get("metadata", {}).get("source", "ARAI/CPCB Guidelines"),
        "vehicle_type": vehicle_type,
        "distance_km": round(distance_km, 2),
        "total_pm25_g": round(total_pm25_g, 3),
        "total_no2_g": round(total_no2_g, 2),
        "total_co2_kg": round(total_co2_kg, 2),
        "emission_impact_score": round(impact_score, 2),
        "km_in_hotspots": round(km_in_hotspots, 2),
        "km_near_sensitive": round(km_near_sensitive, 2)
    }
