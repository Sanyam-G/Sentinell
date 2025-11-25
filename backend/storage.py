"""Thread-safe in-memory storage for configuration and incident data.

This is a temporary persistence layer so we can wire the new APIs without
blocking on Postgres/Redis setup. Replace with a real database once the API
contract stabilizes.
"""
from __future__ import annotations

from threading import RLock
from typing import Dict, List, Optional

from schemas import (
    GithubEventPayload,
    IncidentRecord,
    LogSource,
    ManualIssueRequest,
    RepoConfig,
    SlackChannelConfig,
)


class InMemoryStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._repos: Dict[str, RepoConfig] = {}
        self._log_sources: Dict[str, LogSource] = {}
        self._slack_channels: Dict[str, SlackChannelConfig] = {}
        self._incidents: Dict[str, IncidentRecord] = {}
        self._github_events: Dict[str, GithubEventPayload] = {}

    # --- Repo configuration -------------------------------------------------
    def add_repo(self, repo: RepoConfig) -> RepoConfig:
        with self._lock:
            self._repos[repo.id] = repo
            return repo

    def list_repos(self) -> List[RepoConfig]:
        with self._lock:
            return list(self._repos.values())

    def get_repo(self, repo_id: str) -> Optional[RepoConfig]:
        with self._lock:
            return self._repos.get(repo_id)

    # --- Log sources --------------------------------------------------------
    def add_log_source(self, source: LogSource) -> LogSource:
        with self._lock:
            self._log_sources[source.id] = source
            return source

    def list_log_sources(self) -> List[LogSource]:
        with self._lock:
            return list(self._log_sources.values())

    # --- Slack channels -----------------------------------------------------
    def add_slack_channel(self, channel: SlackChannelConfig) -> SlackChannelConfig:
        with self._lock:
            self._slack_channels[channel.id] = channel
            return channel

    def list_slack_channels(self) -> List[SlackChannelConfig]:
        with self._lock:
            return list(self._slack_channels.values())

    # --- Incidents ----------------------------------------------------------
    def add_incident(self, incident: IncidentRecord) -> IncidentRecord:
        with self._lock:
            self._incidents[incident.id] = incident
            return incident

    def list_incidents(self) -> List[IncidentRecord]:
        with self._lock:
            return sorted(
                self._incidents.values(), key=lambda item: item.created_at, reverse=True
            )

    def update_incident(self, incident: IncidentRecord) -> IncidentRecord:
        with self._lock:
            if incident.id not in self._incidents:
                raise KeyError(f"Incident {incident.id} missing")
            self._incidents[incident.id] = incident
            return incident

    # --- GitHub events ------------------------------------------------------
    def add_github_event(self, event: GithubEventPayload) -> GithubEventPayload:
        with self._lock:
            self._github_events[event.delivery_id] = event
            return event

    def list_github_events(self) -> List[GithubEventPayload]:
        with self._lock:
            return list(self._github_events.values())


store = InMemoryStore()
