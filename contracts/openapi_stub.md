# ClearPath API OpenAPI Specification Stub

All JSON responses use `snake_case`. All timestamps are ISO 8601 UTC.
Every data response includes `data_status` (`live` | `cached` | `snapshot`) and `as_of`.

## Endpoints

### 1. Health
`GET /api/health`
Response:
```json
{
  "status": "ok",
  "data_status": "live",
  "as_of": "2026-11-15T12:00:00Z",
  "sources": {
    "openaq": "live",
    "open_meteo_aq": "live",
    "open_meteo_weather": "live",
    "traffic": "synthetic"
  }
}
```

### 2. Station AQI Readings
`GET /api/aqi/stations`
Response: Array of station objects:
```json
{
  "stations": [
    {
      "id": "delhi_anand_vihar",
      "name": "Anand Vihar, Delhi",
      "lat": 28.6508,
      "lon": 77.3152,
      "pm25": 284.5,
      "pm10": 395.2,
      "no2": 68.4,
      "aqi": 348,
      "category": "Severe",
      "dominant_pollutant": "pm25",
      "updated_at": "2026-11-15T11:45:00Z"
    }
  ],
  "data_status": "live",
  "as_of": "2026-11-15T12:00:00Z"
}
```

### 3. AQI Interpolated Grid
`GET /api/aqi/grid`
Response:
```json
{
  "grid": [
    {
      "lat": 28.61,
      "lon": 77.23,
      "pm25": 142.3,
      "aqi": 317,
      "category": "Very Poor"
    }
  ],
  "bounds": {
    "min_lat": 28.40,
    "max_lat": 28.88,
    "min_lon": 76.84,
    "max_lon": 77.35
  },
  "resolution_km": 1.0,
  "data_status": "live",
  "as_of": "2026-11-15T12:00:00Z"
}
```

### 4. Hourly Forecast
`GET /api/aqi/forecast?hours=24`
Response:
```json
{
  "forecast": [
    {
      "timestamp": "2026-11-15T13:00:00Z",
      "horizon_h": 1,
      "avg_pm25": 165.2,
      "avg_aqi": 335,
      "category": "Very Poor",
      "top_hotspots": ["hs_anand_vihar", "hs_wazirpur"]
    }
  ],
  "data_status": "live",
  "as_of": "2026-11-15T12:00:00Z"
}
```

### 5. Hotspot Detection
`GET /api/hotspots?horizon_h=0`
Response:
```json
{
  "horizon_h": 0,
  "hotspots": [
    {
      "id": "hs_001",
      "name": "Anand Vihar Hub",
      "centroid": {"lat": 28.6508, "lon": 77.3152},
      "radius_m": 1500,
      "pm25": 284.5,
      "aqi": 348,
      "category": "Severe",
      "horizon_h": 0,
      "drivers": ["low wind speed (< 1.5 m/s)", "heavy interstate bus idling", "boundary layer inversion"],
      "nearby_sensitive_zones": [
        {"type": "school", "name": "St. Andrews Senior School", "distance_m": 420},
        {"type": "hospital", "name": "Max Super Speciality Hospital", "distance_m": 850}
      ]
    }
  ],
  "data_status": "live",
  "as_of": "2026-11-15T12:00:00Z"
}
```

### 6. Traffic Congestion
`GET /api/traffic/congestion?hour=18`
Response:
```json
{
  "hour": 18,
  "provider": "synthetic",
  "city_congestion_index": 0.74,
  "road_classes": {
    "motorway": {"speed_factor_car": 0.65, "speed_factor_truck": 0.50},
    "trunk": {"speed_factor_car": 0.55, "speed_factor_truck": 0.40},
    "primary": {"speed_factor_car": 0.45, "speed_factor_truck": 0.32},
    "secondary": {"speed_factor_car": 0.50, "speed_factor_truck": 0.35},
    "tertiary": {"speed_factor_car": 0.60, "speed_factor_truck": 0.45}
  },
  "data_status": "live",
  "as_of": "2026-11-15T12:00:00Z"
}
```

### 7. Sensitive Zones (Schools, Hospitals, Clinics)
`GET /api/sensitive-zones`
Response: GeoJSON FeatureCollection of schools and healthcare facilities.

### 8. Presets
`GET /api/presets?vehicle_type=car`
Response:
```json
{
  "presets": [
    {
      "id": "noida62_karolbagh",
      "name": "Noida Sector 62 → Karol Bagh",
      "from_name": "Noida Sector 62",
      "to_name": "Karol Bagh",
      "from_coords": [28.6271, 77.3629],
      "to_coords": [28.6514, 77.1907],
      "tag": "general",
      "baseline_distance_km": 24.2,
      "baseline_duration_min_car": 46.5,
      "baseline_duration_min_truck": 72.0
    }
  ]
}
```

### 9. Route Planning
`POST /api/route`
Request:
```json
{
  "preset_id": "noida62_karolbagh",
  "reverse": false,
  "vehicle_type": "car",
  "depart_at": "2026-11-15T18:00:00Z",
  "balance": 0.5
}
```
Response:
```json
{
  "vehicle_type": "car",
  "preset_id": "noida62_karolbagh",
  "routes": [
    {
      "mode": "fastest",
      "geometry": [[28.6271, 77.3629], [28.6514, 77.1907]],
      "distance_km": 24.2,
      "duration_min": 48.0,
      "avg_pm25": 195.4,
      "exposure_index": 9379.2,
      "sensitive_zones_passed": 7,
      "truck": null
    },
    {
      "mode": "cleanest",
      "geometry": [[28.6271, 77.3629], [28.6514, 77.1907]],
      "distance_km": 26.8,
      "duration_min": 53.5,
      "avg_pm25": 142.0,
      "exposure_index": 7597.0,
      "sensitive_zones_passed": 2,
      "truck": null
    },
    {
      "mode": "balanced",
      "geometry": [[28.6271, 77.3629], [28.6514, 77.1907]],
      "distance_km": 25.1,
      "duration_min": 50.2,
      "avg_pm25": 160.5,
      "exposure_index": 8057.1,
      "sensitive_zones_passed": 3,
      "truck": null
    }
  ],
  "comparison": {
    "time_delta_min": 5.5,
    "exposure_reduction_pct": 19.0
  },
  "data_status": "live",
  "as_of": "2026-11-15T12:00:00Z"
}
```

### 10. Truck Restrictions & Rules
`GET /api/truck/restrictions`
Response:
GeoJSON FeatureCollection of restricted segments + truck timing metadata.

### 11. Policy Proposals
`GET /api/policy/proposals?status=pending`
`POST /api/policy/proposals/{id}/decision`
Request: `{"decision": "approved | rejected", "officer_note": "Approved for 4 hours"}`

### 12. Metrics Summary
`GET /api/metrics/summary`

### 13. Agent Chat SSE Stream
`POST /api/agent/chat/stream`
Stream SSE events:
- `event: agent_start` `{"agent": "supervisor"}`
- `event: tool_call` `{"agent": "routing", "tool": "compute_routes", "args_summary": "..."}`
- `event: tool_result` `{"agent": "routing", "tool": "compute_routes", "summary": "..."}`
- `event: token` `{"text": "..."}`
- `event: approval_required` `{"proposal_id": "pp_001"}`
- `event: final` `{"message": "...", "route": {...}, "hotspots": [...]}`
- `event: error` `{"message": "..."}`
