from fastapi import APIRouter, Query
from app.models import HotspotsResponse
from app.services.hotspots import detect_hotspots

router = APIRouter(prefix="/api", tags=["Hotspots"])

@router.get("/hotspots", response_model=HotspotsResponse)
async def get_hotspots(horizon_h: int = Query(0, ge=0, le=24)):
    hotspots, status, as_of = await detect_hotspots(horizon_h)
    return HotspotsResponse(
        horizon_h=horizon_h,
        hotspots=hotspots,
        data_status=status,
        as_of=as_of
    )
