"""Grounded answer generator with evidence_json.

The LLM is forced to cite [doc_N] for every claim. If the LLM output
doesn't cover >= 50% of retrieved docs, the answer is refused. This
is the anti-hallucination contract.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel

from .apex_retriever import RetrievedDoc
from .apex_router import load_prompt

Collection = Literal["hr_policies", "tech_docs", "product_docs"]


class EvidenceSpan(BaseModel):
    doc_id: str
    offset: int
    text: str
    score: float


class EvidenceJSON(BaseModel):
    query: str
    collection: Collection
    answer: str
    spans: list[EvidenceSpan]
    refused: bool = False
    refusal_reason: str | None = None


def _extract_citations(answer: str, marker: str) -> list[int]:
    """Extract doc indices from citation markers like [doc_N]."""
    # marker is e.g. "[doc_{i}]" -> escape then replace {i} with (\d+)
    regex = re.escape(marker).replace(re.escape("{i}"), r"(\d+)")
    return [int(m) for m in re.findall(regex, answer)]


def _enforce_grounding(answer: str, retrieved: list[RetrievedDoc],
                       marker: str) -> tuple[bool, str | None]:
    """Refuse if < 50% of retrieved docs are cited."""
    cited = _extract_citations(answer, marker)
    if not cited:
        return False, "No citations in answer"
    cited_set = set(cited)
    retrieved_set = set(range(1, len(retrieved) + 1))
    coverage = len(cited_set & retrieved_set) / max(1, len(retrieved_set))
    if coverage < 0.5:
        return False, f"Citation coverage {coverage:.0%} below 50% threshold"
    return True, None


def grounded_answer(query: str, collection: Collection,
                    retrieved: list[RetrievedDoc]) -> tuple[EvidenceJSON, str]:
    """Build a grounded answer. The LLM is a function call here.

    In production this calls your model gateway. The contract is:
    1. LLM sees the evidence context + citation marker rules.
    2. LLM output must include [doc_N] for every claim.
    3. If citations cover < 50% of retrieved docs, the answer is refused.
    """
    template = load_prompt(collection)
    marker = template.get("citation_marker", "[doc_{i}]")
    # In production: call model gateway with template + evidence context.
    # For the prototype: simulate a fully-grounded response that cites
    # every doc. This is the happy path.
    if not retrieved:
        return EvidenceJSON(
            query=query, collection=collection, answer="",
            spans=[], refused=True,
            refusal_reason="No retrieved evidence",
        ), ""
    cited_indices = list(range(1, len(retrieved) + 1))
    raw = " ".join(f"[doc_{i}]" for i in cited_indices)
    raw += " " + " ".join(d.text for d in retrieved)
    is_grounded, reason = _enforce_grounding(raw, retrieved, marker)
    spans: list[EvidenceSpan] = []
    for idx in cited_indices:
        if 1 <= idx <= len(retrieved):
            d = retrieved[idx - 1]
            spans.append(EvidenceSpan(
                doc_id=d.doc_id, offset=0, text=d.text[:200], score=d.rrf_score,
            ))
    if is_grounded:
        return EvidenceJSON(
            query=query, collection=collection, answer=raw, spans=spans,
        ), raw
    return EvidenceJSON(
        query=query, collection=collection, answer="", spans=[],
        refused=True, refusal_reason=reason,
    ), raw
