from __future__ import annotations

from typing import Iterable, List

from openai import OpenAI

client = OpenAI()


def embed_texts(texts: Iterable[str], model: str = "text-embedding-3-large", dimensions: int = 1024) -> List[List[float]]:
    batch = list(texts)
    if not batch:
        return []
    response = client.embeddings.create(input=batch, model=model, dimensions=dimensions)
    # Response order matches inputs
    return [item.embedding for item in response.data]
