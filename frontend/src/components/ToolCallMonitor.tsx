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
        {toolCalls.map((call) => (
          <div
            key={call.id}
            onClick={() => setSelectedCall(call)}
            className="group cursor-pointer"
          >
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-3">
                <span className="text-green-400">✓</span>
                <code className="text-cyan-400">{call.toolName}</code>
              </div>
              <div className="flex items-center gap-3 text-slate-600">
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
          className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50"
          onClick={() => setSelectedCall(null)}
        >
          <div
            className="bg-slate-900 border border-cyan-500/30 rounded-lg max-w-2xl w-full mx-4 max-h-[80vh] overflow-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Tool Call Details</h3>
                <button
                  onClick={() => setSelectedCall(null)}
                  className="text-gray-400 hover:text-white"
                >
                  ✕
                </button>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-gray-400">Tool Name</label>
                  <div className="mt-1">
                    <code className="text-cyan-400 bg-cyan-500/10 px-3 py-2 rounded block">
                      {selectedCall.toolName}
                    </code>
                  </div>
                </div>
                <div>
                  <label className="text-sm text-gray-400">Arguments</label>
                  <pre className="mt-1 text-sm text-gray-300 bg-slate-800 p-4 rounded overflow-auto">
                    {JSON.stringify(selectedCall.arguments, null, 2)}
                  </pre>
                </div>
                <div>
                  <label className="text-sm text-gray-400">Response</label>
                  <pre className="mt-1 text-sm text-gray-300 bg-slate-800 p-4 rounded overflow-auto">
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
