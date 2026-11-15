import httpx
import logging
from datetime import datetime, timezone
from typing import List, Tuple
from app.config import settings
from app.data.cache import cache
from app.models import StationReading
from app.services.aqi import calculate_cpcb_aqi

logger = logging.getLogger(__name__)

CACHE_KEY = "openaq_delhi_stations"
CACHE_TTL = 1800 # 30 min

async def fetch_delhi_stations() -> Tuple[List[StationReading], str, str]:
    """
    Fetch station readings for Delhi from OpenAQ v3 (or fallback to snapshot).
    Returns (stations, data_status, as_of).
    """
    cached = cache.get(CACHE_KEY)
    if cached:
        return cached[0], cached[1], cached[2]

    # Try Live API if key is configured
    if settings.OPENAQ_API_KEY:
        try:
            headers = {"X-API-Key": settings.OPENAQ_API_KEY}
            params = {
                "bbox": "76.84,28.40,77.38,28.88",
                "limit": 50
            }
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.get("https://api.openaq.org/v3/locations", headers=headers, params=params)
                if res.status_code == 200:
                    data = res.json()
                    stations = []
                    now_iso = datetime.now(timezone.utc).isoformat()
                    for loc in data.get("results", []):
                        # Extract sensors
                        coords = loc.get("coordinates", {})
                        lat = coords.get("latitude")
                        lon = coords.get("longitude")
                        if not lat or not lon:
                            continue
                        
                        pm25_val = None
                        pm10_val = None
                        no2_val = None
                        for sensor in loc.get("sensors", []):
                            param_name = sensor.get("parameter", {}).get("name")
                            val = sensor.get("latest", {}).get("value")
                            if param_name == "pm25":
                                pm25_val = val
                            elif param_name == "pm10":
                                pm10_val = val
                            elif param_name == "no2":
                                no2_val = val

                        aqi, cat, dominant, _ = calculate_cpcb_aqi(pm25_val, pm10_val, no2_val)
                        stations.append(StationReading(
                            id=f"openaq_{loc.get('id')}",
                            name=loc.get("name", "Delhi Station"),
                            lat=lat,
                            lon=lon,
                            pm25=pm25_val,
                            pm10=pm10_val,
                            no2=no2_val,
                            aqi=aqi,
                            category=cat,
                            dominant_pollutant=dominant,
                            updated_at=loc.get("datetimeLast", {}).get("utc", now_iso),
                            source="openaq_live"
                        ))
                    if stations:
                        cache.set(CACHE_KEY, stations, CACHE_TTL, now_iso)
                        cache.save_snapshot("stations_delhi.json", {
                            "updated_at": now_iso,
                            "stations": [s.model_dump() for s in stations]
                        })
                        return stations, "live", now_iso
        except Exception as e:
            logger.warning(f"OpenAQ Live fetch failed: {e}. Falling back to snapshot.")

    # Fallback to snapshot
    snapshot = cache.load_snapshot("stations_delhi.json")
    if snapshot and "stations" in snapshot:
        as_of = snapshot.get("updated_at", datetime.now(timezone.utc).isoformat())
        stations = [StationReading(**s) for s in snapshot["stations"]]
        cache.set(CACHE_KEY, stations, CACHE_TTL, as_of)
        return stations, "snapshot", as_of

    # Last resort minimal mock
    now_iso = datetime.now(timezone.utc).isoformat()
    return [], "snapshot", now_iso
