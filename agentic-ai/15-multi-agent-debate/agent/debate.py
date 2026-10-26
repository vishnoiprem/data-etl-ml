"""
Multi-agent debate: two agents argue, a third judges.

The verifier scores the two arguments on three axes:
  - groundedness (cites evidence, doesn't hallucinate)
  - evidence (more cited facts, fewer unsupported claims)
  - logical soundness (no obvious fallacies)

Toy implementation: keyword overlap for evidence scoring, position-consistency
for logical soundness. Real impl: a judge LLM with a calibrated prompt.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Optional


STOP = {"the", "a", "an", "and", "or", "but", "is", "are", "to", "of", "in", "on", "for", "with", "as", "at", "by"}


def tokenize(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP and len(w) > 3}


def groundedness_score(arg: str) -> float:
    """Toy: presence of hedging markers and citation tokens."""
    hedge = len(re.findall(r"\b(may|might|could|suggests|appears|according to|source)\b", arg.lower()))
    citations = len(re.findall(r"\[(\d+|[a-z]+ ?\d{4})\]", arg))
    markers = hedge + citations
    return min(1.0, markers / 5)


def evidence_score(arg: str) -> float:
    """Toy: more unique content words = more evidence."""
    return min(1.0, len(tokenize(arg)) / 60)


def logical_soundness(arg: str, position: str) -> float:
    """Toy: how often the argument reaffirms its position vs contradicts it."""
    tokens = tokenize(arg)
    pos_tokens = tokenize(position) - tokens
    confirmed = sum(1 for t in pos_tokens if t in tokens)
    return min(1.0, confirmed / max(1, len(pos_tokens)))


@dataclass
class Argument:
    agent: str
    position: str
    text: str


@dataclass
class Verdict:
    winner: str
    confidence: float
    reasoning: str


def verifier_judge(a: Argument, b: Argument) -> Verdict:
    """A toy verifier. Real impl: a judge LLM with a calibrated rubric."""
    score_a = (
        0.4 * groundedness_score(a.text)
        + 0.3 * evidence_score(a.text)
        + 0.3 * logical_soundness(a.text, a.position)
    )
    score_b = (
        0.4 * groundedness_score(b.text)
        + 0.3 * evidence_score(b.text)
        + 0.3 * logical_soundness(b.text, b.position)
    )
    diff = score_a - score_b
    confidence = min(1.0, abs(diff) * 5)
    if diff > 0.05:
        return Verdict(winner=a.agent, confidence=round(confidence, 3), reasoning=f"higher score {score_a:.2f} vs {score_b:.2f}")
    if diff < -0.05:
        return Verdict(winner=b.agent, confidence=round(confidence, 3), reasoning=f"higher score {score_b:.2f} vs {score_a:.2f}")
    return Verdict(winner="tie", confidence=round(1 - confidence, 3), reasoning=f"scores within 0.05: {score_a:.2f} vs {score_b:.2f}")


if __name__ == "__main__":
    a = Argument(agent="A", position="yes, the patient should see a cardiologist",
                 text="According to recent meta-analyses, the elevated troponin levels suggest cardiac involvement. The ECG shows ST changes that may be ischemic in origin. Suggests cardiology consult is warranted, with statin therapy as a first-line intervention [1].")
    b = Argument(agent="B", position="no, primary care follow-up is sufficient",
                 text="Although troponin is elevated, the patient's symptoms could be explained by the recent viral illness. The ECG is borderline. Primary care with repeat testing may be more appropriate.")
    v = verifier_judge(a, b)
    print(f"winner: {v.winner}, confidence: {v.confidence}, reason: {v.reasoning}")
