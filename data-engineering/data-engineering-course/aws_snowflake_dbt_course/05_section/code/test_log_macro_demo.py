"""Tests for 05_section/code/log_macro_demo.sql."""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from conftest import render_jinja  # noqa: E402

SQL_PATH = pathlib.Path(__file__).resolve().parent / "log_macro_demo.sql"


def _sql() -> str:
    return SQL_PATH.read_text()


def test_macro_uses_execute_guard():
    s = _sql()
    assert "{% if execute %}" in s, "expected `{% if execute %}` guard"


def test_macro_uses_log_call():
    s = _sql()
    assert "{{ log(" in s, "expected `{{ log(...) }}` call"


def test_macro_uses_run_query():
    assert "{% set results = run_query(" in _sql()


def test_macro_returns_value():
    assert "{{ return(" in _sql()


def test_renders_without_errors():
    """The macro file should render without raising.

    {% macro %} bodies are also consumed by the dbt tag extension in
    tests, but this assertion just checks that no Jinja syntax error
    fires on the file.
    """
    rendered = render_jinja(_sql())
    assert isinstance(rendered, str)


def test_author_signature():
    s = _sql()
    assert "Prem Vishnoi" in s
    assert "pvishnoi@avilx.com" in s
    assert "pvilx.com" not in s
