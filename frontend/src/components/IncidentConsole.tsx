import { Incident, AgentStep } from '../types';

interface IncidentConsoleProps {
  incident: Incident;
  steps: AgentStep[];
  onStart: () => void;
  isRunning: boolean;
}

export default function IncidentConsole({ incident, steps, onStart, isRunning }: IncidentConsoleProps) {
  return (
    <div className="p-6 space-y-6">
      {/* Incident Header */}
      <div className="bg-gradient-to-r from-red-500/10 to-orange-500/10 border border-red-500/30 rounded-lg p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-1 text-xs font-semibold rounded bg-red-500/20 text-red-400 border border-red-500/30">
                ACTIVE
              </span>
              <span className="text-gray-400 text-sm">
                {new Date(incident.timestamp).toLocaleTimeString()}
              </span>
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">{incident.title}</h2>
            <p className="text-gray-300">{incident.description}</p>
          </div>
          <button
            onClick={onStart}
            disabled={isRunning}
            className="px-6 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-all"
          >
            {isRunning ? 'Running...' : 'Ask Agent'}
          </button>
        </div>
      </div>

      {/* Agent Steps Timeline */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <span className="h-1 w-1 rounded-full bg-cyan-400"></span>
          Investigation Timeline
        </h3>
        <div className="space-y-3">
          {steps.map((step, index) => (
            <div
              key={step.id}
              className="bg-slate-800/50 border border-cyan-500/20 rounded-lg p-4 hover:border-cyan-500/40 transition-all cursor-pointer group"
            >
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 mt-1">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    step.status === 'completed' ? 'bg-green-500/20 text-green-400 border border-green-500/30' :
                    step.status === 'in_progress' ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 animate-pulse' :
                    step.status === 'failed' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                    'bg-gray-500/20 text-gray-400 border border-gray-500/30'
                  }`}>
                    {step.status === 'completed' ? '✓' : index + 1}
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-semibold text-white">{step.title}</h4>
                    <span className="text-xs text-gray-400">
                      {new Date(step.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-sm text-gray-400 mb-2">{step.description}</p>
                  {step.details && (
                    <div className="text-sm text-cyan-400 bg-cyan-500/10 border border-cyan-500/20 rounded px-3 py-2 group-hover:bg-cyan-500/20 transition-all">
                      {step.details}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Final Output */}
      {steps.some(s => s.status === 'in_progress') && (
        <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/30 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
            <span className="animate-pulse">●</span>
            Remediation Plan
          </h3>
          <div className="space-y-2 text-gray-300">
            <p className="font-semibold text-white">Recommended Actions:</p>
            <ol className="list-decimal list-inside space-y-1 text-sm">
              <li>Implement exponential backoff in queue processing loop</li>
              <li>Add circuit breaker pattern to prevent cascading failures</li>
              <li>Increase worker pool size temporarily to handle backlog</li>
              <li>Add monitoring alerts for queue depth thresholds</li>
            </ol>
          </div>
        </div>
      )}
    </div>
  );
}
