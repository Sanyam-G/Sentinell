"""Helpers to fetch context windows from Pinecone by repo and time range."""
from __future__ import annotations

from datetime import datetime
from typing import List

from .client import DIMENSION, get_index


def fetch_documents(repo_id: str, namespace: str, start: datetime, end: datetime, top_k: int = 50):
    index = get_index()
    filter_query = {
        "repo_id": {"$eq": repo_id},
        "timestamp_epoch": {
            "$gte": start.timestamp(),
            "$lte": end.timestamp(),
        },
    }
    response = index.query(
        vector=[0.0] * DIMENSION,
        filter=filter_query,
        namespace=namespace,
        top_k=top_k,
        include_metadata=True,
    )
    return response.matches
