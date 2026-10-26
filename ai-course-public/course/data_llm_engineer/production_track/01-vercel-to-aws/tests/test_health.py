"""
Smoke tests for the production backend.

This suite is small on purpose — it's the wire test, not the eval. The bulk
of the test surface (token streaming correctness, auth, billing gates) lives
in later weeks of the production track.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

with patch.dict(
    "os.environ",
    {"OPENAI_API_KEY": "test-key-not-a-real-secret"},
    clear=False,
):
    with patch("app.main.AsyncOpenAI") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        from app.main import app

client = TestClient(app)


def test_healthz_returns_200() -> None:
    """Cheap liveness probe — must always pass regardless of OpenAI state."""
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_openapi_lists_chat_endpoint() -> None:
    """Spec drift kills CI. Confirm /chat is registered at import time."""
    spec = client.get("/openapi.json").json()
    assert "/chat" in spec["paths"]
    assert "/healthz" in spec["paths"]


def test_chat_rejects_empty_messages() -> None:
    """An empty messages array must fail validation, not call OpenAI."""
    res = client.post("/chat", json={"messages": []})
    assert res.status_code == 422


def test_cors_allows_configured_origin_only() -> None:
    """CORS preflight from an unknown origin must NOT echo back.

    This is the case that catches the most common misconfiguration: a
    wildcard `allow_origins=["*"]` with `allow_credentials=True`, which the
    CORS spec forbids and which defeats cookie-based Clerk auth.
    """
    res = client.options(
        "/chat",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    # Either no Access-Control-Allow-Origin echoed (good) or 403 — but never
    # the wildcard + credentials misconfiguration.
    if "Access-Control-Allow-Origin" in res.headers:
        echoed = res.headers["Access-Control-Allow-Origin"]
        assert echoed != "*", "CORS misconfiguration: wildcard with credentials"
        assert echoed != "https://evil.example", "CORS misconfiguration: reflected origin"