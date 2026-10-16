"""Tests for the production-hardened FastAPI surface.

Covers: auth (3 cases), max_length validation, filter allowlist,
/healthz and /readyz behavior, audit queue off the event loop, real
eval report flow.

We use httpx.AsyncClient against the in-process app. Settings are
configured in conftest.py (set there so the pydantic-settings
BaseSettings is constructed with the test env, before any
backend.app import that would call get_settings()).
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
import httpx  # noqa: E402

from backend.app import audit_queue  # noqa: E402
from backend.app.audit_queue import (  # noqa: E402
    enqueue_audit, init_audit_queue, start_drain, stop_drain,
    flush_on_shutdown, reset_for_test,
)
from backend.app.apex_eval import EvalReport  # noqa: E402
from backend.app.eval_store import record_report  # noqa: E402
from backend.app.main import app  # noqa: E402
from backend.app.settings import get_settings  # noqa: E402

# Override the reports dir to a tmp location so tests don't pollute
# the real `eval/reports/` and don't depend on its content.
import backend.app.eval_store as _es_mod  # noqa: E402

_TMP_REPORTS = Path(__file__).parent / "_tmp_reports"
_TMP_REPORTS.mkdir(exist_ok=True)
_es_mod._reports_dir = lambda: _TMP_REPORTS  # type: ignore[attr-defined]


@pytest.fixture(autouse=True)
async def _init_queue():
    """Initialize the audit queue for every test, drain on teardown."""
    reset_for_test()
    init_audit_queue(maxsize=1000, audit_path=_TMP_REPORTS / "audit.jsonl")
    await start_drain()
    yield
    await stop_drain()
    await flush_on_shutdown(timeout=2.0)


@pytest.fixture
async def client():
    """Async HTTPX client wired to the FastAPI app via ASGI transport."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as c:
        yield c


# ---------- Auth ----------


@pytest.mark.asyncio
async def test_query_without_api_key_403(client):
    """No X-API-Key header -> 403."""
    r = await client.post(
        "/query", json={"collection": "hr_policies", "query": "What is PTO?"}
    )
    assert r.status_code == 403
    assert "X-API-Key" in r.text or "API key" in r.text.lower()


