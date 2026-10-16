"""Grounded answer generator with evidence_json.

Contract (the anti-hallucination guarantee):
  1. Every sentence in the answer is copied verbatim from a retrieved
     passage and ends with a [doc_N] citation pointing at that passage.
  2. `spans` contains exactly the cited passages, numbered 1..N in the order
     they first appear, so [doc_N] always resolves to spans[N-1].
  3. If no passage is relevant enough, the answer is refused — never guessed.

This is an extractive answerer (no LLM call), so it cannot fabricate text.
`stream_tokens` is the seam where a model gateway's token stream plugs in.
"""
from __future__ import annotations

import re
from typing import Iterator, Literal

from pydantic import BaseModel

from .apex_retriever import RetrievedDoc
from .local_index import get_index, tokens

Collection = Literal["hr_policies", "tech_docs", "product_docs"]

MIN_SENTENCE_SCORE = 0.5  # IDF-weighted share of the query a sentence must cover
RELATIVE_CUT = 0.75  # keep sentences within 75% of the best sentence's score
MAX_SENTENCES = 4
MAX_DOCS_CONSIDERED = 5
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
_CITE = re.compile(r"\[doc_(\d+)\]")


class EvidenceSpan(BaseModel):
    doc_id: str
    offset: int
    text: str
    score: float
    title: str = ""


class EvidenceJSON(BaseModel):
    query: str
    collection: Collection
    answer: str
    spans: list[EvidenceSpan]
    refused: bool = False
    refusal_reason: str | None = None
    # Set by the pipeline after the hallucination check / sanitization.
    groundedness: float | None = None
    flags: list[str] = []


def _refuse(query: str, collection: Collection, reason: str) -> EvidenceJSON:
    return EvidenceJSON(query=query, collection=collection, answer="",
                        spans=[], refused=True, refusal_reason=reason)


def _verify(answer: str, n_spans: int) -> bool:
    """Every answer line carries >=1 citation and all citations resolve."""
    lines = [l for l in answer.splitlines() if l.strip()]
    if not lines:
        return False
    for l in lines:
        cites = [int(m) for m in _CITE.findall(l)]
        if not cites or any(c < 1 or c > n_spans for c in cites):
            return False
    return True


def grounded_answer(query: str, collection: Collection,
                    retrieved: list[RetrievedDoc]) -> tuple[EvidenceJSON, str]:
    if not retrieved:
        return _refuse(query, collection, "No retrieved evidence"), ""
    qterms = set(tokens(query))
    if not qterms:
        return _refuse(query, collection, "Query has no searchable terms"), ""

    idf = get_index(collection).idf
    # Terms absent from the collection can never match; they must not
    # penalise an otherwise well-covered question ("vacation" vs "PTO").
    w = {t: idf[t] for t in qterms if t in idf}
    total_w = sum(w.values())
    if not total_w:
        return _refuse(query, collection, "No query term appears in this collection"), ""

    picks: list[tuple[int, int, str, float]] = []  # (doc rank, sent idx, sentence, score)
    for rank, d in enumerate(retrieved[:MAX_DOCS_CONSIDERED]):
        sents = [s.strip() for s in _SENT_SPLIT.split(d.text) if s.strip()]
        title_terms = set(tokens(d.title))
        for i, s in enumerate(sents):
            st = set(tokens(s))
            # Title words count: "PTO Policy §2 Carryover" gives context to its sentences.
            score = sum(w.get(t, 0.0) for t in qterms & (st | title_terms)) / total_w
            if (qterms & st & w.keys()) and score >= MIN_SENTENCE_SCORE:
                picks.append((rank, i, s, score))
    if not picks:
        return _refuse(query, collection,
                       "No passage covers enough of the question"), ""

    top = max(p[3] for p in picks)
    picks = [p for p in picks if p[3] >= RELATIVE_CUT * top]  # drop weaker distractors
    best = sorted(picks, key=lambda p: (-p[3], p[0], p[1]))[:MAX_SENTENCES]
    best.sort(key=lambda p: (p[0], p[1]))  # reading order: doc rank, then position

    numbering: dict[int, int] = {}
    spans: list[EvidenceSpan] = []
    lines: list[str] = []
    for rank, _i, sent, _score in best:
        if rank not in numbering:
            d = retrieved[rank]
            numbering[rank] = len(spans) + 1
            spans.append(EvidenceSpan(doc_id=d.doc_id, offset=0, text=d.text,
                                      score=d.rrf_score, title=d.title))
        lines.append(f"- {sent} [doc_{numbering[rank]}]")
    answer = "\n".join(lines)
    if not _verify(answer, len(spans)):  # defensive; unreachable by construction
        return _refuse(query, collection, "Grounding check failed"), answer
    return EvidenceJSON(query=query, collection=collection,
                        answer=answer, spans=spans), answer


_TOKEN_RE = re.compile(r"\s*\S+")


def stream_tokens(answer: str) -> Iterator[str]:
    """Yield the answer in word-sized deltas (whitespace preserved), so
    ''.join(stream_tokens(a)) == a. A citation marker is a single
    whitespace-free token, so it is never split across two deltas.

    Swap for the model gateway's token stream in production; the SSE
    contract in main.py does not change.
    """
    for m in _TOKEN_RE.finditer(answer):
        yield m.group(0)
    tail = answer[len(answer.rstrip()):]
    if tail:
        yield tail
