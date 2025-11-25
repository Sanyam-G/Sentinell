"""Automated polling utilities that run repo health checks and raise incidents."""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from db import crud, models
from db.base import SessionLocal
from schemas import RepoPollResult, RepoSnapshot, Severity
from services.repo_runner import repo_runner

logger = logging.getLogger(__name__)
POLL_INTERVAL_SECONDS = float(os.getenv("SRE_POLL_INTERVAL_SECONDS", "300"))


async def poll_repo(session: AsyncSession, repo: models.Repo) -> RepoPollResult:
    """Clone/pull a repo, run its health checks, and record incidents on failure."""
    snapshot = RepoSnapshot(
        id=repo.id,
        name=repo.name,
        repo_url=repo.repo_url,
        default_branch=repo.default_branch,
    )

    result = await asyncio.to_thread(repo_runner.run_checks, snapshot)

    if not result.success:
        result = await _record_failure(session, repo, result)

    await _record_poll_metadata(session, repo, result)
    return result


async def poll_registered_repos() -> None:
    """Poll every repo that has auto polling enabled."""
    async with SessionLocal() as session:
        repos = await crud.list_repos(session)
        for repo in repos:
            if not _auto_poll_enabled(repo):
                continue
            try:
                await poll_repo(session, repo)
            except FileNotFoundError as exc:
                logger.warning("Poll skipped for %s: %s", repo.name, exc)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.exception("Auto poll failed for %s: %s", repo.name, exc)


async def run_polling_loop(interval: Optional[float] = None) -> None:
    """Background task that continuously polls repos on a fixed interval."""
    poll_interval = interval or POLL_INTERVAL_SECONDS
    while True:
        try:
            await poll_registered_repos()
        except Exception as exc:
            logger.exception("Polling loop crashed: %s", exc)
        await asyncio.sleep(poll_interval)


async def _record_failure(
    session: AsyncSession, repo: models.Repo, result: RepoPollResult
) -> RepoPollResult:
    stdout_tail = result.stdout[-4000:]
    stderr_tail = result.stderr[-4000:]
    incident = await crud.create_incident(
        session,
        {
            "signal_type": "log",
            "title": f"Repo checks failed ({repo.name})",
            "description": stderr_tail or stdout_tail or "Check script failed",
            "repo_id": repo.id,
            "severity": Severity.high,
            "source_ref": f"poll/{result.ran_at.isoformat()}",
            "metadata": {
                "occurred_at": result.ran_at.isoformat(),
                "poll_exit_code": result.exit_code,
                "stdout": stdout_tail,
                "stderr": stderr_tail,
            },
        },
    )

    updated = result.model_copy()
    updated.incident_id = incident.id
    return updated


async def _record_poll_metadata(
    session: AsyncSession, repo: models.Repo, result: RepoPollResult
) -> None:
    # Get the repo from the current session to avoid detached instance issues
    from sqlalchemy import select
    result_repo = await session.execute(select(models.Repo).where(models.Repo.id == repo.id))
    attached_repo = result_repo.scalar_one_or_none()
    
    if not attached_repo:
        return
    
    meta = dict(attached_repo.meta or {})
    meta["last_poll"] = {
        "at": result.ran_at.isoformat(),
        "success": result.success,
        "exit_code": result.exit_code,
    }
    attached_repo.meta = meta
    attached_repo.updated_at = datetime.utcnow()
    await session.commit()


def _auto_poll_enabled(repo: models.Repo) -> bool:
    meta = repo.meta or {}
    # Handle case where meta might be a JSON string instead of dict
    if isinstance(meta, str):
        import json
        try:
            meta = json.loads(meta)
        except Exception:
            meta = {}
    return meta.get("auto_poll_enabled", True)
