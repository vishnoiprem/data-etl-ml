"""
test_qualifier.py — exercise the LLM-stub qualifier.

These tests assert on the *shape* and *invariants* of the qualification
output (score in [0,100], deal_usd ≥ 0, reasons is a list). The exact
keyword scoring is verified separately by the stub router itself; we
just want to know qualification flows through cleanly.
"""

from __future__ import annotations

from qualifier import Qualification, qualify, qualify_batch, top_n
from router import StubRouter
from signals import Lead


def _lead(text: str = "AI consulting engagement, budget approved, urgent", **kw) -> Lead:
    return Lead(
        source="hn_hiring",
        company=kw.get("company", "Acme"),
        title=kw.get("title", "Senior AI engineer"),
        url="https://example.com",
        text=text,
        posted_at="2026-10-12",
        contact=None,
        tags=kw.get("tags", []),
    )


def test_qualify_returns_valid_score_range():
    q = qualify(_lead(), StubRouter())
    assert 0 <= q.score <= 100
    assert q.deal_usd >= 0
    assert isinstance(q.reasons, list)
    assert len(q.reasons) >= 1


def test_budget_signal_increases_score():
    q_budget = qualify(_lead("budget approved, $50k funded, urgent AI work"), StubRouter())
    q_no_budget = qualify(_lead("junior intern, equity only, no budget"), StubRouter())
    assert q_budget.score > q_no_budget.score


def test_junior_signal_drags_score_below_40():
    # Pure "junior" penalty, no other boosts. Use a neutral title and a
    # body with no budget/urgency/niche keywords — just the four cold
    # signals. Stub scoring starts at 50 and -30 → 20.
    q = qualify(
        _lead("junior intern entry-level graduate", title="generalist"),
        StubRouter(),
    )
    assert q.score < 40, f"expected cold lead, got {q.score}"


def test_weighted_usd_is_deal_times_probability():
    q = Qualification(score=80, deal_usd=10_000, reasons=["x"])
    assert q.weighted_usd == 8000


def test_tier_thresholds():
    assert Qualification(score=90, deal_usd=1, reasons=[]).tier == "hot"
    assert Qualification(score=60, deal_usd=1, reasons=[]).tier == "warm"
    assert Qualification(score=20, deal_usd=1, reasons=[]).tier == "cold"


def test_qualify_batch_sorts_descending_and_handles_errors():
    leads = [
        _lead("budget approved AI LLM RAG agent"),
        _lead("junior intern entry-level"),
        _lead("urgent AI/ML engagement"),
    ]
    out = qualify_batch(leads, StubRouter())
    scores = [q.score for _, q in out]
    assert scores == sorted(scores, reverse=True)
    assert all(isinstance(q, Qualification) for _, q in out)


def test_top_n_drops_cold_leads():
    leads = [
        _lead("budget approved AI"),
        _lead("junior intern"),
    ]
    out = qualify_batch(leads, StubRouter())
    top = top_n(out, n=10)
    assert all(q.score >= 40 for _, q in top)
