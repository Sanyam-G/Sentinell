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
      <div className="p-8">
        <div className="rounded-2xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 text-sm text-gray-500 dark:text-slate-400">
          Fetching incident context…
        </div>
      </div>
    );
  }

  if (!incident) {
    return (
      <div className="p-8">
        <div className="rounded-2xl border border-dashed border-gray-300 dark:border-slate-700 bg-white dark:bg-slate-900/60 p-6 text-sm text-gray-600 dark:text-slate-400">
          No incidents yet. Submit one using the form to the left to watch the agent respond.
        </div>
      </div>
    );
  }

  const severityColorMap: Record<string, string> = {
    low: 'border-emerald-200 text-emerald-600 dark:border-emerald-500/30 dark:text-emerald-300',
    medium: 'border-amber-200 text-amber-600 dark:border-amber-500/30 dark:text-amber-300',
    high: 'border-orange-200 text-orange-600 dark:border-orange-500/30 dark:text-orange-300',
    critical: 'border-red-200 text-red-600 dark:border-red-500/30 dark:text-red-300',
  };
  const severityColor = severityColorMap[incident.severity] ?? 'border-gray-200 text-gray-600';
  const statusLabel = incident.status === 'resolved' ? 'Resolved' : incident.status === 'processing' ? 'Investigating' : 'Queued';
  const repoName = context?.repo?.name ?? (incident.repo_id || 'Unassigned');
  const incidentTimestamp = new Date(incident.created_at).toLocaleString();

  return (
    <div className="p-8 space-y-8 text-gray-900 dark:text-slate-100">
      <div className="rounded-3xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-950/40 p-6 shadow-sm">
        <div className="flex flex-wrap gap-4 items-start justify-between">
          <div className="space-y-3">
            <div className="flex items-center gap-3 text-xs uppercase tracking-wide">
              <span className={`h-2 w-2 rounded-full ${incident.status === 'resolved' ? 'bg-emerald-400' : 'bg-amber-400 animate-pulse'}`} />
              <span className="text-gray-500 dark:text-slate-400">{statusLabel}</span>
              <span className={`px-3 py-1 rounded-full border text-[10px] font-semibold ${severityColor}`}>
                {incident.severity}
              </span>
            </div>
            <h2 className="text-3xl font-semibold text-balance">{incident.title}</h2>
            <p className="text-sm text-gray-600 dark:text-slate-300 max-w-2xl leading-relaxed">{incident.description}</p>
            <div className="flex flex-wrap gap-5 text-xs text-gray-500 dark:text-slate-400">
              <span>Repo <span className="font-medium text-gray-900 dark:text-white">{repoName}</span></span>
              <span>Occurred <span className="font-medium text-gray-900 dark:text-white">{incidentTimestamp}</span></span>
            </div>
          </div>
        </div>

        <div className="grid sm:grid-cols-3 gap-4 mt-6">
          <div className="rounded-2xl border border-gray-100 dark:border-slate-800 bg-gray-50 dark:bg-slate-900/40 p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500 dark:text-slate-400">CPU</p>
              <p className="text-lg font-semibold text-rose-500">95%</p>
            </div>
            <Sparkline data={mockMetrics.cpu} color="#f43f5e" />
          </div>
          <div className="rounded-2xl border border-gray-100 dark:border-slate-800 bg-gray-50 dark:bg-slate-900/40 p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500 dark:text-slate-400">Memory</p>
              <p className="text-lg font-semibold text-amber-500">68%</p>
            </div>
            <Sparkline data={mockMetrics.memory} color="#fbbf24" />
          </div>
          <div className="rounded-2xl border border-gray-100 dark:border-slate-800 bg-gray-50 dark:bg-slate-900/40 p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500 dark:text-slate-400">Latency</p>
              <p className="text-lg font-semibold text-orange-500">490ms</p>
            </div>
            <Sparkline data={mockMetrics.latency} color="#fb923c" />
          </div>
        </div>
      </div>

      <div className="rounded-3xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-950/40">
        <div className="divide-y divide-gray-100 dark:divide-slate-800">
          {steps.length === 0 && (
            <div className="p-8 text-center text-sm text-gray-500 dark:text-slate-400">
              Waiting for agent steps. As soon as the worker processes this incident, updates will appear here.
            </div>
          )}
          {steps.map((step, index) => (
            <div key={step.id} className="p-5 hover:bg-gray-50 dark:hover:bg-slate-900/40 transition-colors">
              <div className="flex items-start gap-4">
                <div className={`w-8 h-8 rounded-2xl flex items-center justify-center text-xs font-semibold ${
                  step.status === 'completed'
                    ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300'
                    : step.status === 'in_progress'
                      ? 'bg-blue-100 text-blue-700 dark:bg-blue-500/10 dark:text-blue-300'
                      : 'bg-gray-100 text-gray-600 dark:bg-slate-800 dark:text-slate-400'
                }`}>
                  {step.status === 'completed' ? '✓' : index + 1}
                </div>
                <div className="flex-1 min-w-0 space-y-1">
                  <div className="flex flex-wrap items-center gap-3">
                    <h4 className="font-semibold text-sm">{step.title}</h4>
                    <span className="text-xs text-gray-400 dark:text-slate-500">
                      {new Date(step.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-slate-300 leading-relaxed">{step.description}</p>
                  {step.details && (
                    <button
                      onClick={() => setSelectedStep(step)}
                      className="text-xs text-blue-600 dark:text-blue-300 mt-2 hover:underline"
                    >
                      View detail →
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {steps.length > 0 && (
        <div className="rounded-3xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-950/40 p-6 shadow-sm">
          <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-gray-500 dark:text-slate-400">
            <span className="h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
            Remediation Plan
            <button
              onClick={copyToClipboard}
              className="ml-auto inline-flex items-center gap-1 px-3 py-1 rounded-xl border border-gray-200 dark:border-slate-700 text-gray-600 dark:text-slate-300 text-[11px] hover:border-blue-400"
            >
              {copied ? 'Copied ✓' : 'Copy plan'}
            </button>
          </div>
          <pre className="mt-4 bg-gray-50 dark:bg-slate-900/60 border border-gray-100 dark:border-slate-800 p-4 rounded-2xl text-xs text-gray-700 dark:text-slate-200 whitespace-pre-wrap leading-relaxed">
            {remediationPlan}
          </pre>
        </div>
      )}

      {selectedStep && (
        <StepDetailModal
          step={selectedStep}
          onClose={() => setSelectedStep(null)}
        />
      )}
    </div>
  );
}
