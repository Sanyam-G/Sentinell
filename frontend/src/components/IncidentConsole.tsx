import { useMemo, useState } from 'react';
import { AgentStep, IncidentContextResponse, IncidentRecord } from '../types';
import StepDetailModal from './StepDetailModal';
import Sparkline from './Sparkline';
import { mockMetrics } from '../data/mockData';

interface IncidentConsoleProps {
  incident: IncidentRecord | null;
  steps: AgentStep[];
  context?: IncidentContextResponse | null;
  isLoading?: boolean;
}

export default function IncidentConsole({ incident, steps, context, isLoading }: IncidentConsoleProps) {
  const [selectedStep, setSelectedStep] = useState<AgentStep | null>(null);
  const [copied, setCopied] = useState(false);

  const remediationPlan = useMemo(() => {
    if (!incident) {
      return 'Select an incident to generate a remediation plan.';
    }
    const planLines: string[] = [
      `Remediation Plan for ${incident.title}`,
      '',
      `Signal type: ${incident.signal_type.toUpperCase()} (${incident.severity})`,
    ];
    if (context?.log_windows?.length) {
      planLines.push(`Inspect ${context.log_windows.length} log windows for correlated errors.`);
    }
    if (context?.slack_messages?.length) {
      planLines.push(`Review ${context.slack_messages.length} Slack messages for on-call context.`);
    }
    if (context?.commits?.length) {
      planLines.push(`Audit ${context.commits.length} recent commits touching affected services.`);
    }
    planLines.push('Validate fix via automated tests and prepare PR for review.');
    return planLines.join('\n');
  }, [context, incident]);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(remediationPlan);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (isLoading) {
    return (
      <div className="p-8 text-slate-500 text-sm">Fetching incident context…</div>
    );
  }

  if (!incident) {
    return (
      <div className="p-8 text-slate-500 text-sm">
        No incidents yet. Submit one using the form to the left to watch the agent respond.
      </div>
    );
  }

  const severityColorMap: Record<string, string> = {
    low: 'text-green-400 border-green-400/40',
    medium: 'text-yellow-400 border-yellow-400/40',
    high: 'text-orange-400 border-orange-400/40',
    critical: 'text-red-400 border-red-400/40',
  };
  const severityColor = severityColorMap[incident.severity] ?? 'text-slate-400 border-slate-500/40';
  const statusLabel = incident.status === 'resolved' ? 'Resolved' : incident.status === 'processing' ? 'Investigating' : 'Queued';
  const repoName = context?.repo?.name ?? (incident.repo_id || 'Unassigned');
  const incidentTimestamp = new Date(incident.created_at).toLocaleString();

  return (
    <div className="p-8 space-y-8 max-w-4xl">
      {/* Incident Header */}
      <div className="space-y-4">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <div className={`h-1.5 w-1.5 rounded-full ${incident.status === 'resolved' ? 'bg-green-400' : 'bg-red-400 animate-pulse'}`}></div>
              <span className="text-xs text-slate-500 uppercase tracking-wide">
                {statusLabel}
              </span>
              <span className={`text-[10px] uppercase tracking-wide border rounded-full px-2 py-0.5 ${severityColor}`}>
                {incident.severity}
              </span>
            </div>
            <h2 className="text-3xl font-light text-white">{incident.title}</h2>
            <p className="text-slate-400 text-sm leading-relaxed max-w-2xl">{incident.description}</p>
            <div className="flex flex-wrap gap-4 text-xs text-slate-500">
              <span>Repo: <span className="text-slate-300">{repoName}</span></span>
              <span>Occurred: <span className="text-slate-300">{incidentTimestamp}</span></span>
            </div>
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
        {steps.length === 0 && (
          <div className="text-xs text-slate-500 py-6 text-center border border-dashed border-slate-800 rounded-lg">
            Waiting for agent steps. As soon as the worker processes this incident, updates will appear here.
          </div>
        )}
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
      {steps.length > 0 && (
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
            <pre className="bg-slate-900/60 border border-slate-800 p-4 rounded text-slate-200 text-xs whitespace-pre-wrap">
              {remediationPlan}
            </pre>
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
