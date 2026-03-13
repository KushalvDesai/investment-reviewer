from __future__ import annotations
import os
from functools import lru_cache

from pinecone import Pinecone, ServerlessSpec

# "investment" index exists in Pinecone with dim=1024 (llama-text-embed-v2).
# HF Spaces /embed_query also produces 1024-dim vectors.
_INDEX_NAME = os.getenv("PINECONE_INDEX", "investment")
_DIMENSION = 1024
_METRIC = "cosine"
_BATCH_SIZE = 100


@lru_cache(maxsize=1)
def _get_index():
    """Return a cached Pinecone Index, creating it if it does not exist."""
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    existing = [idx.name for idx in pc.list_indexes()]
    if _INDEX_NAME not in existing:
        pc.create_index(
            name=_INDEX_NAME,
            dimension=_DIMENSION,
            metric=_METRIC,
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
    return pc.Index(_INDEX_NAME)


def upsert_chunks(
    chunks: list[dict],
    embeddings: list[list[float]],
    namespace: str,
) -> int:
    """
    Upsert chunk embeddings into Pinecone under the given namespace.

    chunks must contain dicts with keys: chunk_index, source_filename,
    chunk_type, month_key, text.

    Returns the number of vectors upserted.
    """
    index = _get_index()
    vectors = []
    for chunk, embedding in zip(chunks, embeddings):
        vec_id = f"{namespace}-{chunk['chunk_index']}"
        metadata = {
            "month_key": chunk["month_key"],
            "chunk_index": chunk["chunk_index"],
            "source_filename": chunk["source_filename"],
            "chunk_type": chunk["chunk_type"],
            "text": chunk["text"][:1000],  # Pinecone metadata value limit
        }
        vectors.append({"id": vec_id, "values": embedding, "metadata": metadata})

    upserted = 0
    for i in range(0, len(vectors), _BATCH_SIZE):
        batch = vectors[i : i + _BATCH_SIZE]
        index.upsert(vectors=batch, namespace=namespace)
        upserted += len(batch)
    return upserted


def query_namespace(
    vector: list[float],
    namespace: str,
    top_k: int = 8,
) -> list[dict]:
    """Similarity search within one namespace. Returns list of match dicts."""
    index = _get_index()
    result = index.query(
        vector=vector,
        top_k=top_k,
        namespace=namespace,
        include_metadata=True,
    )
    return [
        {"id": m["id"], "score": m["score"], "metadata": m.get("metadata", {})}
        for m in result.get("matches", [])
    ]


def query_cross_namespace(
    vector: list[float],
    namespaces: list[str],
    top_k: int = 5,
) -> list[dict]:
    """
    Query multiple namespaces individually and merge results, re-ranked by score
    descending, returning the global top_k.
    """
    all_matches: list[dict] = []
    for ns in namespaces:
        matches = query_namespace(vector, ns, top_k=top_k)
        all_matches.extend(matches)
    all_matches.sort(key=lambda m: m["score"], reverse=True)
    return all_matches[:top_k]


def list_namespaces() -> list[str]:
    """Return all stored month_keys (namespace names) sorted descending."""
    index = _get_index()
    stats = index.describe_index_stats()
    namespaces = list(stats.get("namespaces", {}).keys())
    namespaces.sort(reverse=True)
    return namespaces


def delete_namespace(month_key: str) -> None:
    """Delete all vectors in the namespace corresponding to month_key."""
    index = _get_index()
    index.delete(delete_all=True, namespace=month_key)
