from fastapi import APIRouter
from datetime import datetime, timezone
from app.models import HealthResponse

router = APIRouter(prefix="/api", tags=["Health"])

@router.get("/health", response_model=HealthResponse)
async def get_health():
    now_iso = datetime.now(timezone.utc).isoformat()
    return HealthResponse(
        status="ok",
        data_status="live",
        as_of=now_iso,
        sources={
            "openaq": "live",
            "open_meteo_aq": "live",
            "open_meteo_weather": "live",
            "traffic": "synthetic"
        }
    )
