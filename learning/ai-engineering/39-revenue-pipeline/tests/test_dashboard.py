"""
test_dashboard.py — money-math invariants.

The dashboard is the only thing the consultant looks at every week, so
the math needs to be right. These tests pin down the formulas:

  $$/week closed     ≈ won_usd (over the chosen window)
  Pipeline $         = Σ weighted_usd for non-closed rows
  Conversion rate    = won / (won + lost), undefined when no closes
  Median TTC days    = median(closed_at - first_seen_at) for won rows
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from dashboard import compute, render
from pipeline import Pipeline
from qualifier import Qualification
from signals import Lead


@pytest.fixture
def empty_db(tmp_path) -> Pipeline:
    return Pipeline(tmp_path / "test.db")


def _lead(company: str, **kw) -> Lead:
    return Lead(
        source=kw.get("source", "hn_hiring"),
        company=company,
        title=kw.get("title", "AI engineer"),
        url="https://example.com",
        text=kw.get("text", "AI consulting, budget approved, urgent"),
        posted_at=kw.get("posted_at", "2026-10-01"),
        contact=None,
        tags=[],
    )


def test_empty_db_returns_zero_stats(empty_db: Pipeline):
    data = compute(empty_db)
    assert data["money"]["won_usd"] == 0
    assert data["money"]["pipeline_usd"] == 0
    assert data["rates"]["conversion"] is None
    assert data["rates"]["median_ttc_days"] is None
    assert data["totals"]["leads"] == 0
    assert data["by_source"] == []


def test_won_usd_aggregates_across_rows(empty_db: Pipeline):
    a = empty_db.upsert_lead(_lead("A"))
    b = empty_db.upsert_lead(_lead("B"))
    empty_db.record_qualification(a, Qualification(score=50, deal_usd=5_000, reasons=[]), email=None)
    empty_db.record_qualification(b, Qualification(score=80, deal_usd=10_000, reasons=[]), email=None)
    empty_db.mark_won(a, 5000)
    empty_db.mark_won(b, 8000)  # actually closed at $8k, not $10k
    data = compute(empty_db)
    assert data["money"]["won_usd"] == 13_000
    assert data["money"]["avg_deal_usd"] == 6500


def test_pipeline_usd_sums_weighted_for_open_opps(empty_db: Pipeline):
    a = empty_db.upsert_lead(_lead("A"))
    b = empty_db.upsert_lead(_lead("B"))
    c = empty_db.upsert_lead(_lead("C"))
    empty_db.record_qualification(a, Qualification(score=50, deal_usd=10_000, reasons=[]), email=None)
    empty_db.record_qualification(b, Qualification(score=80, deal_usd=10_000, reasons=[]), email=None)
    empty_db.mark_won(c, 9999)
    empty_db.record_qualification(c, Qualification(score=0, deal_usd=0, reasons=[]), email=None)
    data = compute(empty_db)
    # a: 10_000 * 0.5 = 5_000 ; b: 10_000 * 0.8 = 8_000 ; c: closed → not in pipeline
    assert data["money"]["pipeline_usd"] == 13_000


def test_conversion_rate_is_won_over_closed(empty_db: Pipeline):
    a = empty_db.upsert_lead(_lead("Won"))
    b = empty_db.upsert_lead(_lead("Lost"))
    empty_db.mark_won(a, 1000)
    empty_db.mark_lost(b, "no budget")
    data = compute(empty_db)
    assert data["rates"]["conversion"] == 0.5


def test_conversion_undefined_with_no_closes(empty_db: Pipeline):
    empty_db.upsert_lead(_lead("New"))
    data = compute(empty_db)
    assert data["rates"]["conversion"] is None


def test_median_time_to_cash_uses_first_seen_to_closed(empty_db: Pipeline):
    a = empty_db.upsert_lead(_lead("A"))
    b = empty_db.upsert_lead(_lead("B"))
    # Force first_seen_at to known values so the math is predictable
    for opp_id, seen in [(a, "2026-09-01T00:00:00+00:00"),
                         (b, "2026-09-15T00:00:00+00:00")]:
        with empty_db._conn() as c:
            c.execute("UPDATE opportunities SET first_seen_at=? WHERE id=?",
                      (seen, opp_id))
    # Mark won: a closed 10d later, b closed 20d later
    closed_a = (datetime(2026, 9, 11, tzinfo=timezone.utc)).isoformat()
    closed_b = (datetime(2026, 10, 5, tzinfo=timezone.utc)).isoformat()
    for opp_id, closed in [(a, closed_a), (b, closed_b)]:
        with empty_db._conn() as c:
            c.execute("UPDATE opportunities SET closed_at=? WHERE id=?",
                      (closed, opp_id))
        empty_db.mark_won(opp_id, 1000)  # overwrites closed_at → use prior loop instead
    # ↑ mark_won overwrites closed_at; recompute by setting it back
    with empty_db._conn() as c:
        c.execute("UPDATE opportunities SET closed_at=? WHERE id=?", (closed_a, a))
        c.execute("UPDATE opportunities SET closed_at=? WHERE id=?", (closed_b, b))
    data = compute(empty_db)
    # median of [10, 20] = 15
    assert data["rates"]["median_ttc_days"] == 15


def test_by_source_aggregates_weighted(empty_db: Pipeline):
    a = empty_db.upsert_lead(_lead("A", source="hn_hiring"))
    b = empty_db.upsert_lead(_lead("B", source="hn_hiring"))
    c = empty_db.upsert_lead(_lead("C", source="inbound"))
    empty_db.record_qualification(a, Qualification(score=50, deal_usd=4_000, reasons=[]), email=None)
    empty_db.record_qualification(b, Qualification(score=80, deal_usd=10_000, reasons=[]), email=None)
    empty_db.record_qualification(c, Qualification(score=30, deal_usd=2_000, reasons=[]), email=None)
    data = compute(empty_db)
    by_src = {row["source"]: row for row in data["by_source"]}
    assert by_src["hn_hiring"]["n"] == 2
    assert by_src["hn_hiring"]["weighted"] == 2000 + 8000
    assert by_src["inbound"]["n"] == 1
    assert by_src["inbound"]["weighted"] == int(2000 * 0.3)


def test_top_source_is_highest_weighted(empty_db: Pipeline):
    a = empty_db.upsert_lead(_lead("A", source="hn_hiring"))
    b = empty_db.upsert_lead(_lead("B", source="inbound"))
    empty_db.record_qualification(a, Qualification(score=10, deal_usd=1_000, reasons=[]), email=None)
    empty_db.record_qualification(b, Qualification(score=90, deal_usd=20_000, reasons=[]), email=None)
    data = compute(empty_db)
    assert data["top_source"] is not None
    assert data["top_source"]["source"] == "inbound"


def test_render_contains_expected_sections(empty_db: Pipeline):
    a = empty_db.upsert_lead(_lead("Acme"))
    empty_db.record_qualification(a, Qualification(score=80, deal_usd=10_000, reasons=[]), email=None)
    data = compute(empty_db)
    text = render(data)
    assert "REVENUE PIPELINE" in text
    assert "$ open in pipeline" in text
    assert "By source" in text
    assert "Top opportunities" in text
    assert "Acme" in text
