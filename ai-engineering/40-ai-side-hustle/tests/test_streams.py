"""test_streams.py — end-to-end of each stream with the StubRouter."""

from __future__ import annotations

from pathlib import Path

import pytest

from ledger import Ledger
from router import StubRouter
from stream_product import Product, run as run_product
from stream_saas import SaaSIdea, run as run_saas
from stream_seo import Keyword, run as run_seo


@pytest.fixture
def out_dir(tmp_path: Path) -> Path:
    d = tmp_path / "output"
    d.mkdir()
    return d


@pytest.fixture
def ledger(tmp_path: Path) -> Ledger:
    return Ledger(tmp_path / "test.db")


def test_seo_run_publishes_articles_and_records_ledger(
    out_dir: Path, ledger: Ledger
):
    res = run_seo("ai agents", StubRouter(), ledger, out_dir, top=2)
    assert res["discovered"] >= 5
    assert res["published"] == 2
    # Articles exist on disk
    articles = list((out_dir / "articles").glob("*.md"))
    assert len(articles) == 2
    # Each has front-matter
    body = articles[0].read_text()
    assert body.startswith("---\n")
    assert "ai agents" in body.lower() or "ai-agents" in body.lower()
    # Ledger got 2 SEO entries
    assert ledger.total("seo") > 0
    assert ledger.units_total("seo") == 2


def test_seo_run_no_record_keeps_ledger_empty(out_dir: Path, ledger: Ledger):
    run_seo("ai agents", StubRouter(), ledger, out_dir, top=1, record_projected=False)
    assert ledger.total() == 0
    # but the article is still on disk
    assert len(list((out_dir / "articles").glob("*.md"))) == 1


def test_saas_run_scaffolds_repo_and_lands_a_listing(
    out_dir: Path, ledger: Ledger
):
    res = run_saas("indie devs", StubRouter(), ledger, out_dir, top=1)
    assert res["ideas"] >= 1
    assert len(res["built"]) == 1
    idea = res["built"][0]
    repo = out_dir / "saas"
    assert repo.exists()
    # Standard files
    for name in ("README.md", "app.py", "requirements.txt", "Dockerfile", "pricing.md", "landing.md"):
        assert (next(iter(repo.iterdir())) / name).exists(), f"missing {name}"
    # Ledger got 1 SaaS entry for 10 customers × price
    assert ledger.total("saas") > 0
    assert ledger.units_total("saas") == 10


def test_product_run_creates_one_file_per_product(
    out_dir: Path, ledger: Ledger
):
    res = run_product("soc2", StubRouter(), ledger, out_dir)
    assert len(res["products"]) == 3
    products_dir = out_dir / "products"
    assert products_dir.exists()
    # Each product has a folder with a listing.md at minimum
    for sub in products_dir.iterdir():
        assert (sub / "listing.md").exists()
    # Ledger has 3 entries, one per product
    assert ledger.units_total("product") == 30  # 3 products × 10 units each


def test_keyword_projection_is_volume_times_ctr_times_rpc():
    kw = Keyword(keyword="x", volume=1000, difficulty=20, intent="info", cpc_usd=2.0)
    # 1000 * 0.05 * 0.50 = 25
    assert kw.expected_monthly_usd == 25.0


def test_saas_idea_projection_is_10_customers_times_price():
    idea = SaaSIdea(name="X", one_liner="", mvp_weeks=1, tam_usd=0, price_usd=29, moat="")
    assert idea.expected_month1_usd == 290.0


def test_product_projection_is_10_sales_times_price():
    p = Product(title="X", format="ebook", price_usd=19, page_count=20, hook="")
    assert p.expected_month1_usd == 190.0


def test_product_slug_is_filename_safe():
    p = Product(title="The 90-Day AI Playbook!!!", format="ebook",
                 price_usd=19, page_count=20, hook="")
    assert "/" not in p.slug
    assert " " not in p.slug
    assert p.slug  # non-empty


def test_seo_resilient_to_router_exception(out_dir: Path, ledger: Ledger):
    class BoomRouter:
        name = "boom"
        def complete(self, *a, **kw): raise RuntimeError("nope")
        def json(self, *a, **kw): raise RuntimeError("nope")
    # Should not raise; should still record nothing
    run_seo("x", BoomRouter(), ledger, out_dir, top=2)  # type: ignore[arg-type]
    assert ledger.total() == 0
