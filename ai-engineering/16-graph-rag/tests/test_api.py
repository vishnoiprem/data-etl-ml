"""End-to-end test of the FastAPI app with a fake ClickHouse.

Verifies:
  - /health works
  - /strategies works (open)
  - /auth/login issues a cookie on correct password
  - /auth/login rejects wrong password
  - /auth/me returns the user when cookie is present
  - /auth/me rejects when cookie is missing
  - Protected /eval/summary rejects without cookie
  - Protected /eval/summary works with cookie
  - /auth/logout clears the cookie
  - /auth/register creates a new user

The actual ClickHouse is not required — `tests/_fake_ch.py` provides a
drop-in in-memory shim that the lifespan-managed `ch` global is patched
to point at.

Each test gets a *fresh* TestClient because TestClient shares cookies
across requests — without a reset, a login in one test would leak into
the next, making the "no cookie" assertions return 200 instead of 401.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Force mock mode
os.environ["LLM_MODE"] = "mock"
os.environ.setdefault("ANTHROPIC_API_KEY", "")
# Important: pin a JWT secret so the test is deterministic
os.environ["JWT_SECRET"] = "test-secret-do-not-use-in-prod"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient

from api.app import main as api_main
from _fake_ch import FakeCHClient


@pytest.fixture
def fake_ch():
    """Return a fresh in-memory ClickHouse shim per test."""
    return FakeCHClient()


@pytest.fixture
def client(fake_ch):
    """Return a fresh TestClient per test, with the lifespan-managed ch
    global pointed at a fresh fake.  This guarantees no cookie leakage
    between tests.

    NOTE: We deliberately do NOT use the TestClient as a context manager,
    because that triggers FastAPI's lifespan handler, which tries to
    connect to a real ClickHouse.  We patch `api_main.ch` directly so
    the routes pick up the fake without any network I/O.
    """
    api_main.ch = fake_ch  # type: ignore[attr-defined]
    c = TestClient(api_main.app)
    yield c


def test_health(client) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_strategies_is_open(client) -> None:
    r = client.get("/strategies")
    assert r.status_code == 200
    assert "vector" in r.json()["strategies"]


def test_eval_summary_requires_auth(client) -> None:
    r = client.get("/eval/summary")
    assert r.status_code == 401
    assert "Not authenticated" in r.text


def test_login_rejects_wrong_password(client, fake_ch) -> None:
    from api.app.auth import register_user
    register_user(fake_ch, "alice", "secret123", "Alice", "user")
    r = client.post("/auth/login", json={"username": "alice", "password": "wrong"})
    assert r.status_code == 401
    assert "Invalid" in r.json()["detail"]


def test_login_rejects_unknown_user(client) -> None:
    r = client.post("/auth/login", json={"username": "ghost", "password": "anything"})
    assert r.status_code == 401


def test_full_auth_flow(client, fake_ch) -> None:
    from api.app.auth import register_user
    register_user(fake_ch, "alice", "secret123", "Alice", "user")

    # 1. Login with correct creds — get a cookie
    r = client.post("/auth/login", json={"username": "alice", "password": "secret123"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["username"] == "alice"
    assert body["display_name"] == "Alice"
    assert body["role"] == "user"
    assert "grag_session" in r.cookies
    cookie = r.cookies["grag_session"]

    # 2. /auth/me works with the cookie
    r2 = client.get("/auth/me", cookies={"grag_session": cookie})
    assert r2.status_code == 200
    assert r2.json()["username"] == "alice"

    # 3. /auth/me fails without the cookie — use a *fresh* client so the
    #    cookie jar from step 1 doesn't leak in.  TestClient shares cookies
    #    across requests, and `cookies={}` doesn't clear them.
    fresh = TestClient(api_main.app)
    api_main.ch = fake_ch  # type: ignore[attr-defined]
    r3 = fresh.get("/auth/me")
    assert r3.status_code == 401

    # 4. /eval/summary fails without the cookie
    r4 = fresh.get("/eval/summary")
    assert r4.status_code == 401

    # 5. /eval/summary works with the cookie
    r5 = fresh.get("/eval/summary", cookies={"grag_session": cookie})
    assert r5.status_code == 200
    assert r5.json() == {"rows": []}  # empty ClickHouse is fine

    # 6. Logout
    r6 = fresh.post("/auth/logout", cookies={"grag_session": cookie})
    assert r6.status_code == 200

    # 7. After logout, cookie is cleared
    r7 = fresh.get("/auth/me")
    assert r7.status_code == 401


def test_register_creates_user(client, fake_ch) -> None:
    from api.app.auth import register_user
    register_user(fake_ch, "alice", "secret123", "Alice", "user")
    r = client.post("/auth/login", json={"username": "alice", "password": "secret123"})
    cookie = r.cookies["grag_session"]

    # 1. Register a new user (Bob) with a valid password
    r2 = client.post(
        "/auth/register",
        json={"username": "bob", "password": "hunter2", "display_name": "Bob"},
        cookies={"grag_session": cookie},
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["username"] == "bob"

    # 2. Bob can now log in
    r3 = client.post("/auth/login", json={"username": "bob", "password": "hunter2"})
    assert r3.status_code == 200
    assert r3.json()["display_name"] == "Bob"

    # 3. Duplicate username -> 409
    r4 = client.post(
        "/auth/register",
        json={"username": "bob", "password": "anotherpw", "display_name": ""},
        cookies={"grag_session": cookie},
    )
    assert r4.status_code == 409, r4.text


def test_query_requires_auth(client) -> None:
    r = client.post(
        "/query",
        json={"question": "What is the PTO policy?", "strategy": "hybrid"},
        cookies={},
    )
    assert r.status_code == 401
