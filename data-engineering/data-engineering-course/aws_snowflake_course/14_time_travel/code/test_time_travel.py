"""Tests for 14_time_travel / time_travel_demo.sql and undrop.sql."""
from __future__ import annotations

from pathlib import Path

import pytest

from conftest import parse_sql_statements

HERE = Path(__file__).resolve().parent
TT_FILE = HERE / "time_travel_demo.sql"
UNDROP_FILE = HERE / "undrop.sql"


@pytest.fixture(scope="module")
def tt_text() -> str:
    return TT_FILE.read_text()


@pytest.fixture(scope="module")
def undrop_text() -> str:
    return UNDROP_FILE.read_text()


# ── time_travel_demo.sql ───────────────────────────────────────────────
def test_tt_sets_data_retention(tt_text):
    assert "DATA_RETENTION_TIME_IN_DAYS" in tt_text.upper()


def test_tt_uses_at_offset(tt_text):
    """`AT (OFFSET => -60*5)` is the masterclass demo for time travel."""
    assert "AT (OFFSET" in tt_text.upper()
    assert "-60*5" in tt_text


def test_tt_uses_before_statement(tt_text):
    """`BEFORE (STATEMENT => ...)` pattern must be present (even commented)."""
    assert "BEFORE (STATEMENT" in tt_text.upper()


def test_tt_restores_with_clone_at_offset(tt_text):
    assert "CLONE" in tt_text.upper()
    assert "AT (OFFSET" in tt_text.upper()


def test_tt_demonstrates_dml(tt_text):
    """The demo must perform INSERT / UPDATE / DELETE before showing TT."""
    upper = tt_text.upper()
    assert "UPDATE" in upper
    assert "DELETE" in upper
    assert "INSERT" in upper


# ── undrop.sql ─────────────────────────────────────────────────────────
def test_undrop_drops_then_undrops(undrop_text):
    upper = undrop_text.upper()
    assert "DROP TABLE" in upper
    assert "UNDROP TABLE" in upper


def test_undrop_supports_schema(undrop_text):
    upper = undrop_text.upper()
    assert "UNDROP SCHEMA" in upper


def test_undrop_supports_database(undrop_text):
    upper = undrop_text.upper()
    assert "UNDROP DATABASE" in upper


def test_undrop_parses_cleanly(undrop_text):
    stmts = parse_sql_statements(undrop_text)
    assert len(stmts) >= 4


def test_undrop_mentions_name_collision(undrop_text):
    """The doc-comment must warn about the rename-then-undrop workaround."""
    assert "rename" in undrop_text.lower() or "RENAME" in undrop_text
