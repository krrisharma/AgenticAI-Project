# ClearPath — Agentic Traffic & Air Quality Manager (Delhi)

> Working name. Rename freely.
> One-line pitch: *Google Maps helps one driver reach a destination. ClearPath's agents help a city manage traffic and air quality together.*

---

## 0. Instructions for the build agent (read first)

You are building this project end to end. Follow these rules throughout:

1. **Read this whole file before writing code.** Then work in the phases of Section 9.
2. **Use three parallel workstreams** (Backend, Agents, Frontend). Each owns its own directory (Section 4). Do not edit another workstream's files; use the interface contracts in Section 5 instead.
3. **Contract first.** Create `contracts/openapi_stub.md` and JSON fixtures in `contracts/fixtures/` before anything else, so the Frontend can build against fixtures while Backend and Agents are still in progress.
4. **Fetch real data.** Every data source in Section 3 must be actually called, verified, and cached. Check each API's current documentation before coding against it; if a field name or URL differs from what is written here, trust the live docs and note the change in `docs/DATA_SOURCES.md`.
5. **Never fabricate data.** If a source fails, fall back as described in Section 3 and show the data status honestly in the UI (`Live`, `Cached`, `Snapshot`). Any assumption (for example emission factors) must be labelled as an estimate in code and in the UI.
6. **Free only.** No paid APIs, no paid hosting assumptions. Respect each provider's rate limits and usage policy (descriptive User-Agent, caching, throttling).
7. **Keep the LLM cheap.** Heavy lifting (AQI math, routing, hotspot detection) is deterministic Python. The LLM is used only for intent routing, explanations, and policy reasoning, and the app must still work (with template-based explanations) if the LLM quota is exhausted.
8. **Make it deployable.** Everything must run with `docker compose up` locally and be deployable to free tiers (Section 11).
9. **Do not ask for clarification unless blocked.** Make a reasonable decision, document it in `docs/DECISIONS.md`, and continue.
10. **Human prerequisites** (API keys) are listed in Section 12. If a key is missing, run in fallback mode, do not stop.
11. **Prototype scope.** Routing is limited to a fixed set of preset origin–destination pairs (Section 3A) and two vehicle types: car and truck / heavy vehicle (Section 3B). There is no free-form address search at runtime.
12. **The LLM provider is Groq** (see "LLM provider: Groq" in Section 7). Never use a Llama model, and never hardcode a single model ID; discover active models at runtime.
