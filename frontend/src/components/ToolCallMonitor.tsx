import { useState } from 'react';
import { ToolCall } from '../types';

interface ToolCallMonitorProps {
  toolCalls: ToolCall[];
}

export default function ToolCallMonitor({ toolCalls }: ToolCallMonitorProps) {
  const [selectedCall, setSelectedCall] = useState<ToolCall | null>(null);

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 overflow-auto scrollbar-thin p-6 space-y-3">
        {toolCalls.length === 0 && (
          <div className="text-xs text-gray-500 dark:text-slate-500">
            The agent has not emitted any tool calls for this incident yet.
          </div>
        )}
        {toolCalls.map((call) => (
          <div
            key={call.id}
            onClick={() => setSelectedCall(call)}
            className="group cursor-pointer rounded-2xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-950/40 p-4 hover:border-blue-400 dark:hover:border-blue-500 transition"
          >
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-3">
                <span className="text-emerald-500">✓</span>
                <code className="text-blue-600 dark:text-cyan-300">{call.toolName}</code>
              </div>
              <div className="flex items-center gap-3 text-gray-500 dark:text-slate-500">
                <span>{call.duration}ms</span>
                <span>{new Date(call.timestamp).toLocaleTimeString()}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Modal for tool call details */}
      {selectedCall && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50"
          onClick={() => setSelectedCall(null)}
        >
          <div
            className="bg-white dark:bg-slate-950 border border-gray-200 dark:border-slate-800 rounded-3xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Tool Call Details</h3>
                <button
                  onClick={() => setSelectedCall(null)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-white"
                >
                  ✕
                </button>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-gray-500 dark:text-slate-400">Tool Name</label>
                  <div className="mt-1">
                    <code className="text-blue-600 dark:text-cyan-300 bg-blue-50 dark:bg-blue-500/10 px-3 py-2 rounded-xl block">
                      {selectedCall.toolName}
                    </code>
                  </div>
                </div>
                <div>
                  <label className="text-sm text-gray-500 dark:text-slate-400">Arguments</label>
                  <pre className="mt-1 text-sm text-gray-700 dark:text-slate-200 bg-gray-50 dark:bg-slate-900/60 p-4 rounded-2xl overflow-auto">
                    {JSON.stringify(selectedCall.arguments, null, 2)}
                  </pre>
                </div>
                <div>
                  <label className="text-sm text-gray-500 dark:text-slate-400">Response</label>
                  <pre className="mt-1 text-sm text-gray-700 dark:text-slate-200 bg-gray-50 dark:bg-slate-900/60 p-4 rounded-2xl overflow-auto">
                    {JSON.stringify(selectedCall.response, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
