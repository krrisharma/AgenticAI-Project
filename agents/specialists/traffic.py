from typing import Dict, Any
from agents.state import AgentState, SSEEvent
from agents.tools import tool_get_congestion, tool_estimate_emissions, tool_simulate_truck_diversion

async def traffic_specialist_node(state: AgentState) -> Dict[str, Any]:
    state.events.append(SSEEvent(
        event="agent_start",
        data={"agent": "traffic", "intent": "traffic_and_congestion_analysis"}
    ))
    
    # 1. Congestion
    state.events.append(SSEEvent(
        event="tool_call",
        data={"agent": "traffic", "tool": "get_congestion", "args_summary": "hour=18"}
    ))
    cong = tool_get_congestion(18)
    state.events.append(SSEEvent(
        event="tool_result",
        data={
            "agent": "traffic",
            "tool": "get_congestion",
            "summary": f"Estimated city congestion index: {cong['city_congestion_index']} (Evening peak). Trunk road speeds reduced by 45%."
        }
    ))
    
    # If truck mode, simulate diversion
    if state.vehicle_type == "truck":
        state.events.append(SSEEvent(
            event="tool_call",
            data={"agent": "traffic", "tool": "simulate_truck_diversion", "args_summary": f"preset_id='{state.preset_id or 'azadpur_ghazipur'}'"}
        ))
        sim = await tool_simulate_truck_diversion(state.preset_id or "azadpur_ghazipur")
        state.events.append(SSEEvent(
            event="tool_result",
            data={
                "agent": "traffic",
                "tool": "simulate_truck_diversion",
                "summary": sim["summary"]
            }
        ))
        
    return {"events": state.events}
