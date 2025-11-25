"""High-level pipeline helpers for Pinecone ingestion and retrieval."""
from __future__ import annotations

from typing import Iterable, List, Sequence

from .client import get_index
from .schemas import BaseDocument
from .vectorizer import embed_texts


def upsert_documents(documents: Sequence[BaseDocument], namespace: str) -> int:
    if not documents:
        return 0

    index = get_index()
    embeddings = embed_texts([doc.text for doc in documents])

    vectors = []
    for doc, vector in zip(documents, embeddings):
        metadata = {
            "repo_id": doc.repo_id,
            "timestamp": doc.timestamp.isoformat(),
            "source_type": doc.source_type,
            "text": doc.text,
            **doc.metadata,
        }

        # Preserve structured document-specific fields so retrievers can rebuild context.
        if hasattr(doc, "files") and "files" not in metadata:
            metadata["files"] = getattr(doc, "files")
        if hasattr(doc, "channel_id") and "channel_id" not in metadata:
            metadata["channel_id"] = getattr(doc, "channel_id")
        if hasattr(doc, "user") and "user" not in metadata:
            metadata["user"] = getattr(doc, "user")
        if hasattr(doc, "level") and "level" not in metadata:
            metadata["level"] = getattr(doc, "level")

        vectors.append({"id": doc.id, "values": vector, "metadata": metadata})

    index.upsert(vectors=vectors, namespace=namespace)
    return len(vectors)


def query_similar(text: str, top_k: int = 5, namespace: str | None = None):
    index = get_index()
    vector = embed_texts([text])[0]
    return index.query(
        vector=vector,
        top_k=top_k,
        include_metadata=True,
        namespace=namespace,
    )
