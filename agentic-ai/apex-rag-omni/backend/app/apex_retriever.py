"""Hybrid retriever: 10-shard Qdrant + Elasticsearch BM25, fused with RRF."""
from __future__ import annotations

import hashlib
from typing import Literal

from pydantic import BaseModel


N_SHARDS = 10
Collection = Literal["hr_policies", "tech_docs", "product_docs"]


# Per-collection allowlist of filter keys. Anything not in the list is
# rejected at the route level. This is the first line of defense against
# payload-key injection (an attacker stuffing arbitrary keys into a
# Qdrant filter JSON and getting unexpected results back).
FILTER_KEYS_BY_COLLECTION: dict[str, frozenset[str]] = {
    "hr_policies": frozenset({"department", "policy_type", "effective_date"}),
    "tech_docs": frozenset({"service", "version", "endpoint"}),
    "product_docs": frozenset({"feature", "status", "release"}),
}


class InvalidFilterKeys(ValueError):
    """Raised when the caller passes filter keys not allowed for the collection."""

    def __init__(self, collection: Collection, unknown: set[str]):
        self.collection = collection
        self.unknown = unknown
        allowed = sorted(FILTER_KEYS_BY_COLLECTION.get(collection, frozenset()))
        super().__init__(
            f"Unknown filter keys for {collection}: {sorted(unknown)}. "
            f"Allowed: {allowed}"
        )


def validate_filter_keys(collection: Collection, filters: dict[str, str]) -> None:
    """Raise InvalidFilterKeys if any filter key is not in the allowlist.

    An empty filter dict is fine; a missing collection is not (route
    layer should reject before reaching here).
    """
    if not filters:
        return
    allowed = FILTER_KEYS_BY_COLLECTION.get(collection, frozenset())
    unknown = set(filters.keys()) - allowed
    if unknown:
        raise InvalidFilterKeys(collection, unknown)


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
                  top_k: int = 32,
                  filters: dict[str, str] | None = None) -> list[RetrievedDoc]:
    """Search 10 Qdrant shards + ES BM25, fuse with RRF.

    `filters` is validated against the per-collection allowlist. The
    route layer should have already called `validate_filter_keys`,
    but we re-check here so the function is safe to call from
    scripts and tests.

    Each shard is queried in parallel (in production via async fan-out).
    Results are merged across shards, then RRF-fused with BM25.
    """
    if filters is not None:
        validate_filter_keys(collection, filters)
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
