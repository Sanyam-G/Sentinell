"""Pinecone client wrapper with namespace helpers."""
from __future__ import annotations

import os
from functools import lru_cache

from pinecone import Pinecone, ServerlessSpec

INDEX_NAME = os.getenv("PINECONE_INDEX", "sentinell-context")
DIMENSION = int(os.getenv("PINECONE_DIMENSION", "1024"))
ENVIRONMENT = os.getenv("PINECONE_ENV", "us-east-1")


@lru_cache(maxsize=1)
def _client() -> Pinecone:
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise RuntimeError("PINECONE_API_KEY not set")
    return Pinecone(api_key=api_key)


def _ensure_index(pc: Pinecone) -> None:
    existing = [idx.name for idx in pc.list_indexes()]
    if INDEX_NAME not in existing:
        pc.create_index(
            name=INDEX_NAME,
            dimension=DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region=ENVIRONMENT),
        )


@lru_cache(maxsize=1)
def get_index():
    pc = _client()
    _ensure_index(pc)
    return pc.Index(INDEX_NAME)
