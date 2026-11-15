import pytest
from app.services.traffic import get_congestion_for_hour
from app.services.emissions import estimate_route_emissions
from app.services.routing import check_truck_compliance, compute_routes_for_preset
from agents.supervisor import classify_intent

def test_traffic_rush_hours():
    # Morning peak 9 AM
    c_morn = get_congestion_for_hour(9)
    assert c_morn.city_congestion_index >= 0.70
    assert c_morn.road_classes["primary"].speed_factor_truck < c_morn.road_classes["primary"].speed_factor_car

    # Night 2 AM free flow
    c_night = get_congestion_for_hour(2)
    assert c_night.city_congestion_index <= 0.25

def test_emissions_estimate():
    em_car = estimate_route_emissions(distance_km=25.0, vehicle_type="car")
    em_truck = estimate_route_emissions(distance_km=25.0, vehicle_type="truck")
    
    assert em_car["is_estimate"] is True
    assert em_truck["is_estimate"] is True
    # Truck emissions must be substantially higher than car
    assert em_truck["total_pm25_g"] > em_car["total_pm25_g"] * 5

def test_truck_compliance_hours():
    # 18:00 IST (peak evening) is prohibited
    status, next_w, reason = check_truck_compliance("2026-11-15T18:00:00+05:30")
    assert status == "not_allowed_at_time"
    assert next_w == "23:00 - 07:00 IST"
    assert "Daytime Restriction" in reason

    # 02:00 IST (night window) is allowed
    status_night, next_w_night, _ = check_truck_compliance("2026-11-15T02:00:00+05:30")
    assert status_night == "allowed"
    assert next_w_night is None

def test_supervisor_intent_classification():
    assert classify_intent("How clean is the route from Noida to Karol Bagh?", "car") == "route_planning"
    assert classify_intent("Plan freight delivery from Azadpur Mandi", "truck") == "truck_routing"
    assert classify_intent("Show me hotspots in Delhi for the next 6 hours") == "air_forecast"
    assert classify_intent("Draft a GRAP Stage II proposal to divert traffic") == "policy_proposal"
    assert classify_intent("What precautions should asthmatic children take?") == "citizen_advisory"

@pytest.mark.anyio
async def test_routing_cleanest_vs_fastest():
    res = await compute_routes_for_preset("noida62_karolbagh", False, "car", "2026-11-15T18:00:00Z", 0.5)
    fastest = res.routes[0]
    cleanest = res.routes[1]
    
    assert cleanest.exposure_index < fastest.exposure_index
    assert res.comparison.exposure_reduction_pct > 0
