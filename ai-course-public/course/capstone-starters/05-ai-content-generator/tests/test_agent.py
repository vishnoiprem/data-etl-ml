"""
Tests for the Content Generator
===============================
Run:  pytest tests/
"""

import os
import pytest


# =============================================================================
# UNIT TESTS (no API calls)
# =============================================================================

def test_flesch_score_basic():
    from optimizer import _flesch_reading_ease
    easy = "The cat sat on the mat. The dog ran. I like cats. Dogs are fun. We play."
    hard = "Pneumonoultramicroscopicsilicovolcanoconiosis is a long word."
    assert _flesch_reading_ease(easy) > 60
    assert _flesch_reading_ease(hard) < 50


def test_score_seo_perfect():
    from optimizer import score_seo
    body = "# Best CRM for Startups\n\n" + ("## Section\n\nA keyword appears here. " * 30) + "\n\n## Section 2\n\nMore content. " * 30
    report = score_seo(body, keyword="best CRM for startups", target_words=600)
    assert report["overall_score"] > 50
    assert "keyword_placement" in report["breakdown"]


def test_score_seo_low_keyword():
    from optimizer import score_seo
    body = "Lorem ipsum dolor sit amet. " * 50
    report = score_seo(body, keyword="completely unrelated keyword xyz", target_words=100)
    # Should score poorly on keyword placement
    assert report["breakdown"]["keyword_placement"]["score"] < 10


def test_score_seo_no_headings():
    from optimizer import score_seo
    body = "Just a wall of text. No headings anywhere. " * 50
    report = score_seo(body, keyword="test", target_words=100)
    assert report["breakdown"]["heading_structure"]["score"] == 0


# =============================================================================
# INTEGRATION TESTS (require API key)
# =============================================================================

@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
def test_meta_generation():
    from optimizer import generate_meta
    title, desc, cost = generate_meta(
        topic="How to choose a CRM",
        keyword="best CRM for startups",
        body="# How to choose a CRM\n\nThere are many CRM options for startups. ...",
        openai_api_key=os.environ["OPENAI_API_KEY"],
    )
    assert 30 <= len(title) <= 70
    assert 100 <= len(desc) <= 200
    assert cost > 0
    assert cost < 0.01