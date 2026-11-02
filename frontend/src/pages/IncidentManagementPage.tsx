import React, { useState } from 'react';
import { IncidentState, Severity } from '../types';
import { PlusCircle, Search, Filter } from 'lucide-react';

interface Props {
  incidents: IncidentState[];
  onSelectIncident: (id: string) => void;
  onCreateIncident: (payload: {
    service: string;
    symptom: string;
    severity: Severity;
    description: string;
  }) => void;
  loading: boolean;
}

export const IncidentManagementPage: React.FC<Props> = ({
  incidents,
  onSelectIncident,
  onCreateIncident,
  loading,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // Form State
  const [service, setService] = useState('payment-api');
  const [severity, setSeverity] = useState<Severity>('critical');
  const [symptom, setSymptom] = useState('HTTP 500 database pool exhaustion');
  const [description, setDescription] = useState(
    'Payment gateway transactions are failing with HTTP 500 error codes.'
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onCreateIncident({ service, symptom, severity, description });
  };

  const filtered = incidents.filter((inc) => {
    const matchesSearch =
      inc.incident_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      inc.service.toLowerCase().includes(searchTerm.toLowerCase()) ||
      inc.symptom.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSev = severityFilter === 'all' || inc.severity === severityFilter;
    const matchesStatus = statusFilter === 'all' || inc.status === statusFilter;
    return matchesSearch && matchesSev && matchesStatus;
  });

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Create Incident Form (Left) */}
      <div className="lg:col-span-1 bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg h-fit">
        <h2 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
          <PlusCircle className="w-5 h-5 text-blue-400" />
          Ingest Production Alert
        </h2>
        <p className="text-xs text-slate-400 mb-4">
          Directly inject a production signal to convene the multi-agent war-room.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Target Service</label>
            <select
              value={service}
              onChange={(e) => setService(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
            >
              <option value="payment-api">payment-api (Tier-1)</option>
              <option value="frontend">frontend (Tier-1)</option>
              <option value="auth-service">auth-service (Tier-1)</option>
              <option value="postgres">postgres (Tier-0)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Severity Level</label>
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value as Severity)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
            >
              <option value="critical">Critical (P1 Outage)</option>
              <option value="high">High (P2 Degradation)</option>
              <option value="medium">Medium (P3 Performance Anomaly)</option>
              <option value="low">Low (P4 Minor Issue)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Symptom Summary</label>
            <input
              type="text"
              value={symptom}
              onChange={(e) => setSymptom(e.target.value)}
              required
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Detailed Description</label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-2.5 px-4 rounded-lg text-sm transition shadow-md disabled:opacity-50"
          >
            {loading ? 'Orchestrating War-Room...' : '🚀 Ingest Alert to War-Room'}
          </button>
        </form>
      </div>

      {/* Incidents Table with Search and Filters (Right) */}
      <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg space-y-4">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <h2 className="text-lg font-semibold text-white">Incident Registry</h2>
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <div className="relative flex-1 sm:w-48">
              <Search className="w-4 h-4 text-slate-500 absolute left-2.5 top-2.5" />
              <input
                type="text"
                placeholder="Search incidents..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
              />
            </div>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-slate-950 border border-slate-700 rounded-lg px-2 py-1.5 text-xs text-slate-300"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-950 border border-slate-700 rounded-lg px-2 py-1.5 text-xs text-slate-300"
            >
              <option value="all">All Statuses</option>
              <option value="investigating">Investigating</option>
              <option value="mitigating">Mitigating</option>
              <option value="escalated">Escalated</option>
              <option value="resolved">Resolved</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs text-slate-400 uppercase bg-slate-950/60 border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">ID</th>
                <th className="py-2.5 px-3">Service</th>
                <th className="py-2.5 px-3">Symptom</th>
                <th className="py-2.5 px-3">Severity</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-xs">
              {filtered.map((inc) => (
                <tr
                  key={inc.incident_id}
                  className="hover:bg-slate-850/50 transition cursor-pointer"
                  onClick={() => onSelectIncident(inc.incident_id)}
                >
                  <td className="py-3 px-3 font-mono font-medium text-blue-400">{inc.incident_id}</td>
                  <td className="py-3 px-3 font-medium text-white">{inc.service}</td>
                  <td className="py-3 px-3 text-slate-300 max-w-xs truncate">{inc.symptom}</td>
                  <td className="py-3 px-3">
                    <span
                      className={`px-2 py-0.5 rounded font-semibold uppercase ${
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
                  <td className="py-3 px-3 capitalize text-slate-300">{inc.status}</td>
                  <td className="py-3 px-3">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectIncident(inc.incident_id);
                      }}
                      className="bg-slate-800 hover:bg-slate-700 text-slate-200 px-2 py-1 rounded text-xs"
                    >
                      Inspect
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
