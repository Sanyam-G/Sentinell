"""Utilities to hydrate SREState instances with repo/log/Slack context."""
from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.ingestion.commits import COMMITS_NAMESPACE
from data.ingestion.logs import LOG_NAMESPACE
from data.ingestion.slack import SLACK_NAMESPACE
from data.pinecone.retriever import fetch_documents
from db import crud, models
from schemas import (
    CommitSummary,
    IncidentContext,
    IncidentContextResponse,
    IncidentRecord,
    LogWindow,
    RepoSnapshot,
    SlackSnippet,
)
from state import SREState
from services.git_manager import repo_manager


async def fetch_next_incident(session: AsyncSession) -> Optional[IncidentRecord]:
    """Fetch the oldest queued incident and mark it as processing."""
    result = await session.execute(
        select(models.Incident)
        .where(models.Incident.status == "queued")
        .order_by(models.Incident.created_at)
        .limit(1)
    )
    incident = result.scalars().first()
    if not incident:
        return None

    incident.status = "processing"
    incident.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(incident)
    return IncidentRecord(**incident.model_dump())


async def mark_incident_resolved(
    session: AsyncSession, incident_id: str, *, success: bool
) -> None:
    result = await session.execute(select(models.Incident).where(models.Incident.id == incident_id))
    record = result.scalar_one_or_none()
    if not record:
        return

    record.status = "resolved" if success else "queued"
    record.updated_at = datetime.utcnow()
    await session.commit()


async def hydrate_state_from_incident(
    session: AsyncSession, state: SREState, incident: IncidentRecord
) -> SREState:
    repo, repo_path, log_windows, slack_messages, commits = await _assemble_context(session, incident)

    state.incident = IncidentContext(
        id=incident.id,
        signal_type=incident.signal_type,
        title=incident.title,
        description=incident.description,
        severity=incident.severity,
        metadata=incident.metadata,
    )
    state.repo = repo
    state.repo_path = repo_path
    state.log_windows = log_windows
    state.slack_messages = slack_messages
    state.commits = commits
    state.add_step(f"Hydrated context for incident {incident.id}")
    return state


async def get_incident_context(
    session: AsyncSession, incident_id: str
) -> Optional[IncidentContextResponse]:
    record = await crud.get_incident(session, incident_id)
    if not record:
        return None
    incident = IncidentRecord(**record.model_dump())
    repo, _, log_windows, slack_messages, commits = await _assemble_context(session, incident)
    return IncidentContextResponse(
        incident=incident,
        repo=repo,
        log_windows=log_windows,
        slack_messages=slack_messages,
        commits=commits,
    )


async def _assemble_context(
    session: AsyncSession, incident: IncidentRecord
) -> tuple[Optional[RepoSnapshot], Optional[str], list[LogWindow], list[SlackSnippet], list[CommitSummary]]:
    repo = await _get_repo_snapshot(session, incident.repo_id)
    repo_path = await _ensure_checkout(repo)
    log_windows = _build_log_windows(incident)
    slack_messages = _build_slack_context(incident)
    commits = await _build_commit_summaries(incident, repo)
    return repo, repo_path, log_windows, slack_messages, commits


async def _get_repo_snapshot(session: AsyncSession, repo_id: Optional[str]) -> Optional[RepoSnapshot]:
    if not repo_id:
        return None
    repo = await crud.get_repo(session, repo_id)
    if not repo:
        return None
    return RepoSnapshot(
        id=repo.id,
        name=repo.name,
        repo_url=repo.repo_url,
        default_branch=repo.default_branch,
    )


async def _ensure_checkout(repo: Optional[RepoSnapshot]) -> Optional[str]:
    if not repo:
        return None
    try:
        path = await asyncio.to_thread(repo_manager.ensure_checkout, repo)
        return path.as_posix()
    except Exception as exc:  # pragma: no cover - best-effort checkout
        print(f"[git] Unable to sync repo {repo.name}: {exc}")
        return None


def _build_log_windows(incident: IncidentRecord) -> list[LogWindow]:
    if not incident.repo_id:
        return _synthetic_log_window(incident)

    start, end = _incident_window(incident)
    matches = _query_namespace(incident.repo_id, LOG_NAMESPACE, start, end, limit=100)
    if not matches:
        return _synthetic_log_window(incident)

    grouped: dict[str, list[tuple[datetime, str]]] = defaultdict(list)
    for match in matches:
        metadata = _metadata(match)
        timestamp = _coerce_datetime(metadata.get("timestamp"))
        level = (metadata.get("level") or "info").upper()
        text = metadata.get("text") or metadata.get("message") or incident.description
        source_id = metadata.get("source_id") or incident.source_ref or "logs"
        grouped[source_id].append((timestamp, f"[{timestamp.isoformat()}] {level} {text}"))

    windows: list[LogWindow] = []
    for source_id, entries in grouped.items():
        entries.sort(key=lambda item: item[0])
        windows.append(
            LogWindow(
                source_id=source_id,
                started_at=entries[0][0],
                ended_at=entries[-1][0],
                lines=[line for _, line in entries],
            )
        )
    return sorted(windows, key=lambda win: win.started_at)


