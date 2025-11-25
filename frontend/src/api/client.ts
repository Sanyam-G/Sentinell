import {
  IncidentContextResponse,
  IncidentRecord,
  IncidentSeverity,
  ManualIssuePayload,
  HealthResponse,
  RepoConfig,
  RepoPollResult,
} from '../types';

const DEFAULT_BASE = 'http://localhost:8000';
const API_BASE = (import.meta.env.VITE_BACKEND_URL ?? DEFAULT_BASE).replace(/\/$/, '');

type RequestOptions = RequestInit & { skipJson?: boolean };

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const detail = await safeParseError(response);
    throw new Error(detail || `Request failed with status ${response.status}`);
  }

  if (options.skipJson) {
    return null as T;
  }

  return (await response.json()) as T;
}

async function safeParseError(response: Response): Promise<string | undefined> {
  try {
    const data = await response.json();
    return typeof data === 'string' ? data : data?.detail;
  } catch (err) {
    return undefined;
  }
}

interface IncidentListResponse {
  incidents: IncidentRecord[];
}

interface RepoListResponse {
  repos: RepoConfig[];
}

export async function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/api/health');
}

export async function fetchIncidents(): Promise<IncidentRecord[]> {
  const data = await request<IncidentListResponse>('/api/incidents');
  return data.incidents;
}

export async function fetchIncidentContext(incidentId: string): Promise<IncidentContextResponse> {
  return request<IncidentContextResponse>(`/api/incidents/${incidentId}/context`);
}

export async function fetchRepos(): Promise<RepoConfig[]> {
  const data = await request<RepoListResponse>('/api/repos');
  return data.repos;
}

export async function pollRepo(repoId: string): Promise<RepoPollResult> {
  return request<RepoPollResult>(`/api/repos/${repoId}/poll`, {
    method: 'POST',
  });
}

export async function createManualIncident(
  payload: ManualIssuePayload
): Promise<IncidentRecord> {
  const body = {
    ...payload,
    severity: payload.severity ?? ('medium' as IncidentSeverity),
    reporter: payload.reporter ?? 'dashboard',
    tags: payload.tags ?? [],
  };
  return request<IncidentRecord>('/api/issues', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}
