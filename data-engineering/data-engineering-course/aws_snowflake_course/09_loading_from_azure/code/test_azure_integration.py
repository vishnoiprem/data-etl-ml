"""Tests for 09_loading_from_azure/code/azure_integration.sql

Asserts the SQL demo covers Azure STORAGE_INTEGRATION, AZURE tenant ID,
and the consent flow. No live Snowflake account required.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from conftest import strip_line_comments  # noqa: E402

SQL_PATH = pathlib.Path(__file__).resolve().parent / "azure_integration.sql"


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


def test_specifies_azure_storage_provider():
    """Azure integrations must use STORAGE_PROVIDER = 'AZURE'."""
    s = _clean()
    assert "STORAGE_PROVIDER" in s and "AZURE" in s, (
        "expected STORAGE_PROVIDER = 'AZURE' marker"
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


def test_references_tenant_id():
    """Azure integrations need a tenant id — demo must mention AZURE_TENANT_ID."""
    assert "AZURE_TENANT_ID" in _clean(), "AZURE_TENANT_ID parameter missing"


def test_creates_stage_with_integration():
    s = _clean()
    assert "STAGE" in s, "no STAGE created"
    assert "STORAGE_INTEGRATION" in s, "stage not bound to a STORAGE_INTEGRATION"


def test_shows_desc_integration_for_consent_url():
    """Demo must show how to find the Azure consent URL via DESC INTEGRATION."""
    assert "DESC INTEGRATION" in _clean(), "DESC INTEGRATION missing"


def test_author_signature():
    s = _sql()
    assert "Prem Vishnoi" in s
    assert "pvishnoi@avilx.com" in s
    assert "pvilx.com" not in s, "typo `pvilx.com` found"