def _synthetic_log_window(incident: IncidentRecord) -> list[LogWindow]:
    base_time = incident.created_at or datetime.utcnow()
    synthetic_lines = [
        f"[{(base_time - timedelta(minutes=5)).isoformat()}] WARN No log entries in Pinecone",
        f"[{base_time.isoformat()}] INFO Using incident payload instead",
        f"[{(base_time + timedelta(minutes=1)).isoformat()}] ERROR {incident.description[:120]}",
    ]
    return [
        LogWindow(
            source_id=incident.source_ref or "synthetic",
            started_at=base_time - timedelta(minutes=10),
            ended_at=base_time + timedelta(minutes=2),
            lines=synthetic_lines,
        )
    ]


def _build_slack_context(incident: IncidentRecord) -> list[SlackSnippet]:
    if not incident.repo_id and incident.signal_type != "slack":
        return []

    start, end = _incident_window(incident)
    incident_metadata = incident.metadata or {}
    matches = []
    if incident.repo_id:
        matches = _query_namespace(incident.repo_id, SLACK_NAMESPACE, start, end, limit=50)

    snippets: list[SlackSnippet] = []
    for match in matches:
        metadata = _metadata(match)
        snippets.append(
            SlackSnippet(
                channel_id=str(metadata.get("channel_id") or incident_metadata.get("channel_id", "unknown")),
                message_ts=str(metadata.get("message_ts") or metadata.get("timestamp") or match.id),
                text=metadata.get("text") or incident.description,
                user=metadata.get("user") or incident_metadata.get("user"),
            )
        )

    if not snippets and incident.signal_type == "slack":
        snippets.append(
            SlackSnippet(
                channel_id=str(incident_metadata.get("channel_id", "unknown")),
                message_ts=str(incident_metadata.get("occurred_at", incident.created_at.isoformat())),
                text=incident.description,
                user=str(incident_metadata.get("user", "unknown")),
            )
        )
    return snippets


async def _build_commit_summaries(
    incident: IncidentRecord, repo: Optional[RepoSnapshot]
) -> list[CommitSummary]:
    commits = _commits_from_pinecone(incident)
    git_commits = await _git_commit_summaries(repo)

    combined: list[CommitSummary] = []
    seen: set[str] = set()
    for entry in commits + git_commits:
        if entry.sha in seen:
            continue
        seen.add(entry.sha)
        combined.append(entry)
    return combined[:10]


def _commits_from_pinecone(incident: IncidentRecord) -> list[CommitSummary]:
    if not incident.repo_id:
        return []
    start, end = _incident_window(incident)
    # widen commit window to capture earlier pushes
    start -= timedelta(hours=12)
    matches = _query_namespace(incident.repo_id, COMMITS_NAMESPACE, start, end, limit=50)
    commits: list[CommitSummary] = []
    for match in matches:
        metadata = _metadata(match)
        timestamp = _coerce_datetime(metadata.get("timestamp"))
        files = metadata.get("files", [])
        if isinstance(files, str):
            try:
                files = json.loads(files)
            except Exception:
                files = [f.strip() for f in files.split(",") if f.strip()]
        commits.append(
            CommitSummary(
                sha=metadata.get("sha") or match.id,
                author=metadata.get("author", "unknown"),
                title=metadata.get("text", ""),
                committed_at=timestamp,
                stats={"files": files},
            )
        )
    return sorted(commits, key=lambda item: item.committed_at, reverse=True)


async def _git_commit_summaries(repo: Optional[RepoSnapshot]) -> list[CommitSummary]:
    if not repo:
        return []
    try:
        raw = await asyncio.to_thread(repo_manager.read_recent_commits, repo)
    except Exception as exc:  # pragma: no cover - git failures should not crash worker
        print(f"[git] Unable to read commits for {repo.name}: {exc}")
        return []

    summaries: list[CommitSummary] = []
    now = datetime.utcnow()
    for line in raw.splitlines():
        if not line or line.startswith(" "):
            continue
        parts = line.split(" ", 1)
        sha = parts[0]
        title = parts[1] if len(parts) > 1 else ""
        summaries.append(
            CommitSummary(
                sha=sha,
                author="git log",
                title=title,
                committed_at=now,
                stats={},
            )
        )
    return summaries


def _incident_window(incident: IncidentRecord, minutes_before: int = 45, minutes_after: int = 15):
    pivot_raw = (incident.metadata or {}).get("occurred_at")
    pivot = _coerce_datetime(pivot_raw) if pivot_raw else incident.created_at
    return pivot - timedelta(minutes=minutes_before), pivot + timedelta(minutes=minutes_after)


def _metadata(match) -> dict[str, Any]:
    metadata = getattr(match, "metadata", None) or {}
    if isinstance(metadata, dict):
        return metadata
    return dict(metadata)


def _coerce_datetime(value: Optional[str]) -> datetime:
    if isinstance(value, datetime):
        return value
    if not value:
        return datetime.utcnow()
    sanitized = value.replace("Z", "+00:00") if isinstance(value, str) else value
    try:
        return datetime.fromisoformat(sanitized)
    except Exception:
        return datetime.utcnow()


def _query_namespace(repo_id: Optional[str], namespace: str, start: datetime, end: datetime, limit: int):
    if not repo_id:
        return []
    try:
        return fetch_documents(repo_id, namespace, start, end, top_k=limit)
    except Exception as exc:  # pragma: no cover - Pinecone outages shouldn't crash worker
        print(f"[pinecone] query failed for {namespace}: {exc}")
        return []