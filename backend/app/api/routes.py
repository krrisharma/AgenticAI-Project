from fastapi import APIRouter, Query
from app.models import PresetsResponse, RouteRequest, RouteResponse
from app.services.routing import load_presets, compute_routes_for_preset

router = APIRouter(prefix="/api", tags=["Routing"])

@router.get("/presets", response_model=PresetsResponse)
async def get_presets(vehicle_type: str = Query("car")):
    presets = load_presets()
    if vehicle_type == "truck":
        # In truck mode, freight presets are listed first
        presets.sort(key=lambda p: 0 if p.tag == "freight" else 1)
    else:
        presets.sort(key=lambda p: 0 if p.tag == "general" else 1)
    return PresetsResponse(presets=presets)

@router.post("/route", response_model=RouteResponse)
async def plan_route(req: RouteRequest):
    return await compute_routes_for_preset(
        preset_id=req.preset_id,
        reverse=req.reverse,
        vehicle_type=req.vehicle_type,
        depart_at=req.depart_at,
        balance=req.balance
    )
