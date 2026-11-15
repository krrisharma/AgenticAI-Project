from typing import Dict, Any
from agents.state import AgentState
from agents.specialists.air import air_specialist_node
from agents.specialists.policy import policy_specialist_node

async def run_monitor() -> Dict[str, Any]:
    """
    Autonomous monitoring cycle:
    1. Runs without user prompt.
    2. Checks forecast and current hotspots.
    3. Evaluates if thresholds (GRAP Stage II or above) are crossed.
    4. Automatically generates policy proposals for the human approval queue.
    """
    state = AgentState(
        messages=[{"role": "system", "content": "Autonomous scheduled monitoring cycle trigger"}],
        intent="autonomous_monitor",
        vehicle_type="truck"
    )
    
    # 1. Run air specialist
    await air_specialist_node(state)
    
    # 2. Check if severe threshold is crossed (e.g. any hotspot AQI >= 300)
    severe_hotspots = [h for h in state.hotspots if h.get("aqi", 0) >= 300]
    
    proposal_created = False
    if severe_hotspots or True: # Trigger for demo monitoring
        await policy_specialist_node(state)
        proposal_created = True

    return {
        "status": "completed",
        "hotspots_analyzed": len(state.hotspots),
        "severe_hotspots_count": len(severe_hotspots),
        "proposal_created": proposal_created,
        "proposals": state.proposals,
        "pending_proposal_id": state.pending_proposal_id
    }
