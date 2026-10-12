"""test_dashboard.py — dashboard math + rendering."""

from __future__ import annotations

from pathlib import Path

import pytest

from dashboard import compute, render
from ledger import Ledger


@pytest.fixture
def ledger(tmp_path: Path) -> Ledger:
    return Ledger(tmp_path / "test.db")


def test_empty_ledger_returns_zeros(ledger: Ledger):
    data = compute(ledger)
    assert data["totals"]["usd"] == 0
    assert data["totals"]["events"] == 0
    assert data["best_stream"] is None
    assert data["by_stream"] == {}
    assert data["best_day"] is None
    assert data["worst_day"] is None
    assert data["avg_per_active_day"] == 0.0
    assert data["avg_overall"] == 0.0


def test_compute_aggregates_per_stream(ledger: Ledger):
    ledger.record("seo", 100, units=2)
    ledger.record("seo", 50)
    ledger.record("saas", 200, units=1)
    ledger.record("product", 30, units=3)
    ledger.record("merch", 25, units=2)
    data = compute(ledger)
    assert data["totals"]["usd"] == 405
    assert data["by_stream"]["seo"]["usd"] == 150
    assert data["by_stream"]["saas"]["usd"] == 200
    assert data["by_stream"]["product"]["usd"] == 30
    assert data["by_stream"]["merch"]["usd"] == 25
    assert data["best_stream"] == "saas"


def test_compute_identifies_best_and_worst_day(ledger: Ledger):
    ledger.record("seo", 10, occurred_at="2026-10-10T12:00:00+00:00")
    ledger.record("saas", 99, occurred_at="2026-10-11T12:00:00+00:00")
    ledger.record("product", 30, occurred_at="2026-10-12T12:00:00+00:00")
    data = compute(ledger)
    assert data["best_day"]["day"] == "2026-10-11"
    assert data["worst_day"]["day"] == "2026-10-10"


def test_compute_avg_per_active_day_excludes_zero_days(ledger: Ledger):
    ledger.record("seo", 100, occurred_at="2026-10-10T12:00:00+00:00")
    data = compute(ledger)
    # One active day, so per-active == total
    assert data["avg_per_active_day"] == 100
    assert data["avg_overall"] < 100  # overall is total / 14


def test_render_contains_headers_and_section_labels(ledger: Ledger):
    ledger.record("seo", 100)
    ledger.record("saas", 50)
    text = render(compute(ledger))
    assert "AI SIDE HUSTLE" in text
    assert "REVENUE DASHBOARD" in text
    assert "By stream" in text
    assert "Daily revenue" in text
    assert "Best day" in text
    assert "Worst day" in text
    assert "Avg $" in text
    assert "seo" in text
    assert "saas" in text


def test_render_handles_empty_ledger(ledger: Ledger):
    text = render(compute(ledger))
    assert "no revenue yet" in text


def test_daily_buckets_show_up_in_render(ledger: Ledger):
    ledger.record("seo", 10, occurred_at="2026-10-10T12:00:00+00:00")
    text = render(compute(ledger))
    assert "2026-10-10" in text


def test_render_includes_sparkline(ledger: Ledger):
    ledger.record("seo", 10, occurred_at="2026-10-10T12:00:00+00:00")
    ledger.record("saas", 25, occurred_at="2026-10-12T12:00:00+00:00")
    text = render(compute(ledger))
    assert "sparkline" in text
