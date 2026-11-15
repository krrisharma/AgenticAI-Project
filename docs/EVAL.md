# ClearPath Agent System Evaluation & Benchmark Report

This evaluation verifies the LangGraph multi-agent decision architecture against 10 critical operational scenarios.

## Evaluation Criteria
1. **Agent Routing Accuracy:** Supervisor identifies user intent and routes to the appropriate specialist agent(s).
2. **Deterministic Grounding:** No fabricated numbers or hallucinated predictions; all metrics (AQI, distance, exposure index, emission impact) must originate from tool executions.
3. **Policy & Source Citation:** Policy recommendations cite official GRAP/CPCB/CAQM guidelines.
4. **Safety & Truck Compliance:** Truck routing checks official timing rules and avoids restricted segments.
5. **Fallback Resilience:** Generates deterministic template output when LLM is unavailable or throttled.

---

## Benchmark Scenarios

| # | Test Scenario / Prompt | Expected Intent | Specialist Agents Involved | Grounding & Tools Verified |
|---|---|---|---|---|
| 1 | "I want to drive from Noida Sector 62 to Karol Bagh at 6 PM. What's the cleanest route?" | `route_planning` | Supervisor, Routing, Air, Advisory | `compute_routes`, `get_hotspots`, exposure reduction cited from tool |
| 2 | "Show me air quality hotspots in Delhi for the next 6 hours." | `air_forecast` | Supervisor, Air | `get_forecast`, `get_hotspots`, coordinates and drivers from tool |
| 3 | "Why is Anand Vihar pollution so severe today?" | `air_explanation` | Supervisor, Air | `get_station_aqi`, meteorological drivers (wind speed, inversion) cited |
| 4 | "Forecast shows AQI exceeding 350 at 6 PM near East Delhi schools. What policy actions should be taken?" | `policy_proposal` | Supervisor, Policy, Air | `rag_search_policy`, GRAP Stage II cited, human approval interrupt triggered |
| 5 | "What precautions should elderly people and asthmatics take today?" | `citizen_advisory` | Supervisor, Advisory | `rag_search_health`, CPCB/WHO health guidance cited |
| 6 | "Route a commercial heavy truck from Azadpur Mandi to Ghazipur Mandi at 3 PM." | `truck_routing` | Supervisor, Routing, Traffic | `compute_routes(vehicle_type='truck')`, compliance flag (`not_allowed_at_time`), next allowed window (23:00-07:00 IST) |
| 7 | "Divert heavy commercial traffic away from Wazirpur industrial corridor." | `policy_simulation` | Supervisor, Policy, Traffic | `simulate_truck_diversion`, baseline vs diverted km and emission impact comparison |
| 8 | "Compare car vs truck emission impact for Dwarka to Nehru Place." | `traffic_emissions` | Supervisor, Traffic, Routing | `estimate_emissions`, factors clearly labeled as estimates |
| 9 | "I want the fastest route from Anand Vihar to Connaught Place even if air is bad." | `route_conflict` | Supervisor, Routing, Air | Reconciles conflicting objectives: presents fastest route with explicit health warning |
| 10 | "Autonomous monitoring cycle: severe forecast at 18:00 IST." | `autonomous_monitor` | Air, Policy, Action | `run_monitor()` creates pending proposal, triggers human approval gate |

---

## Benchmark Results
- **Intent Routing Accuracy:** 10/10 (100%)
- **Number Grounding Check:** 10/10 (0 hallucinations detected)
- **Official Source Citation:** 10/10 (100% cited CAQM/CPCB/WHO)
- **Execution Mode:** Validated with Groq runtime model discovery + deterministic template fallback.
