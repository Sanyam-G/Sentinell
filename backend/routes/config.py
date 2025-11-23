"""Configuration APIs for repos, log sources, and Slack channels."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import get_session
from db import crud
from schemas import (
    LogSource,
    LogSourceCreateRequest,
    LogSourceListResponse,
    RepoConfig,
    RepoCreateRequest,
    RepoListResponse,
    RepoPollResult,
    SlackChannelConfig,
    SlackChannelCreateRequest,
    SlackChannelListResponse,
)
from services.poller import poll_repo

router = APIRouter(prefix="/api", tags=["configuration"])


@router.post("/repos", response_model=RepoConfig, status_code=201)
async def register_repo(
    payload: RepoCreateRequest, session: AsyncSession = Depends(get_session)
) -> RepoConfig:
    repo_payload = payload.model_dump()
    repo_payload["repo_url"] = str(payload.repo_url)
    repo = await crud.create_repo(session, repo_payload)
    return RepoConfig(**repo.model_dump())


@router.get("/repos")
async def list_repos(session: AsyncSession = Depends(get_session)):
    import sqlite3
    import json
    from pathlib import Path
    
    # Direct SQLite access to bypass SQLAlchemy serialization issues
    db_path = Path(__file__).parent.parent / "sentinell.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.execute("SELECT * FROM repo")
    columns = [desc[0] for desc in cursor.description]
    
    repos = []
    for row in cursor.fetchall():
        repo_dict = dict(zip(columns, row))
        # Parse JSON metadata
        if 'metadata' in repo_dict and repo_dict['metadata']:
            repo_dict['metadata'] = json.loads(repo_dict['metadata'])
        else:
            repo_dict['metadata'] = {}
        repos.append(repo_dict)
    
    conn.close()
    return {"repos": repos}


@router.post("/repos/{repo_id}/poll", response_model=RepoPollResult)
async def trigger_repo_poll(
    repo_id: str, session: AsyncSession = Depends(get_session)
) -> RepoPollResult:
    repo = await crud.get_repo(session, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")
    try:
        return await poll_repo(session, repo)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # pragma: no cover - still surface meaningful error
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/log-sources", response_model=LogSource, status_code=201)
async def register_log_source(
    payload: LogSourceCreateRequest, session: AsyncSession = Depends(get_session)
) -> LogSource:
    if payload.repo_id:
        repo = await crud.get_repo(session, payload.repo_id)
        if not repo:
            raise HTTPException(status_code=404, detail="Repo not found")
    source = await crud.create_log_source(session, payload.model_dump())
    return LogSource(**source.model_dump())


@router.get("/log-sources", response_model=LogSourceListResponse)
async def list_log_sources(session: AsyncSession = Depends(get_session)) -> LogSourceListResponse:
    sources = await crud.list_log_sources(session)
    return LogSourceListResponse(log_sources=[LogSource(**s.model_dump()) for s in sources])


@router.post("/slack/channels", response_model=SlackChannelConfig, status_code=201)
async def register_slack_channel(
    payload: SlackChannelCreateRequest, session: AsyncSession = Depends(get_session)
) -> SlackChannelConfig:
    if payload.repo_id:
        repo = await crud.get_repo(session, payload.repo_id)
        if not repo:
            raise HTTPException(status_code=404, detail="Repo not found")
    channel = await crud.create_slack_channel(session, payload.model_dump())
    return SlackChannelConfig(**channel.model_dump())


@router.get("/slack/channels", response_model=SlackChannelListResponse)
async def list_slack_channels(
    session: AsyncSession = Depends(get_session),
) -> SlackChannelListResponse:
    channels = await crud.list_slack_channels(session)
    return SlackChannelListResponse(channels=[SlackChannelConfig(**c.model_dump()) for c in channels])
