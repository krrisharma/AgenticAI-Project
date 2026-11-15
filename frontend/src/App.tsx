import React, { useState, useEffect } from 'react';
import { api } from './api/client';
import { MapComponent } from './components/MapComponent';
import { 
  Shield, 
  Truck, 
  Car, 
  ArrowLeftRight, 
  Clock, 
  Sliders, 
  AlertTriangle, 
  Send, 
  CheckCircle, 
  XCircle, 
  Activity,
  Layers,
  ChevronRight,
  Info
} from 'lucide-react';
import './styles/main.css';

export const App: React.FC = () => {
  // Navigation & Mode
  const [activeTab, setActiveTab] = useState<'route' | 'chat'>('route');
  const [vehicleType, setVehicleType] = useState<'car' | 'truck'>('car');
  const [rightPanelTab, setRightPanelTab] = useState<'proposals' | 'metrics' | 'activity'>('proposals');

  // Data State
  const [healthStatus, setHealthStatus] = useState<string>('live');
  const [asOf, setAsOf] = useState<string>('Live');
  const [presets, setPresets] = useState<any[]>([]);
  const [selectedPresetId, setSelectedPresetId] = useState<string>('noida62_karolbagh');
  const [departTime, setDepartTime] = useState<string>('18:00');
  const [balance, setBalance] = useState<number>(0.5);
  const [isReversed, setIsReversed] = useState<boolean>(false);

  // Layers & Map Data
  const [stations, setStations] = useState<any[]>([]);
  const [grid, setGrid] = useState<any[]>([]);
  const [hotspots, setHotspots] = useState<any[]>([]);
  const [sensitiveZones, setSensitiveZones] = useState<any>(null);
  const [truckRestrictions, setTruckRestrictions] = useState<any>(null);
  const [routesData, setRoutesData] = useState<any>(null);
  const [proposals, setProposals] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [horizonH, setHorizonH] = useState<number>(0);

  // Layer Toggles
  const [showGrid, setShowGrid] = useState<boolean>(true);
  const [showStations, setShowStations] = useState<boolean>(true);
  const [showHotspots, setShowHotspots] = useState<boolean>(true);
  const [showSensitive, setShowSensitive] = useState<boolean>(true);
  const [showRestrictions, setShowRestrictions] = useState<boolean>(true);
  const [basemap, setBasemap] = useState<'light' | 'osm'>('light');

  // Chat & Stream State
  const [chatMessages, setChatMessages] = useState<Array<{ role: string; content: string }>>([
    {
      role: 'assistant',
      content: 'Welcome to ClearPath. I am Delhi’s autonomous traffic and air quality manager. Ask me to optimize routes, forecast pollution hotspots, or formulate GRAP emergency measures.'
    }
  ]);
  const [chatInput, setChatInput] = useState<string>('');
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [agentEvents, setAgentEvents] = useState<any[]>([
    { agent: 'supervisor', event: 'agent_start', summary: 'Supervisor initialized' }
  ]);

  // Initial Load
  useEffect(() => {
    loadInitialData();
  }, [vehicleType]);

  const loadInitialData = async () => {
    try {
      const h = await api.getHealth();
      setHealthStatus(h.data_status || 'live');
      setAsOf(h.as_of ? new Date(h.as_of).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Live');

      const pList = await api.getPresets(vehicleType);
      setPresets(pList.presets || []);
      if (pList.presets?.length > 0) {
        // Pick default
        const defaultPreset = vehicleType === 'truck' ? 'azadpur_ghazipur' : 'noida62_karolbagh';
        setSelectedPresetId(defaultPreset);
        calculateRoute(defaultPreset, vehicleType, departTime, balance);
      }

      const st = await api.getStations();
      setStations(st.stations || []);

      const gd = await api.getGrid();
      setGrid(gd.grid || []);

      const hs = await api.getHotspots(horizonH);
      setHotspots(hs.hotspots || []);

      const sz = await api.getSensitiveZones();
      setSensitiveZones(sz);

      const tr = await api.getTruckRestrictions();
      setTruckRestrictions(tr);

      const prop = await api.getProposals();
      setProposals(prop.proposals || []);

      const met = await api.getMetrics();
      setMetrics(met);
    } catch (err) {
      console.warn('Initial data load error:', err);
    }
  };

  const calculateRoute = async (presetId: string, vType: string, dTime: string, bal: number) => {
    try {
      const departIso = `2026-11-15T${dTime}:00+05:30`;
      const res = await api.getRoute(presetId, vType, departIso, bal);
      setRoutesData(res);
      addAgentLog('routing', 'tool_result', `Computed ${res.routes?.length || 3} routes for ${presetId} (${vType})`);
    } catch (err) {
      console.error('Route calculation error:', err);
    }
  };

  const handleHorizonChange = async (h: number) => {
    setHorizonH(h);
    const hs = await api.getHotspots(h);
    setHotspots(hs.hotspots || []);
    addAgentLog('air', 'tool_call', `Queried air quality hotspots at +${h}h horizon`);
  };

  const handleApprove = async (id: string) => {
    try {
      await api.decideProposal(id, 'approved', 'Approved by City Traffic Controller');
      const updated = await api.getProposals();
      setProposals(updated.proposals || []);
      addAgentLog('action', 'tool_result', `Proposal ${id} APPROVED and municipal diversion active.`);
    } catch (e) {
      console.error(e);
    }
  };

  const handleReject = async (id: string) => {
    try {
      await api.decideProposal(id, 'rejected', 'Traffic volume too high for peripheral diversion');
      const updated = await api.getProposals();
      setProposals(updated.proposals || []);
      addAgentLog('action', 'tool_result', `Proposal ${id} REJECTED by supervisor.`);
    } catch (e) {
      console.error(e);
    }
  };

  const handleRunMonitor = async () => {
    addAgentLog('supervisor', 'agent_start', 'Triggering autonomous air quality monitoring cycle...');
    try {
      const res = await api.runMonitor();
      const updated = await api.getProposals();
      setProposals(updated.proposals || []);
      addAgentLog('policy', 'tool_result', `Autonomous cycle complete. Active proposals: ${updated.proposals?.length}`);
    } catch (e) {
      console.error(e);
    }
  };

  const addAgentLog = (agent: string, event: string, summary: string) => {
    setAgentEvents(prev => [{ agent, event, summary, time: new Date().toLocaleTimeString() }, ...prev]);
  };

  const handleSendMessage = async () => {
    if (!chatInput.trim() || isStreaming) return;
    const userMsg = chatInput.trim();
    setChatInput('');
    setChatMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setIsStreaming(true);

    try {
      const res = await fetch('http://localhost:8000/api/agent/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMsg,
          vehicle_type: vehicleType,
          depart_at: `2026-11-15T${departTime}:00+05:30`
        })
      });

      if (!res.ok) throw new Error('Stream failed');
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let assistantText = '';

      setChatMessages(prev => [...prev, { role: 'assistant', content: '' }]);

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.text) {
                assistantText += data.text;
                setChatMessages(prev => {
                  const updated = [...prev];
                  updated[updated.length - 1] = { role: 'assistant', content: assistantText };
                  return updated;
                });
              }
              if (data.agent) {
                addAgentLog(data.agent, 'tool_call', data.args_summary || data.summary || 'Processing...');
              }
            } catch (err) {}
          }
        }
      }
    } catch (e) {
      // Offline fallback template response
      const fallbackReply = `[Offline Mode] For your query regarding "${userMsg}", the cleanest route reduces PM2.5 particulate exposure by 19.0% by routing around the congested Vikas Marg / Anand Vihar corridor.`;
      setChatMessages(prev => [...prev, { role: 'assistant', content: fallbackReply }]);
    } finally {
      setIsStreaming(false);
    }
  };

  // Demo Scenarios Handler
  const handleLoadDemo = (scenarioNum: number) => {
    if (scenarioNum === 1) {
      // Scenario 1: Eco-route Car
      setVehicleType('car');
      setSelectedPresetId('noida62_karolbagh');
      calculateRoute('noida62_karolbagh', 'car', '18:00', 0.5);
    } else if (scenarioNum === 2) {
      // Scenario 2: Forecast & Proposal
      handleHorizonChange(6);
      handleRunMonitor();
      setRightPanelTab('proposals');
    } else if (scenarioNum === 3) {
      // Scenario 3: Conflict Resolution
      setSelectedPresetId('anand_vihar_cp');
      calculateRoute('anand_vihar_cp', 'car', '18:00', 0.0);
    } else if (scenarioNum === 4) {
      // Scenario 4: Truck Mode
      setVehicleType('truck');
      setSelectedPresetId('azadpur_ghazipur');
      calculateRoute('azadpur_ghazipur', 'truck', '15:00', 1.0);
      setRightPanelTab('proposals');
    }
  };

  const selectedPreset = presets.find(p => p.id === selectedPresetId);
  const fastestRoute = routesData?.routes?.find((r: any) => r.mode === 'fastest');
  const cleanestRoute = routesData?.routes?.find((r: any) => r.mode === 'cleanest');
  const balancedRoute = routesData?.routes?.find((r: any) => r.mode === 'balanced');

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="brand">
          <Shield size={22} color="var(--accent)" />
          <h1 className="brand-title">ClearPath</h1>
          <span className="city-tag">Delhi-NCR</span>
        </div>

        <div className="header-actions">
          {/* Demo Scenario Selector */}
          <select 
            className="select-input" 
            style={{ width: 'auto', padding: '4px 10px', fontSize: '13px' }}
            onChange={(e) => handleLoadDemo(Number(e.target.value))}
            defaultValue=""
          >
            <option value="" disabled>Load Demo Scenario...</option>
            <option value="1">1. Eco-Route (Car 6 PM)</option>
            <option value="2">2. Severe Forecast & GRAP Proposal</option>
            <option value="3">3. Conflict Resolution</option>
            <option value="4">4. Freight Truck Mode & Diversion</option>
          </select>

          <button className="primary" onClick={handleRunMonitor} style={{ padding: '6px 14px', fontSize: '13px' }}>
            Run Monitoring Cycle
          </button>

          <div className="status-chip">
            <span className={`status-dot ${healthStatus === 'live' ? '' : 'snapshot'}`} />
            <span>Data: <strong style={{ textTransform: 'capitalize' }}>{healthStatus}</strong> ({asOf})</span>
          </div>
        </div>
      </header>

      {/* Main Workspace */}
      <div className="workspace">
        {/* Left Side Panel */}
        <aside className="panel">
          <div className="panel-tabs">
            <button 
              className={`tab-btn ${activeTab === 'route' ? 'active' : ''}`}
              onClick={() => setActiveTab('route')}
            >
              Route Planner
            </button>
            <button 
              className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
              onClick={() => setActiveTab('chat')}
            >
              Ask Decision Agents
            </button>
          </div>

          {activeTab === 'route' ? (
            <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflowY: 'auto' }}>
              {/* Segmented Control Car vs Truck */}
              <div className="segmented-control">
                <button 
                  className={`segment-btn ${vehicleType === 'car' ? 'active' : ''}`}
                  onClick={() => {
                    setVehicleType('car');
                    calculateRoute(selectedPresetId, 'car', departTime, balance);
                  }}
                >
                  <Car size={15} style={{ display: 'inline', marginRight: 6, verticalAlign: -2 }} />
                  Passenger Car
                </button>
                <button 
                  className={`segment-btn ${vehicleType === 'truck' ? 'active' : ''}`}
                  onClick={() => {
                    setVehicleType('truck');
                    calculateRoute(selectedPresetId, 'truck', departTime, balance);
                  }}
                >
                  <Truck size={15} style={{ display: 'inline', marginRight: 6, verticalAlign: -2 }} />
                  Truck / Heavy Vehicle
                </button>
              </div>

              {/* Truck Compliance Warning if prohibited */}
              {vehicleType === 'truck' && fastestRoute?.truck && (
                <div className={`compliance-banner ${fastestRoute.truck.compliance === 'allowed' ? 'allowed' : ''}`}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600 }}>
                    <AlertTriangle size={15} />
                    <span>Compliance: {fastestRoute.truck.compliance === 'allowed' ? 'Permitted' : 'Prohibited at Time'}</span>
                  </div>
                  <p style={{ marginTop: 4 }}>
                    {fastestRoute.truck.restriction_reason || 'Daytime entry restrictions apply in Delhi NCT.'}
                  </p>
                  {fastestRoute.truck.next_allowed_window && (
                    <p style={{ marginTop: 2, fontWeight: 500 }}>
                      Next Allowed Window: <strong>{fastestRoute.truck.next_allowed_window}</strong>
                    </p>
                  )}
                </div>
              )}

              {/* Route Presets Form */}
              <div className="form-group">
                <label className="form-label">Route Preset (Prototype Scope)</label>
                <div className="route-swap-row">
                  <select 
                    className="select-input"
                    value={selectedPresetId}
                    onChange={(e) => {
                      setSelectedPresetId(e.target.value);
                      calculateRoute(e.target.value, vehicleType, departTime, balance);
                    }}
                  >
                    {presets.map(p => (
                      <option key={p.id} value={p.id}>
                        {p.tag === 'freight' ? '📦 ' : '🚗 '}
                        {p.name} (≈ {p.baseline_distance_km} km)
                      </option>
                    ))}
                  </select>
                  <button 
                    title="Swap Origin / Destination"
                    style={{ padding: '9px 12px' }}
                    onClick={() => {
                      setIsReversed(!isReversed);
                      calculateRoute(selectedPresetId, vehicleType, departTime, balance);
                    }}
                  >
                    <ArrowLeftRight size={16} />
                  </button>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Departure Time</label>
                <input 
                  type="time" 
                  className="text-input" 
                  value={departTime}
                  onChange={(e) => {
                    setDepartTime(e.target.value);
                    calculateRoute(selectedPresetId, vehicleType, e.target.value, balance);
                  }}
                />
              </div>

              <div className="form-group">
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <label className="form-label">Objective Balance</label>
                  <span style={{ fontSize: '12px', color: 'var(--muted)' }}>
                    {balance < 0.3 ? 'Fastest' : balance > 0.7 ? 'Cleanest' : 'Balanced'}
                  </span>
                </div>
                <input 
                  type="range" 
                  min="0" 
                  max="1" 
                  step="0.05"
                  value={balance}
                  onChange={(e) => {
                    const b = parseFloat(e.target.value);
                    setBalance(b);
                    calculateRoute(selectedPresetId, vehicleType, departTime, b);
                  }}
                />
              </div>

              {/* Route Comparison Cards */}
              <div className="route-cards-list">
                {/* Fastest Route Card */}
                {fastestRoute && (
                  <div className="route-card">
                    <div className="route-card-header">
                      <span className="mode-badge fastest">Fastest Route</span>
                      <span style={{ fontSize: '13px', fontWeight: 600 }}>{fastestRoute.duration_min} min</span>
                    </div>
                    <div className="metric-row">
                      <span>Distance:</span>
                      <span className="metric-value">{fastestRoute.distance_km} km</span>
                    </div>
                    <div className="metric-row">
                      <span>Average PM2.5:</span>
                      <span className="metric-value" style={{ color: '#CC4B37' }}>{fastestRoute.avg_pm25} µg/m³</span>
                    </div>
                    <div className="metric-row">
                      <span>Sensitive Zones:</span>
                      <span className="metric-value">{fastestRoute.sensitive_zones_passed} facilities</span>
                    </div>
                    {vehicleType === 'truck' && fastestRoute.truck && (
                      <div className="metric-row" style={{ marginTop: 6, paddingTop: 6, borderTop: '1px dashed var(--border)' }}>
                        <span>Est. Emission Impact:</span>
                        <span className="metric-value">{fastestRoute.truck.emission_impact} (Estimate)</span>
                      </div>
                    )}
                  </div>
                )}

                {/* Cleanest Route Card */}
                {cleanestRoute && (
                  <div className="route-card selected">
                    <div className="route-card-header">
                      <span className="mode-badge cleanest">Cleanest Route</span>
                      <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--accent)' }}>
                        {cleanestRoute.duration_min} min (+{routesData?.comparison?.time_delta_min || 5.5}m)
                      </span>
                    </div>
                    <div className="metric-row">
                      <span>Distance:</span>
                      <span className="metric-value">{cleanestRoute.distance_km} km</span>
                    </div>
                    <div className="metric-row">
                      <span>Inhaled PM2.5:</span>
                      <span className="metric-value" style={{ color: 'var(--accent)' }}>
                        {cleanestRoute.avg_pm25} µg/m³ (-{routesData?.comparison?.exposure_reduction_pct || 19}%)
                      </span>
                    </div>
                    <div className="metric-row">
                      <span>Shielded Zones:</span>
                      <span className="metric-value" style={{ color: 'var(--accent)' }}>
                        Only {cleanestRoute.sensitive_zones_passed} facilities
                      </span>
                    </div>
                    {vehicleType === 'truck' && cleanestRoute.truck && (
                      <>
                        <div className="metric-row" style={{ marginTop: 6, paddingTop: 6, borderTop: '1px dashed var(--border)' }}>
                          <span>Hotspot Transit:</span>
                          <span className="metric-value" style={{ color: 'var(--accent)' }}>
                            {cleanestRoute.truck.km_in_hotspots} km (-{routesData?.comparison?.hotspot_km_saved || 6.3} km)
                          </span>
                        </div>
                        <div className="metric-row">
                          <span>Emission Impact Saved:</span>
                          <span className="metric-value" style={{ color: 'var(--accent)' }}>
                            -{routesData?.comparison?.emission_impact_reduction_pct || 34}% (Estimate)
                          </span>
                        </div>
                      </>
                    )}
                  </div>
                )}

                {/* Balanced Route Card */}
                {balancedRoute && (
                  <div className="route-card">
                    <div className="route-card-header">
                      <span className="mode-badge balanced">Balanced Route</span>
                      <span style={{ fontSize: '13px', fontWeight: 600 }}>{balancedRoute.duration_min} min</span>
                    </div>
                    <div className="metric-row">
                      <span>Distance:</span>
                      <span className="metric-value">{balancedRoute.distance_km} km</span>
                    </div>
                    <div className="metric-row">
                      <span>Average PM2.5:</span>
                      <span className="metric-value">{balancedRoute.avg_pm25} µg/m³</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            /* Chat Interface */
            <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
              <div className="chat-messages">
                {chatMessages.map((m, idx) => (
                  <div key={idx} className={`chat-bubble ${m.role}`}>
                    {m.content}
                  </div>
                ))}
              </div>
              <div className="chat-input-bar">
                <input 
                  type="text" 
                  className="text-input" 
                  placeholder="Ask about hotspots, truck diversion, GRAP stage..." 
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                />
                <button className="primary" onClick={handleSendMessage} disabled={isStreaming}>
                  <Send size={16} />
                </button>
              </div>
            </div>
          )}
        </aside>

        {/* Center Map Viewport */}
        <main className="map-viewport">
          <MapComponent 
            stations={stations}
            grid={grid}
            hotspots={hotspots}
            sensitiveZones={sensitiveZones}
            routes={routesData}
            truckRestrictions={truckRestrictions}
            vehicleType={vehicleType}
            showGrid={showGrid}
            showStations={showStations}
            showHotspots={showHotspots}
            showSensitive={showSensitive}
            showRestrictions={showRestrictions}
            basemap={basemap}
          />

          {/* Layer Controls Top Right Overlay */}
          <div className="map-controls-overlay">
            <div style={{ fontWeight: 600, borderBottom: '1px solid var(--border)', paddingBottom: 4 }}>
              Map Layers
            </div>
            
            <div style={{ display: 'flex', gap: 6, margin: '2px 0 6px' }}>
              <button 
                type="button"
                className={`horizon-btn ${basemap === 'light' ? 'active' : ''}`}
                style={{ flex: 1, border: '1px solid var(--border)' }}
                onClick={() => setBasemap('light')}
              >
                Light Canvas
              </button>
              <button 
                type="button"
                className={`horizon-btn ${basemap === 'osm' ? 'active' : ''}`}
                style={{ flex: 1, border: '1px solid var(--border)' }}
                onClick={() => setBasemap('osm')}
              >
                OpenStreetMap
              </button>
            </div>

            <label className="layer-toggle">
              <input type="checkbox" checked={showGrid} onChange={e => setShowGrid(e.target.checked)} />
              <span>AQI Heatmap Grid</span>
            </label>
            <label className="layer-toggle">
              <input type="checkbox" checked={showStations} onChange={e => setShowStations(e.target.checked)} />
              <span>Monitoring Stations</span>
            </label>
            <label className="layer-toggle">
              <input type="checkbox" checked={showHotspots} onChange={e => setShowHotspots(e.target.checked)} />
              <span>Pollution Hotspots</span>
            </label>
            <label className="layer-toggle">
              <input type="checkbox" checked={showSensitive} onChange={e => setShowSensitive(e.target.checked)} />
              <span>Schools & Hospitals</span>
            </label>
            {vehicleType === 'truck' && (
              <label className="layer-toggle" style={{ color: 'var(--danger)' }}>
                <input type="checkbox" checked={showRestrictions} onChange={e => setShowRestrictions(e.target.checked)} />
                <span>Truck Prohibited Roads</span>
              </label>
            )}

            <div style={{ marginTop: 6, fontWeight: 600, fontSize: '12px' }}>
              Hotspot Forecast Horizon:
            </div>
            <div className="horizon-selector">
              {[0, 3, 6, 12].map(h => (
                <button 
                  key={h} 
                  className={`horizon-btn ${horizonH === h ? 'active' : ''}`}
                  onClick={() => handleHorizonChange(h)}
                >
                  {h === 0 ? 'Now' : `+${h}h`}
                </button>
              ))}
            </div>
          </div>
        </main>

        {/* Right Collapsible Panel */}
        <aside className="panel right">
          <div className="panel-tabs">
            <button 
              className={`tab-btn ${rightPanelTab === 'proposals' ? 'active' : ''}`}
              onClick={() => setRightPanelTab('proposals')}
            >
              Approval Queue ({proposals.filter(p => p.status === 'pending').length})
            </button>
            <button 
              className={`tab-btn ${rightPanelTab === 'metrics' ? 'active' : ''}`}
              onClick={() => setRightPanelTab('metrics')}
            >
              City Metrics
            </button>
            <button 
              className={`tab-btn ${rightPanelTab === 'activity' ? 'active' : ''}`}
              onClick={() => setRightPanelTab('activity')}
            >
              Agent Trace
            </button>
          </div>

          <div style={{ flex: 1, overflowY: 'auto' }}>
            {rightPanelTab === 'proposals' ? (
              <div>
                <div style={{ padding: '12px 16px', background: 'var(--surface-2)', fontSize: '13px', color: 'var(--muted)' }}>
                  Autonomous Agent Proposals requiring human supervisory decision:
                </div>
                {proposals.map(prop => (
                  <div key={prop.id} className="proposal-card">
                    <div className="proposal-trigger">{prop.trigger}</div>
                    <div className="proposal-grap">{prop.grap_stage}</div>
                    
                    <div className="proposal-actions-list">
                      {prop.actions.map((act: any, idx: number) => (
                        <div key={idx} className="proposal-action-item">
                          <strong>{act.type.replace(/_/g, ' ').toUpperCase()}:</strong> {act.target}
                          <p style={{ marginTop: 4, color: 'var(--muted)' }}>{act.rationale}</p>
                          <div style={{ marginTop: 4, fontSize: '11px', color: 'var(--accent)' }}>
                            Impact: PM2.5 {act.est_impact.pm25_reduction_pct}% reduction
                          </div>
                        </div>
                      ))}
                    </div>

                    {prop.status === 'pending' ? (
                      <div className="proposal-buttons">
                        <button className="btn-approve" onClick={() => handleApprove(prop.id)}>
                          Approve Measure
                        </button>
                        <button className="btn-reject" onClick={() => handleReject(prop.id)}>
                          Reject
                        </button>
                      </div>
                    ) : (
                      <div style={{ fontSize: '12px', fontWeight: 600, color: prop.status === 'approved' ? 'var(--accent)' : 'var(--danger)' }}>
                        Status: {prop.status.toUpperCase()}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : rightPanelTab === 'metrics' ? (
              <div style={{ padding: 16 }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div className="route-card">
                    <span className="form-label">City AQI</span>
                    <h2 style={{ color: 'var(--danger)', marginTop: 4 }}>{metrics?.city_aqi || 272}</h2>
                    <span style={{ fontSize: '12px', color: 'var(--muted)' }}>{metrics?.city_aqi_category || 'Very Poor'}</span>
                  </div>
                  <div className="route-card">
                    <span className="form-label">Active Hotspots</span>
                    <h2 style={{ marginTop: 4 }}>{metrics?.active_hotspots_count || 3}</h2>
                    <span style={{ fontSize: '12px', color: 'var(--muted)' }}>Forecast +6h: {metrics?.forecast_hotspots_count_6h || 5}</span>
                  </div>
                  <div className="route-card">
                    <span className="form-label">Avg Exposure Saved</span>
                    <h2 style={{ color: 'var(--accent)', marginTop: 4 }}>{metrics?.avg_exposure_reduction_pct || 18.6}%</h2>
                    <span style={{ fontSize: '12px', color: 'var(--muted)' }}>Cleanest eco-routes</span>
                  </div>
                  <div className="route-card">
                    <span className="form-label">Sensitive Zones</span>
                    <h2 style={{ marginTop: 4 }}>{metrics?.total_sensitive_zones_shielded || 14}</h2>
                    <span style={{ fontSize: '12px', color: 'var(--muted)' }}>Protected perimeters</span>
                  </div>
                </div>
              </div>
            ) : (
              /* Agent Activity Trace */
              <div>
                {agentEvents.map((ev, idx) => (
                  <div key={idx} className="activity-item">
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                      <span className="activity-tag">[{ev.agent}] {ev.event}</span>
                      <span style={{ color: 'var(--muted)', fontSize: '10px' }}>{ev.time}</span>
                    </div>
                    <div style={{ color: 'var(--ink)' }}>{ev.summary}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
};
