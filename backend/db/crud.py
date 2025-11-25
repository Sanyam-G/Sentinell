"""CRUD helpers for async SQLModel operations."""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from db import models


def _generate_id() -> str:
    return uuid4().hex


async def create_repo(session: AsyncSession, payload: dict) -> models.Repo:
    repo = models.Repo(id=_generate_id(), **payload)
    session.add(repo)
    await session.commit()
    await session.refresh(repo)
    return repo


async def list_repos(session: AsyncSession) -> list[models.Repo]:
    import json
    from sqlalchemy import text
    
    # Direct query to get all fields including metadata
    query = text("SELECT * FROM repo")
    result = await session.execute(query)
    rows = result.mappings().all()
    
    # Manually construct Repo objects with metadata properly mapped to meta
    repos = []
    for row in rows:
        row_dict = dict(row)
        # Map 'metadata' column to 'meta' attribute and parse JSON string
        if 'metadata' in row_dict:
            raw_meta = row_dict.pop('metadata')
            # SQLite returns JSON as string, need to parse it
            if isinstance(raw_meta, str):
                try:
                    raw_meta = json.loads(raw_meta)
                except (json.JSONDecodeError, TypeError):
                    raw_meta = {}
            row_dict['meta'] = raw_meta or {}
        repos.append(models.Repo(**row_dict))
    
    return repos


async def get_repo(session: AsyncSession, repo_id: str) -> models.Repo | None:
    result = await session.execute(select(models.Repo).where(models.Repo.id == repo_id))
    return result.scalar_one_or_none()


async def create_log_source(session: AsyncSession, payload: dict) -> models.LogSource:
    source = models.LogSource(id=_generate_id(), **payload)
    session.add(source)
    await session.commit()
    await session.refresh(source)
    return source


async def list_log_sources(session: AsyncSession) -> list[models.LogSource]:
    result = await session.execute(select(models.LogSource))
    return list(result.scalars())


async def create_slack_channel(session: AsyncSession, payload: dict) -> models.SlackChannel:
    channel = models.SlackChannel(id=_generate_id(), **payload)
    session.add(channel)
    await session.commit()
    await session.refresh(channel)
    return channel


async def list_slack_channels(session: AsyncSession) -> list[models.SlackChannel]:
    result = await session.execute(select(models.SlackChannel))
    return list(result.scalars())


async def create_incident(session: AsyncSession, payload: dict) -> models.Incident:
    incident = models.Incident(id=_generate_id(), **payload)
    session.add(incident)
    await session.commit()
    await session.refresh(incident)
    return incident


async def list_incidents(session: AsyncSession) -> list[models.Incident]:
    result = await session.execute(select(models.Incident).order_by(models.Incident.created_at.desc()))
    return list(result.scalars())


async def get_incident(session: AsyncSession, incident_id: str) -> models.Incident | None:
    result = await session.execute(select(models.Incident).where(models.Incident.id == incident_id))
    return result.scalar_one_or_none()


async def update_incident_status(session: AsyncSession, incident_id: str, status: str) -> None:
    result = await session.execute(select(models.Incident).where(models.Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise NoResultFound(incident_id)
    incident.status = status
    incident.updated_at = datetime.utcnow()
    await session.commit()


async def create_github_event(session: AsyncSession, payload: dict) -> models.GithubEvent:
    event = models.GithubEvent(id=_generate_id(), **payload)
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event


async def list_github_events(session: AsyncSession) -> list[models.GithubEvent]:
    result = await session.execute(select(models.GithubEvent))
    return list(result.scalars())
