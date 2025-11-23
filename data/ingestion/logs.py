"""Utilities to transform log entries into Pinecone documents."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable, List
from uuid import uuid4

from data.pinecone.pipeline import upsert_documents
from data.pinecone.schemas import LogDocument

LOG_NAMESPACE = "logs"


def ingest_logs(entries: Iterable[dict]) -> int:
    docs: List[LogDocument] = []
    for entry in entries:
        raw_ts = entry.get("timestamp") or datetime.utcnow().isoformat()
        timestamp = _coerce_datetime(raw_ts)
        extra = {k: str(v) for k, v in entry.items() if k not in {"repo_id", "timestamp", "message", "level"}}
        extra["timestamp_epoch"] = timestamp.timestamp()
        extra["level"] = entry.get("level", "info")
        doc = LogDocument(
            id=uuid4().hex,
            repo_id=entry.get("repo_id", "unknown"),
            timestamp=timestamp,
            level=entry.get("level", "info"),
            text=entry.get("message", ""),
            metadata=extra,
        )
        docs.append(doc)
    return upsert_documents(docs, namespace=LOG_NAMESPACE)


def _coerce_datetime(value: str) -> datetime:
    sanitized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(sanitized)
