from fastapi import APIRouter, Query
from app.models import StationListResponse, GridResponse, ForecastResponse, GridBounds
from app.data.openaq import fetch_delhi_stations
from app.data.open_meteo import fetch_open_meteo_forecast
from app.services.grid import generate_interpolated_grid, DELHI_BOUNDS
from app.data.cache import cache

router = APIRouter(prefix="/api", tags=["Air Quality"])

@router.get("/aqi/stations", response_model=StationListResponse)
async def get_stations():
    stations, status, as_of = await fetch_delhi_stations()
    return StationListResponse(
        stations=stations,
        data_status=status,
        as_of=as_of
    )

@router.get("/aqi/grid", response_model=GridResponse)
async def get_grid(resolution_km: float = 2.0):
    grid, status, as_of = await generate_interpolated_grid(resolution_km)
    return GridResponse(
        grid=grid,
        bounds=DELHI_BOUNDS,
        resolution_km=resolution_km,
        data_status=status,
        as_of=as_of
    )

@router.get("/aqi/forecast", response_model=ForecastResponse)
async def get_forecast(hours: int = Query(24, ge=1, le=72)):
    points, status, as_of = await fetch_open_meteo_forecast(hours)
    return ForecastResponse(
        forecast=points,
        data_status=status,
        as_of=as_of
    )

@router.get("/sensitive-zones")
async def get_sensitive_zones():
    snapshot = cache.load_snapshot("sensitive_zones.json")
    if snapshot:
        return snapshot
    return {"type": "FeatureCollection", "features": []}
