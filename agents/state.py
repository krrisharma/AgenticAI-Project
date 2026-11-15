from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class SSEEvent(BaseModel):
    event: str
    data: Dict[str, Any]

class AgentState(BaseModel):
    messages: List[Dict[str, str]] = Field(default_factory=list)
    intent: Optional[str] = None
    preset_id: Optional[str] = None
    vehicle_type: str = "car"
    depart_at: Optional[str] = None
    balance: float = 0.5
    
    # Tool artifacts
    hotspots: List[Dict[str, Any]] = Field(default_factory=list)
    routes: Optional[Dict[str, Any]] = None
    proposals: List[Dict[str, Any]] = Field(default_factory=list)
    actions_taken: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Event tracking
    events: List[SSEEvent] = Field(default_factory=list)
    final_message: Optional[str] = None
    approval_required: bool = False
    pending_proposal_id: Optional[str] = None
