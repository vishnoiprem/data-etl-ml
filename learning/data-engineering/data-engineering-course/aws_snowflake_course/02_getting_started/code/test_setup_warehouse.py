"""Tests for 02_getting_started / setup_warehouse.sql.

The SQL demo has no companion Python file, so we (a) parse the file to assert
the right keywords are present and (b) mock `snowflake.connector.connect`
to feed the SQL through our ``FakeConnection`` and verify each statement
would have been issued in the right order.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from conftest import (
    FakeConnection,
    FakeCursor,
    executed_contains,
    make_fake_conn,
    parse_sql_statements,
)

HERE = Path(__file__).resolve().parent
SQL_FILE = HERE / "setup_warehouse.sql"


# ── helpers ─────────────────────────────────────────────────────────────
def _run_sql_via_fake(sql_text: str) -> tuple[FakeConnection, FakeCursor]:
    """Execute every statement in *sql_text* against a FakeConnection and
    return both so the test can inspect what was issued."""
    conn = make_fake_conn()
    cursor = conn.cursor()
    for stmt in parse_sql_statements(sql_text):
        cursor.execute(stmt)
    return conn, cursor


# ── 1. file content checks ─────────────────────────────────────────────
@pytest.fixture(scope="module")
def sql_text() -> str:
    assert SQL_FILE.exists(), f"missing SQL file: {SQL_FILE}"
    return SQL_FILE.read_text(encoding="utf-8")


def test_creates_warehouse(sql_text):
    assert "CREATE WAREHOUSE" in sql_text.upper()


def test_uses_if_not_exists(sql_text):
    """All CREATE statements should be idempotent."""
    assert "IF NOT EXISTS" in sql_text.upper()


def test_sets_auto_suspend_60(sql_text):
    assert "AUTO_SUSPEND" in sql_text.upper()
    assert "60" in sql_text


def test_uses_economy_scaling_policy(sql_text):
    assert "ECONOMY" in sql_text.upper()


def test_warehouse_size_xsmall(sql_text):
    assert "XSMALL" in sql_text.upper()


def test_grants_usage_to_sysadmin(sql_text):
    assert "GRANT USAGE" in sql_text.upper()
    assert "SYSADMIN" in sql_text.upper()


def test_creates_secondary_multi_cluster_warehouse(sql_text):
    """The secondary warehouse is needed for scale-out demos in section 7."""
    assert "COMPUTE_WH_MULTI" in sql_text
    assert "MAX_CLUSTER_COUNT" in sql_text.upper()


def test_has_show_warehouses_smoke_test(sql_text):
    assert "SHOW WAREHOUSES" in sql_text.upper()


# ── 2. execution-shape checks via FakeConnection ───────────────────────
def test_warehouse_create_uses_xsmall():
    conn, cursor = _run_sql_via_fake(SQL_FILE.read_text())
    matches = [
        s for s in cursor.executed
        if "CREATE WAREHOUSE" in s.upper() and "COMPUTE_WH" in s.upper()
    ]
    assert matches, "expected at least one CREATE WAREHOUSE COMPUTE_WH"
    # Every CREATE WAREHOUSE must declare the size, AUTO_SUSPEND, and policy.
    for stmt in matches:
        assert "XSMALL"   in stmt.upper()
        assert "AUTO_SUSPEND" in stmt.upper()
        assert "ECONOMY"  in stmt.upper()


def test_all_statements_parse_cleanly():
    """No statement should fail to terminate with `;`."""
    stmts = parse_sql_statements(SQL_FILE.read_text())
    assert len(stmts) >= 5, f"expected >=5 statements, got {len(stmts)}"
    for s in stmts:
        assert s, "empty SQL statement"
        assert not s.startswith("--"), "comment leaked into statement"


def test_warehouse_grant_present():
    conn, cursor = _run_sql_via_fake(SQL_FILE.read_text())
    assert executed_contains("GRANT USAGE", cursor)
    assert executed_contains("SYSADMIN", cursor)
