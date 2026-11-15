from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.models import ProposalsResponse, PolicyProposal, ProposalDecisionRequest
from app.services.proposals import list_proposals, decide_proposal

router = APIRouter(prefix="/api/policy", tags=["Policy Proposals"])

@router.get("/proposals", response_model=ProposalsResponse)
async def get_proposals(status: Optional[str] = Query(None)):
    props = list_proposals(status)
    return ProposalsResponse(proposals=props)

@router.post("/proposals/{proposal_id}/decision", response_model=PolicyProposal)
async def submit_decision(proposal_id: str, req: ProposalDecisionRequest):
    updated = decide_proposal(proposal_id, req.decision, req.officer_note)
    if not updated:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return updated
