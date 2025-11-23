"""Slack ingestion helpers."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable, List
from uuid import uuid4

from data.pinecone.pipeline import upsert_documents
from data.pinecone.schemas import SlackDocument

SLACK_NAMESPACE = "slack"


def ingest_slack_messages(messages: Iterable[dict]) -> int:
    docs: List[SlackDocument] = []
    for msg in messages:
        raw_ts = msg.get("timestamp") or msg.get("message_ts") or datetime.utcnow().isoformat()
        timestamp = _coerce_datetime(raw_ts)
        extra = {
            k: str(v)
            for k, v in msg.items()
            if k not in {"repo_id", "timestamp", "message_ts", "text", "channel_id", "user"}
        }
        extra["timestamp_epoch"] = timestamp.timestamp()
        extra["channel_id"] = msg.get("channel_id", "unknown")
        doc = SlackDocument(
            id=uuid4().hex,
            repo_id=msg.get("repo_id", "unknown"),
            timestamp=timestamp,
            channel_id=msg.get("channel_id", "unknown"),
            user=msg.get("user", "bot"),
            text=msg.get("text", ""),
            metadata=extra,
        )
        docs.append(doc)
    return upsert_documents(docs, namespace=SLACK_NAMESPACE)


def _coerce_datetime(value: str) -> datetime:
    sanitized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(sanitized)
