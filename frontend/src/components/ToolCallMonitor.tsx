import { useState } from 'react';
import { ToolCall } from '../types';

interface ToolCallMonitorProps {
  toolCalls: ToolCall[];
}

export default function ToolCallMonitor({ toolCalls }: ToolCallMonitorProps) {
  const [selectedCall, setSelectedCall] = useState<ToolCall | null>(null);

  return (
    <div className="h-full flex flex-col bg-slate-900/20">
      <div className="px-4 py-3 border-b border-cyan-500/20">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <span className="h-1 w-1 rounded-full bg-cyan-400"></span>
          Tool Call Monitor
          <span className="ml-auto text-xs text-gray-400">{toolCalls.length} calls</span>
        </h3>
      </div>
      <div className="flex-1 overflow-auto scrollbar-thin">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-slate-900 border-b border-cyan-500/20">
            <tr className="text-gray-400">
              <th className="text-left p-3 font-medium">Time</th>
              <th className="text-left p-3 font-medium">Tool</th>
              <th className="text-left p-3 font-medium">Duration</th>
              <th className="text-left p-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {toolCalls.map((call) => (
              <tr
                key={call.id}
                onClick={() => setSelectedCall(call)}
                className="border-b border-slate-800 hover:bg-cyan-500/5 cursor-pointer transition-colors"
              >
                <td className="p-3 text-gray-400 text-xs">
                  {new Date(call.timestamp).toLocaleTimeString()}
                </td>
                <td className="p-3">
                  <code className="text-cyan-400 bg-cyan-500/10 px-2 py-1 rounded text-xs">
                    {call.toolName}
                  </code>
                </td>
                <td className="p-3 text-gray-400">{call.duration}ms</td>
                <td className="p-3">
                  <span className="text-green-400 text-xs">✓ Success</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
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
