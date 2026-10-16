"""End-to-end smoke test with a single document.

Goal: prove the entire request flow works for one doc, not the
hundred-million-doc case. We bypass Qdrant/ES (they're not running)
and inject a single doc directly into the answerer. This exercises:
  - Settings load
  - Auth (X-API-Key)
  - CORS preflight
  - Filter validation
  - Input length limit
  - /query → hybrid_search → rerank → grounded_answer
  - Audit enqueue + drain
  - /traces reads the audit log back
  - /eval returns the empty envelope

The retriever still returns its synthetic `*-vec-NNNN` / `*-bm25-NNNN`
doc IDs (we don't replace that here — that's B8 in the backlog).
This test asserts the FULL HTTP-level contract works for a
representative call: an hr_policies question, an allowed filter, a
200 response, the answer references the docs that were returned,
the trace_id is in the audit log, and the response envelope is
correct.

Env is configured in conftest.py (so the pydantic-settings
BaseSettings sees `APEX_API_KEYS=test-key-1,test-key-2` before
any backend.app import).
"""
from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

import pytest
import httpx  # noqa: E402

from backend.app import audit_queue  # noqa: E402
from backend.app.audit_queue import (  # noqa: E402
    init_audit_queue, start_drain, stop_drain, flush_on_shutdown, reset_for_test,
)
from backend.app.main import app  # noqa: E402
from backend.app.apex_audit import recent_traces  # noqa: E402

# Use one of the keys set in conftest.py.
TEST_KEY = "test-key-1"

_TMP_AUDIT = Path(__file__).parent / "_tmp_reports" / "one_doc_audit.jsonl"
_TMP_AUDIT.parent.mkdir(parents=True, exist_ok=True)
_TMP_AUDIT.write_text("")  # start clean


@pytest.fixture(autouse=True)
async def _init_queue():
    """Reset and start the audit queue around every test."""
    reset_for_test()
    # Wipe the audit log so each test starts clean.
    _TMP_AUDIT.write_text("")
    init_audit_queue(maxsize=1000, audit_path=_TMP_AUDIT)
    await start_drain()
    yield
    await stop_drain()
    await flush_on_shutdown(timeout=2.0)


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------- The one-doc flow ----------


