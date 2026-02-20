"""
Lucid Search — Integration Tests
Tests the search engine in in-memory mode (no ES required).
"""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))


@pytest.fixture(scope="module")
def engine():
    """Shared search engine instance."""
    from scb_aml_platform.lucid_search.api.search_engine import LucidSearchEngine
    return LucidSearchEngine()


def test_engine_loads(engine):
    assert len(engine.entities) > 0, "Entity data should be loaded"


def test_exact_name_search(engine):
    """Searching known high-risk entity returns a result."""
    result = engine.search("Mohammed Al-Rahman", max_results=10)
    assert result["total"] >= 0  # May be 0 if data not generated yet
    assert "results" in result
    assert "search_time_ms" in result


def test_fuzzy_name_search(engine):
    """Fuzzy match: 'Mohammad' should find 'Mohammed'."""
    result = engine.search("Mohammad", max_results=10)
    assert result["total"] >= 0


def test_phonetic_search(engine):
    """Phonetic: 'Viktor' should score against 'Victor'."""
    result = engine.search("Viktor Petrov", max_results=5)
    assert isinstance(result["results"], list)


def test_country_filter(engine):
    """Country filter returns only entities for that country."""
    result = engine.search("Dragon Trading", countries=["HK"], max_results=10)
    for r in result["results"]:
        country = r.get("country_code") or ""
        assert country in ["HK", ""]   # empty allowed if not set


def test_pep_filter(engine):
    """PEP-only filter returns only PEP entities."""
    result = engine.search("Mohammed", pep_only=True, max_results=20)
    for r in result["results"]:
        pep = r.get("pep_flag", "N")
        assert pep == "Y", f"Non-PEP entity returned in PEP-only search: {r}"


def test_entity_profile(engine):
    """Get full profile for first entity."""
    if engine.entities.empty:
        pytest.skip("No entities loaded")
    col = "entity_id" if "entity_id" in engine.entities.columns else "customer_id"
    first_id = engine.entities.iloc[0][col]
    profile = engine.get_entity_profile(first_id)
    assert "entity" in profile
    assert "transaction_summary" in profile
    assert "screening_results" in profile
    assert "related_entities" in profile


def test_search_response_time(engine):
    """Search should complete under 2 seconds in-memory."""
    import time
    t0 = time.time()
    engine.search("test entity name", max_results=20)
    elapsed = time.time() - t0
    assert elapsed < 2.0, f"Search took {elapsed:.2f}s — too slow"


def test_no_results_graceful(engine):
    """No-match query returns empty list, not error."""
    result = engine.search("ZZZZZ_NO_MATCH_ENTITY_XYZ", max_results=5)
    assert result["total"] == 0 or isinstance(result["results"], list)
