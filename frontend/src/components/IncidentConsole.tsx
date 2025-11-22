import { useState } from 'react';
import { Incident, AgentStep } from '../types';
import StepDetailModal from './StepDetailModal';
import Sparkline from './Sparkline';
import { mockMetrics } from '../data/mockData';

interface IncidentConsoleProps {
  incident: Incident;
  steps: AgentStep[];
  onStart: () => void;
  isRunning: boolean;
}

export default function IncidentConsole({ incident, steps, onStart, isRunning }: IncidentConsoleProps) {
  const [selectedStep, setSelectedStep] = useState<AgentStep | null>(null);
  const [copied, setCopied] = useState(false);

  const remediationPlan = `Remediation Plan for Worker-17 CPU Spike

1. Implement exponential backoff in queue processing loop
2. Add circuit breaker pattern to prevent cascading failures
3. Increase worker pool size temporarily to handle backlog
4. Add monitoring alerts for queue depth thresholds`;

  const copyToClipboard = () => {
    navigator.clipboard.writeText(remediationPlan);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="p-8 space-y-8 max-w-4xl">
      {/* Incident Header */}
      <div className="space-y-4">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <div className="h-1.5 w-1.5 rounded-full bg-red-400 animate-pulse"></div>
              <span className="text-xs text-slate-500 uppercase tracking-wide">
                Active Incident
              </span>
            </div>
            <h2 className="text-3xl font-light text-white">{incident.title}</h2>
            <p className="text-slate-400 text-sm leading-relaxed max-w-2xl">{incident.description}</p>
          </div>
        </div>

        {/* Metrics Sparklines */}
        <div className="flex gap-6 pt-4">
          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className="text-xs text-slate-500">CPU</div>
              <div className="text-lg font-medium text-red-400">95%</div>
            </div>
            <Sparkline data={mockMetrics.cpu} color="#f87171" />
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className="text-xs text-slate-500">Memory</div>
              <div className="text-lg font-medium text-yellow-400">68%</div>
            </div>
            <Sparkline data={mockMetrics.memory} color="#fbbf24" />
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className="text-xs text-slate-500">Latency</div>
              <div className="text-lg font-medium text-orange-400">490ms</div>
            </div>
            <Sparkline data={mockMetrics.latency} color="#fb923c" />
          </div>
        </div>
      </div>

      {/* Agent Steps Timeline */}
      <div className="space-y-1">
        {steps.map((step, index) => (
          <div
            key={step.id}
            className="group py-4 border-b border-slate-800/50 hover:bg-slate-900/30 transition-colors -mx-4 px-4"
          >
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 mt-1">
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                  step.status === 'completed' ? 'bg-green-500/10 text-green-400' :
                  step.status === 'in_progress' ? 'bg-cyan-500/10 text-cyan-400' :
                  'bg-slate-500/10 text-slate-500'
                }`}>
                  {step.status === 'completed' ? '✓' : index + 1}
                </div>
              </div>
              <div className="flex-1 min-w-0 space-y-1">
                <div className="flex items-center gap-3">
                  <h4 className="font-medium text-white text-sm">{step.title}</h4>
                  <span className="text-xs text-slate-600">
                    {new Date(step.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-sm text-slate-500 leading-relaxed">{step.description}</p>
                {step.details && (
                  <button
                    onClick={() => setSelectedStep(step)}
                    className="text-xs text-cyan-400/80 mt-2 hover:text-cyan-400 transition-colors cursor-pointer text-left"
                  >
                    → {step.details}
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Final Output */}
      {steps.some(s => s.status === 'in_progress') && (
        <div className="mt-8 pt-8 border-t border-slate-800">
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse"></div>
              <span className="text-xs text-slate-500 uppercase tracking-wide">
                Remediation Plan
              </span>
              <button
                onClick={copyToClipboard}
                className="p-1 rounded hover:bg-cyan-500/10 text-cyan-400/60 hover:text-cyan-400 transition-colors"
                title={copied ? 'Copied!' : 'Copy to clipboard'}
              >
                {copied ? (
                  <span className="text-xs">✓</span>
                ) : (
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                )}
              </button>
            </div>
            <div className="space-y-3 text-sm">
              <div className="flex gap-3">
                <span className="text-slate-600">1.</span>
                <p className="text-slate-300">Implement exponential backoff in queue processing loop</p>
              </div>
              <div className="flex gap-3">
                <span className="text-slate-600">2.</span>
                <p className="text-slate-300">Add circuit breaker pattern to prevent cascading failures</p>
              </div>
              <div className="flex gap-3">
                <span className="text-slate-600">3.</span>
                <p className="text-slate-300">Increase worker pool size temporarily to handle backlog</p>
              </div>
              <div className="flex gap-3">
                <span className="text-slate-600">4.</span>
                <p className="text-slate-300">Add monitoring alerts for queue depth thresholds</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {selectedStep && (
        <StepDetailModal
          step={selectedStep}
          onClose={() => setSelectedStep(null)}
        />
      )}
    </div>
  );
}
