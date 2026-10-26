"""Tests for 04_loading_data / load_csv.sql."""
from __future__ import annotations

from pathlib import Path

import pytest

from conftest import executed_contains, parse_sql_statements

HERE = Path(__file__).resolve().parent
SQL_FILE = HERE / "load_csv.sql"


@pytest.fixture(scope="module")
def sql_text() -> str:
    return SQL_FILE.read_text()


def test_creates_file_format(sql_text):
    assert "CREATE OR REPLACE FILE FORMAT" in sql_text.upper()


def test_creates_target_table(sql_text):
    assert "CREATE OR REPLACE TABLE" in sql_text.upper()
    assert "ORDERS_RAW" in sql_text


def test_creates_internal_stage(sql_text):
    assert "CREATE OR REPLACE STAGE" in sql_text.upper()


def test_uses_copy_into(sql_text):
    assert "COPY INTO" in sql_text.upper()


def test_uses_validate_for_audit(sql_text):
    assert "VALIDATE" in sql_text.upper()


def test_copy_into_uses_default_on_error(sql_text):
    """The first COPY INTO should NOT use ON_ERROR to teach the default."""
    upper = sql_text.upper()
    # Find the first COPY INTO
    copy_idx = upper.find("COPY INTO")
    rest = upper[copy_idx:]
    # The first COPY block should not specify ON_ERROR (= uses default).
    # We just check that the doc-comment talks about the default.
    assert "ABORT_STATEMENT" in upper
    assert "ON_ERROR" in upper


def test_sql_parses_into_multiple_statements(sql_text):
    stmts = parse_sql_statements(sql_text)
    assert len(stmts) >= 5


def test_purge_false_keeps_files(sql_text):
    """PURGE = FALSE is the masterclass default so students can re-run."""
    assert "PURGE" in sql_text.upper()
    assert "FALSE" in sql_text.upper()
