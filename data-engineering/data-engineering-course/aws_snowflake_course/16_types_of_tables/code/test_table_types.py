"""Tests for 16_types_of_tables/code/table_types.sql

Asserts the SQL demo covers PERMANENT, TRANSIENT, and TEMPORARY tables
plus the retention semantics of each. No live Snowflake account required.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from conftest import strip_line_comments  # noqa: E402

SQL_PATH = pathlib.Path(__file__).resolve().parent / "table_types.sql"


def _sql() -> str:
    return SQL_PATH.read_text()


def _clean() -> str:
    return strip_line_comments(_sql()).upper()


def test_file_exists_and_non_empty():
    assert SQL_PATH.exists()
    assert len(_sql()) > 500


def test_creates_permanent_table():
    s = _clean()
    assert "PERMANENT TABLE" in s, "PERMANENT TABLE missing"


def test_creates_transient_table():
    s = _clean()
    assert "TRANSIENT TABLE" in s, "TRANSIENT TABLE missing"


def test_creates_temporary_table():
    s = _clean()
    assert "TEMPORARY TABLE" in s, "TEMPORARY TABLE missing"


def test_sets_data_retention_days():
    """Retention time must be explicit so Fail-Safe behaviour is correct."""
    s = _clean()
    assert "DATA_RETENTION_TIME_IN_DAYS" in s, "DATA_RETENTION_TIME_IN_DAYS missing"


def test_uses_idempotent_ddl():
    body = _sql()
    creates = [line for line in body.splitlines() if line.lstrip().upper().startswith("CREATE")]
    assert creates, "no CREATE statements found"
    for line in creates:
        upper = line.upper()
        assert "IF NOT EXISTS" in upper or "OR REPLACE" in upper, (
            f"non-idempotent CREATE: {line.strip()!r}"
        )


def test_has_author_signature():
    s = _sql()
    assert "Prem Vishnoi" in s
    assert "pvishnoi@avilx.com" in s
    assert "pvilx.com" not in s, "typo `pvilx.com` found"
