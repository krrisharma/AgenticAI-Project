import pytest
from app.services.aqi import calculate_cpcb_aqi, calculate_sub_index, get_category, BREAKPOINTS_PM25

def test_pm25_sub_index():
    # Good band: 15 µg/m³ -> 25 AQI
    assert calculate_sub_index(15.0, BREAKPOINTS_PM25) == 25
    # Boundary: 30 µg/m³ -> 50 AQI
    assert calculate_sub_index(30.0, BREAKPOINTS_PM25) == 50
    # Satisfactory: 45 µg/m³ -> 76 AQI
    assert 70 <= calculate_sub_index(45.0, BREAKPOINTS_PM25) <= 80
    # Very Poor: 150 µg/m³ -> between 301 and 400
    assert 301 <= calculate_sub_index(150.0, BREAKPOINTS_PM25) <= 400
    # Severe: 300 µg/m³ -> > 400
    assert calculate_sub_index(300.0, BREAKPOINTS_PM25) >= 401

def test_category_labels():
    assert get_category(45) == "Good"
    assert get_category(85) == "Satisfactory"
    assert get_category(150) == "Moderate"
    assert get_category(250) == "Poor"
    assert get_category(350) == "Very Poor"
    assert get_category(450) == "Severe"

def test_overall_aqi_dominant():
    # PM2.5 = 200 (Very Poor, ~360 AQI), NO2 = 40 (Good, 50 AQI)
    overall, cat, dominant, subs = calculate_cpcb_aqi(pm25=200.0, no2=40.0)
    assert dominant == "pm25"
    assert cat == "Very Poor"
    assert 301 <= overall <= 400
    assert subs["pm25"] == overall
