import React, { useState } from 'react';
import { IncidentState } from '../types';
import { Scale, CheckCircle2, AlertOctagon, ShieldCheck, ArrowRight, UserCheck, Loader2 } from 'lucide-react';

interface Props {
  incident: IncidentState | null;
  onApproveMitigation?: (incidentId: string, action: string, targetService: string) => Promise<void>;
  onEscalate?: (incidentId: string) => Promise<void>;
  loading?: boolean;
}

export const DecisionPage: React.FC<Props> = ({
  incident,
  onApproveMitigation,
  onEscalate,
  loading: parentLoading = false,
}) => {
  const [actionLoading, setActionLoading] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

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

  const isEscalated = dec.decision_status === 'insufficient_evidence' || dec.escalation_required || incident.status === 'escalated';
  const isMitigated = incident.status === 'mitigated' || incident.status === 'resolved';

  const handleApprove = async () => {
    if (!onApproveMitigation) return;
    setActionLoading(true);
    setActionSuccess(null);
    try {
      await onApproveMitigation(incident.incident_id, dec.mitigation_decision, dec.target_service);
      setActionSuccess(`Mitigation [${dec.mitigation_decision.toUpperCase()}] executed and recorded in the audit trail.`);
    } catch (e: any) {
      console.error(e);
    } finally {
      setActionLoading(false);
    }
  };

  const handleEscalate = async () => {
    if (!onEscalate) return;
    setActionLoading(true);
    setActionSuccess(null);
    try {
      await onEscalate(incident.incident_id);
      setActionSuccess(`Incident ${incident.incident_id} successfully escalated to Senior SRE on-call team.`);
    } catch (e: any) {
      console.error(e);
    } finally {
      setActionLoading(false);
    }
  };

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
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-amber-300 text-xs font-semibold">
                <UserCheck className="w-4 h-4" />
                Human Operator Confirmation (Safety Gate)
              </div>
              {isMitigated && (
                <span className="text-[11px] bg-emerald-900/80 border border-emerald-700 text-emerald-200 px-2.5 py-0.5 rounded font-semibold flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> MITIGATED
                </span>
              )}
              {isEscalated && (
                <span className="text-[11px] bg-purple-900/80 border border-purple-700 text-purple-200 px-2.5 py-0.5 rounded font-semibold flex items-center gap-1">
                  <AlertOctagon className="w-3.5 h-3.5 text-purple-400" /> ESCALATED
                </span>
              )}
            </div>

            <p className="text-xs text-slate-300">
              In adherence to engineering safety invariants, automated destructive actions are halted by default.
              An authorized Incident Responder or SRE must authorize execution.
            </p>

            {actionSuccess && (
              <div className="p-2.5 bg-emerald-950/80 border border-emerald-800 rounded text-xs text-emerald-300 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>{actionSuccess}</span>
              </div>
            )}

            <div className="flex items-center gap-3 pt-1">
              <button
                onClick={handleApprove}
                disabled={actionLoading || parentLoading || isMitigated}
                className="bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-500 disabled:cursor-not-allowed text-white font-medium text-xs px-4 py-2 rounded-lg transition flex items-center gap-2"
              >
                {actionLoading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                {isMitigated ? 'Mitigation Executed' : 'Approve & Execute Mitigation'}
              </button>
              <button
                onClick={handleEscalate}
                disabled={actionLoading || parentLoading || isEscalated}
                className="bg-slate-800 hover:bg-slate-700 disabled:bg-slate-900 disabled:text-slate-600 disabled:cursor-not-allowed text-slate-300 text-xs px-3 py-2 rounded-lg transition flex items-center gap-2"
              >
                {isEscalated ? 'Escalated to Senior SRE' : 'Escalate to Senior SRE'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
