"""Tests for 11_snowpipe / snowpipe_setup.sql."""
from __future__ import annotations

from pathlib import Path

import pytest

from conftest import parse_sql_statements

HERE = Path(__file__).resolve().parent
SQL_FILE = HERE / "snowpipe_setup.sql"


@pytest.fixture(scope="module")
def sql_text() -> str:
    return SQL_FILE.read_text()


def test_creates_notification_integration(sql_text):
    assert "CREATE NOTIFICATION INTEGRATION" in sql_text.upper()


def test_notification_is_sqs(sql_text):
    upper = sql_text.upper()
    assert "NOTIFICATION_PROVIDER" in upper
    assert "AWS_SQS" in upper


def test_pipe_uses_auto_ingest(sql_text):
    assert "AUTO_INGEST" in sql_text.upper()
    assert "TRUE" in sql_text.upper()


def test_pipe_uses_error_integration(sql_text):
    assert "ERROR_INTEGRATION" in sql_text.upper()


def test_pipe_uses_copy_into(sql_text):
    """Snowpipe's body is just a COPY INTO statement."""
    assert "CREATE OR REPLACE PIPE" in sql_text.upper()
    assert "COPY INTO" in sql_text.upper()


def test_uses_system_pipe_status_for_validation(sql_text):
    assert "SYSTEM$PIPE_STATUS" in sql_text.upper()


def test_desc_pipe_for_notification_channel(sql_text):
    assert "DESC PIPE" in sql_text.upper()


def test_on_error_continue(sql_text):
    assert "ON_ERROR" in sql_text.upper()
    assert "CONTINUE" in sql_text.upper()


def test_target_table_has_data_retention(sql_text):
    """Production-grade tables should declare DATA_RETENTION_TIME_IN_DAYS."""
    assert "DATA_RETENTION_TIME_IN_DAYS" in sql_text.upper()


def test_sql_parses_cleanly(sql_text):
    stmts = parse_sql_statements(sql_text)
    assert len(stmts) >= 5
