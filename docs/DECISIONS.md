# ClearPath Architecture & Design Decisions

This document records architectural decisions, assumptions, and design choices made during development.

## 1. Prototype Scope & Presets
- **Decision:** As specified in Section 3A, routing is strictly prototype-scoped to fixed preset origin-destination pairs with no runtime geocoding or free-form address search.
- **Reasoning:** Minimizes external API dependency latency, ensures graph connectivity and sub-500m snapping for all routes, and enables fast deterministic routing for demo reliability.

## 2. Road Network and Routing Graph
- **Decision:** The routing graph is built over Delhi NCT plus the Noida corridor (extending eastward to include Noida Sector 62).
- **Graph construction:** Built with major drivable road classes (`motorway`, `trunk`, `primary`, `secondary`, `tertiary` and links), retaining truck attributes (`highway`, `hgv`, `maxweight`, `maxheight`, `maxwidth`, `maxspeed`, `lanes`, `oneway`).
- **Memory footprint:** Stored as precomputed graph data structure with fast Dijkstra/A* routing in deterministic Python under 50MB disk and ~100MB RAM, fitting easily into free-tier container limits (< 512 MB).

## 3. Dual Vehicle Routing & Truck Restrictions
- **Decision:** Separate cost models and restrictions for **Car** vs **Truck / Heavy Vehicle**:
  - **Car:** `cost = travel_time + λ * (travel_time * pm25_norm) + sensitive_zone_penalty`.
  - **Truck:** Hard removal of restricted roads (e.g. inner Delhi core, peak hour prohibitions). Cleanest route minimizes emission impact (`length * emission_factor * pm25_norm * zone_multiplier`) avoiding schools, hospitals, and high-AQI clusters.
  - **Compliance:** Evaluates `depart_at` against Delhi Traffic Police official peak-hour entry restrictions (07:00-23:00 prohibition for non-destined commercial heavy vehicles; 23:00-07:00 window).

## 4. LLM Strategy & Groq Provider
- **Decision:** Use Groq Cloud with dynamic model discovery.
- **Rule:** Strictly no Llama models. Preferred order:
  1. Active Qwen chat model (`qwen/qwen-2.5-32b` or latest Qwen variant detected via `GET /models`).
  2. `openai/gpt-oss-120b`.
  3. `openai/gpt-oss-20b`.
- **Reasoning extraction:** Strips any `<think>` or internal chain-of-thought tokens prior to sending SSE `token` events to the client.
- **Graceful degradation:** If Groq API key is not supplied or rate limits / quotas are reached, template-based deterministic explanations are generated from tool metrics so the entire application remains 100% operational.

## 5. RAG System
- **Decision:** Local embeddings via lightweight ONNX / fast cosine similarity to keep RAM usage low (< 200MB) without requiring heavy PyTorch installations.
- **Knowledge base:** Official CPCB National Air Quality Index documents, CAQM Graded Response Action Plan (GRAP Stages I-IV), and WHO Air Quality Guidelines (2021).

## 6. Frontend Palette Rule
- **Decision:** Strictly NO blue, indigo, violet, or purple anywhere in the UI.
- **Palette:** Forest Green (`#2E6B4F`), Warm Off-White (`#F6F4EF`), Amber (`#C7782A`), Brick Red (`#B5412F`), Neutral Charcoal (`#1F2421` / `#3A3F3B`).
