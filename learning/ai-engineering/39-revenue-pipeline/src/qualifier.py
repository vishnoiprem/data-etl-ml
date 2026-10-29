"""
qualifier.py — Score each lead 0-100 on revenue probability.

The qualifier asks the LLM to play the role of a senior sales
qualifier and produce:
  - score:    int 0-100 (probability of closing within 30 days)
  - deal_usd: int estimated deal size in USD
  - reasons:  list[str] (3-5 short strings explaining the score)

Why an LLM and not a hand-rolled classifier?
  - Easy to retrain on a new niche by editing the system prompt.
  - Reasons are human-readable → the consultant can sanity-check.
  - One model handles all 6 sources (text length varies wildly).

The stub router uses keyword heuristics so the demo is reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass

from router import LLMRouter
from signals import Lead


@dataclass
class Qualification:
    score: int               # 0-100, probability of close within 30 days
    deal_usd: int            # estimated deal size
    reasons: list[str]       # 3-5 short explanations
    raw_text: str = ""       # for debugging

    @property
    def weighted_usd(self) -> int:
        """Pipeline value: deal size × probability."""
        return int(self.deal_usd * (self.score / 100.0))

    @property
    def tier(self) -> str:
        if self.score >= 70:
            return "hot"
        if self.score >= 40:
            return "warm"
        return "cold"


QUALIFY_SYSTEM = """You are a senior sales qualifier for an independent AI/data
consultant (Prem). The consultant's niche: LLM/RAG/agent engineering, ML
platform, data pipelines. Engagements: 4-12 weeks, $5-15k typical, $25k+ for
multi-month work. Your job: score the lead 0-100 on probability of closing
within 30 days, estimate deal size, and explain in 3-5 short bullet reasons.

High-score signals (boost):
  - "budget approved", "funded", "Series B/C", "$ raised", explicit $
  - "urgent", "ASAP", "this quarter", short timeline
  - "AI/ML/LLM/RAG/agent/data" match to niche
  - Inbound DM, named contact, or referral

Low-score signals (cut):
  - "junior", "intern", "entry-level"
  - "equity only", "pre-seed", "no budget"
  - "permanent role" (the consultant does contract, not full-time)
  - "US-only" or "on-site" if the consultant is remote

Output strictly valid JSON: {"score": int, "deal_usd": int, "reasons": [str]}"""


def qualify(lead: Lead, router: LLMRouter) -> Qualification:
    """Score one lead. Returns a Qualification object."""
    prompt = (
        f"Source: {lead.source}\n"
        f"Company: {lead.company}\n"
        f"Title: {lead.title}\n"
        f"Posted: {lead.posted_at}\n"
        f"Contact: {lead.contact or 'unknown'}\n"
        f"Tags: {', '.join(lead.tags) or 'none'}\n\n"
        f"Text:\n{lead.text}\n\n"
        f"JSON response:"
    )
    data = router.json(prompt, schema_hint='{"score": int, "deal_usd": int, "reasons": [str]}')
    return Qualification(
        score=int(data.get("score", 0)),
        deal_usd=int(data.get("deal_usd", 0)),
        reasons=list(data.get("reasons", [])),
        raw_text=str(data),
    )


def qualify_batch(leads: list[Lead], router: LLMRouter) -> list[tuple[Lead, Qualification]]:
    """Score a batch. Returns list of (lead, qualification) sorted by score desc."""
    out: list[tuple[Lead, Qualification]] = []
    for ld in leads:
        try:
            out.append((ld, qualify(ld, router)))
        except Exception as e:
            # Don't let one bad lead kill the batch
            out.append((ld, Qualification(score=0, deal_usd=0, reasons=[f"qualify error: {e}"])))
    out.sort(key=lambda x: x[1].score, reverse=True)
    return out


def top_n(qualified: list[tuple[Lead, Qualification]], n: int = 5) -> list[tuple[Lead, Qualification]]:
    """Return top N leads by score, dropping anything below 40 (cold)."""
    return [pair for pair in qualified[:n] if pair[1].score >= 40]