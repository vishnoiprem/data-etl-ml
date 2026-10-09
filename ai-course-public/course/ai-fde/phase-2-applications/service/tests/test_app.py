"""
tests/test_app.py — pytest coverage for the PacificFreight Phase 2 service.

Tests (use FastAPI's TestClient — no need to boot uvicorn):
  1. test_health                     — /health returns 200 with n_chunks_loaded
  2. test_draft_known_shipment       — /draft for a known shipment returns a draft
  3. test_draft_extracts_id          — /draft extracts the ID from the email
  4. test_retrieve_top_chunk         — /retrieve ranks the right policy chunk top
  5. test_eval_runs                  — /eval runs without error and returns 4 metrics
  6. test_regression_trips           — /eval with an artificially high baseline
                                       trips the regression check

Run from the service/ directory:
    pytest tests/ -v

Or from the repo root:
    pytest course/ai-fde/phase-2-applications/service/tests/ -v
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Make the service package importable.
import sys
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))

from app import app  # noqa: E402

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def eval_set_path() -> Path:
    return HERE.parent.parent / "shared" / "eval_set.jsonl"


# ---------------------------------------------------------------------------
# 1. /health
# ---------------------------------------------------------------------------
def test_health() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["service"] == "pf-phase2"
    # 7 policy chunks + 15 shipments = 22 chunks
    assert body["n_chunks_loaded"] == 22


# ---------------------------------------------------------------------------
# 2. /draft with an explicit shipment_id
# ---------------------------------------------------------------------------
def test_draft_known_shipment() -> None:
    r = client.post("/draft", json={
        "email": "Hi, can you check on my shipment PF-1003?",
        "shipment_id": "PF-1003",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["shipment_id"] == "PF-1003"
    assert "PF-1003" in body["draft"]
    # Mock LLM should have returned a deterministic reply mentioning customs.
    assert "customs" in body["draft"].lower()
    # Contexts should include the PF-1003 shipment chunk.
    ctx_ids = [c["id"] for c in body["contexts"]]
    assert "shipment:PF-1003" in ctx_ids
    # Provider / cost fields populated.
    assert body["is_mock"] is True
    assert body["cost_usd"] == 0.0


# ---------------------------------------------------------------------------
# 3. /draft extracts the ID when not given
# ---------------------------------------------------------------------------
def test_draft_extracts_id() -> None:
    r = client.post("/draft", json={
        "email": "Where is PF-1001? Should have arrived last week. — Aisha",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["shipment_id"] == "PF-1001"
    # Mock LLM canned reply for PF-1001 mentions Aisha.
    assert "Aisha" in body["draft"]


def test_draft_no_id() -> None:
    r = client.post("/draft", json={
        "email": "Hi, where is my parcel?",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["shipment_id"] is None


# ---------------------------------------------------------------------------
# 4. /retrieve
# ---------------------------------------------------------------------------
def test_retrieve_top_chunk_is_policy() -> None:
    r = client.get("/retrieve", params={"q": "customs duty import held", "k": 3, "source": "policy"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert len(body["chunks"]) > 0
    # Top policy chunk should be the customs-duty / status-specific section.
    assert body["chunks"][0]["source"] == "policy"


def test_retrieve_shipment_source() -> None:
    r = client.get("/retrieve", params={"q": "PF-1003 held at customs", "k": 3, "source": "shipment"})
    assert r.status_code == 200
    body = r.json()
    assert all(c["source"] == "shipment" for c in body["chunks"])
    # Top shipment chunk should be PF-1003 (it has "customs" in the email + id).
    assert body["chunks"][0]["id"] == "shipment:PF-1003"


# ---------------------------------------------------------------------------
# 5. /eval runs without error
# ---------------------------------------------------------------------------
def test_eval_runs(eval_set_path: Path) -> None:
    r = client.post("/eval", json={"set": str(eval_set_path)})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["n_rows"] == 30
    assert body["n_errors"] == 0
    # 4 metrics, all in [0, 1]
    for k in ("faithfulness", "answer_relevance", "context_precision", "context_recall"):
        v = body[k]
        assert 0.0 <= v <= 1.0, f"{k} = {v} not in [0,1]"
    # Markdown report should mention the metric names.
    md = body["report_markdown"]
    assert "faithfulness" in md
    assert "answer_relevance" in md
    assert "context_precision" in md
    assert "context_recall" in md


# ---------------------------------------------------------------------------
# 6. /eval trips regression when baseline is artificially high
# ---------------------------------------------------------------------------
def test_regression_trips(eval_set_path: Path, tmp_path: Path) -> None:
    # Write a baseline that's +0.20 above what we'd realistically get.
    baseline_path = tmp_path / "high_baseline.jsonl"
    baseline_path.write_text(
        "\n".join([
            json.dumps({"metric": "faithfulness", "value": 0.95}),
            json.dumps({"metric": "answer_relevance", "value": 0.50}),
            json.dumps({"metric": "context_precision", "value": 0.99}),
            json.dumps({"metric": "context_recall", "value": 0.95}),
        ]) + "\n"
    )
    r = client.post("/eval", json={
        "set": str(eval_set_path),
        "baseline": str(baseline_path),
        "threshold": 0.05,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["any_regressed"] is True
    # At least 3 of 4 metrics should have tripped.
    regressed = [x for x in body["regressions"] if x["regressed"]]
    assert len(regressed) >= 3
