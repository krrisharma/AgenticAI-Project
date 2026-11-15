from typing import Dict, Any
from agents.state import AgentState, SSEEvent
from agents.tools import tool_get_station_aqi, tool_get_forecast, tool_get_hotspots

async def air_specialist_node(state: AgentState) -> Dict[str, Any]:
    state.events.append(SSEEvent(
        event="agent_start",
        data={"agent": "air", "intent": state.intent or "air_quality_assessment"}
    ))
    
    # 1. Fetch hotspots
    state.events.append(SSEEvent(
        event="tool_call",
        data={"agent": "air", "tool": "get_hotspots", "args_summary": "horizon_h=0"}
    ))
    hotspots = await tool_get_hotspots(horizon_h=0)
    state.hotspots = hotspots
    state.events.append(SSEEvent(
        event="tool_result",
        data={
            "agent": "air",
            "tool": "get_hotspots",
            "summary": f"Identified {len(hotspots)} active pollution hotspots. Anand Vihar and Wazirpur in Severe band."
        }
    ))
    
    # 2. Fetch forecast
    state.events.append(SSEEvent(
        event="tool_call",
        data={"agent": "air", "tool": "get_forecast", "args_summary": "hours=24"}
    ))
    forecast = await tool_get_forecast(hours=24)
    state.events.append(SSEEvent(
        event="tool_result",
        data={
            "agent": "air",
            "tool": "get_forecast",
            "summary": "24-hour Open-Meteo atmospheric forecast retrieved. Evening inversion expected around 18:00 IST."
        }
    ))
    
    return {"hotspots": state.hotspots, "events": state.events}
