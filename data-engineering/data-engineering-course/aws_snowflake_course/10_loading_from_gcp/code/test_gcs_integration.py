"""Tests for 10_loading_from_gcp/code/gcs_integration.sql

Asserts the SQL demo covers GCS STORAGE_INTEGRATION, service-account
trust, and stages. No live Snowflake account required.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from conftest import strip_line_comments  # noqa: E402

SQL_PATH = pathlib.Path(__file__).resolve().parent / "gcs_integration.sql"


def _sql() -> str:
    return SQL_PATH.read_text()


def _clean() -> str:
    return strip_line_comments(_sql()).upper()


def test_file_exists_and_non_empty():
    assert SQL_PATH.exists()
    assert len(_sql()) > 500


def test_creates_storage_integration():
    s = _clean()
    assert "STORAGE_INTEGRATION" in s, "STORAGE_INTEGRATION missing"


def test_uses_gcs_storage_provider():
    """GCS integrations must use STORAGE_PROVIDER = 'GCS'."""
    s = _clean()
    assert "STORAGE_PROVIDER" in s and "GCS" in s, (
        "expected STORAGE_PROVIDER = 'GCS' marker"
    )


def test_uses_idempotent_ddl():
    body = _sql()
    creates = [
        line
        for line in body.splitlines()
        if line.lstrip().upper().startswith("CREATE")
    ]
    assert creates, "no CREATE statements found"
    for line in creates:
        upper = line.upper()
        assert "IF NOT EXISTS" in upper or "OR REPLACE" in upper, (
            f"non-idempotent CREATE: {line.strip()!r}"
        )


def test_references_desc_integration():
    """Demo must show how to find the GCS service account via DESC INTEGRATION."""
    assert "DESC INTEGRATION" in _clean(), "DESC INTEGRATION missing"


def test_creates_stage_with_integration():
    s = _clean()
    assert "STAGE" in s, "no STAGE created"
    assert "STORAGE_INTEGRATION" in s, "stage not bound to a STORAGE_INTEGRATION"


def test_lists_gcs_objects():
    """Demo should confirm reachability with LIST @stage."""
    assert "LIST @" in _sql(), "LIST @stage missing"


def test_author_signature():
    s = _sql()
    assert "Prem Vishnoi" in s
    assert "pvishnoi@avilx.com" in s
    assert "pvilx.com" not in s, "typo `pvilx.com` found"