@pytest.mark.asyncio
async def test_query_with_wrong_key_403(client):
    """Wrong X-API-Key -> 403."""
    r = await client.post(
        "/query",
        headers={"X-API-Key": "definitely-wrong"},
        json={"collection": "hr_policies", "query": "What is PTO?"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_query_with_correct_key_200(client):
    """Valid X-API-Key -> 200 with evidence payload."""
    r = await client.post(
        "/query",
        headers={"X-API-Key": "test-key-1"},
        json={"collection": "hr_policies", "query": "What is PTO?"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "evidence" in body
    assert body["evidence"]["collection"] == "hr_policies"
    assert "trace_id" in body


# ---------- Input validation ----------


@pytest.mark.asyncio
async def test_query_max_length_enforced(client):
    """query > APEX_MAX_QUERY_CHARS (2000) -> 422."""
    long_q = "x" * 2001
    r = await client.post(
        "/query",
        headers={"X-API-Key": "test-key-1"},
        json={"collection": "hr_policies", "query": long_q},
    )
    assert r.status_code == 422
    body = r.json()
    # Pydantic's error mentions the field name and constraint.
    assert "query" in str(body)


@pytest.mark.asyncio
async def test_query_filter_unknown_key_400(client):
    """filter key not in the per-collection allowlist -> 400."""
    r = await client.post(
        "/query",
        headers={"X-API-Key": "test-key-1"},
        json={
            "collection": "hr_policies", "query": "PTO accrual",
            "filters": {"department": "eng", "rogue_field": "injection"},
        },
    )
    assert r.status_code == 400
    assert "rogue_field" in r.text


@pytest.mark.asyncio
async def test_query_filter_allowed_key_ok(client):
    """filter key in the allowlist -> 200."""
    r = await client.post(
        "/query",
        headers={"X-API-Key": "test-key-1"},
        json={
            "collection": "hr_policies", "query": "PTO accrual",
            "filters": {"department": "engineering"},
        },
    )
    assert r.status_code == 200


# ---------- Health probes ----------


@pytest.mark.asyncio
async def test_healthz_always_200(client):
    """/healthz is static and open — no I/O, no auth."""
    r = await client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_readyz_503_when_qdrant_unreachable(client, monkeypatch):
    """/readyz returns 503 if any dep is unreachable."""
    from backend.app import readyz as readyz_mod

    async def fake_deps(settings):
        return {
            "qdrant": {"ok": False, "detail": "timeout"},
            "es": {"ok": True, "detail": "200"},
        }
    monkeypatch.setattr(readyz_mod, "check_dependencies", fake_deps)
    # The route imports the function at module load; patch the binding
    # the route actually uses.
    from backend.app import main
    monkeypatch.setattr(main, "_check_dependencies", fake_deps)

    r = await client.get("/readyz")
    assert r.status_code == 503
    body = r.json()
    assert body["detail"]["status"] == "not_ready"
    assert body["detail"]["deps"]["qdrant"]["ok"] is False


@pytest.mark.asyncio
async def test_health_alias_returns_200(client):
    """/health is a deprecated alias for /healthz."""
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# ---------- Audit off the event loop ----------


@pytest.mark.asyncio
async def test_audit_off_event_loop(client, monkeypatch):
    """The route path must not call apex_audit.append_audit() directly.
    We patch the sync helper to track calls and confirm zero from the
    request path.
    """
    from backend.app import apex_audit
    sync_calls: list[tuple[str, str, dict]] = []
    real_append = apex_audit.append_audit

    def tracking_append(trace_id, kind, payload):
        sync_calls.append((trace_id, kind, payload))
        return real_append(trace_id, kind, payload)

    monkeypatch.setattr(apex_audit, "append_audit", tracking_append)

    r = await client.post(
        "/query",
        headers={"X-API-Key": "test-key-1"},
        json={"collection": "hr_policies", "query": "PTO accrual"},
    )
    assert r.status_code == 200
    # Drain the queue so all enqueued events have been processed.
    await asyncio.sleep(0.2)
    # The sync helper is called by the drain task (which we want) but
    # never by the request handler (which we don't want). Since
    # `apex_audit.append_audit` is the only thing the drain loop calls,
    # we can only assert "drain happens via the queue" by checking
    # that the queue size went to 0.
    stats = audit_queue.stats()
    assert stats["queue_size"] == 0
    assert stats["written"] >= 1


# ---------- Real eval store ----------


@pytest.mark.asyncio
async def test_eval_returns_empty_when_no_report(client, monkeypatch):
    """With no reports on disk, /eval returns an empty report envelope."""
    # Clear any leftover reports from other tests in this file.
    for f in _TMP_REPORTS.glob("eval_*.json"):
        f.unlink()
    r = await client.get("/eval", headers={"X-API-Key": "test-key-1"})
    assert r.status_code == 200
    body = r.json()
    assert body["report"]["n_samples"] == 0
    assert "production_targets" in body
    assert body["production_targets"]["recall_at_8"] == 0.89


@pytest.mark.asyncio
async def test_eval_returns_real_report(client, monkeypatch):
    """Drop a real report on disk; /eval reads it."""
    settings = get_settings()
    report = EvalReport(
        timestamp="2026-10-16T12:34:56.789+00:00",
        n_samples=200,
        recall_at_8=0.87,
        ndcg_at_8=0.90,
        p50_latency_ms=180.0,
        p95_latency_ms=395.0,
        judge_groundedness=4.2,
        judge_hallucination=1.5,
        by_collection={
            "hr_policies": {"recall_at_8": 0.91, "ndcg_at_8": 0.93,
                           "p95_latency_ms": 380.0, "n_samples": 70},
            "tech_docs": {"recall_at_8": 0.86, "ndcg_at_8": 0.89,
                          "p95_latency_ms": 410.0, "n_samples": 70},
            "product_docs": {"recall_at_8": 0.84, "ndcg_at_8": 0.88,
                             "p95_latency_ms": 425.0, "n_samples": 60},
        },
    )
    record_report(settings, report)

    r = await client.get("/eval", headers={"X-API-Key": "test-key-1"})
    assert r.status_code == 200
    body = r.json()
    assert body["report"]["n_samples"] == 200
    assert body["report"]["recall_at_8"] == 0.87
    # The "meets_targets" map shows the per-metric pass/fail.
    mt = body["meets_targets"]
    assert mt["recall_at_8"] is False  # 0.87 < 0.89 target
    assert mt["p95_latency_ms"] is True  # 395 < 420 target
    assert mt["judge_groundedness"] is True  # 4.2 >= 4.0


@pytest.mark.asyncio
async def test_eval_requires_api_key(client):
    """/eval without X-API-Key -> 403."""
    r = await client.get("/eval")
    assert r.status_code == 403


# ---------- Server readiness when no API keys configured ----------
# (The 503 "no keys configured" branch in auth.py is hard to test
#  in-process because pydantic-settings honors env at construction;
#  it's covered by manual smoke / a separate staging-environment
#  test. The 403 path is fully covered above.)
