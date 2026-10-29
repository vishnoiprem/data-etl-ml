"""Shared pytest fixtures and helpers for the snowflake_course tests.

This conftest lives at the course root so the test runner picks it up
for every `section/code/test_*.py` discovered.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ── make the course root importable so tests can do `from conftest import …`
# (only matters for tests that want a Python import path; pytest itself
#  auto-discovers conftest.py so fixtures are usable from anywhere.)
COURSE_ROOT = Path(__file__).resolve().parent
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

import pytest


# ── SQL parsing ─────────────────────────────────────────────────────────
_LINE_COMMENT_RE = re.compile(r"--[^\n]*")


def strip_line_comments(sql: str) -> str:
    """Drop ``-- ...`` line comments while preserving newlines."""
    return _LINE_COMMENT_RE.sub("", sql)


def parse_sql_statements(sql_text: str) -> list[str]:
    """Naively split a multi-statement .sql file on `;` (post-comment strip)."""
    cleaned = strip_line_comments(sql_text)
    return [s.strip() for s in cleaned.split(";") if s.strip()]


# ── In-memory fake of snowflake.connector ───────────────────────────────
@dataclass
class FakeCursor:
    """Records every SQL statement handed to it.

    A test can inspect ``cursor.executed`` and assert on the SQL Snowflake
    would have received.  Use ``cursor.fetchall.return_value = [...]`` to
    return canned data.
    """

    executed: list[str] = field(default_factory=list)
    fetchall_return_value: list[tuple] = field(default_factory=list)
    fetchone_return_value: tuple | None = None
    description: tuple = ()

    def execute(self, sql: str, *args: Any, **kwargs: Any) -> "FakeCursor":
        self.executed.append(sql)
        return self

    def executemany(self, sql: str, seq: Any = None) -> "FakeCursor":
        self.executed.append(sql)
        return self

    def fetchall(self) -> list[tuple]:
        return self.fetchall_return_value

    def fetchone(self) -> tuple | None:
        return self.fetchone_return_value

    def close(self) -> None:
        pass


@dataclass
class FakeConnection:
    cursors: list[FakeCursor] = field(default_factory=list)

    def cursor(self) -> FakeCursor:
        c = FakeCursor()
        self.cursors.append(c)
        return c

    def close(self) -> None:
        pass

    def commit(self) -> None:
        pass


def make_fake_conn() -> FakeConnection:
    return FakeConnection()


def executed_contains(needle: str, cursor: FakeCursor) -> bool:
    n = needle.upper()
    return any(n in s.upper() for s in cursor.executed)


# ── pytest fixtures ─────────────────────────────────────────────────────
@pytest.fixture
def fake_conn() -> FakeConnection:
    """A fresh FakeConnection per test."""
    return make_fake_conn()
