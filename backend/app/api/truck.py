import json
from fastapi import APIRouter
from app.config import settings

router = APIRouter(prefix="/api/truck", tags=["Truck Restrictions"])

@router.get("/restrictions")
async def get_truck_restrictions():
    fixtures_path = settings.CONFIG_DIR.parent.parent / "contracts" / "fixtures" / "truck_restrictions.json"
    if fixtures_path.exists():
        with open(fixtures_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "type": "FeatureCollection",
        "metadata": {
            "authority": "Delhi Traffic Police",
            "allowed_window": "23:00 - 07:00 IST"
        },
        "features": []
    }
