import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.data.openaq import fetch_delhi_stations
from app.data.open_meteo import fetch_open_meteo_forecast, fetch_open_meteo_weather
from app.services.hotspots import detect_hotspots
from app.services.traffic import get_congestion_for_hour
from app.services.emissions import estimate_route_emissions
from app.services.routing import compute_routes_for_preset
from app.services.proposals import add_proposal, list_proposals, decide_proposal
from app.models import PolicyProposal, ProposalAction, ProposalActionImpact
from agents.rag.retriever import rag_search_policy, rag_search_health

async def tool_get_station_aqi() -> List[Dict[str, Any]]:
    stations, _, _ = await fetch_delhi_stations()
    return [s.model_dump() for s in stations]

async def tool_get_forecast(hours: int = 24) -> List[Dict[str, Any]]:
    forecast, _, _ = await fetch_open_meteo_forecast(hours)
    return [f.model_dump() for f in forecast]

async def tool_get_hotspots(horizon_h: int = 0) -> List[Dict[str, Any]]:
    hotspots, _, _ = await detect_hotspots(horizon_h)
    return [h.model_dump() for h in hotspots]

def tool_get_congestion(hour: int = 18) -> Dict[str, Any]:
    res = get_congestion_for_hour(hour)
    return res.model_dump()

def tool_estimate_emissions(distance_km: float, vehicle_type: str = "car", km_in_hotspots: float = 0.0) -> Dict[str, Any]:
    return estimate_route_emissions(distance_km, vehicle_type, km_in_hotspots)

async def tool_compute_routes(
    preset_id: str,
    vehicle_type: str = "car",
    depart_at: Optional[str] = None,
    balance: float = 0.5
) -> Dict[str, Any]:
    res = await compute_routes_for_preset(preset_id, False, vehicle_type, depart_at, balance)
    return res.model_dump()

async def tool_simulate_truck_diversion(preset_id: str = "azadpur_ghazipur") -> Dict[str, Any]:
    """
    Simulates diverting heavy freight traffic around urban hotspots (via peripheral bypass).
    Compares baseline direct route vs diverted route.
    """
    res = await compute_routes_for_preset(preset_id, False, "truck", "2026-11-15T18:00:00Z", 1.0)
    data = res.model_dump()
    fastest = data["routes"][0]
    cleanest = data["routes"][1]
    
    added_km = round(cleanest["distance_km"] - fastest["distance_km"], 1)
    added_min = round(cleanest["duration_min"] - fastest["duration_min"], 1)
    
    fastest_em = fastest["truck"]["emission_impact"]
    cleanest_em = cleanest["truck"]["emission_impact"]
    em_saved_pct = round(((fastest_em - cleanest_em) / fastest_em) * 100.0, 1)
    
    hs_km_saved = round(fastest["truck"]["km_in_hotspots"] - cleanest["truck"]["km_in_hotspots"], 1)

    return {
        "preset_id": preset_id,
        "baseline_distance_km": fastest["distance_km"],
        "baseline_duration_min": fastest["duration_min"],
        "diverted_distance_km": cleanest["distance_km"],
        "diverted_duration_min": cleanest["duration_min"],
        "added_distance_km": added_km,
        "added_delay_min": added_min,
        "emission_impact_reduction_pct": em_saved_pct,
        "hotspot_km_avoided": hs_km_saved,
        "truck_restricted_segments": 0,
        "summary": f"Diverting trucks saves {em_saved_pct}% toxic hotspot emissions and bypasses {hs_km_saved} km of severe pollution zones with a {added_min} min transit delay."
    }

def tool_create_proposal(trigger: str, grap_stage: str, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    prop_id = f"pp_{uuid.uuid4().hex[:6]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    parsed_actions = []
    for a in actions:
        impact = a.get("est_impact", {})
        parsed_actions.append(ProposalAction(
            type=a["type"],
            target=a["target"],
            rationale=a["rationale"],
            est_impact=ProposalActionImpact(
                pm25_reduction_pct=impact.get("pm25_reduction_pct", 10.0),
                added_delay_min=impact.get("added_delay_min", 15.0),
                confidence=impact.get("confidence", "medium")
            ),
            source_refs=a.get("source_refs", ["CAQM GRAP Directives"])
        ))
    
    prop = PolicyProposal(
        id=prop_id,
        created_at=now_iso,
        trigger=trigger,
        grap_stage=grap_stage,
        actions=parsed_actions,
        status="pending"
    )
    add_proposal(prop)
    return prop.model_dump()

def tool_execute_action(proposal_id: str, officer_note: str = "Executed following officer approval") -> Dict[str, Any]:
    decided = decide_proposal(proposal_id, "approved", officer_note)
    if decided:
        return {
            "status": "success",
            "proposal_id": proposal_id,
            "decision": "approved",
            "message": f"Proposal {proposal_id} approved and municipal traffic directives published."
        }
    return {"status": "error", "message": f"Proposal {proposal_id} not found."}
