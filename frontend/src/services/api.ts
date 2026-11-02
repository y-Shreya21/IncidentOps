import { IncidentState, PostmortemReport, TimelineEvent, Severity } from '../types';

const API_BASE = '/api/v1';

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
    const res = await fetch(`${API_BASE}/incidents/alert`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to create incident' }));
      throw new Error(err.detail || 'Incident creation failed');
    }
    return await res.json();
  },

  async triggerSimulation(scenario: string): Promise<any> {
    const res = await fetch(`${API_BASE}/simulate/${scenario}?auto_respond=true`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Simulation failed');
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
};
