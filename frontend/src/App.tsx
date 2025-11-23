import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';
import IncidentConsole from './components/IncidentConsole';
import ToolCallMonitor from './components/ToolCallMonitor';
import SlackViewer from './components/SlackViewer';
import CodeViewer from './components/CodeViewer';
import ReasoningStream from './components/ReasoningStream';
import LogWindowList from './components/LogWindowList';
import {
  AgentStep,
  CodeFile,
  HealthResponse,
  IncidentContextResponse,
  IncidentRecord,
  IncidentSeverity,
  ReasoningStep,
  SlackMessage,
  ToolCall,
  RepoConfig,
  RepoMetadata,
} from './types';
import {
  createManualIncident,
  fetchHealth,
  fetchIncidentContext,
  fetchIncidents,
  fetchRepos,
  pollRepo,
} from './api/client';

const POLL_INTERVAL_MS = 5000;

type Tab = 'reasoning' | 'signals' | 'code' | 'tools';

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('reasoning');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [incidents, setIncidents] = useState<IncidentRecord[]>([]);
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  const [context, setContext] = useState<IncidentContextResponse | null>(null);
  const [loadingIncidents, setLoadingIncidents] = useState(true);
  const [loadingContext, setLoadingContext] = useState(false);
  const [repos, setRepos] = useState<RepoConfig[]>([]);
  const [loadingRepos, setLoadingRepos] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [issueSuccess, setIssueSuccess] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [pollingRepoId, setPollingRepoId] = useState<string | null>(null);
  const [issueForm, setIssueForm] = useState({
    title: '',
    description: '',
    repo_id: '',
    severity: 'medium' as IncidentSeverity,
    reporter: 'dashboard',
  });

  const loadRepos = useCallback(async () => {
    setLoadingRepos(true);
    try {
      const data = await fetchRepos();
      setRepos(data);
      setError(null);
      setIssueForm((prev) => {
        if (data.length === 0) {
          return { ...prev, repo_id: '' };
        }
        if (prev.repo_id) {
          return prev;
        }
        return { ...prev, repo_id: data[0].id };
      });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoadingRepos(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  useEffect(() => {
    loadRepos();
  }, [loadRepos]);

  const loadIncidents = useCallback(async () => {
    setLoadingIncidents(true);
    try {
      const data = await fetchIncidents();
      setIncidents(data);
      if (!selectedIncidentId && data.length > 0) {
        setSelectedIncidentId(data[0].id);
      } else if (
        selectedIncidentId &&
        data.length > 0 &&
        !data.find((incident) => incident.id === selectedIncidentId)
      ) {
        setSelectedIncidentId(data[0].id);
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoadingIncidents(false);
    }
  }, [selectedIncidentId]);

  useEffect(() => {
    loadIncidents();
    const interval = setInterval(loadIncidents, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [loadIncidents]);

  useEffect(() => {
    if (!selectedIncidentId) {
      setContext(null);
      return;
    }
    setLoadingContext(true);
    fetchIncidentContext(selectedIncidentId)
      .then((data) => {
        setContext(data);
        setError(null);
      })
      .catch((err) => setError((err as Error).message))
      .finally(() => setLoadingContext(false));
  }, [selectedIncidentId]);

  const selectedIncident = incidents.find((incident) => incident.id === selectedIncidentId) ?? null;

  const repoLookup = useMemo(() => {
    const map = new Map<string, RepoConfig>();
    repos.forEach((repo) => map.set(repo.id, repo));
    return map;
  }, [repos]);

  const selectedRepo = useMemo(() => {
    if (!selectedIncident?.repo_id) {
      return null;
    }
    return repoLookup.get(selectedIncident.repo_id) ?? null;
  }, [repoLookup, selectedIncident?.repo_id]);

  const lastPoll = selectedRepo?.metadata?.last_poll;
  const autoPollEnabled = selectedRepo ? selectedRepo.metadata?.auto_poll_enabled !== false : true;

  const agentSteps = useMemo(() => buildAgentSteps(selectedIncident, context), [selectedIncident, context]);
  const slackMessages = useMemo(
    () => buildSlackMessages(selectedIncident, context),
    [selectedIncident, context]
  );
  const reasoningSteps = useMemo(() => buildReasoningSteps(selectedIncident, context), [selectedIncident, context]);
  const codeFiles = useMemo(() => buildCodeFiles(context), [context]);
  const toolCalls = useMemo(() => buildToolCalls(context), [context]);

  const incidentActive = Boolean(selectedIncident && selectedIncident.status !== 'resolved');
  const severityBadgeMap: Record<IncidentSeverity, string> = {
    low: 'border-emerald-500/40 text-emerald-300',
    medium: 'border-amber-500/40 text-amber-300',
    high: 'border-orange-500/40 text-orange-300',
    critical: 'border-red-500/40 text-red-300',
  };

  const formatTimestamp = (value?: string) => (value ? new Date(value).toLocaleString() : 'Never');

  const statusCards = useMemo(
    () => [
      {
        label: 'Worker Status',
        value: incidentActive ? 'Investigating' : incidents.length > 0 ? 'Idle' : 'Awaiting signal',
        meta: selectedIncident
          ? `Updated ${new Date(selectedIncident.updated_at).toLocaleTimeString()}`
          : 'Queue empty',
        accent: incidentActive ? 'text-cyan-300' : 'text-slate-400',
      },
      {
        label: 'Active Incident',
        value: selectedIncident ? selectedIncident.title : 'None',
        meta: selectedIncident
          ? `${selectedIncident.signal_type} · ${selectedIncident.severity}`
          : 'Use the form to submit an incident',
        accent: 'text-white',
      },
      {
        label: 'Target Repo',
        value: selectedRepo?.name ?? 'Unassigned',
        meta: selectedRepo ? `Branch ${selectedRepo.default_branch}` : 'Link a repo to enable PR automation',
      },
      {
        label: 'Last Poll',
        value: lastPoll ? formatTimestamp(lastPoll.at) : 'Never',
        meta: lastPoll
          ? lastPoll.success
            ? 'Health checks passing'
            : `Failed · exit ${lastPoll.exit_code}`
          : 'Auto poll pending',
      },
    ],
    [incidentActive, incidents.length, lastPoll, selectedIncident, selectedRepo],
  );

  const handleInputChange = (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = event.target;
    setIssueForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleIssueSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!issueForm.title || !issueForm.description) {
      setError('Title and description are required.');
      return;
    }
    setIsSubmitting(true);
    setError(null);
    setIssueSuccess(null);
    try {
      const created = await createManualIncident({
        title: issueForm.title,
        description: issueForm.description,
        repo_id: issueForm.repo_id || undefined,
        severity: issueForm.severity,
        reporter: issueForm.reporter,
        tags: [],
      });
      setIssueForm((prev) => ({
        title: '',
        description: '',
        repo_id: prev.repo_id,
        severity: prev.severity,
        reporter: prev.reporter,
      }));
      await loadIncidents();
      setSelectedIncidentId(created.id);
      setIssueSuccess('Incident queued. The agent is on it.');
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handlePollRepo = useCallback(async () => {
    if (!selectedRepo) {
      return;
    }
    setPollingRepoId(selectedRepo.id);
    try {
      await pollRepo(selectedRepo.id);
      await Promise.all([loadRepos(), loadIncidents()]);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setPollingRepoId(null);
    }
  }, [selectedRepo, loadRepos, loadIncidents]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Animated background gradient orbs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-cyan-500/5 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-blue-500/5 rounded-full blur-3xl animate-pulse" style={{animationDelay: '1s'}}></div>
      </div>

      <header className="relative border-b border-slate-800/50 backdrop-blur-xl bg-slate-950/80">
        <div className="px-8 py-4 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 shadow-lg shadow-cyan-500/20 flex items-center justify-center">
                <span className="text-white font-bold text-lg">S</span>
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
                  Sentinel Operations Console
                </h1>
                <p className="text-xs text-slate-500">AI-Powered SRE Agent</p>
              </div>
            </div>
            <div className="flex items-center gap-4 text-xs">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/50 border border-slate-800/50">
                <div className={`h-2 w-2 rounded-full ${health?.ok ? 'bg-green-400 shadow-lg shadow-green-400/50' : 'bg-red-400'} animate-pulse`}></div>
                <span className={health?.ok ? 'text-green-400' : 'text-red-400'}>
                  {health?.ok ? 'Backend online' : 'Backend unreachable'}
                </span>
              </div>
              <div className="px-3 py-1.5 rounded-lg bg-slate-900/50 border border-slate-800/50">
                <span className="text-slate-400">Incidents: </span>
                <span className="text-cyan-400 font-medium">{incidents.length}</span>
              </div>
            </div>
          </div>
          {error && (
            <div className="rounded-lg bg-red-500/10 border border-red-500/30 px-4 py-2">
              <p className="text-xs text-red-400">{error}</p>
            </div>
          )}
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
            {statusCards.map((card, idx) => (
              <div
                key={card.label}
                className="group rounded-xl border border-slate-800/50 bg-gradient-to-br from-slate-900/60 to-slate-900/30 backdrop-blur-sm p-4 hover:border-cyan-500/30 transition-all duration-300 hover:shadow-lg hover:shadow-cyan-500/5"
                style={{animationDelay: `${idx * 100}ms`}}
              >
                <p className="text-[11px] uppercase tracking-wide text-slate-500">{card.label}</p>
                <p className={`mt-1.5 text-base font-semibold ${card.accent ?? 'text-white'} group-hover:scale-105 transition-transform`}>
                  {card.value}
                </p>
                <p className="text-[11px] text-slate-500 mt-1">{card.meta}</p>
              </div>
            ))}
          </div>
        </div>
      </header>

      <div className="flex h-[calc(100vh-100px)] relative">
        <aside className="w-80 border-r border-slate-800/50 bg-slate-950/80 backdrop-blur-xl flex flex-col relative">
          <div className="px-4 py-3 border-b border-slate-800/50 text-xs flex justify-between items-center bg-gradient-to-r from-slate-900/50 to-transparent">
            <span className="font-semibold text-slate-300 uppercase tracking-wide">Incidents</span>
            {loadingIncidents && (
              <div className="flex items-center gap-2">
                <div className="h-1 w-1 rounded-full bg-cyan-400 animate-ping"></div>
                <span className="text-slate-500">Refreshing…</span>
              </div>
            )}
          </div>
          <div className="flex-1 overflow-auto">
            {incidents.length === 0 && (
              <div className="p-4 text-xs text-slate-500">
                No incidents yet. Submit one below to kick off the agent loop.
              </div>
            )}
            <div className="divide-y divide-slate-900">
              {incidents.map((incident) => {
                const repoLabel = incident.repo_id
                  ? repoLookup.get(incident.repo_id)?.name ?? 'Unknown repo'
                  : 'Unassigned';
                const severityClass = severityBadgeMap[incident.severity] ?? 'border-slate-700 text-slate-400';
                const statusTint =
                  incident.status === 'resolved'
                    ? 'text-green-400'
                    : incident.status === 'processing'
                      ? 'text-amber-400'
                      : 'text-slate-400';
                return (
                  <button
                    key={incident.id}
                    onClick={() => setSelectedIncidentId(incident.id)}
                    className={`w-full text-left px-4 py-3 transition-all duration-200 relative group ${
                      incident.id === selectedIncidentId 
                        ? 'bg-gradient-to-r from-cyan-500/10 to-transparent border-l-2 border-cyan-400 shadow-lg shadow-cyan-500/5' 
                        : 'hover:bg-slate-900/40'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <p className={`text-sm line-clamp-2 font-medium ${incident.id === selectedIncidentId ? 'text-white' : 'text-slate-300'}`}>
                        {incident.title}
                      </p>
                      <span
                        className={`text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full border ${severityClass} shadow-sm`}
                      >
                        {incident.severity}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-slate-500 mt-1.5">
                      <span>
                        {new Date(incident.created_at).toLocaleTimeString()} · {incident.signal_type}
                      </span>
                      <span className={`uppercase text-[10px] font-semibold ${statusTint}`}>{incident.status}</span>
                    </div>
                    <div className="text-[11px] text-slate-500 mt-1">
                      Repo: <span className="text-slate-300 font-medium">{repoLabel}</span>
                    </div>
                    {incident.id === selectedIncidentId && (
                      <div className="absolute inset-y-0 left-0 w-0.5 bg-gradient-to-b from-transparent via-cyan-400 to-transparent"></div>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
          <form onSubmit={handleIssueSubmit} className="border-t border-slate-800/50 p-4 space-y-3 bg-gradient-to-t from-slate-900/50 to-transparent">
            <div className="flex items-center justify-between text-xs uppercase tracking-wide">
              <p className="font-semibold text-cyan-400">Report Issue</p>
              {issueSuccess && (
                <span className="text-[10px] text-green-400 animate-pulse">{issueSuccess}</span>
              )}
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Describe a reliability task and the agent will immediately begin collecting context and drafting a fix.
            </p>
            <input
              type="text"
              name="title"
              value={issueForm.title}
              onChange={handleInputChange}
              placeholder="Title"
              className="w-full bg-slate-900/50 backdrop-blur-sm text-white text-xs px-3 py-2.5 rounded-lg border border-slate-700/50 focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/20 outline-none transition-all"
            />
            <textarea
              name="description"
              value={issueForm.description}
              onChange={handleInputChange}
              placeholder="Describe the incident"
              rows={3}
              className="w-full bg-slate-900/50 backdrop-blur-sm text-white text-xs px-3 py-2.5 rounded-lg border border-slate-700/50 focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/20 outline-none transition-all resize-none"
            />
            <label className="block text-[11px] text-slate-400">
              Target repository
              <select
                name="repo_id"
                value={issueForm.repo_id}
                onChange={handleInputChange}
                disabled={loadingRepos || repos.length === 0}
                className="mt-1.5 w-full bg-slate-900/50 backdrop-blur-sm text-white text-xs px-3 py-2.5 rounded-lg border border-slate-700/50 focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/20 outline-none transition-all disabled:opacity-60"
              >
                {repos.length === 0 && <option value="">No repos registered</option>}
                {repos.length > 0 &&
                  repos.map((repo) => (
                    <option key={repo.id} value={repo.id}>
                      {repo.name}
                    </option>
                  ))}
              </select>
            </label>
            <select
              name="severity"
              value={issueForm.severity}
              onChange={handleInputChange}
              className="w-full bg-slate-900/50 backdrop-blur-sm text-white text-xs px-3 py-2.5 rounded-lg border border-slate-700/50 focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/20 outline-none transition-all"
            >
              {['low', 'medium', 'high', 'critical'].map((level) => (
                <option key={level} value={level}>
                  {level}
                </option>
              ))}
            </select>
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 text-xs font-semibold py-2.5 rounded-lg border border-cyan-500/40 hover:from-cyan-500/30 hover:to-blue-500/30 hover:shadow-lg hover:shadow-cyan-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            >
              {isSubmitting ? 'Submitting…' : 'Create Incident'}
            </button>
            <p className="text-[10px] text-slate-500 leading-relaxed">
              💡 Tip: leave repo blank for general tasks or select a repo to give the SRE immediate clone + test access.
            </p>
          </form>
        </aside>

        <div className="flex-1 flex">
          <div className="flex-1 overflow-auto">
            <div className="min-h-full">
              <IncidentConsole incident={selectedIncident} steps={agentSteps} context={context} isLoading={loadingContext} />
              <RepoInsightsPanel
                repo={selectedRepo}
                lastPoll={lastPoll}
                autoPollEnabled={autoPollEnabled}
                onPollRepo={handlePollRepo}
                isPolling={selectedRepo ? pollingRepoId === selectedRepo.id : false}
              />
            </div>
          </div>

          <div className="w-[500px] border-l border-slate-800/50 flex flex-col bg-slate-950/40 backdrop-blur-xl">
            <div className="flex border-b border-slate-800/50 bg-gradient-to-r from-slate-900/60 to-slate-900/40">
              <TabButton label="Reasoning" active={activeTab === 'reasoning'} onClick={() => setActiveTab('reasoning')} />
              <TabButton label="Signals" active={activeTab === 'signals'} onClick={() => setActiveTab('signals')} />
              <TabButton label="Code" active={activeTab === 'code'} onClick={() => setActiveTab('code')} />
              <TabButton label="Tools" active={activeTab === 'tools'} onClick={() => setActiveTab('tools')} />
            </div>

            <div className="flex-1 overflow-hidden">
              {activeTab === 'reasoning' && (
                <div className="h-full overflow-auto scrollbar-thin p-6">
                  <ReasoningStream steps={reasoningSteps} />
                </div>
              )}
              {activeTab === 'signals' && (
                <div className="h-full overflow-auto scrollbar-thin p-6 space-y-6">
                  <section>
                    <p className="text-xs text-slate-500 uppercase tracking-wide mb-2">Slack threads</p>
                    <div className="border border-slate-800 rounded-xl bg-slate-900/40 p-4">
                      <SlackViewer messages={slackMessages} />
                    </div>
                  </section>
                  <section>
                    <p className="text-xs text-slate-500 uppercase tracking-wide mb-2">Log excerpts</p>
                    <LogWindowList windows={context?.log_windows ?? []} />
                  </section>
                </div>
              )}
              {activeTab === 'code' && (
                <div className="h-full overflow-auto scrollbar-thin">
                  <CodeViewer files={codeFiles} />
                </div>
              )}
              {activeTab === 'tools' && (
                <div className="h-full overflow-auto scrollbar-thin">
                  <ToolCallMonitor toolCalls={toolCalls} />
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;

interface TabButtonProps {
  label: string;
  active: boolean;
  onClick: () => void;
}

function TabButton({ label, active, onClick }: TabButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`relative px-6 py-3 text-sm font-semibold transition-all duration-300 ${
        active 
          ? 'text-cyan-400' 
          : 'text-slate-400 hover:text-slate-200'
      }`}
    >
      {label}
      {active && (
        <>
          <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-cyan-500 to-blue-500 shadow-lg shadow-cyan-500/50"></div>
          <div className="absolute inset-0 bg-gradient-to-b from-cyan-500/5 to-transparent"></div>
        </>
      )}
    </button>
  );
}

function buildAgentSteps(incident: IncidentRecord | null, context: IncidentContextResponse | null): AgentStep[] {
  if (!incident) {
    return [];
  }
  const baseTime = Date.parse(incident.updated_at ?? incident.created_at);
  const steps: AgentStep[] = [
    {
      id: `${incident.id}-observe`,
      timestamp: baseTime,
      type: 'analyze',
      title: 'Observe signal',
      description: `Processing ${incident.signal_type} signal with severity ${incident.severity}.`,
      status: 'completed',
    },
  ];

  if (context?.log_windows?.length) {
    steps.push({
      id: `${incident.id}-logs`,
      timestamp: baseTime + 1000,
      type: 'read_file',
      title: 'Inspect logs',
      description: `Retrieved ${context.log_windows.length} log windows for correlation.`,
      status: 'completed',
      details: context.log_windows[0]?.lines?.[0]?.slice(0, 160),
    });
  }

  if (context?.slack_messages?.length) {
    steps.push({
      id: `${incident.id}-slack`,
      timestamp: baseTime + 2000,
      type: 'search_slack',
      title: 'Review Slack context',
      description: `Found ${context.slack_messages.length} relevant Slack messages.`,
      status: 'completed',
    });
  }

  if (context?.commits?.length) {
    steps.push({
      id: `${incident.id}-commits`,
      timestamp: baseTime + 3000,
      type: 'read_file',
      title: 'Compare recent commits',
      description: `Analyzing ${context.commits.length} commits touching this repo.`,
      status: 'completed',
    });
  }

  steps.push({
    id: `${incident.id}-plan`,
    timestamp: baseTime + 4000,
    type: 'generate_plan',
    title: 'Draft remediation plan',
    description: 'Summarizing findings and preparing automation plan for worker.',
    status: incident.status === 'resolved' ? 'completed' : 'in_progress',
  });

  return steps;
}

function buildSlackMessages(
  incident: IncidentRecord | null,
  context: IncidentContextResponse | null
): SlackMessage[] {
  if (context?.slack_messages?.length) {
    return context.slack_messages.map((message) => ({
      id: message.message_ts,
      channel: message.channel_id,
      user: message.user || 'unknown',
      timestamp: Date.parse(message.message_ts) || Date.now(),
      text: message.text,
      isRetrieved: true,
      relevanceScore: 0.9,
    }));
  }

  if (!incident) {
    return [];
  }

  return [
    {
      id: `${incident.id}-placeholder-slack`,
      channel: '#incidents',
      user: 'auto-bot',
      timestamp: Date.now(),
      text: 'Waiting for Slack ingestion to provide relevant context.',
      isRetrieved: false,
    },
  ];
}

function buildReasoningSteps(
  incident: IncidentRecord | null,
  context: IncidentContextResponse | null
): ReasoningStep[] {
  if (!incident) {
    return [];
  }

  const steps: ReasoningStep[] = [
    {
      type: 'thought',
      content: `Received ${incident.signal_type} signal for "${incident.title}" (${incident.severity}).`,
    },
  ];

  if (context?.log_windows?.length) {
    steps.push({
      type: 'observation',
      content: `Found ${context.log_windows.length} log windows showing correlated errors near incident timestamp.`,
    });
  }

  if (context?.slack_messages?.length) {
    steps.push({
      type: 'thought',
      content: 'On-call chatter suggests elevated latency for payment service. Prioritize rollout check.',
    });
  }

  if (context?.commits?.length) {
    steps.push({
      type: 'action',
      content: `Diffing ${context.commits.length} recent commits to isolate risky change.`,
    });
  }

  steps.push({
    type: 'observation',
    content: incident.status === 'resolved'
      ? 'Worker marked this incident resolved after remediation plan execution.'
      : 'Worker still processing remediation plan; awaiting final confirmation.',
  });

  return steps;
}

function buildCodeFiles(context: IncidentContextResponse | null): CodeFile[] {
  if (!context?.commits?.length) {
    return [];
  }

  return context.commits.slice(0, 3).map((commit) => ({
    path: `commit/${commit.sha.slice(0, 7)}`,
    language: 'python',
    content: [
      `# ${commit.title}`,
      `# Author: ${commit.author}`,
      '',
      'diff --git a/service.py b/service.py',
      '--- a/service.py',
      '+++ b/service.py',
      '+ # pseudo diff snippet generated from commit metadata',
    ].join('\n'),
    highlightedLines: [4, 5, 6],
  }));
}

function buildToolCalls(context: IncidentContextResponse | null): ToolCall[] {
  if (!context) {
    return [];
  }

  const now = Date.now();
  const calls: ToolCall[] = [];

  if (context.log_windows.length) {
    calls.push({
      id: `${context.incident.id}-logs`,
      timestamp: now - 4000,
      toolName: 'logs.fetch_window',
      arguments: { windows: context.log_windows.length },
      response: { status: 'ok' },
      duration: 1200,
    });
  }

  if (context.slack_messages.length) {
    calls.push({
      id: `${context.incident.id}-slack`,
      timestamp: now - 2500,
      toolName: 'slack.search_channel',
      arguments: { channel: context.slack_messages[0].channel_id },
      response: { matches: context.slack_messages.length },
      duration: 800,
    });
  }

  if (context.commits.length) {
    calls.push({
      id: `${context.incident.id}-git`,
      timestamp: now - 1200,
      toolName: 'git.get_recent_commits',
      arguments: { count: context.commits.length },
      response: { commits: context.commits.map((commit) => commit.sha) },
      duration: 600,
    });
  }

  if (!calls.length) {
    calls.push({
      id: `${context.incident.id}-noop`,
      timestamp: now - 500,
      toolName: 'context.wait',
      arguments: {},
      response: { message: 'Awaiting ingestion.' },
      duration: 300,
    });
  }

  return calls;
}

interface RepoInsightsPanelProps {
  repo: RepoConfig | null;
  lastPoll?: RepoMetadata['last_poll'];
  autoPollEnabled: boolean;
  onPollRepo?: () => void;
  isPolling?: boolean;
}

function RepoInsightsPanel({ repo, lastPoll, autoPollEnabled, onPollRepo, isPolling }: RepoInsightsPanelProps) {
  return (
    <div className="px-8 pb-10">
      <div className="rounded-2xl border border-slate-700/50 bg-gradient-to-br from-slate-900/60 via-slate-900/40 to-slate-900/60 backdrop-blur-xl p-6 space-y-6 shadow-2xl hover:border-slate-600/50 transition-all duration-300">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <div className="h-2 w-2 rounded-full bg-cyan-400 shadow-lg shadow-cyan-400/50 animate-pulse"></div>
              <p className="text-xs uppercase tracking-wider font-bold text-cyan-400">Repository health</p>
            </div>
            <p className="text-sm text-slate-400">Live status for the repo tied to this incident.</p>
          </div>
          <button
            type="button"
            onClick={onPollRepo}
            disabled={!repo || !onPollRepo || isPolling}
            className="relative text-xs px-5 py-2.5 rounded-lg bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-400/40 text-cyan-300 font-semibold hover:from-cyan-500/30 hover:to-blue-500/30 hover:shadow-lg hover:shadow-cyan-500/20 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200 overflow-hidden group"
          >
            {isPolling && (
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-500/20 to-transparent animate-shimmer"></div>
            )}
            <span className="relative z-10">{isPolling ? 'Running checks…' : 'Run repo checks'}</span>
          </button>
        </div>
        {repo ? (
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-[11px] text-slate-500 uppercase">Repository</p>
              <p className="text-white text-sm font-medium">{repo.name}</p>
              <a
                href={repo.repo_url}
                target="_blank"
                rel="noreferrer"
                className="text-xs text-cyan-400 hover:text-cyan-200"
              >
                {repo.repo_url}
              </a>
            </div>
            <div>
              <p className="text-[11px] text-slate-500 uppercase">Default branch</p>
              <p className="text-sm text-white font-medium">{repo.default_branch}</p>
              <p className="text-[11px] text-slate-500">Used for PR generation</p>
            </div>
            <div>
              <p className="text-[11px] text-slate-500 uppercase">Last poll</p>
              <p className="text-sm text-white font-medium">{lastPoll ? new Date(lastPoll.at).toLocaleString() : 'Never'}</p>
              <p className={`text-[11px] ${lastPoll?.success ? 'text-green-400' : 'text-red-400'}`}>
                {lastPoll
                  ? lastPoll.success
                    ? 'Health checks passing'
                    : `Failed · exit ${lastPoll.exit_code}`
                  : 'Auto poll pending'}
              </p>
            </div>
            <div>
              <p className="text-[11px] text-slate-500 uppercase">Auto polling</p>
              <p className={`text-sm font-medium ${autoPollEnabled ? 'text-green-400' : 'text-slate-400'}`}>
                {autoPollEnabled ? 'Enabled' : 'Paused'}
              </p>
              <p className="text-[11px] text-slate-500">
                {autoPollEnabled ? 'Runs every few minutes via backend poller' : 'Re-enable in repo metadata'}
              </p>
            </div>
          </div>
        ) : (
          <div className="text-sm text-slate-400">
            Attach this incident to a repository to unlock git context, automated fixes, and PR creation.
          </div>
        )}
      </div>
    </div>
  );
}
