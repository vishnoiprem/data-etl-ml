"""
test_pipeline.py — SQLite pipeline state machine.

Each test uses a fresh temp DB so they're independent. The schema
gets re-created on every Pipeline() init, so this is fast and clean.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from outreach import Email
from pipeline import Pipeline
from qualifier import Qualification
from signals import Lead


@pytest.fixture
def db(tmp_path: Path) -> Pipeline:
    return Pipeline(tmp_path / "test.db")


def _lead(company: str = "Acme", title: str = "AI engineer", **kw) -> Lead:
    return Lead(
        source=kw.get("source", "hn_hiring"),
        company=company,
        title=title,
        url="https://example.com",
        text=kw.get("text", "AI consulting, budget approved, urgent"),
        posted_at="2026-10-12",
        contact=kw.get("contact"),
        tags=kw.get("tags", []),
    )


def test_upsert_inserts_new_opportunity(db: Pipeline):
    lead = _lead()
    opp_id = db.upsert_lead(lead)
    row = db.get(opp_id)
    assert row is not None
    assert row["company"] == "Acme"
    assert row["status"] == "new"
    assert row["score"] == 0


def test_upsert_dedupes_by_fingerprint(db: Pipeline):
    """Same source+company+title → same row, no duplicate."""
    a = _lead("Acme", "AI engineer")
    b = _lead("Acme", "AI engineer")
    a_id = db.upsert_lead(a)
    b_id = db.upsert_lead(b)
    assert a_id == b_id
    # and there's only one row in the DB
    assert len(db.list_by_status("new")) == 1


def test_upsert_normalizes_title_for_dedup(db: Pipeline):
    """Title case + whitespace should still dedup."""
    a = _lead("Acme", "Senior AI  Engineer")
    b = _lead("Acme", "senior ai engineer")
    assert db.upsert_lead(a) == db.upsert_lead(b)


def test_record_qualification_promotes_to_qualified_and_persists_email(db: Pipeline):
    opp_id = db.upsert_lead(_lead())
    q = Qualification(score=72, deal_usd=12_000, reasons=["budget", "urgent"])
    email = Email(subject="Quick q", body="hi", to="@founder")
    db.record_qualification(opp_id, q, email=email)
    row = db.get(opp_id)
    assert row["status"] == "qualified"
    assert row["score"] == 72
    assert row["weighted_usd"] == int(12000 * 0.72)
    assert row["email_subject"] == "Quick q"


def test_record_qualification_does_not_overwrite_closed_status(db: Pipeline):
    """If a row is already 'won', record_qualification shouldn't un-win it."""
    opp_id = db.upsert_lead(_lead())
    db.mark_won(opp_id, 5000)
    db.record_qualification(
        opp_id, Qualification(score=99, deal_usd=1, reasons=[]), email=None
    )
    assert db.get(opp_id)["status"] == "won"


def test_state_transitions_sent_replied_won_lost(db: Pipeline):
    opp_id = db.upsert_lead(_lead())
    db.mark_sent(opp_id)
    assert db.get(opp_id)["status"] == "sent"
    assert db.get(opp_id)["sent_at"] is not None

    db.mark_replied(opp_id)
    assert db.get(opp_id)["status"] == "replied"
    assert db.get(opp_id)["replied_at"] is not None

    db.mark_won(opp_id, 7500)
    row = db.get(opp_id)
    assert row["status"] == "won"
    assert row["won_usd"] == 7500
    assert row["closed_at"] is not None


def test_mark_won_rejects_nonpositive_amount(db: Pipeline):
    opp_id = db.upsert_lead(_lead())
    with pytest.raises(ValueError):
        db.mark_won(opp_id, 0)
    with pytest.raises(ValueError):
        db.mark_won(opp_id, -100)


def test_mark_lost_records_reason(db: Pipeline):
    opp_id = db.upsert_lead(_lead())
    db.mark_lost(opp_id, "no budget")
    assert db.get(opp_id)["status"] == "lost"
    assert db.get(opp_id)["lost_reason"] == "no budget"


def test_top_opportunities_filters_by_status_and_score(db: Pipeline):
    hot = db.upsert_lead(_lead("Hot", "AI"))
    warm = db.upsert_lead(_lead("Warm", "ML"))
    cold = db.upsert_lead(_lead("Cold", "ds"))
    db.record_qualification(hot, Qualification(score=80, deal_usd=10_000, reasons=[]), email=None)
    db.record_qualification(warm, Qualification(score=50, deal_usd=5_000, reasons=[]), email=None)
    db.record_qualification(cold, Qualification(score=20, deal_usd=1_000, reasons=[]), email=None)
    top = db.top_opportunities(min_score=40, limit=10)
    companies = {r["company"] for r in top}
    assert "Hot" in companies
    assert "Warm" in companies
    assert "Cold" not in companies


def test_stats_counts_by_status(db: Pipeline):
    ids = [db.upsert_lead(_lead(f"C{i}", f"role {i}")) for i in range(3)]
    db.record_qualification(ids[0], Qualification(score=50, deal_usd=1, reasons=[]), email=None)
    db.mark_sent(ids[1])
    db.mark_lost(ids[2], "nope")
    s = db.stats()
    assert s["total"] == 3
    assert s["qualified"] == 1
    assert s["sent"] == 1
    assert s["lost"] == 1


def test_upsert_many_returns_all_ids(db: Pipeline):
    leads = [_lead(f"C{i}", f"role {i}") for i in range(5)]
    ids = db.upsert_many(leads)
    assert len(ids) == 5
    assert len(set(ids)) == 5  # unique
