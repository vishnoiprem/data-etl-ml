"""Cross-encoder reranking.

Bi-encoders (the embedding model) score query and doc independently — fast,
but lossy. Cross-encoders score them jointly with attention over both —
slow, but ~5–15 points more accurate at the top.

Strategy: use cheap retrieval to get top 50 candidates, then rerank with
a cross-encoder to pick the top 5 we'll actually feed to the LLM.

LOCAL: sentence-transformers cross-encoder (CPU-friendly).
AWS:   Bedrock Cohere Rerank 3 (managed, 100 docs/call).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from loguru import logger

from src.config import settings
from src.retrieval.hybrid import RetrievalResult


class Reranker(ABC):
    @abstractmethod
    def rerank(self, query: str, results: Sequence[RetrievalResult], top_k: int) -> list[RetrievalResult]:
        ...


class LocalReranker(Reranker):
    """Cross-encoder reranker using sentence-transformers."""

    def __init__(self, model_name: str | None = None):
        from sentence_transformers import CrossEncoder
        self.model_name = model_name or settings.LOCAL_RERANKER_MODEL
        logger.info(f"Loading local cross-encoder: {self.model_name}")
        self.model = CrossEncoder(self.model_name)

    def rerank(self, query: str, results: Sequence[RetrievalResult], top_k: int) -> list[RetrievalResult]:
        if not results:
            return []
        pairs = [[query, r.chunk.text] for r in results]
        scores = self.model.predict(pairs, show_progress_bar=False)
        # Normalize to ~[0, 1] via sigmoid (raw scores are unbounded logits)
        import numpy as np
        normalized = 1.0 / (1.0 + np.exp(-scores))
        for r, s in zip(results, normalized):
            r.score = float(s)
        return sorted(results, key=lambda r: r.score, reverse=True)[:top_k]


class BedrockReranker(Reranker):
    """Bedrock Cohere Rerank backend."""

    def __init__(self, model_id: str | None = None):
        import boto3
        self.model_id = model_id or settings.BEDROCK_RERANK_MODEL
        self.client = boto3.client("bedrock-runtime", region_name=settings.AWS_REGION)

    def rerank(self, query: str, results: Sequence[RetrievalResult], top_k: int) -> list[RetrievalResult]:
        if not results:
            return []
        import json
        body = json.dumps({
            "query": query,
            "documents": [r.chunk.text for r in results],
            "top_n": top_k,
            "api_version": 2,
        })
        resp = self.client.invoke_model(modelId=self.model_id, body=body)
        payload = json.loads(resp["body"].read())
        out = []
        for entry in payload["results"]:
            r = results[entry["index"]]
            r.score = float(entry["relevance_score"])
            out.append(r)
        return out


class NoOpReranker(Reranker):
    """Identity reranker — used when cross-encoder weights aren't available.

    Keeps the existing fusion order from hybrid retrieval and just trims to
    top_k. Quality is worse than a true cross-encoder, but the pipeline still
    runs end-to-end.
    """

    def rerank(self, query: str, results: Sequence[RetrievalResult], top_k: int) -> list[RetrievalResult]:
        # Normalize the RRF score to roughly [0, 1] so the refusal gate still works.
        if not results:
            return []
        max_score = max((r.score for r in results), default=1.0) or 1.0
        for r in results:
            r.score = r.score / max_score
        return list(results)[:top_k]


def get_reranker() -> Reranker:
    if settings.is_aws:
        return BedrockReranker()
    try:
        return LocalReranker()
    except Exception as e:
        logger.warning(
            f"Falling back to NoOpReranker ({e.__class__.__name__}: {e}). "
            "For better top-K precision, ensure HuggingFace is reachable or use AWS mode."
        )
        return NoOpReranker()
