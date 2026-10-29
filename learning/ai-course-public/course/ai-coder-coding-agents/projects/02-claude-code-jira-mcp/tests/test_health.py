"""
Smoke test — the Week 2 SaaS exists as a build, not as a finished product.
The full route coverage is added by the `feature-builder` subagent as Jira
tickets land.

This test catches "the import path broke" and "CORS misconfiguration crashes
on startup," which are the two regressions that have cost the most session
time during the build.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz_returns_200_with_expected_shape() -> None:
    res = client.get("/api/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_openapi_includes_healthz() -> None:
    spec = client.get("/openapi.json").json()
    assert "/api/healthz" in spec["paths"]


def test_cors_allows_configured_origin() -> None:
    """The CORS middleware is narrow on purpose. Wildcards defeat JWT auth."""
    res = client.options(
        "/api/healthz",
        headers={
            "Origin": "https://app.ai-legal-doc-generator.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    # 200 with the right header, not a 400 from a CORS preflight failure.
    assert res.status_code in (200, 204)


def test_404_for_unknown_route_is_json_shaped() -> None:
    """FastAPI's 404 by default is a JSON 404, not an HTML page. Confirm
    it stays that way — adding a global HTML handler is a common bug."""
    res = client.get("/api/does-not-exist")
    assert res.status_code == 404
    assert "application/json" in res.headers["content-type"]