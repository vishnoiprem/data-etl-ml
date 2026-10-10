"""Tests for 05_copy_options/code/copy_options.sql

Asserts the SQL demo covers the COPY INTO options taught in L33–L40.
No live Snowflake account required — we only parse the SQL.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from conftest import strip_line_comments  # noqa: E402

SQL_PATH = pathlib.Path(__file__).resolve().parent / "copy_options.sql"


def _sql() -> str:
    return SQL_PATH.read_text()


def _clean() -> str:
    return strip_line_comments(_sql()).upper()


def test_file_exists_and_non_empty():
    assert SQL_PATH.exists()
    assert len(_sql()) > 500


def test_covers_on_error_option():
    s = _clean()
    assert "ON_ERROR" in s, "ON_ERROR option missing"
    for mode in ("ABORT_STATEMENT", "CONTINUE", "SKIP_FILE"):
        assert mode in s, f"ON_ERROR mode {mode!r} missing"


def test_covers_force_option():
    assert "FORCE" in _clean(), "FORCE option missing"


def test_covers_size_limit_option():
    assert "SIZE_LIMIT" in _clean(), "SIZE_LIMIT option missing"


def test_covers_truncate_columns_option():
    assert "TRUNCATECOLUMNS" in _clean(), "TRUNCATECOLUMNS option missing"


def test_covers_return_failed_only_option():
    assert "RETURN_FAILED_ONLY" in _clean(), "RETURN_FAILED_ONLY option missing"


def test_uses_validate_function():
    """Demo should show how to inspect failed rows via VALIDATE()."""
    assert "VALIDATE(" in _clean(), "VALIDATE() function call missing"


def test_uses_idempotent_ddl():
    """Every CREATE in the script must use IF NOT EXISTS or OR REPLACE."""
    body = _sql()
    creates = [
        line
        for line in body.splitlines()
        if line.lstrip().upper().startswith("CREATE")
    ]
    assert creates, "no CREATE statements found"
    for line in creates:
        upper = line.upper()
        assert (
            "IF NOT EXISTS" in upper or "OR REPLACE" in upper
        ), f"non-idempotent CREATE: {line.strip()!r}"


def test_references_copy_into():
    assert "COPY INTO" in _clean(), "no COPY INTO statement"


def test_author_signature():
    s = _sql()
    assert "Prem Vishnoi" in s
    assert "pvishnoi@avilx.com" in s
    assert "pvilx.com" not in s, "typo `pvilx.com` found"
