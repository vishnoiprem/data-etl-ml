"""Pytest setup: spin up app + temp DB."""
import os
import tempfile
import pytest
from fastapi.testclient import TestClient

# Use temp DB before importing app
fd, path = tempfile.mkstemp(suffix=".db")
os.environ["RAG_DB_PATH"] = path
os.close(fd)

from app.main import app  # noqa: E402
from app.database import init_db, db_cursor  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_db():
    init_db()
    with db_cursor(commit=True) as cur:
        cur.execute("DELETE FROM feedback")
        cur.execute("DELETE FROM traces")
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def seed():
    """Insert a few deterministic traces."""
    rows = [
        ("t001", "2026-01-01T00:00:00+00:00", "v1.0", "q1", "[]", "[]", 100, 200, "ok", None),
        ("t002", "2026-01-02T00:00:00+00:00", "v1.1", "q2", "[]", "[]", 200, 400, "ok", None),
        ("t003", "2026-01-03T00:00:00+00:00", "v1.2", "q3", "[]", "[]", 300, 1500, "error", None),
    ]
    with db_cursor(commit=True) as cur:
        for r in rows:
            cur.execute(
                """INSERT INTO traces(trace_id, created_at, prompt_version, user_query, prompt,
                                    retrieved_chunks, model_response, citations,
                                    token_usage, latency_ms, status, feedback)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (r[0], r[1], r[2], r[3], "p", r[4], "resp", r[5], r[6], r[7], r[8], r[9]),
            )
    return rows