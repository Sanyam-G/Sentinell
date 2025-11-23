"""Commit ingestion helpers."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable, List
from uuid import uuid4

from data.pinecone.pipeline import upsert_documents
from data.pinecone.schemas import CommitDocument

COMMITS_NAMESPACE = "commits"


def ingest_commits(commits: Iterable[dict]) -> int:
    docs: List[CommitDocument] = []
    for commit in commits:
        raw_ts = commit.get("timestamp") or datetime.utcnow().isoformat()
        timestamp = _coerce_datetime(raw_ts)
        extra = {
            k: str(v)
            for k, v in commit.items()
            if k not in {"repo_id", "timestamp", "sha", "message", "files"}
        }
        extra["timestamp_epoch"] = timestamp.timestamp()
        extra["sha"] = commit.get("sha", "")
        doc = CommitDocument(
            id=uuid4().hex,
            repo_id=commit.get("repo_id", "unknown"),
            timestamp=timestamp,
            sha=commit.get("sha", ""),
            text=commit.get("message", ""),
            files=commit.get("files", []),
            metadata=extra,
        )
        docs.append(doc)
    return upsert_documents(docs, namespace=COMMITS_NAMESPACE)


def _coerce_datetime(value: str) -> datetime:
    sanitized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(sanitized)
