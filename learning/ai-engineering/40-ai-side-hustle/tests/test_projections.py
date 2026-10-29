"""test_projections.py — calibrated revenue projection model."""

from __future__ import annotations

from projections import (
    project_product,
    project_saas,
    project_seo_article,
    summarize,
)


def test_seo_projection_increases_with_volume():
    low = project_seo_article(volume=100, difficulty=20, cpc_usd=2.0)
    high = project_seo_article(volume=10_000, difficulty=20, cpc_usd=2.0)
    assert high.base > low.base * 50  # ~100x volume → ~100x revenue


def test_seo_projection_decreases_with_difficulty():
    easy = project_seo_article(volume=1000, difficulty=10, cpc_usd=2.0)
    hard = project_seo_article(volume=1000, difficulty=80, cpc_usd=2.0)
    assert easy.base > hard.base


def test_seo_projection_increases_with_cpc():
    cheap = project_seo_article(volume=1000, difficulty=20, cpc_usd=0.5)
    pricey = project_seo_article(volume=1000, difficulty=20, cpc_usd=10.0)
    assert pricey.base > cheap.base * 5


def test_seo_projection_returns_pessimistic_less_than_base_less_than_optimistic():
    p = project_seo_article(volume=1000, difficulty=30, cpc_usd=3.0)
    assert p.pessimistic <= p.base <= p.optimistic
    assert p.pessimistic > 0


def test_seo_projection_confidence_label_present():
    p = project_seo_article(volume=1000, difficulty=30, cpc_usd=3.0)
    assert p.confidence in ("high", "medium", "low", "speculative")


def test_saas_projection_zero_when_no_visitors():
    p = project_saas(price_usd=29, mvp_weeks=1, tam_usd=0, launch_visitors=0)
    assert p.base == 0


def test_saas_projection_scales_with_visitors():
    p1 = project_saas(19, 1, 0, launch_visitors=100)
    p2 = project_saas(19, 1, 0, launch_visitors=1000)
    assert p2.base > p1.base * 5


def test_saas_projection_penalizes_slow_mvp():
    fast = project_saas(29, 1, 0)
    slow = project_saas(29, 8, 0)
    assert slow.base < fast.base


def test_saas_projection_includes_assumptions_dict():
    p = project_saas(29, 1, 0, launch_visitors=500)
    assert "trial_rate" in p.assumptions
    assert "paying_customers" in p.assumptions
    assert p.assumptions["paying_customers"] > 0


def test_product_projection_increases_with_price():
    cheap = project_product(price_usd=7)
    pricey = project_product(price_usd=49)
    assert pricey.base > cheap.base * 5


def test_product_projection_zero_when_no_impressions():
    p = project_product(price_usd=19, impressions_per_day=0)
    assert p.base == 0


def test_summarize_returns_one_line_string():
    p = project_seo_article(volume=1000, difficulty=30, cpc_usd=3.0)
    line = summarize("seo", p)
    assert "seo" in line
    assert "$" in line
    assert "confidence" in line