async def test_full_flow_one_doc(client):
    """The full HTTP-level contract for a single query.

    1. /healthz returns 200 (liveness, no auth)
    2. /query without X-API-Key returns 403
    3. /query with X-API-Key returns 200 with an evidence envelope
    4. The answer references the doc IDs that were returned by the retriever
    5. The audit log captures the event (after drain)
    6. /traces reads the audit log back via recent_traces()
    7. /eval returns 200 with the empty envelope (no harness run yet)
    8. Filter validation: an allowed filter is accepted, an unknown
       filter is rejected with 400
    """
    # 1. liveness
    r = await client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

    # 2. no auth
    r = await client.post(
        "/query",
        json={"collection": "hr_policies", "query": "How much PTO do I get?"},
    )
    assert r.status_code == 403

    # 3. with auth
    r = await client.post(
        "/query",
        headers={"X-API-Key": TEST_KEY},
        json={"collection": "hr_policies", "query": "How much PTO do I get?"},
    )
    assert r.status_code == 200, r.text
    body = r.json()

    # 4. evidence envelope shape
    ev = body["evidence"]
    assert ev["collection"] == "hr_policies"
    assert ev["query"] == "How much PTO do I get?"
    # Grounding contract: every answer line ends in a citation, every
    # citation resolves to a span, and the answer is real corpus text.
    answer = ev["answer"]
    n_returned = len(ev["spans"])
    assert n_returned > 0
    for line in answer.splitlines():
        cites = [int(c) for c in re.findall(r"\[doc_(\d+)\]", line)]
        assert cites, f"uncited line: {line!r}"
        assert all(1 <= c <= n_returned for c in cites), (cites, n_returned)
    assert "20 days" in answer  # PTO accrual from the HR corpus
    for span in ev["spans"]:
        assert span["doc_id"].startswith("hr-"), span["doc_id"]
        assert span["score"] > 0
    # Not refused.
    assert ev["refused"] is False
    assert ev["refusal_reason"] is None
    # Timing envelope has the 4 phases.
    assert set(body["timing_ms"].keys()) == {"hybrid_ms", "rerank_ms", "answer_ms", "total_ms"}

    # 5. trace_id is a UUID; audit log captured it (after drain).
    trace_id = body["trace_id"]
    assert len(trace_id) == 36  # uuid4 hex
    # Drain the queue so the audit log file is fully written.
    await asyncio.sleep(0.3)
    stats = audit_queue.stats()
    assert stats["written"] >= 1, f"audit drain didn't write anything: {stats}"
    # The audit file should contain a JSON line with this trace_id.
    lines = [json.loads(line) for line in _TMP_AUDIT.read_text().splitlines() if line]
    matching = [e for e in lines if e.get("trace_id") == trace_id]
    assert matching, f"trace {trace_id} not in audit log: {lines!r}"
    audit_event = matching[0]
    assert audit_event["kind"] == "query"
    assert audit_event["payload"]["collection"] == "hr_policies"
    assert audit_event["payload"]["actor_prefix"].startswith("test-k")  # 6-char prefix

    # 6. /traces reads the audit log back.
    day = audit_event["ts"][:10]
    r = await client.get(
        f"/traces?day={day}",
        headers={"X-API-Key": TEST_KEY},
    )
    assert r.status_code == 200
    rows = r.json()["traces"]
    our_row = next((row for row in rows if row["trace_id"] == trace_id), None)
    assert our_row is not None, f"trace {trace_id} not in /traces response: {rows!r}"
    assert our_row["collection"] == "hr_policies"
    assert our_row["query"] == "How much PTO do I get?"
    assert our_row["refused"] is False

    # 7. /eval returns 200 with a report envelope (may be empty if no
    # harness has run, or contain a real report from a prior run).
    r = await client.get("/eval", headers={"X-API-Key": TEST_KEY})
    assert r.status_code == 200
    body = r.json()
    # The envelope shape is stable: `report` + `production_targets` + `meets_targets`.
    assert "report" in body
    assert "production_targets" in body
    assert "meets_targets" in body
    assert body["production_targets"]["recall_at_8"] == 0.89
    # n_samples is 0 (no reports) or > 0 (a previous run left one).
    n = body["report"]["n_samples"]
    assert n >= 0
    if n == 0:
        assert body["meets_targets"] == {}

    # 8. filter validation: allowed key passes, unknown key fails.
    r = await client.post(
        "/query",
        headers={"X-API-Key": TEST_KEY},
        json={
            "collection": "hr_policies",
            "query": "PTO accrual by department",
            "filters": {"department": "engineering"},
        },
    )
    assert r.status_code == 200, r.text
    r = await client.post(
        "/query",
        headers={"X-API-Key": TEST_KEY},
        json={
            "collection": "hr_policies",
            "query": "PTO accrual",
            "filters": {"not_a_real_filter": "x"},
        },
    )
    assert r.status_code == 400
    assert "not_a_real_filter" in r.text


async def test_input_length_limit(client):
    """A 2001-char query is rejected with 422."""
    r = await client.post(
        "/query",
        headers={"X-API-Key": TEST_KEY},
        json={"collection": "hr_policies", "query": "x" * 2001},
    )
    assert r.status_code == 422


async def test_cors_preflight(client):
    """CORS preflight (OPTIONS) for the frontend origin returns the
    correct Access-Control-Allow-Origin header."""
    r = await client.options(
        "/query",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-API-Key",
        },
    )
    assert r.status_code in (200, 204)
    # CORS middleware echoes the origin back.
    assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"


async def test_feedback_round_trip(client):
    """A /feedback call lands in the audit log and the response is 200."""
    r = await client.post(
        "/feedback",
        headers={"X-API-Key": TEST_KEY},
        json={"trace_id": "trace-test-123", "rating": 5, "comment": "good"},
    )
    assert r.status_code == 200
    assert r.json() == {"ok": True, "trace_id": "trace-test-123"}
    # Drain and verify the feedback event landed in the audit log.
    await asyncio.sleep(0.3)
    lines = [json.loads(line) for line in _TMP_AUDIT.read_text().splitlines() if line]
    feedback = [e for e in lines if e.get("kind") == "feedback"
                and e.get("trace_id") == "trace-test-123"]
    assert feedback, f"feedback event not in audit log: {lines!r}"
    assert feedback[0]["payload"]["rating"] == 5
    assert feedback[0]["payload"]["comment"] == "good"
    assert feedback[0]["payload"]["actor_prefix"].startswith("test-k")
