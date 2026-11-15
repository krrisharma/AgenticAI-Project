import sys
from pathlib import Path

# Automatically ensure project root and backend dir are in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.services.proposals import init_db
from app.api import (
    health,
    aqi,
    hotspots,
    traffic,
    routes,
    truck,
    policy,
    metrics,
    agents
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("clearpath")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing ClearPath Database and Services...")
    init_db()
    yield
    logger.info("Shutting down ClearPath Services...")

app = FastAPI(
    title="ClearPath — Agentic Traffic & Air Quality Decision System",
    description="Multi-agent decision system optimizing traffic management and environmental exposure across Delhi-NCR.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration - Allow all origins for seamless Vercel / Render cloud deployment
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(health.router)
app.include_router(aqi.router)
app.include_router(hotspots.router)
app.include_router(traffic.router)
app.include_router(routes.router)
app.include_router(truck.router)
app.include_router(policy.router)
app.include_router(metrics.router)
app.include_router(agents.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
