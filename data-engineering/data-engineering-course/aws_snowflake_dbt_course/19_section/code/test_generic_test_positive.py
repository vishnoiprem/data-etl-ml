"""Tests for 19_section/code/generic_test_positive.sql."""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

SQL_PATH = pathlib.Path(__file__).resolve().parent / "generic_test_positive.sql"


def _sql() -> str:
    return SQL_PATH.read_text()


def test_uses_test_block():
    s = _sql()
    assert "{% test" in s
    assert "{% endtest %}" in s


def test_takes_model_and_column_args():
    s = _sql()
    assert "model" in s
    assert "column_name" in s


def test_returns_failing_rows():
    """A generic test should return rows that *fail* the test."""
    s = _sql()
    assert "where" in s.lower()
    assert "<= 0" in s or "< 0" in s


def test_renders_with_mock_context():
    from conftest import render_jinja
    # The {% test %} body is consumed by our dbt tag extension, but
    # the file should still parse + render without raising.
    rendered = render_jinja(_sql())
    assert isinstance(rendered, str)


def test_author_signature():
    s = _sql()
    assert "Prem Vishnoi" in s
    assert "pvishnoi@avilx.com" in s
    assert "pvilx.com" not in s
