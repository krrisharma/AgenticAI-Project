# ClearPath Data Sources & Attribution

All data sources used in ClearPath are cited, verified, cached, and carry fallback snapshots to guarantee offline and resilient operation.

## 1. Air Quality Station Measurements
- **Primary Provider:** OpenAQ API v3 (`https://api.openaq.org/v3`)
- **Parameters:** PM2.5, PM10, NO2 for Delhi-NCR continuous monitoring stations (CPCB & DPCC).
- **Secondary Provider:** WAQI (World Air Quality Index - aqicn.org) API
- **Cache TTL:** 30 minutes
- **Fallback:** Pre-packaged JSON snapshot (`backend/data/snapshots/stations_delhi.json`)

## 2. Air Quality Gridded Forecast
- **Provider:** Open-Meteo Air Quality API (`https://air-quality-api.open-meteo.com/v1/air-quality`)
- **Parameters:** Hourly `pm2_5`, `pm10`, `nitrogen_dioxide` up to 5 days ahead across Delhi bounding coordinates.
- **Cache TTL:** 60 minutes
- **Fallback:** Forecast snapshot (`backend/data/snapshots/forecast_delhi.json`)

## 3. Atmospheric Weather
- **Provider:** Open-Meteo Forecast API (`https://api.open-meteo.com/v1/forecast`)
- **Parameters:** Wind speed (10m), wind direction, temperature, relative humidity, boundary layer height.
- **Cache TTL:** 60 minutes
- **Fallback:** Weather snapshot

## 4. Road Network & Sensitive Zones
- **Road Network Source:** OpenStreetMap contributors via Overpass / osmnx.
- **Coverage:** Delhi NCT bounding polygon extended east to encompass Noida Sector 62 corridor.
- **Sensitive Features:** `amenity=school`, `amenity=hospital`, `amenity=clinic`, `amenity=college`.
- **License:** Open Database License (ODbL) © OpenStreetMap contributors.

## 5. Traffic Congestion Model
- **Primary Source:** Deterministic synthetic traffic congestion model:
  - Hour-of-day rush curves (morning peak 8:00-11:00, evening peak 17:30-21:00).
  - Road functional hierarchy (motorway, trunk, primary, secondary, tertiary).
  - Differentiated car vs heavy vehicle speed reduction curves.
- **Labeling:** Explicitly labeled as "Estimated Congestion" in all UI cards and tool outputs.

## 6. Official Policies & Health Knowledge Base
- **CPCB:** National Air Quality Index (NAQI) breakpoints and calculation methodology (Central Pollution Control Board, Ministry of Environment, Forest and Climate Change, Govt. of India).
- **CAQM:** Graded Response Action Plan (GRAP) Stages I to IV directives for Delhi-NCR (Commission for Air Quality Management in NCR and Adjoining Areas).
- **WHO:** WHO Global Air Quality Guidelines (2021).
- **Delhi Traffic Police:** Heavy commercial vehicle entry restrictions, time windows, and no-entry zones.
