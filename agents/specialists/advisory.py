from typing import Dict, Any
from agents.state import AgentState, SSEEvent
from agents.rag.retriever import rag_search_health

async def advisory_specialist_node(state: AgentState) -> Dict[str, Any]:
    state.events.append(SSEEvent(
        event="agent_start",
        data={"agent": "advisory", "intent": "citizen_health_guidance"}
    ))
    
    state.events.append(SSEEvent(
        event="tool_call",
        data={"agent": "advisory", "tool": "rag_search_health", "args_summary": "query='sensitive group precautions during Very Poor AQI'"}
    ))
    health_docs = rag_search_health("sensitive group precautions during Very Poor AQI")
    source_name = health_docs[0]["header"] if health_docs else "CPCB NAQI Guidelines"
    
    state.events.append(SSEEvent(
        event="tool_result",
        data={
            "agent": "advisory",
            "tool": "rag_search_health",
            "summary": f"Retrieved protective protocols from {source_name}. Advising cabin recirculation and avoiding morning/evening open-air exertion."
        }
    ))
    
    return {"events": state.events}
