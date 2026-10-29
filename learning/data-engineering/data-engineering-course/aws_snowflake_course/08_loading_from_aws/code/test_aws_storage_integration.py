"""Tests for 08_loading_from_aws / aws_storage_integration.sql."""
from __future__ import annotations

from pathlib import Path

import pytest

from conftest import parse_sql_statements

HERE = Path(__file__).resolve().parent
SQL_FILE = HERE / "aws_storage_integration.sql"


@pytest.fixture(scope="module")
def sql_text() -> str:
    return SQL_FILE.read_text()


def test_creates_storage_integration(sql_text):
    assert "CREATE STORAGE INTEGRATION" in sql_text.upper()


def test_integration_is_aws_s3(sql_text):
    assert "STORAGE_PROVIDER" in sql_text.upper()
    assert "AWS_S3" in sql_text.upper()


def test_integration_specifies_role_arn(sql_text):
    assert "STORAGE_AWS_ROLE_ARN" in sql_text.upper()


def test_integration_lists_allowed_locations(sql_text):
    assert "STORAGE_ALLOWED_LOCATIONS" in sql_text.upper()
    assert "s3://" in sql_text


def test_creates_external_stage(sql_text):
    assert "CREATE OR REPLACE STAGE" in sql_text.upper()
    assert "STORAGE_INTEGRATION" in sql_text.upper()


def test_stage_uses_s3_url(sql_text):
    assert "s3://" in sql_text


def test_uses_desc_integration_for_trust_values(sql_text):
    """DESC INTEGRATION is required to extract the trust ARN/external-id."""
    assert "DESC INTEGRATION" in sql_text.upper()


def test_copy_into_uses_s3_stage(sql_text):
    assert "COPY INTO" in sql_text.upper()
    assert "S3_ORDERS_STAGE" in sql_text


def test_on_error_continue(sql_text):
    """We use CONTINUE so one bad file doesn't fail the whole COPY."""
    assert "ON_ERROR" in sql_text.upper()
    assert "CONTINUE" in sql_text.upper()


def test_sql_parses_cleanly(sql_text):
    stmts = parse_sql_statements(sql_text)
    assert len(stmts) >= 5
