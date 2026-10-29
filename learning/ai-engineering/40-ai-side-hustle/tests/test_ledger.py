"""test_ledger.py — SQLite revenue ledger."""

from __future__ import annotations

from pathlib import Path

import pytest

from ledger import VALID_STREAMS, Ledger


@pytest.fixture
def db(tmp_path: Path) -> Ledger:
    return Ledger(tmp_path / "test.db")


def test_record_inserts_row(db: Ledger):
    rid = db.record("seo", amount_usd=10.0, units=1, source="x", note="hi")
    assert rid > 0
    assert db.total() == 10.0


def test_record_validates_stream(db: Ledger):
    with pytest.raises(ValueError):
        db.record("nope", 1.0)


def test_record_rejects_negative_amount(db: Ledger):
    with pytest.raises(ValueError):
        db.record("seo", -1.0)
    with pytest.raises(ValueError):
        db.record("seo", 1.0, units=-1)


def test_total_filters_by_stream(db: Ledger):
    db.record("seo", 100)
    db.record("saas", 200)
    db.record("product", 300)
    assert db.total() == 600
    assert db.total("seo") == 100
    assert db.total("saas") == 200
    assert db.total("product") == 300


def test_units_total_per_stream(db: Ledger):
    db.record("seo", 5, units=2)
    db.record("seo", 5, units=3)
    db.record("saas", 99, units=1)
    assert db.units_total("seo") == 5
    assert db.units_total("saas") == 1


def test_by_stream_groups_correctly(db: Ledger):
    db.record("seo", 100)
    db.record("seo", 50)
    db.record("saas", 200)
    out = {r["stream"]: r for r in db.by_stream()}
    assert out["seo"]["usd"] == 150
    assert out["seo"]["events"] == 2
    assert out["saas"]["usd"] == 200


def test_by_stream_orders_by_revenue_desc(db: Ledger):
    db.record("seo", 100)
    db.record("saas", 500)
    db.record("product", 250)
    rows = db.by_stream()
    assert [r["stream"] for r in rows] == ["saas", "product", "seo"]


def test_stats_reports_per_stream_totals_and_best(db: Ledger):
    db.record("seo", 100)
    db.record("saas", 50)
    db.record("product", 200)
    s = db.stats()
    assert s["total_usd"] == 350
    assert s["seo_usd"] == 100
    assert s["saas_usd"] == 50
    assert s["product_usd"] == 200
    assert s["best_stream"] == "product"


def test_stats_best_stream_none_when_empty(db: Ledger):
    assert db.stats()["best_stream"] is None


def test_by_day_returns_daily_buckets(db: Ledger):
    db.record("seo", 10, occurred_at="2026-10-10T12:00:00+00:00")
    db.record("seo", 20, occurred_at="2026-10-10T18:00:00+00:00")
    db.record("saas", 5, occurred_at="2026-10-11T09:00:00+00:00")
    rows = db.by_day(days=30)
    by_day = {r["day"]: r for r in rows}
    assert by_day["2026-10-10"]["usd"] == 30
    assert by_day["2026-10-10"]["units"] == 2
    assert by_day["2026-10-11"]["usd"] == 5


def test_by_day_filters_by_stream(db: Ledger):
    db.record("seo", 10, occurred_at="2026-10-10T12:00:00+00:00")
    db.record("saas", 99, occurred_at="2026-10-10T12:00:00+00:00")
    rows = db.by_day(stream="seo", days=30)
    assert len(rows) == 1
    assert rows[0]["usd"] == 10


def test_valid_streams_constant_is_complete():
    assert set(VALID_STREAMS) == {"seo", "saas", "product", "merch"}
