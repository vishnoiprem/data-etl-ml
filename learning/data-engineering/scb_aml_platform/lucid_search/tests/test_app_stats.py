"""
Tests for the FastAPI app.py — specifically the /stats endpoint.

The /stats endpoint had a real bug where `df.get("risk_band", ...)` was
used on a pandas DataFrame, which doesn't behave like dict.get. The
fix uses `in df.columns` first, then indexes. These tests pin the
correctness of that fix so it doesn't regress.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(HERE))

# Ensure dummy data exists before app loads
from scb_aml_platform.data.dummy.generate_dummy_data import main as _gen  # noqa: E402
_gen()


@pytest.fixture(scope="module")
def client():
    """FastAPI TestClient for the app."""
    from fastapi.testclient import TestClient
    from scb_aml_platform.lucid_search.api.app import app
    return TestClient(app)


def test_stats_returns_total_entities(client):
    r = client.get("/stats")
    assert r.status_code == 200
    data = r.json()
    assert "total_entities" in data
    assert data["total_entities"] > 0


def test_stats_high_risk_count_is_nonnegative_int(client):
    r = client.get("/stats")
    data = r.json()
    assert "high_risk_count" in data
    assert isinstance(data["high_risk_count"], int)
    assert data["high_risk_count"] >= 0


def test_stats_pep_count_is_nonnegative_int(client):
    r = client.get("/stats")
    data = r.json()
    assert "pep_count" in data
    assert isinstance(data["pep_count"], int)
    assert data["pep_count"] >= 0


def test_stats_relationship_edges_is_int(client):
    r = client.get("/stats")
    data = r.json()
    assert "relationship_edges" in data
    assert isinstance(data["relationship_edges"], int)
    assert data["relationship_edges"] >= 0


def test_stats_works_when_only_risk_rating_column_present(monkeypatch):
    """Regression: /stats must work even when the loaded data has
    'risk_rating' (low/medium/high) instead of 'risk_band' (LOW/HIGH).
    The previous bug crashed with KeyError on the case mismatch.
    """
    from fastapi.testclient import TestClient
    from scb_aml_platform.lucid_search.api import app as app_module

    # Patch the engine to return data with risk_rating (not risk_band)
    class FakeEngine:
        entities = pd.DataFrame([
            {"customer_id": "C1", "customer_name": "X", "country_code": "SG",
             "pep_flag": "Y", "risk_rating": "high"},
            {"customer_id": "C2", "customer_name": "Y", "country_code": "HK",
             "pep_flag": "N", "risk_rating": "low"},
        ])
        screening = pd.DataFrame()
        relationships = pd.DataFrame()

    monkeypatch.setattr(app_module, "_engine", FakeEngine())
    client = TestClient(app_module.app)
    r = client.get("/stats")
    assert r.status_code == 200
    data = r.json()
    assert data["high_risk_count"] == 1
    assert data["pep_count"] == 1
