import React from 'react';
import { IncidentState } from '../types';
import { Scale, CheckCircle2, AlertOctagon, ShieldCheck, ArrowRight, UserCheck } from 'lucide-react';

interface Props {
  incident: IncidentState | null;
}

export const DecisionPage: React.FC<Props> = ({ incident }) => {
  if (!incident) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-400">
        Please select an active incident to view the Incident Commander's decision.
      </div>
    );
  }

  const dec = incident.decision;

  if (!dec) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-400">
        Incident Commander is currently analyzing the shared Blackboard evidence...
      </div>
    );
  }

  const isEscalated = dec.decision_status === 'insufficient_evidence' || dec.escalation_required;

  return (
    <div className="space-y-6">
      {/* Decision Banner */}
      <div
        className={`border rounded-xl p-6 shadow-xl ${
          isEscalated
            ? 'bg-purple-950/40 border-purple-800/80'
            : 'bg-emerald-950/40 border-emerald-800/80'
        }`}
      >
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <span
              className={`text-xs font-bold uppercase tracking-wider px-2.5 py-1 rounded-full ${
                isEscalated
                  ? 'bg-purple-900 text-purple-200 border border-purple-700'
                  : 'bg-emerald-900 text-emerald-200 border border-emerald-700'
              }`}
            >
              DECISION STATUS: {dec.decision_status.toUpperCase()}
            </span>
            <h2 className="text-xl font-bold text-white mt-2">
              {isEscalated ? '⚠️ Automated Mitigation Held: Safe Escalation' : 'Binding Mitigation Recommendation Issued'}
            </h2>
            <p className="text-xs text-slate-300 mt-1">
              Decided by <strong className="text-white">Incident Commander</strong> exclusively using verified Blackboard evidence.
            </p>
          </div>

          <div className="bg-slate-900/80 border border-slate-700 rounded-xl p-4 text-center min-w-[160px]">
            <span className="text-xs text-slate-400 block mb-1">Calculated Confidence</span>
            <div
              className={`text-3xl font-extrabold ${
                dec.confidence >= 0.8
                  ? 'text-emerald-400'
                  : dec.confidence >= 0.6
                  ? 'text-amber-400'
                  : 'text-purple-400'
              }`}
            >
              {(dec.confidence * 100).toFixed(0)}%
            </div>
            <span className="text-[10px] text-slate-500">Based on cross-validated IDs</span>
          </div>
        </div>
      </div>

      {/* Decision Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Root Cause Analysis (Left) */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg space-y-4">
          <h3 className="font-bold text-white text-base flex items-center gap-2">
            <Scale className="w-5 h-5 text-blue-400" />
            Probable Root Cause Assessment
          </h3>

          <div className="bg-slate-950 border border-slate-800 p-4 rounded-lg">
            <span className="text-xs text-slate-500 uppercase tracking-wider block mb-1">Identified Root Cause:</span>
            <div className="text-base font-semibold text-white">{dec.likely_root_cause}</div>
          </div>

          <div>
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
              Cross-Validated Supporting Evidence Citations:
            </span>
            <div className="space-y-2">
              {dec.root_cause_evidence.map((eid) => {
                const ev = incident.evidence.find((e) => e.evidence_id === eid);
                return (
                  <div
                    key={eid}
                    className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-xs space-y-1"
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-mono font-bold text-blue-400">{eid}</span>
                      <span className="text-[10px] text-emerald-400 font-semibold flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" /> Grounded in Blackboard
                      </span>
                    </div>
                    {ev && <p className="text-slate-300 text-[11px]">{ev.finding}</p>}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Action & Safety Governance (Right) */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg space-y-4">
          <h3 className="font-bold text-white text-base flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            Mitigation Governance & Safety
          </h3>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-slate-950 border border-slate-800 p-3.5 rounded-lg">
              <span className="text-slate-500 text-xs block mb-1">Recommended Action:</span>
              <span className="font-mono text-base font-bold text-emerald-400 uppercase">
                {dec.mitigation_decision}
              </span>
            </div>
            <div className="bg-slate-950 border border-slate-800 p-3.5 rounded-lg">
              <span className="text-slate-500 text-xs block mb-1">Target Service:</span>
              <span className="font-mono text-base font-bold text-white">
                {dec.target_service}
              </span>
            </div>
          </div>

          <div className="bg-slate-950 border border-slate-800 p-4 rounded-lg space-y-2 text-xs">
            <span className="text-slate-500 uppercase tracking-wider block font-semibold">
              Commander Justification Rationale:
            </span>
            <p className="text-slate-200 leading-relaxed">{dec.decision_reason}</p>
          </div>

          {/* Safety Approval Panel */}
          <div className="border border-amber-800/60 bg-amber-950/30 p-4 rounded-lg space-y-3">
            <div className="flex items-center gap-2 text-amber-300 text-xs font-semibold">
              <UserCheck className="w-4 h-4" />
              Human Operator Confirmation (Safety Gate)
            </div>
            <p className="text-xs text-slate-300">
              In adherence to engineering safety invariants, automated destructive actions are halted by default.
              An authorized Incident Responder or SRE must authorize execution.
            </p>
            <div className="flex items-center gap-3 pt-1">
              <button
                onClick={() => alert(`Mitigation [${dec.mitigation_decision.toUpperCase()}] approved on ${dec.target_service}. Logged to append-only audit trail.`)}
                className="bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs px-4 py-2 rounded-lg transition"
              >
                Approve & Execute Mitigation
              </button>
              <button
                onClick={() => alert('Incident flagged for manual senior SRE triage war-room.')}
                className="bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs px-3 py-2 rounded-lg transition"
              >
                Escalate to Senior SRE
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
