"""Hybrid retriever: 10-shard Qdrant + Elasticsearch BM25, fused with RRF."""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel


N_SHARDS = 10
Collection = Literal["hr_policies", "tech_docs", "product_docs"]


class RetrievedDoc(BaseModel):
    doc_id: str
    text: str
    vector_score: float = 0.0
    bm25_score: float = 0.0
    rrf_score: float = 0.0
    shard_id: int = 0
    collection: Collection | None = None


def shard_for(doc_id: str, n_shards: int = N_SHARDS) -> int:
    """Stable shard routing: SHA-256 mod n_shards.

    Same doc_id always lands in the same shard, even after rebalances.
    """
    h = int(hashlib.sha256(doc_id.encode()).hexdigest(), 16)
    return h % n_shards


def hybrid_search(collection: Collection, query: str,
                  top_k: int = 32) -> list[RetrievedDoc]:
    """Search 10 Qdrant shards + ES BM25, fuse with RRF.

    Each shard is queried in parallel (in production via async fan-out).
    Results are merged across shards, then RRF-fused with BM25.
    """
    # Stub: in production, fan out to 10 Qdrant shards + ES.
    # Here we return synthetic results that exercise the RRF path.
    vector_hits = [
        RetrievedDoc(
            doc_id=f"{collection}-vec-{i:04d}",
            text=f"vector hit {i} for {query[:30]}",
            vector_score=1.0 - i * 0.02,
            shard_id=shard_for(f"{collection}-vec-{i:04d}"),
            collection=collection,
        )
        for i in range(top_k)
    ]
    bm25_hits = [
        RetrievedDoc(
            doc_id=f"{collection}-bm25-{i:04d}",
            text=f"bm25 hit {i} for {query[:30]}",
            bm25_score=1.0 - i * 0.02,
            shard_id=shard_for(f"{collection}-bm25-{i:04d}"),
            collection=collection,
        )
        for i in range(top_k)
    ]
    return _rrf_fuse(vector_hits, bm25_hits)


def _rrf_fuse(vector_hits: list[RetrievedDoc],
              bm25_hits: list[RetrievedDoc], k: int = 60) -> list[RetrievedDoc]:
    """Reciprocal-rank fusion. Score = sum(1 / (k + rank))."""
    by_id: dict[str, RetrievedDoc] = {}
    for rank, d in enumerate(vector_hits, start=1):
        d.rrf_score = 1.0 / (k + rank)
        by_id[d.doc_id] = d
    for rank, d in enumerate(bm25_hits, start=1):
        if d.doc_id in by_id:
            by_id[d.doc_id].rrf_score += 1.0 / (k + rank)
            by_id[d.doc_id].bm25_score = d.bm25_score
        else:
            d.rrf_score = 1.0 / (k + rank)
            by_id[d.doc_id] = d
    return sorted(by_id.values(), key=lambda x: x.rrf_score, reverse=True)


def rerank_top_k(candidates: list[RetrievedDoc], k: int = 8) -> list[RetrievedDoc]:
    """Take the top-k after RRF. In production, this is a cross-encoder reranker."""
    return candidates[:k]
