"""Pydantic schemas shared between routers, storage, and the agent runtime."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl


class Severity(str, Enum):
    """Severity levels for incoming incidents."""

    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class RepoCreateRequest(BaseModel):
    name: str = Field(..., description="Human friendly label")
    repo_url: HttpUrl = Field(..., description="Git or GitHub HTTPS URL")
    default_branch: str = Field("main", description="Branch to watch")
    github_app_installation_id: Optional[str] = Field(
        None, description="GitHub App installation used for write access"
    )
    description: Optional[str] = Field(
        None, description="Optional notes shown in the dashboard"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RepoConfig(RepoCreateRequest):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class LogSourceType(str, Enum):
    loki = "loki"
    cloudwatch = "cloudwatch"
    elasticsearch = "elasticsearch"
    file = "file"
    custom = "custom"


class LogSourceCreateRequest(BaseModel):
    name: str
    repo_id: Optional[str] = Field(
        None, description="Associate source with a repo; optional"
    )
    source_type: LogSourceType = LogSourceType.loki
    endpoint: Optional[str] = Field(None, description="Ingress endpoint or bucket")
    auth_mode: Optional[str] = Field(None, description="How to auth (iam, basic, token)")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LogSource(LogSourceCreateRequest):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SlackChannelCreateRequest(BaseModel):
    team_id: str
    channel_id: str
    channel_name: Optional[str] = None
    repo_id: Optional[str] = None
    description: Optional[str] = None


class SlackChannelConfig(SlackChannelCreateRequest):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ManualIssueRequest(BaseModel):
    title: str
    description: str
    repo_id: Optional[str] = None
    severity: Severity = Severity.medium
    reporter: Optional[str] = Field(None, description="Email/Slack handle")
    tags: List[str] = Field(default_factory=list)


class LogSignalRequest(BaseModel):
    repo_id: Optional[str] = None
    source_id: Optional[str] = None
    message: str
    level: Optional[str] = None
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SlackSignalRequest(BaseModel):
    team_id: str
    channel_id: str
    message_ts: str
    user: Optional[str] = None
    text: str
    repo_id: Optional[str] = None
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    thread_ts: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GithubEventPayload(BaseModel):
    delivery_id: str
    event: str
    payload: Dict[str, Any]
    repo_id: Optional[str] = None
    received_at: datetime = Field(default_factory=datetime.utcnow)


class IncidentRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    signal_type: Literal["manual", "slack", "log", "github"]
    title: str
    description: str
    repo_id: Optional[str] = None
    severity: Severity = Severity.medium
    status: Literal["queued", "processing", "resolved"] = "queued"
    source_ref: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IncidentListResponse(BaseModel):
    incidents: List[IncidentRecord]


class RepoListResponse(BaseModel):
    repos: List[RepoConfig]


class LogSourceListResponse(BaseModel):
    log_sources: List[LogSource]


class SlackChannelListResponse(BaseModel):
    channels: List[SlackChannelConfig]


class RepoSnapshot(BaseModel):
    id: str
    name: str
    repo_url: str
    default_branch: str


class RepoPollResult(BaseModel):
    repo_id: str
    success: bool
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    ran_at: datetime = Field(default_factory=datetime.utcnow)
    incident_id: Optional[str] = None


class IncidentContext(BaseModel):
    id: str
    signal_type: str
    title: str
    description: str
    severity: Severity
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LogWindow(BaseModel):
    source_id: Optional[str]
    started_at: datetime
    ended_at: datetime
    lines: List[str] = Field(default_factory=list)


class SlackSnippet(BaseModel):
    channel_id: str
    message_ts: str
    text: str
    user: Optional[str] = None


class CommitSummary(BaseModel):
    sha: str
    author: str
    title: str
    committed_at: datetime
    stats: Dict[str, Any] = Field(default_factory=dict)


class ActionPlan(BaseModel):
    summary: str
    commands: List[str] = Field(default_factory=list)
    files_to_touch: List[str] = Field(default_factory=list)
    pr_title: Optional[str] = None
    pr_body: Optional[str] = None


class IncidentContextResponse(BaseModel):
    incident: IncidentRecord
    repo: Optional[RepoSnapshot] = None
    log_windows: List[LogWindow] = Field(default_factory=list)
    slack_messages: List[SlackSnippet] = Field(default_factory=list)
    commits: List[CommitSummary] = Field(default_factory=list)
