export type IncidentSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface IncidentRecord {
  id: string;
  signal_type: 'manual' | 'slack' | 'log' | 'github';
  title: string;
  description: string;
  repo_id?: string | null;
  severity: IncidentSeverity;
  status: 'queued' | 'processing' | 'resolved';
  source_ref?: string | null;
  created_at: string;
  updated_at: string;
  metadata: Record<string, any>;
}

export interface RepoMetadata {
  last_poll?: {
    at: string;
    success: boolean;
    exit_code: number;
  };
  auto_poll_enabled?: boolean;
  [key: string]: any;
}

export interface RepoConfig {
  id: string;
  name: string;
  repo_url: string;
  default_branch: string;
  github_app_installation_id?: string | null;
  description?: string | null;
  metadata: RepoMetadata;
  created_at: string;
  updated_at: string;
}

export interface RepoSnapshot {
  id: string;
  name: string;
  repo_url: string;
  default_branch: string;
}

export interface RepoPollResult {
  repo_id: string;
  success: boolean;
  exit_code: number;
  stdout: string;
  stderr: string;
  ran_at: string;
  incident_id?: string | null;
}

export interface LogWindow {
  source_id?: string | null;
  started_at: string;
  ended_at: string;
  lines: string[];
}

export interface SlackSnippet {
  channel_id: string;
  message_ts: string;
  text: string;
  user?: string | null;
}

export interface CommitSummary {
  sha: string;
  author: string;
  title: string;
  committed_at: string;
  stats: Record<string, any>;
}

export interface IncidentContextResponse {
  incident: IncidentRecord;
  repo?: RepoSnapshot | null;
  log_windows: LogWindow[];
  slack_messages: SlackSnippet[];
  commits: CommitSummary[];
}

export interface ManualIssuePayload {
  title: string;
  description: string;
  repo_id?: string;
  severity: IncidentSeverity;
  reporter?: string;
  tags?: string[];
}

export interface HealthResponse {
  ok: boolean;
  graph_ready: boolean;
}

export interface AgentStep {
  id: string;
  timestamp: number;
  type: 'search_slack' | 'read_file' | 'analyze' | 'generate_plan' | 'execute_tool';
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  details?: string;
}

export interface ToolCall {
  id: string;
  timestamp: number;
  toolName: string;
  arguments: Record<string, any>;
  response: any;
  duration?: number;
}

export interface SlackMessage {
  id: string;
  channel: string;
  user: string;
  timestamp: number;
  text: string;
  isRetrieved: boolean;
  relevanceScore?: number;
}

export interface CodeFile {
  path: string;
  content: string;
  language: string;
  highlightedLines?: number[];
}

export interface ReasoningStep {
  type: 'thought' | 'action' | 'observation';
  content: string;
}

export interface AgentState {
  currentNode: string;
  pastNodes: string[];
  loopIteration: number;
  memory: {
    retrievedContext: string[];
    pastActions: string[];
  };
}
