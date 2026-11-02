import React from 'react';
import { IncidentState } from '../types';
import { FileText, Download, CheckCircle2, Shield, Calendar } from 'lucide-react';

interface Props {
  incident: IncidentState | null;
}

export const PostmortemPage: React.FC<Props> = ({ incident }) => {
  if (!incident) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-400">
        Please select an incident to view or export the postmortem report.
      </div>
    );
  }

  const dec = incident.decision;
  const logsFindings = incident.evidence
    .filter((e) => e.agent === 'Logs Agent')
    .map((e) => `[${e.evidence_id}] ${e.finding} (Source: ${e.evidence_source})`);
  const depFindings = incident.evidence
    .filter((e) => e.agent === 'Dependency Agent')
    .map((e) => `[${e.evidence_id}] ${e.finding} (Service: ${e.service})`);

  const mdReport = `# Incident Postmortem: ${incident.incident_id}
**Target Service:** ${incident.service}  
**Severity Level:** ${incident.severity.toUpperCase()}  
**Incident Lifecycle Status:** ${incident.status.toUpperCase()}  
**Generated At:** ${new Date().toISOString()}  

---

## 1. Executive Summary
${incident.description || incident.symptom}

## 2. Root Cause Analysis
- **Determined Cause:** ${dec?.likely_root_cause || 'Under active investigation'}
- **Cross-Validated Evidence IDs:** ${dec?.root_cause_evidence.join(', ') || 'N/A'}
- **Confidence Rating:** ${dec ? (dec.confidence * 100).toFixed(0) + '%' : 'Pending'}

## 3. Multi-Agent Investigative Findings
### Application & System Logs Findings:
${logsFindings.length > 0 ? logsFindings.map((f) => `- ${f}`).join('\n') : '- Clean logs; no stack traces.'}

### Service Dependency Findings:
${depFindings.length > 0 ? depFindings.map((f) => `- ${f}`).join('\n') : '- All dependency checks normal.'}

## 4. Remediation & Commander Decision
- **Mitigation Action Recommended:** ${dec?.mitigation_decision.toUpperCase() || 'None'}
- **Target Component:** ${dec?.target_service || incident.service}
- **Decision Status:** ${dec?.decision_status || 'Pending'}
- **Commander Justification:** ${dec?.decision_reason || 'Investigation in progress'}
- **Escalation Required:** ${incident.escalation_status}

## 5. Stakeholder Communication
> ${incident.status_updates[0]?.message || 'No status broadcast recorded.'}

---
*Report auto-compiled by AI IncidentOps Blackboard Architecture.*
`;

  const downloadMarkdown = () => {
    const blob = new Blob([mdReport], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `postmortem_${incident.incident_id}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const downloadJson = () => {
    const data = {
      incident_id: incident.incident_id,
      service: incident.service,
      symptom: incident.symptom,
      severity: incident.severity,
      status: incident.status,
      created_at: incident.created_at,
      decision: incident.decision,
      evidence: incident.evidence,
      timeline: incident.timeline,
      status_updates: incident.status_updates,
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `incident_${incident.incident_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-400" />
            Structured Postmortem Report: <span className="font-mono text-blue-400">{incident.incident_id}</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Grounded post-incident documentation compiled automatically from Blackboard evidence.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={downloadMarkdown}
            className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium px-3.5 py-2 rounded-lg transition shadow"
          >
            <Download className="w-4 h-4" /> Export Markdown (.md)
          </button>
          <button
            onClick={downloadJson}
            className="flex items-center gap-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium px-3.5 py-2 rounded-lg transition border border-slate-700"
          >
            <Download className="w-4 h-4" /> Export JSON
          </button>
        </div>
      </div>

      {/* Rendered Postmortem */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 shadow-xl max-w-4xl mx-auto space-y-6 text-sm">
        <div className="border-b border-slate-800 pb-4">
          <div className="flex justify-between items-start">
            <div>
              <span className="font-mono text-xs text-blue-400 font-bold uppercase tracking-wider block mb-1">
                INCIDENT POSTMORTEM
              </span>
              <h1 className="text-2xl font-bold text-white">Outage Review: {incident.service}</h1>
            </div>
            <span
              className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${
                incident.severity === 'critical'
                  ? 'bg-red-950 text-red-300 border border-red-800'
                  : 'bg-amber-950 text-amber-300 border border-amber-800'
              }`}
            >
              {incident.severity}
            </span>
          </div>
          <div className="flex items-center gap-4 text-xs text-slate-400 mt-2">
            <span>Incident ID: <strong>{incident.incident_id}</strong></span>
            <span>Created: <strong>{incident.created_at}</strong></span>
            <span>Final Status: <strong className="capitalize text-slate-200">{incident.status}</strong></span>
          </div>
        </div>

        {/* Summary */}
        <section className="space-y-2">
          <h3 className="font-bold text-white text-sm uppercase tracking-wider text-slate-400">1. Incident Summary</h3>
          <p className="text-slate-200 leading-relaxed bg-slate-950 p-4 rounded-lg border border-slate-800">
            {incident.description || incident.symptom}
          </p>
        </section>

        {/* Root Cause */}
        <section className="space-y-2">
          <h3 className="font-bold text-white text-sm uppercase tracking-wider text-slate-400">2. Root Cause Analysis</h3>
          <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-2">
            <div className="font-semibold text-white">{dec?.likely_root_cause || 'Under Investigation'}</div>
            <div className="text-xs text-slate-400">
              Supporting Evidence Citations:{' '}
              <span className="font-mono text-blue-400 font-bold">{dec?.root_cause_evidence.join(', ') || 'None'}</span>
            </div>
          </div>
        </section>

        {/* Findings */}
        <section className="space-y-3">
          <h3 className="font-bold text-white text-sm uppercase tracking-wider text-slate-400">3. Multi-Agent Evidence Findings</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-slate-950 p-4 rounded-lg border border-slate-800">
              <span className="text-xs font-bold text-amber-400 block mb-2">Logs Agent Findings</span>
              <ul className="text-xs text-slate-300 space-y-1.5 list-disc pl-4">
                {logsFindings.length > 0 ? (
                  logsFindings.map((f, i) => <li key={i}>{f}</li>)
                ) : (
                  <li>No error patterns found in logs.</li>
                )}
              </ul>
            </div>

            <div className="bg-slate-950 p-4 rounded-lg border border-slate-800">
              <span className="text-xs font-bold text-purple-400 block mb-2">Dependency Agent Findings</span>
              <ul className="text-xs text-slate-300 space-y-1.5 list-disc pl-4">
                {depFindings.length > 0 ? (
                  depFindings.map((f, i) => <li key={i}>{f}</li>)
                ) : (
                  <li>All dependency health probes normal.</li>
                )}
              </ul>
            </div>
          </div>
        </section>

        {/* Action Taken */}
        <section className="space-y-2">
          <h3 className="font-bold text-white text-sm uppercase tracking-wider text-slate-400">4. Recovery Action & Rationale</h3>
          <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-1 text-xs">
            <div>
              Recommended Action:{' '}
              <strong className="text-emerald-400 font-mono text-sm uppercase">{dec?.mitigation_decision}</strong> on{' '}
              <strong className="text-white font-mono">{dec?.target_service}</strong>
            </div>
            <p className="text-slate-300 pt-1">{dec?.decision_reason}</p>
          </div>
        </section>

        {/* Stakeholder Announcement */}
        {incident.status_updates[0] && (
          <section className="space-y-2">
            <h3 className="font-bold text-white text-sm uppercase tracking-wider text-slate-400">5. Stakeholder Communication</h3>
            <blockquote className="border-l-4 border-blue-500 pl-4 py-2 italic text-xs text-slate-300 bg-slate-950/60 rounded-r">
              "{incident.status_updates[0].message}"
            </blockquote>
          </section>
        )}
      </div>
    </div>
  );
};
