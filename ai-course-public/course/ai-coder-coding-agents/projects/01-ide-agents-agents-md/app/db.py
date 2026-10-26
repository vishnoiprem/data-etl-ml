"""
Database engine and session factory.

One session per request — never a global. The `get_db` generator below is the
ONLY way routes should obtain a session; creating one inside a route handler
will silently skip the cleanup step.
"""

from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://kanban:kanban@localhost:5432/kanban",
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # avoid stale connections in dev
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency. Always `yield`, never `return`."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
