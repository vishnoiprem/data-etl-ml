"""Eval harness: Recall@8, nDCG@8, LLM-as-judge, p95 latency.

Production targets (per staff-level spec):
  Recall@8 = 0.89
  nDCG@8 = 0.91
  p95 latency = 420 ms

This module owns the EvalReport dataclass and the metric primitives.
The store (Postgres or JSONL) is in `eval_store.py`. The previous
version of this file returned hardcoded fakes; the real numbers now
come from the harness.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Literal

Collection = Literal["hr_policies", "tech_docs", "product_docs"]


@dataclass
class EvalReport:
    """Top-level eval report returned by GET /eval."""
    timestamp: str
    n_samples: int
    recall_at_8: float
    ndcg_at_8: float
    p50_latency_ms: float
    p95_latency_ms: float
    judge_groundedness: float
    judge_hallucination: float
    by_collection: dict[str, dict[str, float]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def empty_report() -> EvalReport:
    """Return an empty EvalReport with current timestamp and zeros.

    Used by the route when no report exists yet. Caller can detect this
    case via the `n_samples == 0` check or `by_collection == {}`.
    """
    return EvalReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        n_samples=0,
        recall_at_8=0.0,
        ndcg_at_8=0.0,
        p50_latency_ms=0.0,
        p95_latency_ms=0.0,
        judge_groundedness=0.0,
        judge_hallucination=0.0,
        by_collection={},
    )


def recall_at_k(retrieved: list[str], gold: list[str], k: int = 8) -> float:
    """Binary recall: at least 1 gold doc in top-k? 1.0 or 0.0."""
    return 1.0 if any(d in gold for d in retrieved[:k]) else 0.0


def ndcg_at_k(retrieved: list[str], graded_relevance: dict[str, int],
              k: int = 8) -> float:
    """nDCG@k: graded relevance with position-discount."""
    dcg = 0.0
    for i, d in enumerate(retrieved[:k], start=1):
        rel = graded_relevance.get(d, 0)
        dcg += rel / (1.0 if i == 1 else math.log2(i + 1))
    ideal_rels = sorted(graded_relevance.values(), reverse=True)[:k]
    idcg = 0.0
    for i, rel in enumerate(ideal_rels, start=1):
        idcg += rel / (1.0 if i == 1 else math.log2(i + 1))
    return dcg / idcg if idcg > 0 else 0.0
