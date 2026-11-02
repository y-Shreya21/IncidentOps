import React from 'react';
import { IncidentState } from '../types';
import { AlertTriangle, CheckCircle, ShieldAlert, Activity, Server, Zap, Clock } from 'lucide-react';

interface Props {
  incidents: IncidentState[];
  onSelectIncident: (id: string) => void;
  onSimulate: (scenario: string) => void;
  loading: boolean;
}

export const OverviewPage: React.FC<Props> = ({
  incidents,
  onSelectIncident,
  onSimulate,
  loading,
}) => {
  const criticalCount = incidents.filter((i) => i.severity === 'critical').length;
  const highCount = incidents.filter((i) => i.severity === 'high').length;
  const escalatedCount = incidents.filter((i) => i.status === 'escalated').length;
  const activeCount = incidents.filter((i) => i.status !== 'resolved').length;

  const services = [
    { name: 'frontend', tier: 'Tier-1', port: 3000, status: 'Healthy' },
    { name: 'payment-api', tier: 'Tier-1', port: 8080, status: criticalCount > 0 ? 'Degraded' : 'Healthy' },
    { name: 'auth-service', tier: 'Tier-1', port: 8081, status: 'Healthy' },
    { name: 'postgres', tier: 'Tier-0', port: 5432, status: criticalCount > 0 ? 'Unhealthy' : 'Healthy' },
  ];

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-slate-400 text-sm font-medium">Active Incidents</span>
            <Activity className="w-5 h-5 text-blue-400" />
          </div>
          <div className="text-3xl font-bold mt-2 text-white">{activeCount}</div>
          <div className="text-xs text-slate-500 mt-1">Total recorded: {incidents.length}</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-slate-400 text-sm font-medium">Critical Outages</span>
            <ShieldAlert className="w-5 h-5 text-red-400" />
          </div>
          <div className="text-3xl font-bold mt-2 text-red-400">{criticalCount}</div>
          <div className="text-xs text-slate-500 mt-1">Sev-1 P1 Priority</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-slate-400 text-sm font-medium">High Severity</span>
            <AlertTriangle className="w-5 h-5 text-amber-400" />
          </div>
          <div className="text-3xl font-bold mt-2 text-amber-400">{highCount}</div>
          <div className="text-xs text-slate-500 mt-1">Sev-2 Degradation</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-slate-400 text-sm font-medium">Escalated to SRE</span>
            <Clock className="w-5 h-5 text-purple-400" />
          </div>
          <div className="text-3xl font-bold mt-2 text-purple-400">{escalatedCount}</div>
          <div className="text-xs text-slate-500 mt-1">Human War-Room Required</div>
        </div>
      </div>

      {/* Quick Simulation Triggers */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
        <h2 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
          <Zap className="w-5 h-5 text-yellow-400" />
          Quick Failure Scenario Simulator
        </h2>
        <p className="text-sm text-slate-400 mb-4">
          Trigger reproducible end-to-end multi-agent IT incident war-room investigations:
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <button
            onClick={() => onSimulate('db_failure')}
            disabled={loading}
            className="flex flex-col text-left p-4 rounded-lg bg-red-950/40 border border-red-800/50 hover:bg-red-900/40 transition disabled:opacity-50"
          >
            <span className="font-semibold text-red-200">💥 Scenario A: DB Outage</span>
            <span className="text-xs text-slate-400 mt-1">Postgres unreachable; connection pool timeouts.</span>
          </button>

          <button
            onClick={() => onSimulate('deployment_failure')}
            disabled={loading}
            className="flex flex-col text-left p-4 rounded-lg bg-amber-950/40 border border-amber-800/50 hover:bg-amber-900/40 transition disabled:opacity-50"
          >
            <span className="font-semibold text-amber-200">🚀 Scenario B: Bad Release</span>
            <span className="text-xs text-slate-400 mt-1">v2.4.1 deployment bug; rollback evaluation.</span>
          </button>

          <button
            onClick={() => onSimulate('high_cpu')}
            disabled={loading}
            className="flex flex-col text-left p-4 rounded-lg bg-blue-950/40 border border-blue-800/50 hover:bg-blue-900/40 transition disabled:opacity-50"
          >
            <span className="font-semibold text-blue-200">🔥 Scenario C: High CPU</span>
            <span className="text-xs text-slate-400 mt-1">98% CPU thread lock; worker restart proposal.</span>
          </button>

          <button
            onClick={() => onSimulate('insufficient_evidence')}
            disabled={loading}
            className="flex flex-col text-left p-4 rounded-lg bg-purple-950/40 border border-purple-800/50 hover:bg-purple-900/40 transition disabled:opacity-50"
          >
            <span className="font-semibold text-purple-200">❓ Scenario D: Vague Blip</span>
            <span className="text-xs text-slate-400 mt-1">Clean logs; safe escalation without hallucination.</span>
          </button>
        </div>
      </div>

      {/* Infrastructure Services Grid */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Server className="w-5 h-5 text-emerald-400" />
          Monitored Service Topology
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {services.map((svc) => (
            <div key={svc.name} className="border border-slate-800 rounded-lg p-4 bg-slate-950/60">
              <div className="flex justify-between items-center mb-2">
                <span className="font-mono text-sm font-semibold text-white">{svc.name}</span>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full ${
                    svc.status === 'Healthy'
                      ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                      : svc.status === 'Degraded'
                      ? 'bg-amber-950 text-amber-300 border border-amber-800'
                      : 'bg-red-950 text-red-300 border border-red-800'
                  }`}
                >
                  {svc.status}
                </span>
              </div>
              <div className="text-xs text-slate-400">Tier: {svc.tier}</div>
              <div className="text-xs text-slate-500">Port: :{svc.port}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Incidents Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
        <h2 className="text-lg font-semibold text-white mb-4">Recent Incident Activity</h2>
        {incidents.length === 0 ? (
          <div className="text-sm text-slate-500 py-6 text-center">
            No incidents recorded. Use the Quick Simulator buttons above to launch an investigation.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs text-slate-400 uppercase bg-slate-950/60 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Incident ID</th>
                  <th className="py-3 px-4">Service</th>
                  <th className="py-3 px-4">Symptom</th>
                  <th className="py-3 px-4">Severity</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Evidence Items</th>
                  <th className="py-3 px-4">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {incidents.map((inc) => (
                  <tr
                    key={inc.incident_id}
                    className="hover:bg-slate-850/50 transition cursor-pointer"
                    onClick={() => onSelectIncident(inc.incident_id)}
                  >
                    <td className="py-3 px-4 font-mono font-medium text-blue-400">{inc.incident_id}</td>
                    <td className="py-3 px-4 font-medium">{inc.service}</td>
                    <td className="py-3 px-4 text-slate-300 truncate max-w-xs">{inc.symptom}</td>
                    <td className="py-3 px-4">
                      <span
                        className={`text-xs px-2 py-0.5 rounded font-semibold uppercase ${
                          inc.severity === 'critical'
                            ? 'bg-red-950 text-red-300'
                            : inc.severity === 'high'
                            ? 'bg-amber-950 text-amber-300'
                            : 'bg-blue-950 text-blue-300'
                        }`}
                      >
                        {inc.severity}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-medium capitalize text-slate-300">{inc.status}</td>
                    <td className="py-3 px-4 text-slate-400">{inc.evidence.length} items</td>
                    <td className="py-3 px-4">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectIncident(inc.incident_id);
                        }}
                        className="text-xs bg-blue-600 hover:bg-blue-500 text-white px-2.5 py-1 rounded"
                      >
                        View War-Room
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
