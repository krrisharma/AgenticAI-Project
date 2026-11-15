from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal

# --- Common ---
class BaseDataResponse(BaseModel):
    data_status: Literal["live", "cached", "snapshot"] = "live"
    as_of: str

# --- Health ---
class HealthResponse(BaseModel):
    status: str = "ok"
    data_status: Literal["live", "cached", "snapshot"] = "live"
    as_of: str
    sources: Dict[str, str]

# --- AQI & Stations ---
class StationReading(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    pm25: Optional[float] = None
    pm10: Optional[float] = None
    no2: Optional[float] = None
    aqi: int
    category: str
    dominant_pollutant: str = "pm25"
    updated_at: str
    source: str = "openaq"

class StationListResponse(BaseDataResponse):
    stations: List[StationReading]

# --- Grid & Heatmap ---
class GridCell(BaseModel):
    lat: float
    lon: float
    pm25: float
    aqi: int
    category: str

class GridBounds(BaseModel):
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float

class GridResponse(BaseDataResponse):
    grid: List[GridCell]
    bounds: GridBounds
    resolution_km: float = 1.0

# --- Forecast ---
class ForecastPoint(BaseModel):
    timestamp: str
    horizon_h: int
    avg_pm25: float
    avg_aqi: int
    category: str
    hotspot_count: int = 0
    top_hotspots: Optional[List[str]] = None

class ForecastResponse(BaseDataResponse):
    forecast: List[ForecastPoint]

# --- Hotspots ---
class Centroid(BaseModel):
    lat: float
    lon: float

class SensitiveZoneRef(BaseModel):
    type: str
    name: str
    distance_m: Optional[int] = None

class Hotspot(BaseModel):
    id: str
    name: str
    centroid: Centroid
    radius_m: int = 1500
    pm25: float
    aqi: int
    category: str
    horizon_h: int = 0
    drivers: List[str]
    nearby_sensitive_zones: List[SensitiveZoneRef] = []

class HotspotsResponse(BaseDataResponse):
    horizon_h: int
    hotspots: List[Hotspot]

# --- Traffic & Congestion ---
class RoadClassFactors(BaseModel):
    speed_factor_car: float
    speed_factor_truck: float

class CongestionResponse(BaseDataResponse):
    hour: int
    provider: str = "synthetic"
    city_congestion_index: float
    road_classes: Dict[str, RoadClassFactors]

# --- Presets ---
class PresetRoute(BaseModel):
    id: str
    name: str
    from_name: str
    to_name: str
    from_coords: List[float] # [lat, lon]
    to_coords: List[float]   # [lat, lon]
    tag: Literal["general", "freight"]
    baseline_distance_km: float
    baseline_duration_min_car: float
    baseline_duration_min_truck: float

class PresetsResponse(BaseModel):
    presets: List[PresetRoute]

# --- Routing ---
class RouteRequest(BaseModel):
    preset_id: str
    reverse: bool = False
    vehicle_type: Literal["car", "truck"] = "car"
    depart_at: Optional[str] = None
    balance: float = 0.5 # 0.0 = fastest, 1.0 = cleanest

class TruckMetrics(BaseModel):
    emission_impact: float
    km_in_hotspots: float
    restricted_segments: int = 0
    compliance: Literal["allowed", "not_allowed_at_time", "unverified"] = "allowed"
    next_allowed_window: Optional[str] = None
    restriction_reason: Optional[str] = None

class RouteOption(BaseModel):
    mode: Literal["fastest", "cleanest", "balanced"]
    geometry: List[List[float]] # [[lat, lon], ...]
    distance_km: float
    duration_min: float
    avg_pm25: float
    exposure_index: float
    sensitive_zones_passed: int
    truck: Optional[TruckMetrics] = None

class RouteComparison(BaseModel):
    time_delta_min: float
    exposure_reduction_pct: float
    emission_impact_reduction_pct: Optional[float] = None
    hotspot_km_saved: Optional[float] = None

class RouteResponse(BaseDataResponse):
    vehicle_type: Literal["car", "truck"]
    preset_id: str
    routes: List[RouteOption]
    comparison: RouteComparison

# --- Proposals ---
class ProposalActionImpact(BaseModel):
    pm25_reduction_pct: float
    added_delay_min: float
    confidence: Literal["low", "medium", "high"] = "medium"

class ProposalAction(BaseModel):
    type: Literal["divert_heavy_vehicles", "adjust_signal_timing", "publish_advisory", "restrict_zone"]
    target: str
    rationale: str
    est_impact: ProposalActionImpact
    source_refs: List[str]

class PolicyProposal(BaseModel):
    id: str
    created_at: str
    trigger: str
    grap_stage: str
    actions: List[ProposalAction]
    status: Literal["pending", "approved", "rejected"] = "pending"
    decided_at: Optional[str] = None
    officer_note: Optional[str] = None

class ProposalsResponse(BaseModel):
    proposals: List[PolicyProposal]

class ProposalDecisionRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    officer_note: Optional[str] = None

# --- Metrics ---
class MetricsSummary(BaseDataResponse):
    city_aqi: int
    city_aqi_category: str
    dominant_pollutant: str
    active_hotspots_count: int
    forecast_hotspots_count_6h: int
    pending_proposals_count: int
    approved_proposals_today: int
    avg_exposure_reduction_pct: float
    total_sensitive_zones_shielded: int

# --- Chat & Agent ---
class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    depart_at: Optional[str] = None
    vehicle_type: Literal["car", "truck"] = "car"
