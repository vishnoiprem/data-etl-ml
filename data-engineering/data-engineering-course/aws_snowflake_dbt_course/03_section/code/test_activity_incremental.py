"""Tests for 03_section/code/activity_incremental.sql.

Asserts the demo incremental model uses the merge strategy + the
is_incremental() guard. No live Snowflake required.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from conftest import render_jinja  # noqa: E402

SQL_PATH = pathlib.Path(__file__).resolve().parent / "activity_incremental.sql"


def _sql() -> str:
    return SQL_PATH.read_text()


def test_uses_incremental_materialization():
    assert "incremental" in _sql(), "expected materialized='incremental'"


def test_uses_merge_strategy():
    assert "incremental_strategy='merge'" in _sql(), "expected merge strategy"


def test_has_is_incremental_guard():
    """Incremental models should guard the source with is_incremental()."""
    assert "is_incremental()" in _sql(), "expected `is_incremental()` guard"


def test_references_this_table():
    """The is_incremental guard must compare against {{ this }}."""
    assert "{{ this }}" in _sql(), "expected `{{ this }}` reference"


def test_renders_with_mock_context():
    rendered = render_jinja(_sql())
    # is_incremental() returns True in our mock context
    assert "where block_timestamp >=" in rendered
    assert "this_table" in rendered


def test_author_signature():
    s = _sql()
    assert "Prem Vishnoi" in s
    assert "pvishnoi@avilx.com" in s
    assert "pvilx.com" not in s
