"""Grounded answer generator.

The LLM is forced to cite [doc_i] markers. If the LLM output doesn't
contain enough citations to cover the retrieved evidence, the answer
is refused. This is the anti-hallucination contract.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .retriever import RetrievedDoc
from .router import (Domain, EvidenceJSON, EvidenceSpan, PromptTemplate,
                     build_evidence_json, load_template)


@dataclass
class AnswerTrace:
    """Full trace of an answer call. Logged to audit/log.py."""
    query: str
    domain: Domain
    template_id: str
    retrieved_ids: list[str]
    rrf_scores: list[float]
    cited_ids: list[str]
    refused: bool
    refusal_reason: str | None
    latency_ms: float


def extract_citations(answer: str, marker_pattern: str = r"\[doc_(\d+)\]") -> list[int]:
    """Pull doc_id indices out of the LLM answer."""
    return [int(m) for m in re.findall(marker_pattern, answer)]


def extract_citations_from_marker(answer: str, marker: str) -> list[int]:
    """Convert a template marker like '[doc_{i}]' to a regex and extract.

    This avoids the bug where the default marker_pattern matches the `d`
    in `doc_` if not anchored properly.
    """
    # marker looks like "[doc_{i}]" -> regex r"\[doc_(\d+)\]"
    regex = re.escape(marker).replace(re.escape("{i}"), r"(\d+)")
    return [int(m) for m in re.findall(regex, answer)]


def enforce_grounding(answer: str, retrieved: list[RetrievedDoc],
                      template: PromptTemplate) -> tuple[bool, str | None]:
    """Refuse the answer if the LLM didn't cite enough of the retrieved docs.

    Rule: at least 50% of retrieved docs must be cited, OR the answer must
    be empty. Otherwise the LLM is making claims without evidence.
    """
    cited = extract_citations_from_marker(answer, template.citation_marker)
    if not cited:
        return False, "No citations in answer"
    cited_set = set(cited)
    retrieved_set = set(range(1, len(retrieved) + 1))
    coverage = len(cited_set & retrieved_set) / max(1, len(retrieved_set))
    if coverage < 0.5:
        return False, f"Citation coverage {coverage:.0%} below 50% threshold"
    return True, None


def build_prompt(template: PromptTemplate, query: str,
                 retrieved: list[RetrievedDoc]) -> tuple[str, str]:
    """Build (system, user) prompt pair with embedded evidence context."""
    context_lines = []
    for i, d in enumerate(retrieved, start=1):
        context_lines.append(
            f"[doc_{i}] (id={d.doc_id}, rrf={d.rrf_score:.3f})\n{d.text[:2000]}"
        )
    context = "\n\n".join(context_lines)
    system = template.system
    user = f"{template.user_prefix}\n\nQuery: {query}\n\nEvidence:\n{context}\n\nAnswer (cite [{template.citation_marker.format(i='N')}] for every claim):"
    return system, user


def make_answer(query: str, domain: Domain, retrieved: list[RetrievedDoc],
                raw_llm_output: str) -> tuple[EvidenceJSON, AnswerTrace]:
    """Convert raw LLM output into a grounded EvidenceJSON + trace.

    The LLM is just a function here: in production this would call your
    model gateway, but the contract is the same.
    """
    template = load_template(domain)
    is_grounded, reason = enforce_grounding(raw_llm_output, retrieved, template)
    cited = extract_citations_from_marker(raw_llm_output, template.citation_marker)
    spans: list[EvidenceSpan] = []
    for idx in cited:
        if 1 <= idx <= len(retrieved):
            d = retrieved[idx - 1]
            spans.append(EvidenceSpan(
                doc_id=d.doc_id, offset=0, text=d.text[:200], score=d.rrf_score,
            ))
    if is_grounded:
        ej = build_evidence_json(query, domain, raw_llm_output, spans)
    else:
        ej = EvidenceJSON(
            query=query, domain=domain, answer="", spans=[],
            refused=True, refusal_reason=reason,
        )
    trace = AnswerTrace(
        query=query, domain=domain, template_id=domain.value,
        retrieved_ids=[d.doc_id for d in retrieved],
        rrf_scores=[d.rrf_score for d in retrieved],
        cited_ids=[s.doc_id for s in spans],
        refused=ej.refused, refusal_reason=ej.refusal_reason, latency_ms=0.0,
    )
    return ej, trace
