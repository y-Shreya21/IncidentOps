import React from 'react';
import { IncidentState } from '../types';
import { Clock, Shield, Terminal, ArrowDown } from 'lucide-react';

interface Props {
  incident: IncidentState | null;
}

export const TimelinePage: React.FC<Props> = ({ incident }) => {
  if (!incident) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-400">
        Please select an active incident to view the chronological event timeline.
      </div>
    );
  }

  const timeline = incident.timeline;

  return (
    <div className="space-y-6">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex justify-between items-center">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Clock className="w-5 h-5 text-blue-400" />
            Append-Only Chronological Event Log
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Immutable SQLite / PostgreSQL audit trail recording every agent transaction with monotonic sequence.
          </p>
        </div>
        <span className="text-xs font-mono bg-blue-950 text-blue-300 border border-blue-800 px-3 py-1 rounded-full font-bold">
          {timeline.length} Recorded Events
        </span>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
        {timeline.length === 0 ? (
          <p className="text-xs text-slate-500 text-center py-8">No timeline events recorded yet.</p>
        ) : (
          <div className="relative border-l border-slate-800 ml-4 space-y-6">
            {timeline.map((evt, idx) => (
              <div key={evt.event_id || idx} className="relative pl-6">
                {/* Dot */}
                <div className="absolute -left-2 top-1.5 w-4 h-4 rounded-full bg-slate-900 border-2 border-blue-500"></div>

                <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 space-y-2">
                  <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-blue-400">{evt.event_id}</span>
                      <span className="text-xs font-bold text-white bg-slate-800 px-2 py-0.5 rounded">
                        {evt.agent}
                      </span>
                      <span className="text-xs font-mono text-emerald-400">({evt.event_type})</span>
                    </div>
                    <span className="text-[11px] font-mono text-slate-500">{evt.timestamp}</span>
                  </div>

                  {evt.evidence_ids && evt.evidence_ids.length > 0 && (
                    <div className="flex items-center gap-1.5 text-xs">
                      <span className="text-slate-400 text-[11px]">Cited Evidence:</span>
                      {evt.evidence_ids.map((id) => (
                        <span
                          key={id}
                          className="font-mono text-[10px] bg-blue-950 text-blue-300 border border-blue-800 px-1.5 py-0.5 rounded font-bold"
                        >
                          {id}
                        </span>
                      ))}
                    </div>
                  )}

                  {evt.payload && Object.keys(evt.payload).length > 0 && (
                    <details className="text-xs pt-1">
                      <summary className="text-[11px] text-slate-500 cursor-pointer hover:text-slate-300">
                        Inspect Event Payload
                      </summary>
                      <pre className="mt-2 bg-slate-900 p-3 rounded text-[11px] font-mono text-slate-300 overflow-x-auto border border-slate-800">
                        {JSON.stringify(evt.payload, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
