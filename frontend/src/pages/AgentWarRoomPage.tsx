import React from 'react';
import { IncidentState } from '../types';
import { Bot, FileText, Network, Wrench, ShieldCheck, Megaphone, CheckCircle2, Clock } from 'lucide-react';

interface Props {
  incident: IncidentState | null;
}

export const AgentWarRoomPage: React.FC<Props> = ({ incident }) => {
  if (!incident) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-400">
        Please select an active incident to view live agent activities.
      </div>
    );
  }

  const agents = [
    {
      id: 'alert_agent',
      name: 'Alert Agent',
      icon: Bot,
      color: 'text-blue-400',
      bgColor: 'bg-blue-950/40 border-blue-800/60',
      role: 'Ingests production signal, verifies required schema, normalizes severity, registers incident.',
      tools: ['validate_alert()', 'lookup_service_metadata()'],
      status: 'Completed',
      evidenceIds: [],
      findings: `Registered ${incident.incident_id} for ${incident.service} with ${incident.severity.toUpperCase()} priority.`,
    },
    {
      id: 'logs_agent',
      name: 'Logs Agent',
      icon: FileText,
      color: 'text-amber-400',
      bgColor: 'bg-amber-950/40 border-amber-800/60',
      role: 'Retrieves actual log files on disk, executes deterministic regex pattern analysis for crashes.',
      tools: ['retrieve_recent_logs()', 'analyze_log_patterns()'],
      status: 'Completed',
      evidenceIds: incident.evidence.filter((e) => e.agent === 'Logs Agent').map((e) => e.evidence_id),
      findings:
        incident.evidence.find((e) => e.agent === 'Logs Agent')?.finding ||
        'Analyzed log lines. No errors found.',
    },
    {
      id: 'dependency_agent',
      name: 'Dependency Agent',
      icon: Network,
      color: 'text-purple-400',
      bgColor: 'bg-purple-950/40 border-purple-800/60',
      role: 'Traverses service topology, queries live HTTP and simulated health probes for upstream/downstream nodes.',
      tools: ['retrieve_service_dependencies()', 'check_service_health()'],
      status: 'Completed',
      evidenceIds: incident.evidence.filter((e) => e.agent === 'Dependency Agent').map((e) => e.evidence_id),
      findings:
        incident.evidence
          .filter((e) => e.agent === 'Dependency Agent')
          .map((e) => e.finding)
          .join(' | ') || 'Dependency health checks executed.',
    },
    {
      id: 'mitigation_agent',
      name: 'Mitigation Agent',
      icon: Wrench,
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-950/40 border-emerald-800/60',
      role: 'Matches evidence signatures against runbook repository, verifies safety preconditions and risks.',
      tools: ['retrieve_runbook()', 'evaluate_mitigation_preconditions()'],
      status: incident.mitigation_proposals.length > 0 ? 'Completed' : 'Pending',
      evidenceIds: incident.mitigation_proposals[0]?.supporting_evidence || [],
      findings: incident.mitigation_proposals[0]
        ? `Proposed [${incident.mitigation_proposals[0].proposed_action.toUpperCase()}] on ${incident.mitigation_proposals[0].target_service} (Risk: ${incident.mitigation_proposals[0].risk_level.toUpperCase()}). Rationale: ${incident.mitigation_proposals[0].reason}`
        : 'Awaiting investigative evidence.',
    },
    {
      id: 'incident_commander',
      name: 'Incident Commander',
      icon: ShieldCheck,
      color: 'text-red-400',
      bgColor: 'bg-red-950/40 border-red-800/60',
      role: 'Final authority. Cross-validates evidence IDs against Blackboard, determines root cause, issues binding decision.',
      tools: ['validate_evidence()', 'record_incident_decision()'],
      status: incident.decision ? 'Completed' : 'Pending',
      evidenceIds: incident.decision?.root_cause_evidence || [],
      findings: incident.decision
        ? `Root Cause: "${incident.decision.likely_root_cause}". Mitigation Decision: [${incident.decision.mitigation_decision.toUpperCase()}]. Confidence: ${(incident.decision.confidence * 100).toFixed(0)}%.`
        : 'Reviewing evidence on Blackboard.',
    },
    {
      id: 'communication_agent',
      name: 'Communication Agent',
      icon: Megaphone,
      color: 'text-cyan-400',
      bgColor: 'bg-cyan-950/40 border-cyan-800/60',
      role: 'Generates public and internal stakeholder status-page broadcasts grounded strictly in verified incident facts.',
      tools: ['retrieve_status_template()', 'generate_status_update()'],
      status: incident.status_updates.length > 0 ? 'Completed' : 'Pending',
      evidenceIds: [],
      findings: incident.status_updates[0]
        ? `Broadcasted: "${incident.status_updates[0].headline}" — ${incident.status_updates[0].message}`
        : 'Status update queued.',
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            Multi-Agent Operations Room: <span className="font-mono text-blue-400">{incident.incident_id}</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Service: <span className="font-mono text-slate-200">{incident.service}</span> • Symptom:{' '}
            <span className="text-slate-200">{incident.symptom}</span> • Status:{' '}
            <span className="capitalize text-slate-200 font-semibold">{incident.status}</span>
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="flex h-3 w-3 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
          </span>
          <span className="text-xs text-slate-300 font-medium">All 6 Agents Synchronized</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {agents.map((ag) => {
          const Icon = ag.icon;
          return (
            <div
              key={ag.id}
              className={`border rounded-xl p-5 shadow-lg flex flex-col justify-between ${ag.bgColor}`}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-lg bg-slate-900/80 border border-slate-700">
                      <Icon className={`w-5 h-5 ${ag.color}`} />
                    </div>
                    <div>
                      <h3 className="font-bold text-white text-sm">{ag.name}</h3>
                      <span className="text-[11px] text-slate-400">Microsoft Agent Framework</span>
                    </div>
                  </div>
                  <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400 bg-emerald-950/60 border border-emerald-800/80 px-2 py-0.5 rounded-full">
                    <CheckCircle2 className="w-3 h-3" />
                    {ag.status}
                  </span>
                </div>

                <p className="text-xs text-slate-300 mb-3 leading-relaxed">{ag.role}</p>

                <div className="mb-3">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                    Python Tools Invoked:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {ag.tools.map((t) => (
                      <span
                        key={t}
                        className="font-mono text-[11px] bg-slate-900/90 text-slate-300 px-2 py-0.5 rounded border border-slate-800"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                </div>

                {ag.evidenceIds.length > 0 && (
                  <div className="mb-3">
                    <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                      Evidence Cited:
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {ag.evidenceIds.map((eid) => (
                        <span
                          key={eid}
                          className="font-mono text-[10px] bg-blue-950 text-blue-300 border border-blue-800 px-1.5 py-0.5 rounded font-bold"
                        >
                          {eid}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800/80 bg-slate-950/40 p-2.5 rounded-lg">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-0.5">
                  Latest Finding / Output:
                </span>
                <p className="text-xs text-slate-200 line-clamp-3 italic">"{ag.findings}"</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
