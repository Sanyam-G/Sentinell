import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';
import IncidentConsole from './components/IncidentConsole';
import ToolCallMonitor from './components/ToolCallMonitor';
import SlackViewer from './components/SlackViewer';
import CodeViewer from './components/CodeViewer';
import ReasoningStream from './components/ReasoningStream';
import LogWindowList from './components/LogWindowList';
import { useTheme } from './contexts/ThemeContext';
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
  const { theme, toggleTheme } = useTheme();
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
    low: 'border-emerald-200 text-emerald-600 dark:border-emerald-500/40 dark:text-emerald-300',
    medium: 'border-amber-200 text-amber-600 dark:border-amber-500/40 dark:text-amber-300',
    high: 'border-orange-200 text-orange-600 dark:border-orange-500/40 dark:text-orange-300',
    critical: 'border-red-200 text-red-600 dark:border-red-500/40 dark:text-red-300',
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
        accent: incidentActive ? 'text-blue-600 dark:text-cyan-300' : 'text-gray-500 dark:text-slate-400',
      },
      {
        label: 'Active Incident',
        value: selectedIncident ? selectedIncident.title : 'None',
        meta: selectedIncident
          ? `${selectedIncident.signal_type} · ${selectedIncident.severity}`
          : 'Use the form to submit an incident',
        accent: 'text-gray-900 dark:text-white',
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
    <div className="min-h-screen bg-white dark:bg-slate-950 text-gray-900 dark:text-slate-100 transition-colors duration-300">
      <header className="relative border-b border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-950 transition-colors duration-300">
        <div className="px-8 py-4 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-blue-600 dark:bg-blue-500 flex items-center justify-center">
                <span className="text-white font-bold text-lg">S</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-blue-600 dark:text-blue-400">
                  Sentinell Operations Console
                </h1>
                <p className="text-xs text-gray-500 dark:text-slate-400">AI-Powered SRE Agent</p>
              </div>
            </div>
            <div className="flex items-center gap-4 text-xs">
              <button
                onClick={toggleTheme}
                className="p-2.5 rounded-xl bg-gray-100 dark:bg-slate-900 border border-gray-300 dark:border-slate-700 hover:bg-gray-200 dark:hover:bg-slate-800 transition-all duration-200"
                aria-label="Toggle theme"
              >
                {theme === 'dark' ? (
                  <svg className="w-4 h-4 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4 text-indigo-600" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
                  </svg>
                )}
              </button>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-100 dark:bg-slate-900 border border-gray-300 dark:border-slate-700 transition-colors duration-300">
                <div className={`h-2 w-2 rounded-full ${health?.ok ? 'bg-green-500' : 'bg-red-500'} animate-pulse`}></div>
                <span className={health?.ok ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
                  {health?.ok ? 'Backend online' : 'Backend unreachable'}
                </span>
              </div>
              <div className="px-3 py-1.5 rounded-lg bg-gray-100 dark:bg-slate-900 border border-gray-300 dark:border-slate-700 transition-colors duration-300">
                <span className="text-gray-600 dark:text-slate-400">Incidents: </span>
                <span className="text-blue-600 dark:text-blue-400 font-medium">{incidents.length}</span>
              </div>
            </div>
          </div>
          {error && (
            <div className="rounded-xl bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30 px-4 py-3">
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            </div>
          )}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
            {statusCards.map((card) => (
              <div
                key={card.label}
                className="rounded-xl border border-gray-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-5 hover:shadow-md hover:border-blue-400 dark:hover:border-blue-600 transition-all duration-200"
              >
                <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-slate-400 font-medium">{card.label}</p>
                <p className={`mt-2 text-lg font-bold ${card.accent ?? 'text-gray-900 dark:text-white'}`}>
                  {card.value}
                </p>
                <p className="text-xs text-gray-500 dark:text-slate-400 mt-1.5">{card.meta}</p>
              </div>
            ))}
          </div>
        </div>
      </header>

      <div className="flex h-[calc(100vh-180px)] relative">
        <aside className="w-80 border-r border-gray-300 dark:border-slate-700 bg-white dark:bg-slate-900 flex flex-col relative transition-colors duration-300">
          <div className="px-4 py-4 border-b border-gray-300 dark:border-slate-700 text-sm flex justify-between items-center">
            <span className="font-bold text-gray-900 dark:text-white">Incidents</span>
            {loadingIncidents && (
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-blue-500 animate-ping"></div>
                <span className="text-gray-500 dark:text-slate-500 text-xs">Refreshing…</span>
              </div>
            )}
          </div>
          <div className="flex-1 overflow-auto">
            {incidents.length === 0 && (
              <div className="p-4 text-sm text-gray-500 dark:text-slate-500">
                No incidents yet. Submit one below to kick off the agent loop.
              </div>
            )}
            <div className="divide-y divide-gray-200 dark:divide-slate-800">
              {incidents.map((incident) => {
                const repoLabel = incident.repo_id
                  ? repoLookup.get(incident.repo_id)?.name ?? 'Unknown repo'
                  : 'Unassigned';
                const severityClass = severityBadgeMap[incident.severity] ?? 'border-gray-300 dark:border-slate-700 text-gray-600 dark:text-slate-400';
                const statusTint =
                  incident.status === 'resolved'
                    ? 'text-green-600 dark:text-green-400'
                    : incident.status === 'processing'
                      ? 'text-amber-600 dark:text-amber-400'
                      : 'text-gray-500 dark:text-slate-400';
                return (
                  <button
                    key={incident.id}
                    onClick={() => setSelectedIncidentId(incident.id)}
                    className={`w-full text-left px-4 py-3 transition-all duration-200 relative group ${
                      incident.id === selectedIncidentId 
                        ? 'bg-blue-50 dark:bg-blue-950/30 border-l-4 border-blue-600 dark:border-blue-500' 
                        : 'hover:bg-gray-50 dark:hover:bg-slate-800'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <p className={`text-sm line-clamp-2 font-semibold ${incident.id === selectedIncidentId ? 'text-blue-700 dark:text-blue-300' : 'text-gray-900 dark:text-slate-300'}`}>
                        {incident.title}
                      </p>
                      <span
                        className={`text-[10px] uppercase tracking-wide px-2 py-1 rounded-md border ${severityClass} font-medium`}
                      >
                        {incident.severity}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs text-gray-500 dark:text-slate-500 mt-2">
                      <span>
                        {new Date(incident.created_at).toLocaleTimeString()} · {incident.signal_type}
                      </span>
                      <span className={`uppercase text-[10px] font-bold ${statusTint}`}>{incident.status}</span>
                    </div>
                    <div className="text-xs text-gray-500 dark:text-slate-500 mt-1.5">
                      Repo: <span className="text-gray-700 dark:text-slate-300 font-semibold">{repoLabel}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
          <form onSubmit={handleIssueSubmit} className="border-t border-gray-300 dark:border-slate-700 p-4 space-y-3 bg-gray-50 dark:bg-slate-800 transition-colors duration-300">
            <div className="flex items-center justify-between text-sm">
              <p className="font-bold text-gray-900 dark:text-white">Report Issue</p>
              {issueSuccess && (
                <span className="text-xs text-green-600 dark:text-green-400 animate-pulse">{issueSuccess}</span>
              )}
            </div>
            <p className="text-xs text-gray-600 dark:text-slate-400 leading-relaxed">
              Describe a reliability task and the agent will immediately begin collecting context and drafting a fix.
            </p>
            <input
              type="text"
              name="title"
              value={issueForm.title}
              onChange={handleInputChange}
              placeholder="Title"
              className="w-full bg-white dark:bg-slate-900 text-gray-900 dark:text-white text-sm px-4 py-3 rounded-xl border border-gray-300 dark:border-slate-700 focus:border-blue-500 dark:focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all"
            />
            <textarea
              name="description"
              value={issueForm.description}
              onChange={handleInputChange}
              placeholder="Describe the incident"
              rows={3}
              className="w-full bg-white dark:bg-slate-900 text-gray-900 dark:text-white text-sm px-4 py-3 rounded-xl border border-gray-300 dark:border-slate-700 focus:border-blue-500 dark:focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all resize-none"
            />
            <label className="block text-xs text-gray-600 dark:text-slate-400 font-medium">
              Target repository
              <select
                name="repo_id"
                value={issueForm.repo_id}
                onChange={handleInputChange}
                disabled={loadingRepos || repos.length === 0}
                className="mt-2 w-full bg-white dark:bg-slate-900 text-gray-900 dark:text-white text-sm px-4 py-3 rounded-xl border border-gray-300 dark:border-slate-700 focus:border-blue-500 dark:focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all disabled:opacity-60"
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
              className="w-full bg-white dark:bg-slate-900 text-gray-900 dark:text-white text-sm px-4 py-3 rounded-xl border border-gray-300 dark:border-slate-700 focus:border-blue-500 dark:focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all"
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
              className="w-full bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold py-3 rounded-xl shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            >
              {isSubmitting ? 'Submitting…' : 'Create Incident'}
            </button>
            <p className="text-xs text-gray-500 dark:text-slate-500 leading-relaxed">
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

          <div className="w-[500px] border-l border-gray-300 dark:border-slate-700 flex flex-col bg-white dark:bg-slate-900 transition-colors duration-300">
            <div className="flex border-b border-gray-300 dark:border-slate-700">
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
                    <p className="text-xs text-gray-500 dark:text-slate-400 uppercase tracking-wide mb-2">Slack threads</p>
                    <div className="border border-gray-300 dark:border-slate-700 rounded-xl bg-gray-50 dark:bg-slate-800 p-4">
                      <SlackViewer messages={slackMessages} />
                    </div>
                  </section>
                  <section>
                    <p className="text-xs text-gray-500 dark:text-slate-400 uppercase tracking-wide mb-2">Log excerpts</p>
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
          ? 'text-blue-600 dark:text-blue-400' 
          : 'text-gray-500 dark:text-slate-400 hover:text-gray-900 dark:hover:text-slate-200'
      }`}
    >
      {label}
      {active && (
        <>
          <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 dark:bg-blue-500"></div>
          <div className="absolute inset-0 bg-blue-50 dark:bg-blue-500/5"></div>
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
      <div className="rounded-2xl border border-gray-200 dark:border-slate-700/50 bg-white dark:bg-slate-900/60 p-6 space-y-6 shadow-lg hover:shadow-xl transition-all duration-300">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></div>
              <p className="text-sm uppercase tracking-wider font-bold text-gray-900 dark:text-white">Repository health</p>
            </div>
            <p className="text-sm text-gray-600 dark:text-slate-400">Live status for the repo tied to this incident.</p>
          </div>
          <button
            type="button"
            onClick={onPollRepo}
            disabled={!repo || !onPollRepo || isPolling}
            className="relative text-sm px-5 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
          >
            <span className="relative z-10">{isPolling ? 'Running checks…' : 'Run repo checks'}</span>
          </button>
        </div>
        {repo ? (
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-xs text-gray-500 dark:text-slate-500 uppercase font-medium">Repository</p>
              <p className="text-gray-900 dark:text-white text-sm font-semibold mt-1">{repo.name}</p>
              <a
                href={repo.repo_url}
                target="_blank"
                rel="noreferrer"
                className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
              >
                {repo.repo_url}
              </a>
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-slate-500 uppercase font-medium">Default branch</p>
              <p className="text-sm text-gray-900 dark:text-white font-semibold mt-1">{repo.default_branch}</p>
              <p className="text-xs text-gray-500 dark:text-slate-500">Used for PR generation</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-slate-500 uppercase font-medium">Last poll</p>
              <p className="text-sm text-gray-900 dark:text-white font-semibold mt-1">{lastPoll ? new Date(lastPoll.at).toLocaleString() : 'Never'}</p>
              <p className={`text-xs ${lastPoll?.success ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                {lastPoll
                  ? lastPoll.success
                    ? 'Health checks passing'
                    : `Failed · exit ${lastPoll.exit_code}`
                  : 'Auto poll pending'}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-slate-500 uppercase font-medium">Auto polling</p>
              <p className={`text-sm font-semibold mt-1 ${autoPollEnabled ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-slate-400'}`}>
                {autoPollEnabled ? 'Enabled' : 'Paused'}
              </p>
              <p className="text-xs text-gray-500 dark:text-slate-500">
                {autoPollEnabled ? 'Runs every few minutes via backend poller' : 'Re-enable in repo metadata'}
              </p>
            </div>
          </div>
        ) : (
          <div className="text-sm text-gray-600 dark:text-slate-400">
            Attach this incident to a repository to unlock git context, automated fixes, and PR creation.
          </div>
        )}
      </div>
    </div>
  );
}
