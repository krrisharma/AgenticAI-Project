from typing import Dict, Any
from agents.state import AgentState, SSEEvent
from agents.tools import tool_compute_routes

async def routing_specialist_node(state: AgentState) -> Dict[str, Any]:
    preset = state.preset_id or ("azadpur_ghazipur" if state.vehicle_type == "truck" else "noida62_karolbagh")
    state.events.append(SSEEvent(
        event="agent_start",
        data={"agent": "routing", "intent": f"compute_{state.vehicle_type}_routes"}
    ))
    
    state.events.append(SSEEvent(
        event="tool_call",
        data={
            "agent": "routing",
            "tool": "compute_routes",
            "args_summary": f"preset_id='{preset}', vehicle_type='{state.vehicle_type}', depart_at='{state.depart_at or '18:00'}'"
        }
    ))
    
    routes_data = await tool_compute_routes(
        preset_id=preset,
        vehicle_type=state.vehicle_type,
        depart_at=state.depart_at,
        balance=state.balance
    )
    state.routes = routes_data
    
    comp = routes_data.get("comparison", {})
    t_delta = comp.get("time_delta_min", 0.0)
    exp_pct = comp.get("exposure_reduction_pct", 0.0)
    
    summary = f"Computed 3 paths. Cleanest route saves {exp_pct}% PM2.5 exposure with a {t_delta} min trade-off."
    if state.vehicle_type == "truck":
        em_pct = comp.get("emission_impact_reduction_pct", 0.0)
        hs_saved = comp.get("hotspot_km_saved", 0.0)
        summary = f"Truck route computed. Cleanest path saves {em_pct}% emission impact, bypasses {hs_saved} km inside hotspots, avoids restricted segments."
        
    state.events.append(SSEEvent(
        event="tool_result",
        data={
            "agent": "routing",
            "tool": "compute_routes",
            "summary": summary
        }
    ))
    
    return {"routes": state.routes, "events": state.events}
