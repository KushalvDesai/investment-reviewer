from __future__ import annotations
import asyncio
import os
from typing import List

import httpx


_HF_URL: str = os.getenv("HF_SPACES_URL", "")
_BATCH_SIZE = 32
_MAX_RETRIES = 3


async def _embed_batch(client: httpx.AsyncClient, texts: list[str]) -> list[list[float]]:
    """Send one batch to HuggingFace Spaces and return embeddings."""
    url = f"{_HF_URL.rstrip('/')}/embed"
    delay = 1.0
    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            response = await client.post(url, json={"texts": texts}, timeout=60.0)
            if response.status_code >= 500:
                raise httpx.HTTPStatusError(
                    f"Server error {response.status_code}",
                    request=response.request,
                    response=response,
                )
            response.raise_for_status()
            data = response.json()
            return data["embeddings"]
        except (httpx.HTTPStatusError, httpx.RequestError) as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES - 1:
                await asyncio.sleep(delay)
                delay *= 2
    raise RuntimeError(f"Embedding request failed after {_MAX_RETRIES} attempts: {last_exc}")


async def get_embeddings(texts: list[str]) -> List[List[float]]:
    """
    Get embeddings for a list of texts.

    Batches in groups of 32 and retries on 5xx errors with exponential backoff.
    Returns a flat list of embedding vectors in the same order as input texts.
    """
    if not texts:
        return []

    batches = [texts[i : i + _BATCH_SIZE] for i in range(0, len(texts), _BATCH_SIZE)]
    all_embeddings: list[list[float]] = []

    async with httpx.AsyncClient() as client:
        for batch in batches:
            embeddings = await _embed_batch(client, batch)
            all_embeddings.extend(embeddings)

    return all_embeddings
