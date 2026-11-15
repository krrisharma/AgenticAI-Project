import httpx
import asyncio
import logging
from typing import Optional, Tuple
from app.config import settings

logger = logging.getLogger(__name__)

async def geocode_nominatim(query: str) -> Optional[Tuple[float, float]]:
    """
    Build-time geocoding helper via Nominatim.
    Respects Nominatim policy: 1 request/sec, custom descriptive User-Agent.
    """
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": settings.NOMINATIM_USER_AGENT}
    params = {
        "q": f"{query}, Delhi NCR, India",
        "format": "json",
        "limit": 1
    }
    try:
        await asyncio.sleep(1.0) # rate limit
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(url, headers=headers, params=params)
            if res.status_code == 200:
                data = res.json()
                if data:
                    lat = float(data[0]["lat"])
                    lon = float(data[0]["lon"])
                    return lat, lon
    except Exception as e:
        logger.warning(f"Nominatim lookup failed for '{query}': {e}")
    return None
