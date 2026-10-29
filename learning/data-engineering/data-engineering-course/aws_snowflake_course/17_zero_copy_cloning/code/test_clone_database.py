"""Tests for 17_zero_copy_cloning / clone_database.sql."""
from __future__ import annotations

from pathlib import Path

import pytest

from conftest import parse_sql_statements

HERE = Path(__file__).resolve().parent
SQL_FILE = HERE / "clone_database.sql"


@pytest.fixture(scope="module")
def sql_text() -> str:
    return SQL_FILE.read_text()


def test_creates_source_table(sql_text):
    assert "CREATE OR REPLACE TABLE" in sql_text.upper()
    assert "SOURCE_ORDERS" in sql_text


def test_creates_plain_clone(sql_text):
    """`CLONE <table>` for a dev copy is the headline pattern."""
    assert "CLONE SOURCE_ORDERS" in sql_text.upper()


def test_creates_time_travel_clone(sql_text):
    """`CLONE <table> AT (OFFSET => ...)` for historical clones."""
    assert "AT (OFFSET" in sql_text.upper()


def test_creates_schema_clone(sql_text):
    assert "CLONE SCHEMA" in sql_text.upper() or "CLONE GETTING_STARTED" in sql_text.upper()


def test_creates_database_clone(sql_text):
    assert "CLONE DATABASE" in sql_text.upper() or "CLONE SNOWFLAKE_DEMO" in sql_text.upper()


def test_demonstrates_divergence(sql_text):
    """Mutating the clone proves divergence starts the per-row storage cost."""
    assert "UPDATE" in sql_text.upper()
    assert "DEV_ORDERS" in sql_text


def test_drops_clones(sql_text):
    assert "DROP TABLE" in sql_text.upper()
    assert "DROP SCHEMA" in sql_text.upper()
    assert "DROP DATABASE" in sql_text.upper()


def test_sql_parses_cleanly(sql_text):
    stmts = parse_sql_statements(sql_text)
    assert len(stmts) >= 5
