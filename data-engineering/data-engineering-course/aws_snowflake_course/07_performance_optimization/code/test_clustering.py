"""Tests for 07_performance_optimization/code/clustering.sql

Asserts the SQL demo covers clustering keys, the
SYSTEM$CLUSTERING_INFORMATION inspection function, and a
zero-copy clone. No live Snowflake account required.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from conftest import strip_line_comments  # noqa: E402

SQL_PATH = pathlib.Path(__file__).resolve().parent / "clustering.sql"


def _sql() -> str:
    return SQL_PATH.read_text()


def _clean() -> str:
    return strip_line_comments(_sql()).upper()


def test_file_exists_and_non_empty():
    assert SQL_PATH.exists()
    assert len(_sql()) > 500


def test_uses_alter_table_for_clustering():
    s = _clean()
    assert "ALTER TABLE" in s and "CLUSTER BY" in s, (
        "expected `ALTER TABLE … CLUSTER BY` statement"
    )


def test_uses_clustering_information_function():
    s = _clean()
    assert "SYSTEM$CLUSTERING_INFORMATION" in s, "call missing"


def test_seeds_a_large_table():
    """Clustering is meaningful only for large tables — demo should seed many rows."""
    s = _clean()
    assert "GENERATOR(ROWCOUNT" in s, "expected GENERATOR(ROWCOUNT => N) seed"


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


def test_demonstrates_zero_copy_clone():
    """Clustering demo should also touch zero-copy cloning for dev envs."""
    assert "CLONE" in _clean(), "expected a CLONE example"


def test_author_signature():
    s = _sql()
    assert "Prem Vishnoi" in s
    assert "pvishnoi@avilx.com" in s
    assert "pvilx.com" not in s, "typo `pvilx.com` found"
