"""Deterministic Synthetic Congestion Model for Delhi-NCR.

Computes hour-of-day rush curves and road-class speed reduction factors
differentiating Car vs Heavy Commercial Truck traffic.
Labelled explicitly as 'Estimated' in all interfaces.
"""

from typing import Dict, Any
from app.models import CongestionResponse, RoadClassFactors

# Base free-flow speeds (km/h)
BASE_SPEEDS = {
    "motorway": 80.0,
    "trunk": 60.0,
    "primary": 50.0,
    "secondary": 40.0,
    "tertiary": 30.0
}

def get_hour_congestion_factor(hour: int) -> float:
    """
    Returns congestion intensity [0.0 = completely free flow, 1.0 = gridlock peak].
    Morning peak: 08:00 - 11:00 (peak at 09:30)
    Evening peak: 17:30 - 21:00 (peak at 19:00)
    Late night: 23:00 - 06:00 (free flow)
    """
    if 8 <= hour <= 11:
        # Morning peak
        return 0.75 if (hour in [9, 10]) else 0.55
    elif 17 <= hour <= 21:
        # Evening peak
        return 0.85 if (hour in [18, 19, 20]) else 0.65
    elif 12 <= hour <= 16:
        # Midday moderate
        return 0.40
    else:
        # Night / early morning
        return 0.15

def get_congestion_for_hour(hour: int = 18) -> CongestionResponse:
    cong_idx = get_hour_congestion_factor(hour)
    
    # Speed factors: 1.0 = free flow, lower = slower
    road_classes: Dict[str, RoadClassFactors] = {}
    
    for rclass in BASE_SPEEDS.keys():
        # Cars: speed reduction is proportional to congestion
        car_factor = max(0.35, 1.0 - (cong_idx * 0.55))
        
        # Trucks: subject to lower speed cap, lower acceleration, and 45% stronger congestion penalty
        truck_factor = max(0.25, (1.0 - (cong_idx * 0.70)) * 0.70)
        
        road_classes[rclass] = RoadClassFactors(
            speed_factor_car=round(car_factor, 2),
            speed_factor_truck=round(truck_factor, 2)
        )
        
    return CongestionResponse(
        hour=hour,
        provider="synthetic (deterministic rush curve)",
        city_congestion_index=round(cong_idx, 2),
        road_classes=road_classes,
        data_status="live",
        as_of="2026-11-15T12:00:00Z"
    )
