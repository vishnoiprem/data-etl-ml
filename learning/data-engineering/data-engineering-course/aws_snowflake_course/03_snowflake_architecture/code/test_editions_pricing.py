"""Tests for the 03_snowflake_architecture editions_pricing.sql demo.

The script is read-only — it queries ACCOUNT_USAGE and emits SHOW commands.
We verify the right ACCOUNT_USAGE views are referenced and the result scans
use the documented LAST_QUERY_ID() pattern.
"""
from __future__ import annotations

from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SQL_FILE = HERE / "editions_pricing.sql"


@pytest.fixture(scope="module")
def sql_text() -> str:
    assert SQL_FILE.exists()
    return SQL_FILE.read_text(encoding="utf-8")


def test_uses_show_warehouses(sql_text):
    assert "SHOW WAREHOUSES" in sql_text.upper()


def test_uses_show_databases(sql_text):
    assert "SHOW DATABASES" in sql_text.upper()


def test_uses_show_tables(sql_text):
    assert "SHOW TABLES" in sql_text.upper()


def test_queries_warehouse_metering_history(sql_text):
    assert "WAREHOUSE_METERING_HISTORY" in sql_text.upper()


def test_queries_query_history(sql_text):
    assert "QUERY_HISTORY" in sql_text.upper()


def test_uses_result_scan_for_show_wrapping(sql_text):
    """Snowflake pattern: wrap SHOW in TABLE(RESULT_SCAN(LAST_QUERY_ID()))."""
    assert "RESULT_SCAN" in sql_text.upper()
    assert "LAST_QUERY_ID()" in sql_text.upper()


def test_selects_current_edition(sql_text):
    assert "CURRENT_EDITION" in sql_text.upper()


def test_no_create_statements(sql_text):
    """This demo is read-only — must not create or alter anything."""
    upper = sql_text.upper()
    assert "CREATE WAREHOUSE"  not in upper
    assert "CREATE TABLE"      not in upper
    assert "ALTER TABLE"       not in upper
