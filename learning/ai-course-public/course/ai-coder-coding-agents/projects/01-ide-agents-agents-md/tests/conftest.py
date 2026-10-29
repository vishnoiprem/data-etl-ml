"""
Pytest configuration.

The ordering here matters and is the lesson of the file: `DATABASE_URL` must
be set *before* `app.db` is imported, because `app/db.py` reads the environment
at module import time to build the engine. A later monkeypatch would be too
late — the engine would already be bound to the real Postgres URL.
"""

from __future__ import annotations

import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

import pytest  # noqa: E402  (must follow the env var above)
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.db import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402

# A single in-memory SQLite connection, shared across the test session.
# StaticPool is required: without it each checkout gets a *different* :memory:
# database, so tables created in one test vanish in the next.
engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    """Drop-in replacement for app.db.get_db, backed by SQLite."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client() -> TestClient:
    """Function-scoped client. Tables persist; rows do not get reset.

    Tests are written to be order-independent (they create their own cards),
    which is why the cheap "no truncation between tests" approach is safe here.
    """
    return TestClient(app)