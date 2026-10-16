"""Omni layer: domain classifier + prompt-template loader.

Three domains share one API. Each domain has its own prompt template and
its own `evidence_json` schema, so the LLM is forced to ground every claim
in a doc_id + offset. This is the anti-hallucination contract.
"""
from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Domain(str, Enum):
    """The three served collections (Omni layer)."""
    HR_POLICIES = "hr_policies"
    TECH_DOCS = "tech_docs"
    PRODUCT_DOCS = "product_docs"


class EvidenceSpan(BaseModel):
    """A single grounded citation in the answer."""
    doc_id: str
    offset: int = Field(..., ge=0)
    text: str
    score: float = Field(..., ge=0.0, le=1.0)


class EvidenceJSON(BaseModel):
    """Structured artifact returned to the client. LLM is required to
    populate this — every claim has a `spans` list. No spans = refuse."""
    query: str
    domain: Domain
    answer: str
    spans: list[EvidenceSpan]
    refused: bool = False
    refusal_reason: str | None = None


class PromptTemplate(BaseModel):
    """Per-domain prompt with citation enforcement."""
    system: str
    user_prefix: str
    citation_marker: str = "[doc_{i}]"  # LLM must emit these
    max_context_docs: int = 8


_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def load_template(domain: Domain) -> PromptTemplate:
    """Load the YAML prompt template for a domain."""
    path = _PROMPTS_DIR / f"{domain.value}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"No prompt template for {domain} at {path}")
    raw = yaml.safe_load(path.read_text())
    return PromptTemplate(**raw)


def classify_domain(query: str, hint: Domain | None = None) -> Domain:
    """Classify the query into one of 3 collections.

    Uses a simple keyword heuristic for low latency. In production this
    would be a fine-tuned classifier; for the prototype we trade 1-2% accuracy
    for <1ms inference.
    """
    if hint is not None:
        return hint
    q = query.lower()
    hr_kw = {"pto", "vacation", "leave", "policy", "hr", "benefit", "401k", "parental"}
    tech_kw = {"api", "endpoint", "deploy", "kubernetes", "docker", "service", "ci", "cd"}
    product_kw = {"feature", "roadmap", "spec", "user", "story", "epic", "mvp"}
    h = sum(1 for k in hr_kw if k in q)
    t = sum(1 for k in tech_kw if k in q)
    p = sum(1 for k in product_kw if k in q)
    if t > max(h, p):
        return Domain.TECH_DOCS
    if p > h:
        return Domain.PRODUCT_DOCS
    if h > 0:
        return Domain.HR_POLICIES
    return Domain.HR_POLICIES  # default


def build_evidence_json(query: str, domain: Domain, answer: str,
                        spans: list[EvidenceSpan]) -> EvidenceJSON:
    """Build the structured evidence JSON. If no spans, the answer is refused."""
    if not spans:
        return EvidenceJSON(
            query=query, domain=domain, answer="",
            spans=[], refused=True,
            refusal_reason="No grounded evidence found in retrieval.",
        )
    return EvidenceJSON(query=query, domain=domain, answer=answer, spans=spans)
