import { LogWindow } from '../types';

interface LogWindowListProps {
  windows: LogWindow[];
}

export default function LogWindowList({ windows }: LogWindowListProps) {
  if (!windows.length) {
    return (
      <div className="text-xs text-gray-500 dark:text-slate-500 border border-dashed border-gray-300 dark:border-slate-700 rounded-xl p-4 bg-white dark:bg-slate-900/40">
        No log excerpts have been ingested for this incident yet.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {windows.map((window) => (
        <div
          key={`${window.source_id}-${window.started_at}`}
          className="border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-950/40 rounded-2xl p-4 space-y-3 shadow-sm"
        >
          <div className="flex items-center justify-between text-xs text-gray-500 dark:text-slate-400">
            <span className="uppercase tracking-wide">{window.source_id || 'logs'}</span>
            <span>
              {new Date(window.started_at).toLocaleTimeString()} –{' '}
              {new Date(window.ended_at).toLocaleTimeString()}
            </span>
          </div>
          <div className="bg-gray-50 dark:bg-slate-900/70 rounded-xl p-3 text-[11px] text-gray-800 dark:text-slate-200 font-mono space-y-1 max-h-48 overflow-auto">
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
