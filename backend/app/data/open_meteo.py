import httpx
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, List
from app.data.cache import cache
from app.models import ForecastPoint
from app.services.aqi import calculate_cpcb_aqi

logger = logging.getLogger(__name__)

CACHE_AQ_KEY = "open_meteo_aq_delhi"
CACHE_WEATHER_KEY = "open_meteo_weather_delhi"
CACHE_TTL = 3600 # 60 min

DELHI_LAT = 28.6139
DELHI_LON = 77.2090

async def fetch_open_meteo_forecast(hours: int = 24) -> Tuple[List[ForecastPoint], str, str]:
    """Fetch hourly air quality forecast from Open-Meteo."""
    cached = cache.get(CACHE_AQ_KEY)
    if cached:
        return cached[0][:hours], cached[1], cached[2]

    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        url = "https://air-quality-api.open-meteo.com/v1/air-quality"
        params = {
            "latitude": DELHI_LAT,
            "longitude": DELHI_LON,
            "hourly": "pm10,pm2_5,nitrogen_dioxide",
            "forecast_days": 2
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(url, params=params)
            if res.status_code == 200:
                data = res.json()
                hourly = data.get("hourly", {})
                times = hourly.get("time", [])
                pm25s = hourly.get("pm2_5", [])
                pm10s = hourly.get("pm10", [])
                no2s = hourly.get("nitrogen_dioxide", [])

                points = []
                for idx, t_str in enumerate(times[:hours]):
                    p25 = pm25s[idx] if idx < len(pm25s) else None
                    p10 = pm10s[idx] if idx < len(pm10s) else None
                    n2 = no2s[idx] if idx < len(no2s) else None
                    
                    aqi, cat, _, _ = calculate_cpcb_aqi(p25, p10, n2)
                    points.append(ForecastPoint(
                        timestamp=f"{t_str}:00Z",
                        horizon_h=idx,
                        avg_pm25=round(p25 or 0.0, 1),
                        avg_aqi=aqi,
                        category=cat,
                        hotspot_count=3 if aqi > 250 else (2 if aqi > 150 else 1)
                    ))
                if points:
                    cache.set(CACHE_AQ_KEY, points, CACHE_TTL, now_iso)
                    cache.save_snapshot("forecast_delhi.json", {
                        "updated_at": now_iso,
                        "source": "open_meteo_live",
                        "hourly": [p.model_dump() for p in points]
                    })
                    return points, "live", now_iso
    except Exception as e:
        logger.warning(f"Open-Meteo Air Quality fetch failed: {e}. Falling back to snapshot.")

    # Fallback to snapshot
    snapshot = cache.load_snapshot("forecast_delhi.json")
    if snapshot and "hourly" in snapshot:
        as_of = snapshot.get("updated_at", now_iso)
        points = []
        for idx, item in enumerate(snapshot["hourly"][:hours]):
            p25 = item.get("pm25", 150.0)
            aqi, cat, _, _ = calculate_cpcb_aqi(p25)
            points.append(ForecastPoint(
                timestamp=item.get("timestamp", now_iso),
                horizon_h=item.get("horizon_h", idx),
                avg_pm25=float(p25),
                avg_aqi=aqi,
                category=cat,
                hotspot_count=3 if aqi > 250 else 2
            ))
        cache.set(CACHE_AQ_KEY, points, CACHE_TTL, as_of)
        return points, "snapshot", as_of

    return [], "snapshot", now_iso


async def fetch_open_meteo_weather() -> Tuple[Dict[str, Any], str, str]:
    """Fetch current Delhi atmospheric weather."""
    cached = cache.get(CACHE_WEATHER_KEY)
    if cached:
        return cached[0], cached[1], cached[2]

    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": DELHI_LAT,
            "longitude": DELHI_LON,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m"
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(url, params=params)
            if res.status_code == 200:
                current = res.json().get("current", {})
                weather_info = {
                    "updated_at": now_iso,
                    "temperature_c": current.get("temperature_2m", 22.0),
                    "relative_humidity_pct": current.get("relative_humidity_2m", 65),
                    "wind_speed_ms": current.get("wind_speed_10m", 1.5),
                    "wind_direction_deg": current.get("wind_direction_10m", 300),
                    "boundary_layer_height_m": 450.0,
                    "conditions": "Low wind, winter haze conditions"
                }
                cache.set(CACHE_WEATHER_KEY, weather_info, CACHE_TTL, now_iso)
                cache.save_snapshot("weather_delhi.json", weather_info)
                return weather_info, "live", now_iso
    except Exception as e:
        logger.warning(f"Open-Meteo Weather fetch failed: {e}. Falling back to snapshot.")

    snapshot = cache.load_snapshot("weather_delhi.json")
    if snapshot:
        as_of = snapshot.get("updated_at", now_iso)
        cache.set(CACHE_WEATHER_KEY, snapshot, CACHE_TTL, as_of)
        return snapshot, "snapshot", as_of

    return {}, "snapshot", now_iso
