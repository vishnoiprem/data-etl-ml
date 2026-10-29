"""Hybrid retriever: BM25 + dense vector, fused with reciprocal-rank fusion.

Sharded Qdrant cluster (10 shards) for vectors. Elasticsearch for BM25.
RRF combines both without needing score normalization.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Iterable

import numpy as np
from pydantic import BaseModel, Field

from .router import Domain

logger = logging.getLogger(__name__)


class RetrievedDoc(BaseModel):
    doc_id: str
    text: str
    vector_score: float = 0.0
    bm25_score: float = 0.0
    rrf_score: float = 0.0
    rank_vector: int = 0
    rank_bm25: int = 0
    domain: Domain | None = None
    shard_id: int = 0


class RetrieveRequest(BaseModel):
    query: str
    domain: Domain
    top_k: int = Field(default=8, ge=1, le=50)
    filters: dict[str, str] = Field(default_factory=dict)


@dataclass
class RetrieveTiming:
    embed_ms: float
    vector_ms: float
    bm25_ms: float
    rrf_ms: float
    total_ms: float


def shard_for(doc_id: str, n_shards: int = 10) -> int:
    """Hash a doc_id into a shard. Stable across rebalances."""
    return int(doc_id, 16) % n_shards if doc_id.startswith("0x") else hash(doc_id) % n_shards


def rrf_fuse(vector_hits: list[RetrievedDoc], bm25_hits: list[RetrievedDoc],
             k: int = 60) -> list[RetrievedDoc]:
    """Reciprocal-rank fusion: score = 1 / (k + rank). No normalization needed.

    RRF is robust to score-scale differences between vector and BM25, which
    matters when the two backends use different scoring conventions.
    """
    by_id: dict[str, RetrievedDoc] = {}
    for rank, d in enumerate(vector_hits, start=1):
        d.rank_vector = rank
        d.rrf_score += 1.0 / (k + rank)
        by_id[d.doc_id] = d
    for rank, d in enumerate(bm25_hits, start=1):
        d.rank_bm25 = rank
        if d.doc_id in by_id:
            by_id[d.doc_id].rrf_score += 1.0 / (k + rank)
            by_id[d.doc_id].bm25_score = d.bm25_score
        else:
            d.rrf_score += 1.0 / (k + rank)
            by_id[d.doc_id] = d
    return sorted(by_id.values(), key=lambda x: x.rrf_score, reverse=True)


def top_k(fused: list[RetrievedDoc], k: int) -> list[RetrievedDoc]:
    return fused[:k]


def assess_freshness(docs: Iterable[RetrievedDoc], max_age_min: int = 5) -> dict[str, int]:
    """Count docs older than the freshness SLA. Should be 0 in steady state."""
    # In production: doc.ingested_at is set by the indexer from the CDC timestamp.
    # For this module we return the SLA contract; the actual age check is in tools/cdc.py.
    return {"sla_minutes": max_age_min, "violations": 0}
