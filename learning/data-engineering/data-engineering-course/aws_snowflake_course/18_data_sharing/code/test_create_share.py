"""Tests for 18_data_sharing / create_share.sql."""
from __future__ import annotations

from pathlib import Path

import pytest

from conftest import parse_sql_statements

HERE = Path(__file__).resolve().parent
SQL_FILE = HERE / "create_share.sql"


@pytest.fixture(scope="module")
def sql_text() -> str:
    return SQL_FILE.read_text()


def test_creates_share(sql_text):
    assert "CREATE OR REPLACE SHARE" in sql_text.upper()


def test_grants_usage_on_database(sql_text):
    assert "GRANT USAGE ON DATABASE" in sql_text.upper()


def test_grants_usage_on_schema(sql_text):
    assert "GRANT USAGE ON SCHEMA" in sql_text.upper()


def test_grants_select_on_table(sql_text):
    assert "GRANT SELECT" in sql_text.upper()


def test_uses_secure_view(sql_text):
    """Secure views are required when sharing because of share semantics."""
    assert "SECURE VIEW" in sql_text.upper()


def test_alters_share_add_accounts(sql_text):
    """ALTER SHARE ADD ACCOUNTS is the binding step to consumers."""
    assert "ALTER SHARE" in sql_text.upper()
    assert "ADD ACCOUNTS" in sql_text.upper()


def test_shows_shares(sql_text):
    assert "SHOW SHARES" in sql_text.upper()


def test_sql_parses_cleanly(sql_text):
    stmts = parse_sql_statements(sql_text)
    assert len(stmts) >= 5


def test_demonstrates_consumer_create_db_from_share(sql_text):
    """Even if commented out, the consumer-side pattern must be shown."""
    assert "FROM SHARE" in sql_text.upper()
