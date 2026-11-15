import json
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse
from app.models import ChatRequest
from agents.graph import workflow_engine
from agents.monitor import run_monitor

router = APIRouter(prefix="/api/agent", tags=["Agents"])

@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    async def event_generator():
        try:
            async for ev in workflow_engine.run_stream(
                query=req.message,
                vehicle_type=req.vehicle_type,
                depart_at=req.depart_at
            ):
                yield {
                    "event": ev.event,
                    "data": json.dumps(ev.data)
                }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"message": str(e)})
            }
            
    return EventSourceResponse(event_generator())

@router.post("/monitor/run")
async def trigger_monitor():
    res = await run_monitor()
    return res
