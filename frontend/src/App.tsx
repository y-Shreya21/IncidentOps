import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { OverviewPage } from './pages/OverviewPage';
import { IncidentManagementPage } from './pages/IncidentManagementPage';
import { AgentWarRoomPage } from './pages/AgentWarRoomPage';
import { BlackboardPage } from './pages/BlackboardPage';
import { DecisionPage } from './pages/DecisionPage';
import { TimelinePage } from './pages/TimelinePage';
import { PostmortemPage } from './pages/PostmortemPage';
import { SettingsPage } from './pages/SettingsPage';
import { api } from './services/api';
import { IncidentState, UserRole, Severity } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [incidents, setIncidents] = useState<IncidentState[]>([]);
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  const [role, setRole] = useState<UserRole>('IncidentResponder');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const fetchIncidents = async () => {
    setLoading(true);
    try {
      const data = await api.listIncidents();
      setIncidents(data);
      if (data.length > 0 && !selectedIncidentId) {
        setSelectedIncidentId(data[0].incident_id);
      }
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
  }, []);

  const selectedIncident = incidents.find((i) => i.incident_id === selectedIncidentId) || incidents[0] || null;

  const getErrorMessage = (e: any, fallback: string): string => {
    if (!e) return fallback;
    if (typeof e === 'string') return e;
    if (typeof e.message === 'string' && e.message !== '[object Object]') return e.message;
    if (typeof e.detail === 'string') return e.detail;
    try {
      return JSON.stringify(e);
    } catch {
      return fallback;
    }
  };

  const handleSimulate = async (scenario: string) => {
    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const res = await api.triggerSimulation(scenario);
      await fetchIncidents();
      if (res?.postmortem?.incident_id) {
        setSelectedIncidentId(res.postmortem.incident_id);
        setActiveTab('war_room');
      }
    } catch (e: any) {
      setErrorMsg(getErrorMessage(e, 'Simulation execution failed'));
    } finally {
      setLoading(false);
    }
  };

  const handleCreateIncident = async (payload: {
    service: string;
    symptom: string;
    severity: Severity;
    description: string;
    timestamp?: string;
  }) => {
    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const report = await api.createAlert(payload);
      await fetchIncidents();
      if (report?.incident_id) {
        setSelectedIncidentId(report.incident_id);
        setActiveTab('war_room');
      }
    } catch (e: any) {
      setErrorMsg(getErrorMessage(e, 'Failed to ingest alert'));
    } finally {
      setLoading(false);
    }
  };

  const handleApproveMitigation = async (incidentId: string, action: string, targetService: string) => {
    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      await api.approveMitigation(incidentId, action, targetService);
      setSuccessMsg(`✅ Mitigation [${action.toUpperCase()}] on ${targetService} executed and recorded in the audit log!`);
      await fetchIncidents();
    } catch (e: any) {
      setErrorMsg(getErrorMessage(e, 'Failed to approve mitigation'));
    } finally {
      setLoading(false);
    }
  };

  const handleEscalateIncident = async (incidentId: string) => {
    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      await api.escalateIncident(incidentId);
      setSuccessMsg(`⚠️ Incident ${incidentId} flagged and escalated to Senior SRE on-call team!`);
      await fetchIncidents();
    } catch (e: any) {
      setErrorMsg(getErrorMessage(e, 'Failed to escalate incident'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        incidents={incidents}
        selectedIncidentId={selectedIncidentId}
        onSelectIncident={(id) => {
          setSelectedIncidentId(id);
          if (activeTab === 'overview') setActiveTab('war_room');
        }}
        role={role}
        onRefresh={fetchIncidents}
        loading={loading}
      />

      {errorMsg && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4 w-full">
          <div className="bg-red-950/80 border border-red-800 text-red-200 p-3 rounded-lg text-xs flex justify-between items-center">
            <span>{errorMsg}</span>
            <button onClick={() => setErrorMsg(null)} className="font-bold ml-4">✕</button>
          </div>
        </div>
      )}

      {successMsg && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4 w-full">
          <div className="bg-emerald-950/80 border border-emerald-800 text-emerald-200 p-3 rounded-lg text-xs flex justify-between items-center">
            <span>{successMsg}</span>
            <button onClick={() => setSuccessMsg(null)} className="font-bold ml-4">✕</button>
          </div>
        </div>
      )}

      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 w-full">
        {activeTab === 'overview' && (
          <OverviewPage
            incidents={incidents}
            onSelectIncident={(id) => {
              setSelectedIncidentId(id);
              setActiveTab('war_room');
            }}
            onSimulate={handleSimulate}
            loading={loading}
          />
        )}

        {activeTab === 'management' && (
          <IncidentManagementPage
            incidents={incidents}
            onSelectIncident={(id) => {
              setSelectedIncidentId(id);
              setActiveTab('war_room');
            }}
            onCreateIncident={handleCreateIncident}
            loading={loading}
          />
        )}

        {activeTab === 'war_room' && <AgentWarRoomPage incident={selectedIncident} />}

        {activeTab === 'blackboard' && <BlackboardPage incident={selectedIncident} />}

        {activeTab === 'decision' && (
          <DecisionPage
            incident={selectedIncident}
            onApproveMitigation={handleApproveMitigation}
            onEscalate={handleEscalateIncident}
            loading={loading}
          />
        )}

        {activeTab === 'timeline' && <TimelinePage incident={selectedIncident} />}

        {activeTab === 'postmortem' && <PostmortemPage incident={selectedIncident} />}

        {activeTab === 'settings' && <SettingsPage role={role} onRoleChange={setRole} />}
      </main>

      <footer className="border-t border-slate-900 bg-slate-950 py-4 text-center text-xs text-slate-600">
        AI IncidentOps • Autonomous Multi-Agent IT Incident Response War-Room • Blackboard Architecture
      </footer>
    </div>
  );
};

export default App;
