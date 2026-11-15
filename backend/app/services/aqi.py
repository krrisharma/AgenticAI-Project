"""CPCB National Air Quality Index (NAQI) calculation service.

Implements the official sub-index method published by the Central Pollution Control Board (CPCB),
Ministry of Environment, Forest and Climate Change, Govt. of India.
Reference: https://cpcb.nic.in/air-quality-index/
"""

from typing import Dict, Optional, Tuple

# Breakpoint tables: (C_low, C_high, I_low, I_high)
BREAKPOINTS_PM25 = [
    (0.0, 30.0, 0, 50),
    (31.0, 60.0, 51, 100),
    (61.0, 90.0, 101, 200),
    (91.0, 120.0, 201, 300),
    (121.0, 250.0, 301, 400),
    (250.1, 500.0, 401, 500),
]

BREAKPOINTS_PM10 = [
    (0.0, 50.0, 0, 50),
    (51.0, 100.0, 51, 100),
    (101.0, 250.0, 101, 200),
    (251.0, 350.0, 201, 300),
    (351.0, 430.0, 301, 400),
    (430.1, 600.0, 401, 500),
]

BREAKPOINTS_NO2 = [
    (0.0, 40.0, 0, 50),
    (41.0, 80.0, 51, 100),
    (81.0, 180.0, 101, 200),
    (181.0, 280.0, 201, 300),
    (281.0, 400.0, 301, 400),
    (400.1, 600.0, 401, 500),
]

CATEGORIES = [
    (0, 50, "Good"),
    (51, 100, "Satisfactory"),
    (101, 200, "Moderate"),
    (201, 300, "Poor"),
    (301, 400, "Very Poor"),
    (401, 1000, "Severe"),
]


def calculate_sub_index(conc: float, breakpoints: list) -> int:
    """Calculate sub-index for a given pollutant concentration."""
    if conc is None or conc < 0:
        return 0
    
    # Clip to max if beyond table
    max_c_high = breakpoints[-1][1]
    if conc > max_c_high:
        return 500

    for c_low, c_high, i_low, i_high in breakpoints:
        if c_low <= conc <= c_high:
            sub = i_low + ((i_high - i_low) / (c_high - c_low)) * (conc - c_low)
            return int(round(sub))
    
    # In case of small floating gap between bands
    for i in range(len(breakpoints) - 1):
        if breakpoints[i][1] < conc < breakpoints[i+1][0]:
            # Associate with the upper boundary of lower band or lower of next
            c_low, c_high, i_low, i_high = breakpoints[i]
            sub = i_low + ((i_high - i_low) / (c_high - c_low)) * (conc - c_low)
            return int(round(sub))

    return 500


def get_category(aqi_value: int) -> str:
    """Map numeric AQI to CPCB descriptor."""
    for low, high, cat in CATEGORIES:
        if low <= aqi_value <= high:
            return cat
    return "Severe"


def calculate_cpcb_aqi(
    pm25: Optional[float] = None,
    pm10: Optional[float] = None,
    no2: Optional[float] = None
) -> Tuple[int, str, str, Dict[str, int]]:
    """
    Calculate the overall CPCB AQI from available pollutant concentrations.
    Returns:
        (overall_aqi, category, dominant_pollutant, sub_indices_dict)
    """
    sub_indices: Dict[str, int] = {}
    
    if pm25 is not None and pm25 >= 0:
        sub_indices["pm25"] = calculate_sub_index(pm25, BREAKPOINTS_PM25)
    if pm10 is not None and pm10 >= 0:
        sub_indices["pm10"] = calculate_sub_index(pm10, BREAKPOINTS_PM10)
    if no2 is not None and no2 >= 0:
        sub_indices["no2"] = calculate_sub_index(no2, BREAKPOINTS_NO2)
        
    if not sub_indices:
        return 0, "Good", "none", {}

    dominant = max(sub_indices, key=sub_indices.get)
    overall_aqi = sub_indices[dominant]
    category = get_category(overall_aqi)
    
    return overall_aqi, category, dominant, sub_indices
