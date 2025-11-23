import { LogWindow } from '../types';

interface LogWindowListProps {
  windows: LogWindow[];
}

export default function LogWindowList({ windows }: LogWindowListProps) {
  if (!windows.length) {
    return (
      <div className="text-xs text-slate-500 border border-dashed border-slate-800 rounded-lg p-4">
        No log excerpts have been ingested for this incident yet.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {windows.map((window) => (
        <div
          key={`${window.source_id}-${window.started_at}`}
          className="border border-slate-800 bg-slate-900/60 rounded-lg p-4 space-y-3"
        >
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="uppercase tracking-wide">{window.source_id || 'logs'}</span>
            <span>
              {new Date(window.started_at).toLocaleTimeString()} –{' '}
              {new Date(window.ended_at).toLocaleTimeString()}
            </span>
          </div>
          <div className="bg-slate-950/50 rounded p-3 text-[11px] text-slate-300 font-mono space-y-1 max-h-48 overflow-auto">
            {window.lines.map((line, idx) => (
              <pre key={idx} className="whitespace-pre-wrap">
                {line}
              </pre>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
