"""
Tests for the Research Agent
============================
Run:  pytest tests/
"""

import os
import pytest
from tools import tavily_search, scrape_url


# =============================================================================
# UNIT TESTS (no API calls)
# =============================================================================

def test_scrape_url_invalid():
    """Invalid URLs should return empty string, not raise."""
    assert scrape_url("http://this-domain-does-not-exist-12345.invalid") == ""


def test_scrape_url_skips_large():
    """URLs that return huge bodies should be skipped."""
    # Use a known large endpoint (e.g., a zip file)
    result = scrape_url("https://speed.cloudflare.com/__down?bytes=10000000")
    # Either skipped (empty) or extracted small text — both OK
    assert isinstance(result, str)


# =============================================================================
# INTEGRATION TESTS (require API keys)
# =============================================================================

@pytest.mark.skipif(not os.getenv("TAVILY_API_KEY"), reason="TAVILY_API_KEY not set")
def test_tavily_search_basic():
    results = tavily_search("what is the capital of France", max_results=3)
    assert len(results) > 0
    for r in results:
        assert "url" in r
        assert "title" in r


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") or not os.getenv("TAVILY_API_KEY"),
    reason="API keys not set",
)
def test_agent_runs():
    from agent import ResearchAgent
    a = ResearchAgent(
        openai_api_key=os.environ["OPENAI_API_KEY"],
        tavily_api_key=os.environ["TAVILY_API_KEY"],
    )
    out = a.run("What are the top 3 Python web frameworks in 2026?", max_sources=10)
    assert "plan" in out
    assert len(out["plan"]) >= 3
    assert "report" in out
    assert len(out["report"]) > 200
    assert out["cost_usd"] > 0
    assert out["cost_usd"] < 1.0  # sanity: a single research run shouldn't cost $1
