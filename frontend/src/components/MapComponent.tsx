import React, { useEffect, useRef } from 'react';
import L from 'leaflet';

interface MapProps {
  stations: any[];
  grid: any[];
  hotspots: any[];
  sensitiveZones: any;
  routes: any;
  truckRestrictions: any;
  vehicleType: string;
  showGrid: boolean;
  showStations: boolean;
  showHotspots: boolean;
  showSensitive: boolean;
  showRestrictions: boolean;
  onSelectHotspot?: (hs: any) => void;
}

const AQI_COLORS: Record<string, string> = {
  Good: '#3F8F4F',
  Satisfactory: '#8DB94A',
  Moderate: '#E3C23A',
  Poor: '#E08A2E',
  'Very Poor': '#CC4B37',
  Severe: '#8E2A24'
};

export const MapComponent: React.FC<MapProps> = ({
  stations,
  grid,
  hotspots,
  sensitiveZones,
  routes,
  truckRestrictions,
  vehicleType,
  showGrid,
  showStations,
  showHotspots,
  showSensitive,
  showRestrictions,
  onSelectHotspot
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const layersRef = useRef<{ [key: string]: L.LayerGroup }>({});

  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    // Center on Delhi NCT
    const map = L.map(mapContainerRef.current, {
      center: [28.625, 77.22],
      zoom: 11,
      zoomControl: true
    });

    // CARTO Positron light basemap
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      maxZoom: 19
    }).addTo(map);

    layersRef.current.grid = L.layerGroup().addTo(map);
    layersRef.current.stations = L.layerGroup().addTo(map);
    layersRef.current.hotspots = L.layerGroup().addTo(map);
    layersRef.current.sensitive = L.layerGroup().addTo(map);
    layersRef.current.restrictions = L.layerGroup().addTo(map);
    layersRef.current.routes = L.layerGroup().addTo(map);

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update Grid
  useEffect(() => {
    const layer = layersRef.current.grid;
    if (!layer) return;
    layer.clearLayers();
    if (!showGrid || !grid) return;

    grid.forEach(cell => {
      const color = AQI_COLORS[cell.category] || '#E08A2E';
      L.circleMarker([cell.lat, cell.lon], {
        radius: 12,
        fillColor: color,
        color: 'transparent',
        weight: 0,
        fillOpacity: 0.28
      }).addTo(layer);
    });
  }, [grid, showGrid]);

  // Update Stations
  useEffect(() => {
    const layer = layersRef.current.stations;
    if (!layer) return;
    layer.clearLayers();
    if (!showStations || !stations) return;

    stations.forEach(st => {
      const color = AQI_COLORS[st.category] || '#E08A2E';
      const icon = L.divIcon({
        className: 'custom-station-icon',
        html: `<div class="station-pin" style="background-color: ${color};">${st.aqi}</div>`,
        iconSize: [28, 28],
        iconAnchor: [14, 14]
      });

      L.marker([st.lat, st.lon], { icon })
        .bindPopup(`
          <div style="font-family: inherit; font-size: 13px;">
            <strong style="color: #1F2421;">${st.name}</strong><br/>
            <span>AQI: <strong style="color: ${color};">${st.aqi} (${st.category})</strong></span><br/>
            <span>PM2.5: ${st.pm25 || 'N/A'} µg/m³</span><br/>
            <span style="font-size: 11px; color: #6B706B;">Updated: ${st.updated_at.slice(11, 16)} UTC</span>
          </div>
        `)
        .addTo(layer);
    });
  }, [stations, showStations]);

  // Update Hotspots
  useEffect(() => {
    const layer = layersRef.current.hotspots;
    if (!layer) return;
    layer.clearLayers();
    if (!showHotspots || !hotspots) return;

    hotspots.forEach(hs => {
      const color = AQI_COLORS[hs.category] || '#CC4B37';
      const circle = L.circle([hs.centroid.lat, hs.centroid.lon], {
        radius: hs.radius_m,
        color: color,
        weight: 2,
        fillColor: color,
        fillOpacity: 0.25,
        dashArray: '4, 4'
      }).addTo(layer);

      circle.bindPopup(`
        <div style="font-family: inherit; font-size: 13px;">
          <strong style="color: #1F2421;">${hs.name}</strong><br/>
          <span>Pollution Band: <strong style="color: ${color};">${hs.category} (AQI ${hs.aqi})</strong></span><br/>
          <span>PM2.5: ${hs.pm25} µg/m³</span><br/>
          <div style="margin-top: 6px; font-size: 12px;"><strong>Key Drivers:</strong></div>
          <ul style="padding-left: 16px; margin: 4px 0; font-size: 11px; color: #3A3F3B;">
            ${hs.drivers.map((d: string) => `<li>${d}</li>`).join('')}
          </ul>
        </div>
      `);
    });
  }, [hotspots, showHotspots]);

  // Update Sensitive Zones
  useEffect(() => {
    const layer = layersRef.current.sensitive;
    if (!layer) return;
    layer.clearLayers();
    if (!showSensitive || !sensitiveZones?.features) return;

    sensitiveZones.features.forEach((feat: any) => {
      const [lon, lat] = feat.geometry.coordinates;
      const isHospital = feat.properties.amenity === 'hospital';
      const color = isHospital ? '#B5412F' : '#C7782A';

      L.circleMarker([lat, lon], {
        radius: 6,
        fillColor: color,
        color: '#FFFFFF',
        weight: 1.5,
        fillOpacity: 0.9
      }).bindPopup(`
        <div style="font-family: inherit; font-size: 12px;">
          <strong>${feat.properties.name}</strong><br/>
          <span>Type: ${feat.properties.amenity}</span><br/>
          <span>Protected Perimeter: ${feat.properties.buffer_m}m</span>
        </div>
      `).addTo(layer);
    });
  }, [sensitiveZones, showSensitive]);

  // Update Truck Restrictions
  useEffect(() => {
    const layer = layersRef.current.restrictions;
    if (!layer) return;
    layer.clearLayers();
    if (!showRestrictions || vehicleType !== 'truck' || !truckRestrictions?.features) return;

    truckRestrictions.features.forEach((feat: any) => {
      const latlngs = feat.geometry.coordinates.map((c: any) => [c[1], c[0]]);
      L.polyline(latlngs, {
        color: '#B5412F',
        weight: 5,
        opacity: 0.85,
        dashArray: '6, 6'
      }).bindPopup(`
        <div style="font-family: inherit; font-size: 12px;">
          <strong style="color: #B5412F;">${feat.properties.name}</strong><br/>
          <span>Restriction: ${feat.properties.restriction_type}</span><br/>
          <span>Allowed: ${feat.properties.allowed_hours}</span>
        </div>
      `).addTo(layer);
    });
  }, [truckRestrictions, showRestrictions, vehicleType]);

  // Update Routes
  useEffect(() => {
    const layer = layersRef.current.routes;
    if (!layer) return;
    layer.clearLayers();
    if (!routes?.routes) return;

    routes.routes.forEach((r: any) => {
      let color = '#3A3F3B'; // fastest = neutral charcoal
      let dashArray = undefined;
      let weight = 4;

      if (r.mode === 'cleanest') {
        color = '#2E6B4F'; // cleanest = forest green
        weight = 5;
      } else if (r.mode === 'balanced') {
        color = '#C7782A'; // balanced = amber
        dashArray = '8, 8';
        weight = 4;
      }

      L.polyline(r.geometry, {
        color,
        weight,
        opacity: 0.9,
        dashArray
      }).bindPopup(`
        <div style="font-family: inherit; font-size: 13px;">
          <strong style="text-transform: capitalize; color: ${color};">${r.mode} Route</strong><br/>
          <span>Distance: ${r.distance_km} km</span><br/>
          <span>Est. Time: ${r.duration_min} min</span><br/>
          <span>Avg PM2.5: ${r.avg_pm25} µg/m³</span><br/>
          ${r.truck ? `<span>Hotspot Transit: ${r.truck.km_in_hotspots} km</span>` : ''}
        </div>
      `).addTo(layer);
    });
  }, [routes]);

  return <div ref={mapContainerRef} className="map-viewport" />;
};
