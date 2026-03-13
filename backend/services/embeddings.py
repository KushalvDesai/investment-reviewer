from __future__ import annotations
import asyncio
import json
import os

import httpx


_HF_URL: str = os.getenv("HF_SPACES_URL", "").rstrip("/")
# Gradio 5 queue endpoint — discovered via /gradio_api/info
_GRADIO_EP = "/gradio_api/call/embed_query"
_MAX_RETRIES = 3
_CONCURRENCY = 8   # parallel jobs sent to HF Spaces simultaneously


async def _submit_job(client: httpx.AsyncClient, text: str) -> str:
    """POST one text to the Gradio queue and return the event_id."""
    url = f"{_HF_URL}{_GRADIO_EP}"
    delay = 1.0
    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            resp = await client.post(url, json={"data": [text]}, timeout=20.0)
            if resp.status_code >= 500:
                raise httpx.HTTPStatusError(
                    f"Server {resp.status_code}", request=resp.request, response=resp
                )
            resp.raise_for_status()
            return resp.json()["event_id"]
        except (httpx.HTTPStatusError, httpx.RequestError) as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES - 1:
                await asyncio.sleep(delay)
                delay *= 2
    raise RuntimeError(f"Submit failed after {_MAX_RETRIES} attempts: {last_exc}")


async def _collect_result(client: httpx.AsyncClient, event_id: str) -> list[float]:
    """
    Stream the SSE result for event_id and return the 1024-dim embedding.

    Gradio 5 SSE format:
        data: [[0.022, -0.017, ...]]   ← payload[0] is the float list
    or if the fn returns a JSON string:
        data: ["[0.022, -0.017, ...]"] ← payload[0] is JSON-encoded
    """
    url = f"{_HF_URL}{_GRADIO_EP}/{event_id}"
    async with client.stream("GET", url,
                             headers={"Accept": "text/event-stream"},
                             timeout=60.0) as resp:
        resp.raise_for_status()
        async for line in resp.aiter_lines():
            if not line.startswith("data:"):
                continue
            payload = json.loads(line[5:])
            if not isinstance(payload, list) or not payload:
                continue
            first = payload[0]
            if isinstance(first, list):        # direct float list
                return first
            if isinstance(first, str):         # JSON-stringified embedding
                parsed = json.loads(first)
                if isinstance(parsed, list):
                    return parsed
                if isinstance(parsed, dict):   # {"embedding": [...]}
                    for v in parsed.values():
                        if isinstance(v, list):
                            return v
    raise RuntimeError(f"No embedding in SSE stream for event_id={event_id}")


async def _embed_one(client: httpx.AsyncClient, text: str) -> list[float]:
    event_id = await _submit_job(client, text)
    return await _collect_result(client, event_id)


async def get_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Get 1024-dimensional embeddings for a list of texts.

    Uses the Gradio 5 queue API on HuggingFace Spaces (/gradio_api/call/embed_query).
    Submits up to _CONCURRENCY jobs concurrently; retries on 5xx with exponential backoff.
    Returns vectors in the same order as input texts.
    """
    if not texts:
        return []

    semaphore = asyncio.Semaphore(_CONCURRENCY)

    async def _guarded(text: str) -> list[float]:
        async with semaphore:
            return await _embed_one(client, text)

    async with httpx.AsyncClient() as client:
        return list(await asyncio.gather(*[_guarded(t) for t in texts]))
