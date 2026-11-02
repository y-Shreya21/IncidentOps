import React from 'react';
import { IncidentState, UserRole } from '../types';
import { Shield, RefreshCw, AlertCircle } from 'lucide-react';

interface Props {
  activeTab: string;
  onTabChange: (tab: string) => void;
  incidents: IncidentState[];
  selectedIncidentId: string | null;
  onSelectIncident: (id: string) => void;
  role: UserRole;
  onRefresh: () => void;
  loading: boolean;
}

export const Navbar: React.FC<Props> = ({
  activeTab,
  onTabChange,
  incidents,
  selectedIncidentId,
  onSelectIncident,
  role,
  onRefresh,
  loading,
}) => {
  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'management', label: 'Incidents' },
    { id: 'war_room', label: 'Agent War-Room' },
    { id: 'blackboard', label: 'Blackboard' },
    { id: 'decision', label: 'Decision' },
    { id: 'timeline', label: 'Timeline' },
    { id: 'postmortem', label: 'Postmortem' },
    { id: 'settings', label: 'Settings & RBAC' },
  ];

  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Title */}
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-600/20 border border-blue-500/30">
              <Shield className="w-6 h-6 text-blue-500" />
            </div>
            <div>
              <span className="font-extrabold text-base tracking-tight text-white flex items-center gap-1.5">
                AI IncidentOps <span className="text-[10px] bg-blue-900/60 text-blue-300 border border-blue-700 px-1.5 py-0.2 rounded">WAR-ROOM</span>
              </span>
              <p className="text-[10px] text-slate-400">Autonomous Multi-Agent Incident Response</p>
            </div>
          </div>

          {/* Active Incident Selector & Quick Controls */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1">
              <span className="text-xs text-slate-400">Incident:</span>
              <select
                value={selectedIncidentId || ''}
                onChange={(e) => onSelectIncident(e.target.value)}
                className="bg-transparent text-xs text-white font-mono font-semibold focus:outline-none cursor-pointer"
              >
                {incidents.length === 0 ? (
                  <option value="">No Incidents</option>
                ) : (
                  incidents.map((inc) => (
                    <option key={inc.incident_id} value={inc.incident_id} className="bg-slate-900 text-white">
                      {inc.incident_id} ({inc.service})
                    </option>
                  ))
                )}
              </select>
            </div>

            <button
              onClick={onRefresh}
              disabled={loading}
              title="Refresh State"
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>

            <span className="text-[11px] font-mono bg-purple-950 text-purple-300 border border-purple-800 px-2.5 py-1 rounded-full font-bold">
              {role}
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex space-x-1 overflow-x-auto py-2 border-t border-slate-800/60 text-xs">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`px-3 py-1.5 rounded-md font-medium whitespace-nowrap transition ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
