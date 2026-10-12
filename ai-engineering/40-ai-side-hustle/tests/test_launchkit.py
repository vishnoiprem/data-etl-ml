"""test_launchkit.py — launch kit generation."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from launchkit import (
    build_all,
    build_checklist,
    build_email_outreach,
    build_kit,
    build_pdf,
    build_reddit_post,
    build_sales_page,
    build_tweet_thread,
)


@pytest.fixture
def product_dir(tmp_path: Path) -> Path:
    """A fake product directory with the same files our stream_product emits."""
    d = tmp_path / "products" / "the-test-product-playbook"
    d.mkdir(parents=True)
    (d / "ebook.md").write_text(
        "# The Test Product Playbook\n\n"
        "**$19**\n\n"
        "Test hook: a test product for testing things.\n\n"
        "## Who this is for\n\n"
        "Testers. People who test things.\n\n"
        "## Chapter 1 — The Setup\n"
        "Most people overthink the start. Here's the minimum viable version.\n\n"
        "## Chapter 2 — The Work\n"
        "Three habits that compound: write daily, ship weekly, review monthly.\n\n"
        "## Chapter 3 — The Payoff\n"
        "Twelve months from now, you'll be in the top 5% if you actually do the work.\n"
    )
    (d / "listing.md").write_text(
        "# The Test Product Playbook\n\n"
        "**$19**\n\n"
        "Test hook.\n\n"
        "## Who this is for\n\n"
        "Testers. People who test things.\n\n"
        "page_count: 20\n"
    )
    return d


def test_build_pdf_creates_a_pdf_file(product_dir: Path):
    pdf = build_pdf(product_dir)
    assert pdf is not None
    assert pdf.exists()
    assert pdf.suffix == ".pdf"
    # FPDF2 output starts with %PDF
    assert pdf.read_bytes()[:4] == b"%PDF"


def test_build_sales_page_creates_html(product_dir: Path):
    out = build_sales_page(product_dir)
    assert out.exists()
    text = out.read_text()
    assert "<!DOCTYPE html>" in text
    assert "$19" in text
    assert "Buy" in text
    # Title pulled from the listing
    assert "Test Product" in text


def test_build_sales_page_uses_audience_from_listing(product_dir: Path):
    out = build_sales_page(product_dir)
    text = out.read_text()
    assert "Testers" in text or "test things" in text


def test_build_tweet_thread_has_8_tweets(product_dir: Path):
    out = build_tweet_thread(product_dir)
    text = out.read_text()
    tweets = [ln for ln in text.splitlines() if re.match(r"^\d+/", ln)]
    assert len(tweets) == 8


def test_build_reddit_post_is_value_first(product_dir: Path):
    out = build_reddit_post(product_dir)
    text = out.read_text()
    # Reddit post should NOT be a hard sales pitch
    assert "buy now" not in text.lower()
    # Should include a link at the end
    assert "gumroad" in text.lower() or "your-gumroad-link" in text


def test_build_email_outreach_has_two_templates(product_dir: Path):
    out = build_email_outreach(product_dir)
    text = out.read_text()
    assert "SUBJECT:" in text
    assert text.count("SUBJECT:") >= 2


def test_build_checklist_includes_price(product_dir: Path):
    out = build_checklist(product_dir)
    text = out.read_text()
    assert "$19" in text
    assert "Day 1" in text
    assert "Day 30" in text


def test_build_kit_returns_all_files(product_dir: Path):
    kit = build_kit(product_dir)
    assert "deliverable.pdf" in kit
    assert "sales-page.html" in kit
    assert "tweet-thread.txt" in kit
    assert "reddit-post.txt" in kit
    assert "email-outreach.txt" in kit
    assert "launch-checklist.md" in kit
    for path in kit.values():
        assert Path(path).exists()


def test_build_all_processes_every_product(tmp_path: Path):
    products = tmp_path / "products"
    for name in ("a-playbook", "b-bundle", "c-printable"):
        d = products / name
        d.mkdir(parents=True)
        (d / "ebook.md").write_text("# Test\n\nBody\n")
        (d / "listing.md").write_text("# Test\n\n**$9**\n")
    results = build_all(tmp_path)
    assert len(results) == 3
    assert all("files" in r for r in results)


def test_build_all_handles_missing_products_dir(tmp_path: Path):
    results = build_all(tmp_path)
    assert results == []


def test_build_kit_resilient_to_partial_product(tmp_path: Path):
    """A product directory with only some files should still get a kit."""
    d = tmp_path / "products" / "minimal-product"
    d.mkdir(parents=True)
    (d / "ebook.md").write_text("# Minimal\n\n## Body\n\nJust text.\n")
    # No listing.md → should still produce everything
    kit = build_kit(d)
    assert "sales-page.html" in kit
    assert Path(kit["sales-page.html"]).exists()
