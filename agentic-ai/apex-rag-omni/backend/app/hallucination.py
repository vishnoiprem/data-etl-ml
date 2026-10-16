"""Hallucination detection: does the cited evidence actually support each claim?

Runs on EVERY answer, whatever produced it (today: extractive; tomorrow: an
LLM). For each answer line we check, against the passages it cites:

  1. citation integrity - every [doc_N] resolves to a span; the line has one.
  2. numeric fidelity   - every number in the claim appears in a cited span
                          (the classic LLM failure: "20 days" -> "25 days").
  3. lexical support    - share of the claim's content words found in the
                          cited spans.

Verdict: pass (>= PASS), warn (>= FAIL), fail (< FAIL or any bad number or
dangling citation). A `fail` is refused by the pipeline.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .local_index import tokens

PASS = 0.80
FAIL = 0.50
_CITE = re.compile(r"\[doc_(\d+)\]")
_NUM = re.compile(r"\d[\d,]*\.?\d*")


@dataclass
class ClaimResult:
    claim: str
    support: float
    ok: bool
    problems: list[str] = field(default_factory=list)


@dataclass
class HallucinationReport:
    groundedness: float  # mean support across claims, 0..1
    verdict: str  # pass | warn | fail
    claims: list[ClaimResult]

    @property
    def problems(self) -> list[str]:
        return [p for c in self.claims for p in c.problems]


def _nums(text: str) -> set[str]:
    return {n.replace(",", "").rstrip(".") for n in _NUM.findall(text)}


def check_answer(answer: str, spans_text: list[str],
                 pass_at: float = PASS, fail_at: float = FAIL) -> HallucinationReport:
    lines = [l.strip() for l in answer.splitlines() if l.strip()]
    if not lines:
        return HallucinationReport(0.0, "fail", [])
    results: list[ClaimResult] = []
    for line in lines:
        cites = [int(c) for c in _CITE.findall(line)]
        claim = _CITE.sub("", line).lstrip("-* ").strip()
        problems: list[str] = []
        if not cites:
            problems.append("claim has no citation")
        bad = [c for c in cites if not 1 <= c <= len(spans_text)]
        if bad:
            problems.append(f"citation(s) {bad} do not resolve to a source")
        evidence = " ".join(spans_text[c - 1] for c in cites if 1 <= c <= len(spans_text))
        ev_toks = set(tokens(evidence))
        claim_toks = [t for t in tokens(claim) if not t.isdigit()]
        support = (sum(t in ev_toks for t in claim_toks) / len(claim_toks)) if claim_toks else 1.0
        if not evidence:
            support = 0.0
        missing = _nums(claim) - _nums(evidence)
        if missing:
            problems.append(f"number(s) {sorted(missing)} not found in cited source")
        results.append(ClaimResult(claim, support, not problems and support >= fail_at, problems))
    g = sum(r.support for r in results) / len(results)
    hard = any(r.problems for r in results)
    verdict = "fail" if hard or g < fail_at else ("pass" if g >= pass_at else "warn")
    return HallucinationReport(round(g, 3), verdict, results)
