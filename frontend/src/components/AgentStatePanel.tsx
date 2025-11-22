import { AgentState } from '../types';

interface AgentStatePanelProps {
  state: AgentState;
}

export default function AgentStatePanel({ state }: AgentStatePanelProps) {
  return (
    <div className="h-full flex flex-col">
      <div className="px-4 py-3 border-b border-cyan-500/20">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <span className="h-1 w-1 rounded-full bg-cyan-400"></span>
          Agent State
        </h3>
      </div>
      <div className="flex-1 overflow-auto scrollbar-thin p-4 space-y-4">
        {/* Current Node */}
        <div className="bg-slate-800/50 border border-cyan-500/30 rounded-lg p-4">
          <div className="text-xs text-gray-400 mb-2">Current Node</div>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse"></span>
            <code className="text-sm text-cyan-400 font-semibold">
              {state.currentNode}
            </code>
          </div>
        </div>

        {/* Loop Iteration */}
        <div className="bg-slate-800/30 border border-slate-700/30 rounded-lg p-4">
          <div className="text-xs text-gray-400 mb-2">Loop Iteration</div>
          <div className="text-2xl font-bold text-white">
            {state.loopIteration}
          </div>
        </div>

        {/* Node History */}
        <div>
          <div className="text-xs text-gray-400 mb-3">Node History</div>
          <div className="space-y-2">
            {state.pastNodes.map((node, idx) => (
              <div
                key={idx}
                className="flex items-center gap-2 text-sm"
              >
                <div className="w-1 h-1 rounded-full bg-green-400"></div>
                <code className="text-gray-400">{node}</code>
              </div>
            ))}
          </div>
        </div>

        {/* Retrieved Context */}
        <div>
          <div className="text-xs text-gray-400 mb-3">Retrieved Context</div>
          <div className="space-y-2">
            {state.memory.retrievedContext.map((context, idx) => (
              <div
                key={idx}
                className="text-xs text-gray-300 bg-slate-800/30 border border-slate-700/30 rounded p-2"
              >
                {context}
              </div>
            ))}
          </div>
        </div>

        {/* Past Actions */}
        <div>
          <div className="text-xs text-gray-400 mb-3">Past Actions</div>
          <div className="space-y-2">
            {state.memory.pastActions.map((action, idx) => (
              <div
                key={idx}
                className="flex items-start gap-2"
              >
                <span className="text-green-400 mt-0.5">✓</span>
                <span className="text-xs text-gray-300">{action}</span>
              </div>
            ))}
          </div>
        </div>

        {/* System Stats */}
        <div className="pt-4 border-t border-slate-700/30">
          <div className="text-xs text-gray-400 mb-3">System Stats</div>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-gray-400">Memory Usage</span>
              <span className="text-cyan-400">45.2 MB</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Tokens Used</span>
              <span className="text-cyan-400">12,847</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Runtime</span>
              <span className="text-cyan-400">3m 42s</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
