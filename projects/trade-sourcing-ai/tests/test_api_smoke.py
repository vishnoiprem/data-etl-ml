"""Smoke test for the API endpoints."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

QUOTES_PATH = Path(__file__).resolve().parents[1] / "data" / "quotes.json"


@pytest.fixture(scope="module")
def client():
    from app import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def primary_quotes():
    payload = json.loads(QUOTES_PATH.read_text(encoding="utf-8"))
    return [q for q in payload["quotes"] if q["product"] == "phone case silicone"]


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["documents"] > 0
    assert body["router"] == "stub"


def test_suppliers(client):
    response = client.get("/suppliers")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 10
    scores = [s["composite_score"] for s in body["suppliers"]]
    assert scores == sorted(scores, reverse=True)


def test_search(client):
    response = client.post("/search", json={"query": "fitness band supplier", "top_k": 3})
    assert response.status_code == 200
    body = response.json()
    assert len(body["hits"]) <= 3
    assert body["total_latency_ms"] >= 0


def test_compare_quotes(client, primary_quotes):
    response = client.post(
        "/quotes/compare",
        json={"quotes": primary_quotes, "status_quo_alibaba_id": "goldstar_2010"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["recommended"] is not None
    assert body["decision_id"]
    assert body["value"]["margin_captured_vs_status_quo_usd"] is not None


def test_compare_quotes_rejects_bad_payload(client):
    response = client.post("/quotes/compare", json={"quotes": [{"alibaba_id": "x"}]})
    assert response.status_code == 400


def test_decisions(client):
    response = client.get("/decisions")
    assert response.status_code == 200
    body = response.json()
    assert "decisions" in body
    assert "summary" in body


def test_find_suppliers(client):
    response = client.post("/suppliers/find", json={"product": "phone case silicone"})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["strategy"]["target_fob_usd"] == pytest.approx(0.45)
    assert body["rfq"]["body"]
    assert body["needs_sourcing"] is True


def test_find_suppliers_rejects_an_unknown_product(client):
    response = client.post("/suppliers/find", json={"product": "not a real product"})
    assert response.status_code == 404


def test_supplier_coverage(client):
    response = client.get("/suppliers/coverage")
    assert response.status_code == 200
    body = response.json()
    assert body["total_viable"] > 0
    assert len(body["covered"]) + len(body["needs_sourcing"]) == body["total_viable"]
    # The honest finding: the verified pool reaches very few viable routes.
    assert body["coverage_pct"] < 50.0
