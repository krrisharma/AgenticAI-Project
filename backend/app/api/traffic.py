from fastapi import APIRouter, Query
from app.models import CongestionResponse
from app.services.traffic import get_congestion_for_hour

router = APIRouter(prefix="/api/traffic", tags=["Traffic"])

@router.get("/congestion", response_model=CongestionResponse)
async def get_congestion(hour: int = Query(18, ge=0, le=23)):
    return get_congestion_for_hour(hour)
