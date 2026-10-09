"""pytest fixtures that build a fresh in-memory SQLite per test.

Track-level tests can ``from common.conftest_helpers import tmp_db,
seeded_db`` in their own ``conftest.py`` and re-export them, or
just import the factory functions directly in fixtures.

These are *plain functions returning factories* rather than
``@pytest.fixture``-decorated callables, so they work whether
pytest is installed or the test is run via ``unittest``. Track
``conftest.py`` files wrap them in ``@pytest.fixture`` to expose
them to pytest.
"""

from __future__ import annotations

import os
import tempfile
from typing import Iterator

from .query import QueryRunner
from .schema import Column, Table, create_table_sqlite


SAMPLE_SCHEMA = [
    Table("users", [
        Column("id", "INTEGER", primary_key=True),
        Column("email", "TEXT", nullable=False),
        Column("name", "TEXT"),
        Column("country", "TEXT"),
    ]),
    Table("orders", [
        Column("order_id", "INTEGER", primary_key=True),
        Column("user_id", "INTEGER", nullable=False, references="users(id)"),
        Column("total", "REAL"),
        Column("status", "TEXT"),
    ]),
]


def tmp_db_path() -> Iterator[str]:
    """Yield a path to a fresh temp SQLite file, deleting it after.

    Use directly in a ``with`` block, or wrap in a ``@pytest.fixture``.
    """
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    try:
        yield path
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def make_tmp_db() -> str:
    """Return a path to a fresh temp SQLite file (caller cleans up)."""
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    return path


def build_seeded_runner() -> QueryRunner:
    """Return a fresh :class:`QueryRunner` with ``SAMPLE_SCHEMA`` applied."""
    q = QueryRunner(":memory:")
    for t in SAMPLE_SCHEMA:
        q.execute(create_table_sqlite(t))
    return q
