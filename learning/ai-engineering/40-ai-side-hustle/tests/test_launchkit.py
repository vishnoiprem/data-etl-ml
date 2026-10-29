"""test_launchkit.py — launch kit generation."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from launchkit import (
    _display_title,
    _format_title,
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
    assert "gumroad-description.md" in kit  # plain-text listing for Gumroad
    for path in kit.values():
        assert Path(path).exists()


def test_build_kit_includes_gumroad_description(product_dir: Path):
    """The kit should include a plain-text copy of listing.md for Gumroad's
    description field (which doesn't accept HTML)."""
    kit = build_kit(product_dir)
    assert "gumroad-description.md" in kit
    text = Path(kit["gumroad-description.md"]).read_text()
    assert "Test Product" in text
    assert "$19" in text


def test_build_kit_omits_gumroad_description_when_no_listing(tmp_path: Path):
    """If there's no listing.md, the description file should not be created."""
    d = tmp_path / "products" / "no-listing"
    d.mkdir(parents=True)
    (d / "ebook.md").write_text("# No Listing\n\nbody\n")
    kit = build_kit(d)
    assert "gumroad-description.md" not in kit


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


def test_buy_url_swaps_into_sales_page(product_dir: Path):
    """When --url is provided, the sales page CTA points to the real link."""
    real = "https://example.gumroad.com/l/soc2-playbook"
    out = build_sales_page(product_dir, buy_url=real)
    text = out.read_text()
    assert real in text
    assert 'href="#buy"' not in text


def test_buy_url_swaps_into_tweet_thread(product_dir: Path):
    real = "https://example.gumroad.com/l/soc2-playbook"
    out = build_tweet_thread(product_dir, buy_url=real)
    text = out.read_text()
    assert real in text
    assert "your-gumroad-link" not in text


def test_buy_url_swaps_into_reddit_post(product_dir: Path):
    real = "https://example.gumroad.com/l/soc2-playbook"
    out = build_reddit_post(product_dir, buy_url=real)
    text = out.read_text()
    assert real in text
    assert "your-gumroad-link" not in text


def test_buy_url_does_not_break_email_outreach(product_dir: Path):
    """The cold-email template intentionally has no buy link — adding
    one would read as spam. Passing --url must not corrupt the email."""
    real = "https://example.gumroad.com/l/soc2-playbook"
    out = build_email_outreach(product_dir, buy_url=real)
    text = out.read_text()
    # All three email templates must still be present (guest post,
    # cross-promo, affiliate test) — the count grows as we add
    # new templates, so we just check the floor.
    assert text.count("SUBJECT:") >= 2
    # No accidental insertion of the URL (no placeholder to swap into)
    assert real not in text


def test_no_buy_url_keeps_placeholder(product_dir: Path):
    """Without --url, the placeholder stays so it's obvious what to replace."""
    out = build_tweet_thread(product_dir)
    text = out.read_text()
    assert "your-gumroad-link" in text


# --- _format_title (acronym preservation) ----------------------------

def test_format_title_preserves_acronyms():
    assert _format_title("the soc2 for solo founders playbook") == "The SOC2 For Solo Founders Playbook"
    assert _format_title("hipaa compliance") == "HIPAA Compliance"
    assert _format_title("gdpr and ai governance") == "GDPR And AI Governance"


def test_format_title_handles_punctuation():
    assert _format_title("soc2, hipaa, gdpr, oh my") == "SOC2, HIPAA, GDPR, Oh My"


# --- Bug fix: sales page should not repeat the tagline in the body ---

def test_sales_page_does_not_duplicate_tagline_in_body(product_dir: Path):
    """The lead paragraph (tagline) must not appear twice in the rendered HTML."""
    out = build_sales_page(product_dir)
    text = out.read_text()
    # The fixture listing has "Test hook." as the first non-heading
    # paragraph. It should appear in <p class="tagline"> but NOT also
    # as a duplicate paragraph in the body.
    tagline_count = text.count("Test hook.")
    assert tagline_count == 1, f"tagline 'Test hook.' appeared {tagline_count} times — should be 1"


def test_sales_page_does_not_dump_raw_markdown_before_html(product_dir: Path):
    """The old bug was that the cleaned listing body was rendered BOTH
    raw (as text) AND as HTML. Confirm the raw markdown ('## Heading')
    doesn't appear before the rendered <h2> tag."""
    out = build_sales_page(product_dir)
    text = out.read_text()
    # Find positions of raw markdown and rendered HTML for "Who this is for"
    raw_pos = text.find("## Who this is for")
    html_pos = text.find("<h2>Who this is for</h2>")
    assert raw_pos == -1, f"raw markdown '## Who this is for' found at {raw_pos} — should be stripped"
    assert html_pos > 0, "rendered <h2> not found in output"


# --- _display_title (acronyms in marketing assets) -------------------

def test_display_title_uses_listing_heading(tmp_path: Path):
    """Marketing assets should use the listing's # heading, not the directory name."""
    d = tmp_path / "some-bad-slug"
    d.mkdir()
    (d / "listing.md").write_text("# HIPAA Compliance for Indie Hackers\n\nbody\n")
    assert _display_title(d) == "HIPAA Compliance For Indie Hackers"


def test_display_title_falls_back_to_dirname(tmp_path: Path):
    """No listing.md → use the directory name, smart-titled."""
    d = tmp_path / "soc2-cheatsheet"
    d.mkdir()
    assert _display_title(d) == "SOC2 Cheatsheet"


def test_tweet_thread_uses_smart_title(tmp_path: Path):
    """The 'I wrote The Soc2' bug should not happen — it should be 'I wrote The SOC2'."""
    d = tmp_path / "x"
    d.mkdir()
    (d / "listing.md").write_text("# The SOC2 Playbook\n")
    out = build_tweet_thread(d)
    text = out.read_text()
    assert "I wrote The SOC2" in text
    assert "Soc2" not in text


# --- Bug fix: tweet 1 grammar -----------------------------------------

def test_tweet_thread_no_double_article(product_dir: Path):
    out = build_tweet_thread(product_dir)
    text = out.read_text()
    # The first tweet shouldn't read "I wrote a The XYZ" — that's a broken article.
    first_tweet = text.split("\n\n")[0]
    assert "I wrote a The" not in first_tweet
    # It should still start with "I wrote"
    assert first_tweet.startswith("1/ I wrote ")


def test_build_kit_threads_url_through_every_asset(product_dir: Path):
    real = "https://buy.example.com/x"
    kit = build_kit(product_dir, buy_url=real)
    # Sales page gets the real URL in its CTA
    assert real in Path(kit["sales-page.html"]).read_text()
    # Tweet + reddit have a placeholder that gets swapped
    for asset in ("tweet-thread.txt", "reddit-post.txt"):
        assert real in Path(kit[asset]).read_text(), f"missing in {asset}"
        assert "your-gumroad-link" not in Path(kit[asset]).read_text(), f"placeholder left in {asset}"


# --- per-product URL map ----------------------------------------------

def test_url_map_overrides_global_url(tmp_path: Path):
    """A per-product URL wins; the global --url is the fallback."""
    products = tmp_path / "products"
    (products / "product-a").mkdir(parents=True)
    (products / "product-a" / "ebook.md").write_text("# A\n\nbody\n")
    (products / "product-a" / "listing.md").write_text("# A\n\n**$9**\n")
    (products / "product-b").mkdir(parents=True)
    (products / "product-b" / "ebook.md").write_text("# B\n\nbody\n")
    (products / "product-b" / "listing.md").write_text("# B\n\n**$9**\n")

    url_map = {"product-a": "https://store.example.com/l/specific-a"}
    results = build_all(tmp_path,
                        buy_url="https://store.example.com/l/storefront",
                        url_map=url_map)
    by_name = {r["product"]: r for r in results}

    # product-a got the specific URL, recorded in the result
    assert by_name["product-a"]["url"] == "https://store.example.com/l/specific-a"
    a_thread = Path(by_name["product-a"]["files"]["tweet-thread.txt"]).read_text()
    assert "specific-a" in a_thread
    assert "storefront" not in a_thread

    # product-b fell back to the global --url
    assert by_name["product-b"]["url"] == "https://store.example.com/l/storefront"
    b_thread = Path(by_name["product-b"]["files"]["tweet-thread.txt"]).read_text()
    assert "storefront" in b_thread


def test_url_map_empty_value_keeps_placeholder(tmp_path: Path):
    """An empty string in url_map means 'I haven't published this one yet' — keep the placeholder."""
    products = tmp_path / "products"
    (products / "unpublished").mkdir(parents=True)
    (products / "unpublished" / "ebook.md").write_text("# U\n\nbody\n")
    (products / "unpublished" / "listing.md").write_text("# U\n\n**$9**\n")

    url_map = {"unpublished": ""}  # explicit empty
    results = build_all(tmp_path, buy_url="https://store.example.com/l/x", url_map=url_map)
    thread = Path(results[0]["files"]["tweet-thread.txt"]).read_text()
    # Empty string is falsy → effective URL is None → placeholder stays
    assert "your-gumroad-link" in thread
    assert "store.example.com" not in thread


def test_load_url_map_reads_json(tmp_path: Path):
    import json
    from launchkit import _load_url_map
    p = tmp_path / "urls.json"
    p.write_text(json.dumps({
        "alpha": "https://x.gumroad.com/l/alpha",
        "beta":  "https://x.gumroad.com/l/beta",
    }))
    m = _load_url_map(p)
    assert m == {
        "alpha": "https://x.gumroad.com/l/alpha",
        "beta":  "https://x.gumroad.com/l/beta",
    }


def test_load_url_map_missing_file_returns_empty(tmp_path: Path):
    from launchkit import _load_url_map
    assert _load_url_map(tmp_path / "nope.json") == {}


def test_load_url_map_rejects_non_object(tmp_path: Path):
    import json
    from launchkit import _load_url_map
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(["not", "a", "dict"]))
    import pytest
    with pytest.raises(ValueError, match="expected a JSON object"):
        _load_url_map(p)
