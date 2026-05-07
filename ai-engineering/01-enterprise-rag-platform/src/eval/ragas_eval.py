"""RAG evaluation harness — retrieval and end-to-end metrics.

Three tiers:

1. Retrieval-only (no LLM needed)
   - Recall@K  : did we retrieve at least one relevant chunk in the top-K?
   - MRR       : mean reciprocal rank of the first relevant chunk

2. End-to-end heuristic metrics (no LLM judge needed; cheap)
   - Faithfulness-lite : fraction of answer tokens grounded in retrieved chunks
   - Coverage          : fraction of expected-keyword targets present in the answer

3. LLM-as-judge metrics (optional, only in AWS mode)
   - Faithfulness, answer relevance, context precision

For the demo we run (1) and (2). The LLM-judge harness is sketched at the
bottom for completeness.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

from src.generation.rag_pipeline import RagPipeline


@dataclass
class GoldenItem:
    """A labeled eval example."""
    question: str
    expected_keywords: list[str]            # words that should appear in a good answer
    relevant_chunk_substrings: list[str]    # any chunk text matching one of these is "relevant"


# ----- Helpers --------------------------------------------------------------

def _tokens(text: str) -> set[str]:
    return {w.lower() for w in re.findall(r"\b\w{3,}\b", text)}


def _chunk_is_relevant(chunk_text: str, item: GoldenItem) -> bool:
    return any(s.lower() in chunk_text.lower() for s in item.relevant_chunk_substrings)


# ----- Retrieval-only metrics ----------------------------------------------

def recall_at_k(pipeline: RagPipeline, items: Sequence[GoldenItem], k: int = 5) -> float:
    hits = 0
    for item in items:
        results = pipeline.retrieve(item.question)[:k]
        if any(_chunk_is_relevant(r.chunk.text, item) for r in results):
            hits += 1
    return hits / len(items) if items else 0.0


def mean_reciprocal_rank(pipeline: RagPipeline, items: Sequence[GoldenItem], k: int = 10) -> float:
    rrs = []
    for item in items:
        results = pipeline.retrieve(item.question)[:k]
        rr = 0.0
        for i, r in enumerate(results, start=1):
            if _chunk_is_relevant(r.chunk.text, item):
                rr = 1.0 / i
                break
        rrs.append(rr)
    return sum(rrs) / len(rrs) if rrs else 0.0


# ----- End-to-end heuristic metrics ----------------------------------------

def faithfulness_lite(answer_text: str, retrieved_chunks_text: str) -> float:
    """Fraction of content tokens in the answer that also appear in retrieved chunks.

    A crude but useful sanity check — high faithfulness ≠ correct, but very
    low faithfulness almost always means hallucinated.
    """
    a = _tokens(answer_text)
    c = _tokens(retrieved_chunks_text)
    if not a:
        return 0.0
    grounded = a & c
    return len(grounded) / len(a)


def coverage(answer_text: str, expected_keywords: Sequence[str]) -> float:
    """Fraction of expected-keyword targets present in the answer."""
    if not expected_keywords:
        return 1.0
    a = answer_text.lower()
    hit = sum(1 for kw in expected_keywords if kw.lower() in a)
    return hit / len(expected_keywords)


# ----- Eval runner ----------------------------------------------------------

@dataclass
class EvalReport:
    n_items: int
    recall_at_5: float
    mrr_at_10: float
    avg_faithfulness: float
    avg_coverage: float
    refusal_rate: float
    avg_total_ms: float


def run_eval(pipeline: RagPipeline, items: Sequence[GoldenItem]) -> EvalReport:
    if not items:
        return EvalReport(0, 0, 0, 0, 0, 0, 0)

    r5 = recall_at_k(pipeline, items, k=5)
    mrr10 = mean_reciprocal_rank(pipeline, items, k=10)

    faith, cov, lat = [], [], []
    refused = 0
    for item in items:
        ans = pipeline.ask(item.question)
        if ans.refused:
            refused += 1
            faith.append(0.0)
            cov.append(0.0)
        else:
            ctx_text = " ".join(s.text_preview for s in ans.sources)
            faith.append(faithfulness_lite(ans.answer, ctx_text))
            cov.append(coverage(ans.answer, item.expected_keywords))
        lat.append(ans.telemetry.get("total_ms", 0))

    return EvalReport(
        n_items=len(items),
        recall_at_5=r5,
        mrr_at_10=mrr10,
        avg_faithfulness=sum(faith) / len(faith),
        avg_coverage=sum(cov) / len(cov),
        refusal_rate=refused / len(items),
        avg_total_ms=sum(lat) / len(lat),
    )


# ----- Default golden set (uses our sample data) ----------------------------

DEFAULT_GOLDEN = [
    GoldenItem(
        question="What is our PTO policy for new hires?",
        expected_keywords=["pto", "new hire", "accrue", "days"],
        relevant_chunk_substrings=["PTO policy", "new hire"],
    ),
    GoldenItem(
        question="How do I rotate an EBS volume's KMS key?",
        expected_keywords=["ebs", "kms", "rotat"],
        relevant_chunk_substrings=["EBS", "KMS rotation"],
    ),
    GoldenItem(
        question="What happens if I miss the open-enrollment window?",
        expected_keywords=["enrollment", "qualifying", "event"],
        relevant_chunk_substrings=["open enrollment", "qualifying life event"],
    ),
    GoldenItem(
        question="What are the access tiers for our customer-data warehouse?",
        expected_keywords=["tier", "access", "data"],
        relevant_chunk_substrings=["data warehouse", "access tier"],
    ),
    GoldenItem(
        question="Who approves SOC 2 control exceptions?",
        expected_keywords=["soc 2", "exception", "approv"],
        relevant_chunk_substrings=["SOC 2", "control exception"],
    ),
]
