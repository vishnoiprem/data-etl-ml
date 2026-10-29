"""Hybrid retrieval: BM25 + dense fused with Reciprocal Rank Fusion.

WHY RRF (vs. weighted sum)?
- Score scales differ wildly: BM25 returns unbounded positive numbers,
  cosine similarity is ∈ [-1, 1]. Naively summing them is dominated by BM25.
- Normalization is fragile (per-query distributions change).
- RRF only uses *ranks*, not scores → robust, parameter-light, well-published.

RRF score for a doc d retrieved by retrievers R_1..R_n:
    rrf(d) = Σ_i  1 / (k + rank_i(d))
where k is a smoothing constant (60 is the canonical value from the original paper).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from loguru import logger

from src.embedding.embedder import Embedder
from src.ingestion.chunker import Chunk
from src.retrieval.bm25 import BM25Retriever
from src.retrieval.vector_store import VectorStore


@dataclass
class RetrievalResult:
    chunk: Chunk
    score: float
    contributors: dict      # which retrievers found it, with their per-retriever ranks
    text_match: float = 0.0
    dense_match: float = 0.0


class HybridRetriever:
    """Reciprocal Rank Fusion of dense + BM25 retrievers."""

    def __init__(
        self,
        embedder: Embedder,
        vector_store: VectorStore,
        bm25: BM25Retriever,
        rrf_k: int = 60,
    ):
        self.embedder = embedder
        self.vector_store = vector_store
        self.bm25 = bm25
        self.rrf_k = rrf_k

    def retrieve(self, query: str, top_k: int = 50, filters: dict | None = None) -> list[RetrievalResult]:
        # 1) Dense retrieval
        q_vec = self.embedder.embed([query])[0]
        dense_hits = self.vector_store.search(q_vec, k=top_k, filters=filters)
        # 2) Sparse retrieval
        sparse_hits = self.bm25.search(query, k=top_k, filters=filters)

        logger.debug(f"dense hits={len(dense_hits)}  sparse hits={len(sparse_hits)}")

        # 3) Reciprocal Rank Fusion
        fused: dict[str, RetrievalResult] = {}

        for rank, (chunk, score) in enumerate(dense_hits, start=1):
            r = fused.setdefault(chunk.chunk_id, RetrievalResult(chunk=chunk, score=0.0, contributors={}))
            r.score += 1.0 / (self.rrf_k + rank)
            r.contributors["dense_rank"] = rank
            r.dense_match = score

        for rank, (chunk, score) in enumerate(sparse_hits, start=1):
            r = fused.setdefault(chunk.chunk_id, RetrievalResult(chunk=chunk, score=0.0, contributors={}))
            r.score += 1.0 / (self.rrf_k + rank)
            r.contributors["sparse_rank"] = rank
            r.text_match = score

        ranked = sorted(fused.values(), key=lambda r: r.score, reverse=True)[:top_k]
        return ranked
