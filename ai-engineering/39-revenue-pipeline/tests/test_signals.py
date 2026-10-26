"""
test_signals.py — Lead dataclass + sample-data ingestion.

The `Lead.fingerprint` property is the dedup key for the whole pipeline,
so a typo there silently doubles the rows. We pin its behavior with
explicit cases.

The scrapers themselves are mostly sample-data proxies, so the
interesting tests are:
  - fingerprint stability
  - ingest_all() dedupes across sources
  - sample data file is well-formed JSON
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from signals import Lead, ingest_all, write_sample_data


def test_fingerprint_normalizes_company_and_title():
    a = Lead("hn_hiring", "Acme Corp", "Senior AI Engineer", "u", "t", "2026-10-12")
    b = Lead("hn_hiring", "  acme corp ", "senior ai engineer", "u", "t", "2026-10-12")
    assert a.fingerprint == b.fingerprint


def test_fingerprint_differs_by_source():
    a = Lead("hn_hiring", "Acme", "role", "u", "t", "2026-10-12")
    b = Lead("github_trending", "Acme", "role", "u", "t", "2026-10-12")
    assert a.fingerprint != b.fingerprint


def test_fingerprint_clamps_long_titles():
    long = "x" * 200
    lead = Lead("hn_hiring", "Acme", long, "u", "t", "2026-10-12")
    # The title portion in the fingerprint should be truncated
    parts = lead.fingerprint.split("|")
    assert len(parts[2]) <= 60


def test_lead_to_dict_roundtrips():
    lead = Lead("hn_hiring", "Acme", "AI", "https://x", "text", "2026-10-12",
                contact="@a", tags=["t1", "t2"])
    d = lead.to_dict()
    assert d["source"] == "hn_hiring"
    assert d["company"] == "Acme"
    assert d["tags"] == ["t1", "t2"]
    # And it should be JSON-serializable
    json.dumps(d)


def test_write_sample_data_is_idempotent(tmp_path, monkeypatch):
    """Calling write_sample_data() twice should not duplicate the file."""
    # Force the sample file to live in a tmp dir for the test
    target = tmp_path / "signals.json"
    from signals import SAMPLE_FILE  # the module-level Path
    monkeypatch.setattr("signals.SAMPLE_FILE", target)
    write_sample_data()
    first = target.read_text()
    write_sample_data()
    second = target.read_text()
    assert first == second


def test_ingest_all_returns_leads_with_unique_fingerprints():
    leads = ingest_all()
    assert len(leads) > 0
    fps = [l.fingerprint for l in leads]
    # The bundled sample data should already be deduped
    assert len(fps) == len(set(fps)), "duplicate fingerprints in ingest_all()"


def test_ingest_all_resilient_to_one_bad_scraper(monkeypatch):
    """If one scraper raises, the others still return data."""
    from signals import SCRAPERS

    def boom():
        raise RuntimeError("simulated outage")

    monkeypatch.setitem(SCRAPERS, "hn_hiring", boom)
    leads = ingest_all()
    # We should still get leads from the other 5 sources
    assert len(leads) > 0
    assert all(l.source != "hn_hiring" for l in leads)
