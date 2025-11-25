"""Signal ingestion endpoints (manual issues, logs, Slack, GitHub webhooks)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from data.ingestion.commits import ingest_commits
from data.ingestion.logs import ingest_logs
from data.ingestion.slack import ingest_slack_messages
from db.base import get_session
from db import crud
from schemas import (
    GithubEventPayload,
    IncidentListResponse,
    IncidentRecord,
    LogSignalRequest,
    ManualIssueRequest,
    Severity,
    SlackSignalRequest,
)

router = APIRouter(prefix="/api", tags=["signals"])


@router.post("/issues", response_model=IncidentRecord, status_code=201)
async def report_manual_issue(
    payload: ManualIssueRequest, session: AsyncSession = Depends(get_session)
) -> IncidentRecord:
    if payload.repo_id:
        repo = await crud.get_repo(session, payload.repo_id)
        if not repo:
            raise HTTPException(status_code=404, detail="Repo not found")

    incident = await crud.create_incident(
        session,
        {
            "signal_type": "manual",
            "title": payload.title,
            "description": payload.description,
            "repo_id": payload.repo_id,
            "severity": payload.severity,
            "metadata": {"reporter": payload.reporter, "tags": payload.tags},
        },
    )
    return IncidentRecord(**incident.model_dump())


@router.post("/signals/logs", response_model=IncidentRecord, status_code=202)
async def ingest_log_signal(
    payload: LogSignalRequest, session: AsyncSession = Depends(get_session)
) -> IncidentRecord:
    incident = await crud.create_incident(
        session,
        {
            "signal_type": "log",
            "title": f"Log alert ({payload.level or 'info'})",
            "description": payload.message,
            "repo_id": payload.repo_id,
            "severity": _log_level_to_severity(payload.level),
            "source_ref": payload.source_id,
            "metadata": {
                "occurred_at": payload.occurred_at.isoformat(),
                "raw": payload.metadata,
            },
        },
    )
    _safe_ingest(
        ingest_logs,
        [
            {
                "repo_id": payload.repo_id or "unknown",
                "timestamp": payload.occurred_at.isoformat(),
                "level": payload.level or "info",
                "message": payload.message,
                **payload.metadata,
            }
        ],
    )
    return IncidentRecord(**incident.model_dump())


@router.post("/signals/slack", response_model=IncidentRecord, status_code=202)
async def ingest_slack_signal(
    payload: SlackSignalRequest, session: AsyncSession = Depends(get_session)
) -> IncidentRecord:
    incident = await crud.create_incident(
        session,
        {
            "signal_type": "slack",
            "title": "Slack escalation",
            "description": payload.text,
            "repo_id": payload.repo_id,
            "severity": Severity.high,
            "source_ref": payload.message_ts,
            "metadata": {
                "team_id": payload.team_id,
                "channel_id": payload.channel_id,
                "thread_ts": payload.thread_ts,
                "user": payload.user,
                "occurred_at": payload.occurred_at.isoformat(),
                "raw": payload.metadata,
            },
        },
    )
    _safe_ingest(
        ingest_slack_messages,
        [
            {
                "repo_id": payload.repo_id or "unknown",
                "timestamp": payload.occurred_at.isoformat(),
                "channel_id": payload.channel_id,
                "user": payload.user or "unknown",
                "text": payload.text,
                **payload.metadata,
            }
        ],
    )
    return IncidentRecord(**incident.model_dump())


@router.post("/signals/github", response_model=GithubEventPayload, status_code=202)
async def ingest_github_event(
    payload: GithubEventPayload, session: AsyncSession = Depends(get_session)
) -> GithubEventPayload:
    event = await crud.create_github_event(session, payload.model_dump())
    commits = payload.payload.get("commits") if isinstance(payload.payload, dict) else None
    if commits:
        commit_docs = []
        for commit in commits:
            commit_docs.append(
                {
                    "repo_id": payload.repo_id or "unknown",
                    "timestamp": commit.get("timestamp") or payload.received_at.isoformat(),
                    "sha": commit.get("id"),
                    "message": commit.get("message", ""),
                    "files": commit.get("modified", []) + commit.get("added", []),
                }
            )
        _safe_ingest(ingest_commits, commit_docs)
    return GithubEventPayload(**event.model_dump())


@router.get("/incidents", response_model=IncidentListResponse)
async def list_incidents(session: AsyncSession = Depends(get_session)) -> IncidentListResponse:
    incidents = await crud.list_incidents(session)
    return IncidentListResponse(
        incidents=[IncidentRecord(**incident.model_dump()) for incident in incidents]
    )


def _log_level_to_severity(level: str | None) -> Severity:
    normalized = (level or "").lower()
    return {
        "debug": Severity.low,
        "info": Severity.low,
        "warning": Severity.medium,
        "warn": Severity.medium,
        "error": Severity.high,
        "critical": Severity.critical,
        "fatal": Severity.critical,
    }.get(normalized, Severity.medium)


def _safe_ingest(func, payload):
    try:
        func(payload)
    except Exception as exc:
        print(f"[Ingestion] failed: {exc}")
