"""Eval harness: Recall@8, nDCG@10, LLM-as-judge.

Three metrics, three views of retrieval quality:
- Recall@8: at least 1 gold doc in top-8 (binary, deterministic, fast)
- nDCG@10: graded relevance with position-discount (1 query = 1 number)
- LLM-as-judge: GPT-4-class judge scoring groundedness / hallucination

The eval runs against a held-out set of 1000 queries with gold doc IDs
and graded relevance. Reports land in reports/eval_<ts>.json.
"""
from __future__ import annotations

import json
import logging
import statistics
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class GoldItem:
    """One gold-standard item: query + relevant docs + graded relevance."""
    query_id: str
    query: str
    gold_doc_ids: list[str]
    graded_relevance: dict[str, int]  # doc_id -> relevance grade (0-3)


@dataclass
class EvalSample:
    """One eval result: a query + what the system returned + scores."""
    query_id: str
    retrieved_doc_ids: list[str]
    recall_at_8: float
    ndcg_at_10: float
    judge_groundedness: float  # 1-5
    judge_completeness: float  # 1-5
    judge_hallucination: float  # 1-5 (lower is better)


@dataclass
class EvalReport:
    """Top-level report. Written to reports/eval_<ts>.json."""
    timestamp: str
    n_samples: int
    recall_at_8: float
    ndcg_at_10: float
    judge_groundedness: float
    judge_completeness: float
    judge_hallucination: float
    samples: list[EvalSample] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "n_samples": self.n_samples,
            "metrics": {
                "recall_at_8": self.recall_at_8,
                "ndcg_at_10": self.ndcg_at_10,
                "judge_groundedness": self.judge_groundedness,
                "judge_completeness": self.judge_completeness,
                "judge_hallucination": self.judge_hallucination,
            },
            "samples": [asdict(s) for s in self.samples],
        }


def recall_at_k(retrieved: list[str], gold: list[str], k: int = 8) -> float:
    """Binary recall: is at least 1 gold doc in top-k? 1.0 or 0.0."""
    return 1.0 if any(d in gold for d in retrieved[:k]) else 0.0


def ndcg_at_k(retrieved: list[str], graded_relevance: dict[str, int],
              k: int = 10) -> float:
    """nDCG@k: graded relevance with position-discount.

    nDCG = DCG / iDCG, where DCG = sum(rel_i / log2(i+1)).
    """
    dcg = 0.0
    for i, d in enumerate(retrieved[:k], start=1):
        rel = graded_relevance.get(d, 0)
        dcg += rel / (1.0 if i == 1 else __import__("math").log2(i + 1))
    ideal_rels = sorted(graded_relevance.values(), reverse=True)[:k]
    idcg = 0.0
    for i, rel in enumerate(ideal_rels, start=1):
        idcg += rel / (1.0 if i == 1 else __import__("math").log2(i + 1))
    return dcg / idcg if idcg > 0 else 0.0


def score_query(gold: GoldItem, retrieved: list[str],
                judge_scores: dict[str, float] | None = None) -> EvalSample:
    """Score a single query against gold + judge."""
    judge_scores = judge_scores or {}
    return EvalSample(
        query_id=gold.query_id,
        retrieved_doc_ids=retrieved,
        recall_at_8=recall_at_k(retrieved, gold.gold_doc_ids, k=8),
        ndcg_at_10=ndcg_at_k(retrieved, gold.graded_relevance, k=10),
        judge_groundedness=judge_scores.get("groundedness", 0.0),
        judge_completeness=judge_scores.get("completeness", 0.0),
        judge_hallucination=judge_scores.get("hallucination", 0.0),
    )


def run_harness(gold: list[GoldItem],
                retrieve_fn,
                judge_fn,
                out_path: str | None = None) -> EvalReport:
    """Run the full harness over a gold set."""
    samples: list[EvalSample] = []
    for g in gold:
        retrieved = retrieve_fn(g.query)
        judge = judge_fn(g.query, retrieved)
        samples.append(score_query(g, retrieved, judge))
    n = len(samples)
    report = EvalReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        n_samples=n,
        recall_at_8=sum(s.recall_at_8 for s in samples) / max(1, n),
        ndcg_at_10=sum(s.ndcg_at_10 for s in samples) / max(1, n),
        judge_groundedness=sum(s.judge_groundedness for s in samples) / max(1, n),
        judge_completeness=sum(s.judge_completeness for s in samples) / max(1, n),
        judge_hallucination=sum(s.judge_hallucination for s in samples) / max(1, n),
        samples=samples,
    )
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(json.dumps(report.to_dict(), indent=2))
    return report


# Acceptance bar
ACCEPTANCE = {
    "recall_at_8": 0.85,
    "ndcg_at_10": 0.78,
    "judge_groundedness": 4.0,
    "judge_hallucination": 2.0,  # at most 2% hallucination
}


def check_acceptance(report: EvalReport) -> tuple[bool, list[str]]:
    """Check the report against the acceptance bar. Return (pass, failures)."""
    failures = []
    if report.recall_at_8 < ACCEPTANCE["recall_at_8"]:
        failures.append(f"Recall@8 {report.recall_at_8:.3f} < {ACCEPTANCE['recall_at_8']}")
    if report.ndcg_at_10 < ACCEPTANCE["ndcg_at_10"]:
        failures.append(f"nDCG@10 {report.ndcg_at_10:.3f} < {ACCEPTANCE['ndcg_at_10']}")
    if report.judge_groundedness < ACCEPTANCE["judge_groundedness"]:
        failures.append(f"Groundedness {report.judge_groundedness:.2f} < {ACCEPTANCE['judge_groundedness']}")
    if report.judge_hallucination > ACCEPTANCE["judge_hallucination"]:
        failures.append(f"Hallucination {report.judge_hallucination:.2f} > {ACCEPTANCE['judge_hallucination']}")
    return (len(failures) == 0, failures)
