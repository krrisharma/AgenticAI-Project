export const API_BASE = import.meta.env.VITE_API_BASE_URL || (typeof window !== 'undefined' && window.location.hostname === 'localhost' ? 'http://localhost:8000' : '');

export async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  if (API_BASE) {
    const url = `${API_BASE}${endpoint}`;
    try {
      const res = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...(options.headers || {})
        }
      });
      if (res.ok) {
        return await res.json();
      }
    } catch (e) {
      console.warn(`API call ${endpoint} failed, falling back to local snapshot fixtures:`, e);
    }
  }
  
  // Monitor Run Fallback
  if (endpoint.includes('/monitor/run')) {
    return {
      status: "completed",
      hotspots_analyzed: 4,
      severe_hotspots_count: 2,
      proposal_created: true,
      pending_proposal_id: "pp_001"
    } as any;
  }

  // Decision Fallback
  if (endpoint.includes('/decision')) {
    return { status: "ok", decision: "approved" } as any;
  }

  // Route fallback handling
  if (endpoint.startsWith('/api/route')) {
    const isTruck = options.body && options.body.toString().includes('"truck"');
    const fRes = await fetch(isTruck ? '/contracts/fixtures/route_truck.json' : '/contracts/fixtures/route_car.json');
    return await fRes.json();
  }

  // Fixture fallback mapping
  const fixtureMap: Record<string, string> = {
    '/api/health': '/contracts/fixtures/health.json',
    '/api/aqi/stations': '/contracts/fixtures/stations.json',
    '/api/aqi/grid': '/contracts/fixtures/grid.json',
    '/api/aqi/forecast': '/contracts/fixtures/forecast.json',
    '/api/hotspots': '/contracts/fixtures/hotspots.json',
    '/api/sensitive-zones': '/contracts/fixtures/sensitive_zones.json',
    '/api/presets': '/contracts/fixtures/presets.json',
    '/api/truck/restrictions': '/contracts/fixtures/truck_restrictions.json',
    '/api/policy/proposals': '/contracts/fixtures/proposals.json',
    '/api/metrics/summary': '/contracts/fixtures/metrics.json'
  };

  const pathKey = Object.keys(fixtureMap).find(k => endpoint.startsWith(k));
  if (pathKey) {
    const fRes = await fetch(fixtureMap[pathKey]);
    return await fRes.json();
  }
  throw new Error(`Endpoint ${endpoint} failed and no fixture matched.`);
}

export const api = {
  getHealth: () => apiRequest<any>('/api/health'),
  getStations: () => apiRequest<any>('/api/aqi/stations'),
  getGrid: () => apiRequest<any>('/api/aqi/grid'),
  getForecast: (hours: number = 24) => apiRequest<any>(`/api/aqi/forecast?hours=${hours}`),
  getHotspots: (horizon_h: number = 0) => apiRequest<any>(`/api/hotspots?horizon_h=${horizon_h}`),
  getSensitiveZones: () => apiRequest<any>('/api/sensitive-zones'),
  getPresets: (vehicle_type: string = 'car') => apiRequest<any>(`/api/presets?vehicle_type=${vehicle_type}`),
  getRoute: (preset_id: string, vehicle_type: string = 'car', depart_at?: string, balance: number = 0.5) => 
    apiRequest<any>('/api/route', {
      method: 'POST',
      body: JSON.stringify({ preset_id, vehicle_type, depart_at, balance })
    }),
  getTruckRestrictions: () => apiRequest<any>('/api/truck/restrictions'),
  getProposals: () => apiRequest<any>('/api/policy/proposals'),
  decideProposal: (id: string, decision: 'approved' | 'rejected', officer_note?: string) =>
    apiRequest<any>(`/api/policy/proposals/${id}/decision`, {
      method: 'POST',
      body: JSON.stringify({ decision, officer_note })
    }),
  getMetrics: () => apiRequest<any>('/api/metrics/summary'),
  runMonitor: () => apiRequest<any>('/api/agent/monitor/run', { method: 'POST' })
};
