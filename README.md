# ClearPath — Agentic Traffic & Air Quality Manager (Delhi)

> *Google Maps helps one driver reach a destination. ClearPath's agents help a city manage traffic and air quality together.*

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11+-brightgreen.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-teal.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2+-blue.svg)](https://reactjs.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-orange.svg)](https://langchain-ai.github.io/langgraph/)

---

## 1. Overview & Goal

ClearPath is a city-level decision and eco-routing system built specifically for the Delhi-National Capital Region (NCR). It bridges the gap between individual navigation and municipal environmental traffic management:

| Capability | What it Means in ClearPath |
|---|---|
| **Forecast** | Predicts pollution hotspots hours ahead using meteorological inversion models and Open-Meteo instead of just showing current readings. |
| **Decide** | LangGraph agents propose city-level measures (truck diversion, signal timing, public advisories) tied directly to the official CAQM Graded Response Action Plan (GRAP Stages I–IV). |
| **Protect** | Guards heavy traffic and citizens away from schools and hospitals when particulate matter reaches hazardous bands. |
| **Explain** | Every recommendation cites the exact data points and regulatory guidelines behind it with zero hallucinated figures. |
| **Truck Mode** | Separate heavy vehicle routing engine respecting Delhi Traffic Police daytime entry bans (07:00–23:00 IST), truck road bans, and emission impact minimization. |

---

## 2. Multi-Agent System Architecture

```
                  ┌──────────────────────────────────────────────┐
                  │          Supervisor Decision Agent           │
                  │   Intent classification & conflict resolve   │
                  └───────┬──────────────────────────────┬───────┘
                          │                              │
         ┌────────────────┴───────────────┐              │
         │                                │              │
┌────────▼─────────┐             ┌────────▼─────────┐    │
│ Air Quality Agent│             │   Traffic Agent  │    │
│ Hotspots & winds │             │ Congestion & HGV │    │
└────────┬─────────┘             └────────┬─────────┘    │
         │                                │              │
         ├────────────────────────────────┼──────────────┤
         │                                │              │
┌────────▼─────────┐             ┌────────▼─────────┐    │
│  Routing Agent   │             │   Policy Agent   │    │
│ Fastest vs Clean │             │ GRAP Proposals   │    │
└──────────────────┘             └────────┬─────────┘    │
                                          │              │
                                 ┌────────▼─────────┐    │
                                 │  Human Approval  │    │
                                 │   Interruption   │    │
                                 └────────┬─────────┘    │
                                          │              │
                                 ┌────────▼─────────┐    │
                                 │  Action Node     │    │
                                 │  Execute & Log   │    │
                                 └────────┬─────────┘    │
                                          │              │
                                 ┌────────▼──────────────▼───────┐
                                 │   Synthesizer & SSE Stream    │
                                 │   Groq (Qwen/GPT-OSS) / Temp  │
                                 └───────────────────────────────┘
```

- **Supervisor Agent:** Orchestrates workflow, classifies intent, merges results, and resolves conflicting goals (e.g., fastest route passing directly through a severe pollution cluster).
- **Air Quality Agent:** Queries continuous monitoring stations (CPCB/DPCC via OpenAQ), Open-Meteo atmospheric forecast, and calculates DBSCAN/distance hotspot clusters with meteorological drivers.
- **Traffic Agent:** Evaluates road-class speed reduction profiles and heavy vehicle congestion multipliers using a deterministic rush-hour model.
- **Routing Agent:** Computes fastest (λ=0), cleanest (high λ), and balanced routes for cars and trucks over the Delhi + Noida corridor.
- **Policy Agent:** Formulates emergency actions mapped to GRAP stages backed by real diversion simulation. **Always routes proposals through the human approval queue**.
- **Advisory Agent:** Generates citizen-facing health guidance with RAG retrieval over CPCB and WHO guidelines.

---

## 3. Design System — Clean & Calm

Strictly adheres to an earthy, calm palette with **no blue or purple anywhere in the UI**:
- **Background:** Warm Off-White (`#F6F4EF`)
- **Accent & Cleanest Route:** Forest Green (`#2E6B4F`)
- **Balanced Route & Caution:** Amber (`#C7782A`)
- **Alerts & Prohibitions:** Brick Red (`#B5412F`)
- **Fastest Route:** Neutral Charcoal (`#3A3F3B`)
- **Map:** CARTO Positron Light Basemap with custom circular pin markers.

---

## 4. Quick Start with Docker Compose

Ensure Docker and Docker Compose are installed:

```bash
# 1. Clone repository
git clone https://github.com/krrisharma/AgenticAI-Project.git
cd AgenticAI-Project

# 2. Configure environment
cp .env.example .env
# Add your GROQ_API_KEY (and optional OPENAQ_API_KEY)

# 3. Start services
docker compose up --build
```

- **Web Dashboard:** http://localhost:5173
- **FastAPI Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/health

---

## 5. Local Development Setup

### Backend & Agents
```bash
cd backend
python -m venv venv
# On Windows: venv\Scripts\activate
# On Linux/macOS: source venv/bin/activate
pip install -r requirements.txt

# Run pytest suite
python -m pytest tests/ -v

# Start development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 6. Demo Scenarios (One-Click Loaded)

1. **Eco-Route (Passenger Car):** Noida Sector 62 → Karol Bagh at 6:00 PM. Displays minutes added (+5.5 min) vs personal PM2.5 particulate exposure saved (-19.0%) avoiding the Anand Vihar corridor and 5 sensitive school zones.
2. **Severe Forecast & GRAP Policy Proposal:** Evaluates +6h forecast showing PM2.5 > 250 µg/m³; Policy Agent drafts GRAP Stage II truck diversion and signal timing adjustment; held in Human Approval Queue.
3. **Conflict Resolution:** Direct arterial route cuts through Anand Vihar Severe hotspot; Supervisor explains the health trade-off between speed and lung exposure.
4. **Heavy Commercial Truck Mode:** Azadpur Mandi → Ghazipur Mandi at 3:00 PM. Flags Delhi Traffic Police daytime prohibition (07:00–23:00 IST), cites next allowed window (23:00–07:00 IST), removes residential roads, and simulates -34% emission impact savings via peripheral bypass.

---

## 7. Data Sources & Attribution

- **Road Network & Sensitive Zones:** © OpenStreetMap contributors (ODbL).
- **Basemap:** CARTO Positron © OpenStreetMap contributors, © CARTO.
- **Air Quality Stations:** OpenAQ API v3 & Central Pollution Control Board (CPCB), Ministry of Environment, Forest and Climate Change.
- **Atmospheric Forecast & Weather:** Open-Meteo Air Quality & Weather Forecast APIs.
- **Policy Directives:** Commission for Air Quality Management in NCR and Adjoining Areas (CAQM) Graded Response Action Plan (GRAP) and CPCB National AQI Guidelines.
- **Traffic Restrictions:** Delhi Traffic Police Official Commercial Vehicle Regulations.
