import React from 'react';
import { UserRole } from '../types';
import { Settings, ShieldCheck, Key, Server, Users } from 'lucide-react';

interface Props {
  role: UserRole;
  onRoleChange: (newRole: UserRole) => void;
}

export const SettingsPage: React.FC<Props> = ({ role, onRoleChange }) => {
  const roles: { id: UserRole; label: string; desc: string }[] = [
    {
      id: 'Administrator',
      label: 'System Administrator',
      desc: 'Full administrative access: manage service registries, configure system secrets, and override governance policies.',
    },
    {
      id: 'IncidentResponder',
      label: 'Incident Responder / Commander',
      desc: 'Operational authority: trigger incident triage, review evidence, approve and execute mitigation runbooks.',
    },
    {
      id: 'SREEngineer',
      label: 'SRE / DevOps Engineer',
      desc: 'Technical diagnostics: inspect raw log traces, analyze dependency health probes, update recovery procedures.',
    },
    {
      id: 'Stakeholder',
      label: 'Read-only Stakeholder',
      desc: 'Auditing access: view published status broadcasts, incident status, and export postmortem summaries.',
    },
  ];

  const permissions = [
    { action: 'Create / Ingest Incident Alerts', admin: true, responder: true, sre: true, stakeholder: false },
    { action: 'Execute Multi-Agent War-Room', admin: true, responder: true, sre: true, stakeholder: false },
    { action: 'Approve & Execute Mitigation Runbooks', admin: true, responder: true, sre: false, stakeholder: false },
    { action: 'Modify Service Registry Topology', admin: true, responder: false, sre: false, stakeholder: false },
    { action: 'View Raw Telemetry & Blackboard State', admin: true, responder: true, sre: true, stakeholder: false },
    { action: 'View Status Updates & Postmortem Reports', admin: true, responder: true, sre: true, stakeholder: true },
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex justify-between items-center">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Settings className="w-5 h-5 text-blue-400" />
            Settings & Access Management (RBAC)
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Role-Based Access Control and operational environment settings.
          </p>
        </div>
        <span className="text-xs font-mono bg-blue-950 text-blue-300 border border-blue-800 px-3 py-1 rounded-full font-bold">
          Active Role: {role}
        </span>
      </div>

      {/* Role Switcher */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg space-y-4">
        <h3 className="font-bold text-white text-sm flex items-center gap-2">
          <Users className="w-4 h-4 text-purple-400" />
          Active Persona Switcher (Demonstration Mode)
        </h3>
        <p className="text-xs text-slate-400">
          Select an operational persona to simulate role-based authorization:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {roles.map((r) => (
            <div
              key={r.id}
              onClick={() => onRoleChange(r.id)}
              className={`p-4 rounded-xl border text-xs cursor-pointer transition ${
                role === r.id
                  ? 'bg-blue-950/60 border-blue-500 shadow-md ring-1 ring-blue-500'
                  : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex justify-between items-center mb-1">
                <span className="font-bold text-white text-sm">{r.label}</span>
                {role === r.id && (
                  <span className="bg-blue-600 text-white text-[10px] font-bold px-2 py-0.5 rounded">
                    ACTIVE
                  </span>
                )}
              </div>
              <p className="text-slate-300 mt-1">{r.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* RBAC Permission Matrix */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg space-y-4">
        <h3 className="font-bold text-white text-sm flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          Role Permission Enforcement Matrix
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 text-slate-400 uppercase border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Operational Capability</th>
                <th className="py-2.5 px-3 text-center">Administrator</th>
                <th className="py-2.5 px-3 text-center">Incident Responder</th>
                <th className="py-2.5 px-3 text-center">SRE / DevOps</th>
                <th className="py-2.5 px-3 text-center">Stakeholder</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {permissions.map((p, i) => (
                <tr key={i} className="hover:bg-slate-850/40">
                  <td className="py-3 px-3 text-slate-200 font-medium">{p.action}</td>
                  <td className="py-3 px-3 text-center">
                    {p.admin ? <span className="text-emerald-400 font-bold">✓</span> : <span className="text-slate-600">—</span>}
                  </td>
                  <td className="py-3 px-3 text-center">
                    {p.responder ? <span className="text-emerald-400 font-bold">✓</span> : <span className="text-slate-600">—</span>}
                  </td>
                  <td className="py-3 px-3 text-center">
                    {p.sre ? <span className="text-emerald-400 font-bold">✓</span> : <span className="text-slate-600">—</span>}
                  </td>
                  <td className="py-3 px-3 text-center">
                    {p.stakeholder ? <span className="text-emerald-400 font-bold">✓</span> : <span className="text-slate-600">—</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Backend Connection */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg space-y-3">
        <h3 className="font-bold text-white text-sm flex items-center gap-2">
          <Server className="w-4 h-4 text-cyan-400" />
          Backend API & Service Target
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono bg-slate-950 p-4 rounded-lg border border-slate-800">
          <div>
            <span className="text-slate-500 block mb-0.5">API Endpoint URL:</span>
            <span className="text-blue-400">http://localhost:8000/api/v1</span>
          </div>
          <div>
            <span className="text-slate-500 block mb-0.5">Persistence Engine:</span>
            <span className="text-emerald-400">Dual Mode (PostgreSQL / SQLite)</span>
          </div>
          <div>
            <span className="text-slate-500 block mb-0.5">Agent Framework:</span>
            <span className="text-purple-400">Microsoft Semantic Kernel / Agent Framework</span>
          </div>
          <div>
            <span className="text-slate-500 block mb-0.5">Execution Mode:</span>
            <span className="text-amber-400">Deterministic Mock / Sandboxed Local Telemetry</span>
          </div>
        </div>
      </div>
    </div>
  );
};
