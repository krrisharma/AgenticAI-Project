from typing import Dict, Any
from agents.state import AgentState, SSEEvent
from agents.tools import tool_create_proposal, tool_simulate_truck_diversion
from agents.rag.retriever import rag_search_policy

async def policy_specialist_node(state: AgentState) -> Dict[str, Any]:
    state.events.append(SSEEvent(
        event="agent_start",
        data={"agent": "policy", "intent": "formulate_grap_policy_proposal"}
    ))
    
    # 1. RAG Search Policy
    state.events.append(SSEEvent(
        event="tool_call",
        data={"agent": "policy", "tool": "rag_search_policy", "args_summary": "query='GRAP Stage II truck diversion and traffic idling'"}
    ))
    policy_docs = rag_search_policy("GRAP Stage II truck diversion and traffic idling")
    source_ref = policy_docs[0]["header"] if policy_docs else "CAQM GRAP Stage II Directives"
    state.events.append(SSEEvent(
        event="tool_result",
        data={"agent": "policy", "tool": "rag_search_policy", "summary": f"Retrieved provisions from {source_ref}."}
    ))
    
    # 2. Simulate diversion impact
    state.events.append(SSEEvent(
        event="tool_call",
        data={"agent": "policy", "tool": "simulate_truck_diversion", "args_summary": "preset_id='azadpur_ghazipur'"}
    ))
    sim = await tool_simulate_truck_diversion("azadpur_ghazipur")
    state.events.append(SSEEvent(
        event="tool_result",
        data={"agent": "policy", "tool": "simulate_truck_diversion", "summary": sim["summary"]}
    ))
    
    # 3. Create Proposal
    actions = [
        {
            "type": "divert_heavy_vehicles",
            "target": "Anand Vihar & Ghazipur Inflow Arterials",
            "rationale": f"Divert heavy transit trucks to Eastern Peripheral Expressway (EPE) based on {sim['emission_impact_reduction_pct']}% emission impact reduction simulation.",
            "est_impact": {
                "pm25_reduction_pct": 14.5,
                "added_delay_min": sim["added_delay_min"],
                "confidence": "medium"
            },
            "source_refs": [f"CAQM GRAP Stage II Directive Item 4: Regulate non-essential commercial vehicles around severe hot spots ({source_ref})"]
        },
        {
            "type": "adjust_signal_timing",
            "target": "Vikas Marg & Road 56 Intersections",
            "rationale": "Extend green split on outflow corridors by 20% to prevent idling exhaust build-up.",
            "est_impact": {
                "pm25_reduction_pct": 6.2,
                "added_delay_min": -4.0,
                "confidence": "medium"
            },
            "source_refs": ["CPCB Comprehensive Action Plan (CAP) Traffic Protocols"]
        }
    ]
    
    prop = tool_create_proposal(
        trigger="Forecast PM2.5 exceeds Very Poor band (>250 µg/m³) at Anand Vihar Hub in 6 h",
        grap_stage="Stage II (Very Poor: AQI 301-400)",
        actions=actions
    )
    state.proposals.append(prop)
    state.approval_required = True
    state.pending_proposal_id = prop["id"]
    
    state.events.append(SSEEvent(
        event="approval_required",
        data={
            "proposal_id": prop["id"],
            "summary": f"Policy Proposal {prop['id']} drafted. Human approval from Traffic/Municipal Officer required before execution."
        }
    ))
    
    return {
        "proposals": state.proposals,
        "approval_required": True,
        "pending_proposal_id": prop["id"],
        "events": state.events
    }
