"""
API tests for the cards router.

These run against SQLite in-memory so `make test` needs no database. The
DATABASE_URL override in conftest.py happens *before* app.db is imported —
that ordering is load-bearing and is why the import lives in conftest, not here.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz() -> None:
    res = client.get("/api/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_create_and_list_card() -> None:
    res = client.post("/api/cards", json={"title": "First card"})
    assert res.status_code == 201

    created = res.json()
    assert created["title"] == "First card"
    assert created["column"] == "backlog"
    assert created["description"] is None

    listing = client.get("/api/cards").json()
    assert any(c["id"] == created["id"] for c in listing)


def test_create_card_rejects_empty_title() -> None:
    res = client.post("/api/cards", json={"title": ""})
    assert res.status_code == 422  # Pydantic min_length violation


def test_create_card_rejects_overlong_title() -> None:
    res = client.post("/api/cards", json={"title": "x" * 201})
    assert res.status_code == 422


def test_move_card_between_columns() -> None:
    card_id = client.post("/api/cards", json={"title": "Movable"}).json()["id"]

    res = client.patch(
        f"/api/cards/{card_id}/move",
        json={"column": "done", "position": 0},
    )
    assert res.status_code == 200
    assert res.json()["column"] == "done"
    assert res.json()["position"] == 0


def test_move_card_rejects_unknown_column() -> None:
    card_id = client.post("/api/cards", json={"title": "Bad move"}).json()["id"]

    res = client.patch(
        f"/api/cards/{card_id}/move",
        json={"column": "archive", "position": 0},
    )
    assert res.status_code == 422  # regex pattern in CardMove rejects it


def test_move_missing_card_returns_404() -> None:
    res = client.patch(
        "/api/cards/999999/move",
        json={"column": "done", "position": 0},
    )
    assert res.status_code == 404


def test_delete_card() -> None:
    card_id = client.post("/api/cards", json={"title": "Doomed"}).json()["id"]

    assert client.delete(f"/api/cards/{card_id}").status_code == 204
    assert client.delete(f"/api/cards/{card_id}").status_code == 404


def test_response_never_leaks_session_state() -> None:
    """CardOut has no `__dict__`, so no SQLAlchemy internals can serialise."""
    created = client.post("/api/cards", json={"title": "Leak check"}).json()
    assert set(created) == {
        "id",
        "title",
        "description",
        "column",
        "position",
        "created_at",
        "updated_at",
    }