"""test_router.py — StubRouter behavior (no API key needed)."""

from __future__ import annotations

import json
import re

from router import StubRouter, _smart_title


def test_stub_seo_article_mentions_keyword():
    out = StubRouter().complete(
        "Keyword: AI agents\nTitle: Foo",
        system="You are an SEO writer.",
    )
    assert "# " in out
    assert "AI agents" in out
    assert "##" in out  # at least one H2


def test_stub_saas_copy_has_pricing():
    out = StubRouter().complete(
        "Idea: AuditBot",
        system="You are a SaaS copywriter.",
    )
    assert "Pro" in out
    assert "$" in out
    assert "CTA" in out or "Start free" in out


def test_stub_ebook_has_chapters():
    out = StubRouter().complete(
        "Title: The 90-Day Plan",
        system="You are an eBook author.",
    )
    assert "Chapter" in out


def test_stub_keyword_json_returns_expected_shape():
    data = StubRouter().json("Seed: ai agents",
                             schema_hint='{"keywords": [...]}')
    assert "keywords" in data
    assert all("keyword" in k and "volume" in k and "difficulty" in k
               for k in data["keywords"])


def test_stub_idea_json_returns_expected_shape():
    data = StubRouter().json("Niche: indie devs",
                             schema_hint='{"ideas": [...]}')
    assert "ideas" in data
    assert all("name" in i and "price_usd" in i for i in data["ideas"])


def test_stub_product_json_returns_expected_shape():
    data = StubRouter().json("Topic: soc2",
                             schema_hint='{"products": [...]}')
    assert "products" in data
    assert all("title" in p and "format" in p and "price_usd" in p
               for p in data["products"])


def test_stub_seo_routes_by_system_not_prompt():
    """The system prompt is the most reliable signal — even if the
    prompt accidentally contains 'email' or 'outreach', we route by
    what the caller said the system is."""
    r = StubRouter()
    seo_text = r.complete("write a thing about cold email subject lines",
                          system="You are an SEO writer.")
    assert "# " in seo_text  # markdown article
    assert "##" in seo_text


def test_stub_falls_back_to_generic_for_unknown_system():
    out = StubRouter().complete("hello", system="you are something else")
    assert isinstance(out, str)


# --- _smart_title -----------------------------------------------------

def test_smart_title_preserves_acronyms():
    assert _smart_title("soc2 for solo founders") == "SOC2 For Solo Founders"
    assert _smart_title("hipaa compliance for indie hackers") == "HIPAA Compliance For Indie Hackers"
    assert _smart_title("gdpr playbook") == "GDPR Playbook"


def test_smart_title_normal_title():
    assert _smart_title("the short guide") == "The Short Guide"
    assert _smart_title("productivity for founders") == "Productivity For Founders"


def test_smart_title_preserves_punctuation():
    assert _smart_title("soc2, hipaa, gdpr, oh my") == "SOC2, HIPAA, GDPR, Oh My"


def test_stub_product_json_uses_smart_title():
    """The product stub must produce titles with acronyms uppercase."""
    out = StubRouter().json(
        "Topic: soc2 for solo founders",
        schema_hint='{"products": [{"title": str, "format": str, "price_usd": int, "page_count": int, "hook": str}]}',
    )
    products = out["products"]
    titles = [p["title"] for p in products]
    assert any("SOC2" in t for t in titles), f"no SOC2 found in {titles}"
    # And the broken 'Soc2' should not appear
    assert not any("Soc2" in t for t in titles), f"old bad casing in {titles}"
