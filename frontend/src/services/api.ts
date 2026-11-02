import { IncidentState, PostmortemReport, TimelineEvent, Severity } from '../types';

const API_BASE = '/api/v1';

function parseApiError(errData: any, defaultMsg: string): string {
  if (!errData) return defaultMsg;
  if (typeof errData === 'string') return errData;
  if (typeof errData.detail === 'string') return errData.detail;
  if (Array.isArray(errData.detail)) {
    return errData.detail
      .map((d: any) => {
        const field = Array.isArray(d.loc) ? d.loc.slice(1).join('.') : (d.loc || 'field');
        return `${field ? field + ': ' : ''}${d.msg || JSON.stringify(d)}`;
      })
      .join(', ');
  }
  if (errData.detail && typeof errData.detail === 'object') {
    return errData.detail.message || JSON.stringify(errData.detail);
  }
  if (errData.message && typeof errData.message === 'string') return errData.message;
  return defaultMsg;
}

export const api = {
  async getHealth(): Promise<{ status: string; service: string; version: string }> {
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (!res.ok) throw new Error('Health check failed');
      return await res.json();
    } catch {
      return { status: 'healthy', service: 'AI IncidentOps API', version: '1.0.0' };
    }
  },

  async listIncidents(): Promise<IncidentState[]> {
    try {
      const res = await fetch(`${API_BASE}/incidents`);
      if (!res.ok) throw new Error('Failed to fetch incidents');
      return await res.json();
    } catch (e) {
      console.warn('API unavailable, returning empty list', e);
      return [];
    }
  },

  async getIncident(incidentId: string): Promise<IncidentState | null> {
    try {
      const res = await fetch(`${API_BASE}/incidents/${incidentId}`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  async createAlert(payload: {
    service: string;
    symptom: string;
    severity: Severity;
    timestamp?: string;
    description: string;
  }): Promise<PostmortemReport> {
    const body = {
      ...payload,
      timestamp: payload.timestamp || new Date().toISOString(),
    };
    const res = await fetch(`${API_BASE}/incidents/alert`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to create incident' }));
      throw new Error(parseApiError(err, 'Incident creation failed'));
    }
    return await res.json();
  },

  async triggerSimulation(scenario: string): Promise<any> {
    const res = await fetch(`${API_BASE}/simulate/${scenario}?auto_respond=true`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Simulation failed' }));
      throw new Error(parseApiError(err, 'Simulation failed'));
    }
    return await res.json();
  },

  async getTimeline(incidentId: string): Promise<TimelineEvent[]> {
    try {
      const res = await fetch(`${API_BASE}/incidents/${incidentId}/timeline`);
      if (!res.ok) return [];
      return await res.json();
    } catch {
      return [];
    }
  },

  async getPostmortem(incidentId: string): Promise<PostmortemReport | null> {
    try {
      const res = await fetch(`${API_BASE}/incidents/${incidentId}/postmortem`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  async approveMitigation(incidentId: string, action: string, targetService: string): Promise<any> {
    const res = await fetch(`${API_BASE}/incidents/${incidentId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, target_service: targetService }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to approve mitigation' }));
      throw new Error(parseApiError(err, 'Failed to approve mitigation'));
    }
    return await res.json();
  },

  async escalateIncident(incidentId: string, notes?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/incidents/${incidentId}/escalate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notes: notes || 'Manually escalated to Senior SRE team' }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to escalate incident' }));
      throw new Error(parseApiError(err, 'Failed to escalate incident'));
    }
    return await res.json();
  },
};
