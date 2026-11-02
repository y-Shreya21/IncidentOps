import React, { useState } from 'react';
import { IncidentState } from '../types';
import { Database, FileCode, CheckSquare, AlertCircle } from 'lucide-react';

interface Props {
  incident: IncidentState | null;
}

export const BlackboardPage: React.FC<Props> = ({ incident }) => {
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | null>(null);

  if (!incident) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-400">
        Please select an incident to inspect the shared Blackboard state.
      </div>
    );
  }

  const selectedEvidence = incident.evidence.find((e) => e.evidence_id === selectedEvidenceId) || incident.evidence[0];

  return (
    <div className="space-y-6">
      {/* Blackboard Metadata Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Database className="w-5 h-5 text-blue-400" />
              <h2 className="text-lg font-bold text-white">
                Blackboard State: <span className="font-mono text-blue-400">{incident.incident_id}</span>
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Centralized, append-only shared state repository accessed by all 6 agents.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs bg-slate-800 border border-slate-700 px-3 py-1 rounded-full text-slate-300">
              Service: <strong className="text-white">{incident.service}</strong>
            </span>
            <span className="text-xs bg-slate-800 border border-slate-700 px-3 py-1 rounded-full text-slate-300">
              Severity: <strong className="text-white uppercase">{incident.severity}</strong>
            </span>
            <span className="text-xs bg-slate-800 border border-slate-700 px-3 py-1 rounded-full text-slate-300">
              Status: <strong className="text-white uppercase">{incident.status}</strong>
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Evidence Registry Column (Left) */}
        <div className="lg:col-span-1 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
          <h3 className="font-semibold text-white text-sm flex items-center justify-between">
            <span>Posted Evidence Registry</span>
            <span className="text-xs bg-blue-950 text-blue-300 px-2 py-0.5 rounded-full font-bold">
              {incident.evidence.length} Items
            </span>
          </h3>

          <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
            {incident.evidence.map((ev) => {
              const isSelected = selectedEvidence?.evidence_id === ev.evidence_id;
              return (
                <div
                  key={ev.evidence_id}
                  onClick={() => setSelectedEvidenceId(ev.evidence_id)}
                  className={`p-3 rounded-lg border text-xs cursor-pointer transition ${
                    isSelected
                      ? 'bg-blue-950/60 border-blue-500 shadow'
                      : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-mono font-bold text-blue-400">{ev.evidence_id}</span>
                    <span className="text-[10px] text-slate-400">{ev.agent}</span>
                  </div>
                  <p className="text-slate-200 line-clamp-2">{ev.finding}</p>
                  <div className="mt-2 text-[10px] text-slate-500 truncate">Source: {ev.evidence_source}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Evidence Deep-Dive (Right) */}
        <div className="lg:col-span-2 space-y-6">
          {selectedEvidence ? (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg space-y-4">
              <div className="flex justify-between items-start">
                <div>
                  <span className="font-mono text-sm font-bold text-blue-400 bg-blue-950/80 px-2.5 py-1 rounded border border-blue-800">
                    {selectedEvidence.evidence_id}
                  </span>
                  <h3 className="text-base font-bold text-white mt-3">{selectedEvidence.finding}</h3>
                </div>
                <span className="text-xs bg-slate-800 text-slate-300 px-2.5 py-1 rounded">
                  Posted by: <strong>{selectedEvidence.agent}</strong>
                </span>
              </div>

              <div className="grid grid-cols-2 gap-4 text-xs bg-slate-950 p-4 rounded-lg border border-slate-800">
                <div>
                  <span className="text-slate-500 block mb-0.5">Target Service:</span>
                  <span className="font-mono text-white font-semibold">{selectedEvidence.service}</span>
                </div>
                <div>
                  <span className="text-slate-500 block mb-0.5">Timestamp:</span>
                  <span className="font-mono text-slate-300">{selectedEvidence.evidence_timestamp}</span>
                </div>
                <div className="col-span-2">
                  <span className="text-slate-500 block mb-0.5">Telemetry / Log Source:</span>
                  <span className="font-mono text-slate-300 break-all">{selectedEvidence.evidence_source}</span>
                </div>
              </div>

              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2 flex items-center gap-1.5">
                  <FileCode className="w-4 h-4 text-slate-400" />
                  Raw Telemetry Payload (Strictly Grounded, Non-Fabricated):
                </span>
                <pre className="bg-slate-950 border border-slate-800 rounded-lg p-4 text-xs font-mono text-emerald-400 overflow-x-auto max-h-80">
                  {JSON.stringify(selectedEvidence.raw_data, null, 2)}
                </pre>
              </div>
            </div>
          ) : (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-500">
              No evidence selected.
            </div>
          )}

          {/* Mitigation Proposals on Board */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <CheckSquare className="w-4 h-4 text-emerald-400" />
              Mitigation Proposals Posted to Blackboard
            </h3>
            {incident.mitigation_proposals.length === 0 ? (
              <p className="text-xs text-slate-500">No mitigation proposals posted yet.</p>
            ) : (
              <div className="space-y-3">
                {incident.mitigation_proposals.map((prop) => (
                  <div
                    key={prop.proposal_id}
                    className="p-4 rounded-lg bg-slate-950 border border-slate-800 text-xs space-y-2"
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-mono font-bold text-emerald-400">
                        [{prop.proposal_id}] ACTION: {prop.proposed_action.toUpperCase()}
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded font-semibold uppercase ${
                          prop.risk_level === 'low'
                            ? 'bg-emerald-950 text-emerald-300'
                            : prop.risk_level === 'medium'
                            ? 'bg-amber-950 text-amber-300'
                            : 'bg-red-950 text-red-300'
                        }`}
                      >
                        Risk: {prop.risk_level}
                      </span>
                    </div>
                    <p className="text-slate-300">{prop.reason}</p>
                    <div className="text-[11px] text-slate-500">
                      Target: <strong className="text-slate-300">{prop.target_service}</strong> • Supporting Evidence:{' '}
                      <span className="font-mono text-blue-400">{prop.supporting_evidence.join(', ')}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
