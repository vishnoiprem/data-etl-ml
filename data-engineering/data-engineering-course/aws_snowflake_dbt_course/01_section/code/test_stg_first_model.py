"""Tests for 01_section/code/stg_first_model.sql.

Asserts the demo staging model renders the right Jinja + uses the
right source. No live Snowflake required.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from conftest import render_jinja  # noqa: E402

SQL_PATH = pathlib.Path(__file__).resolve().parent / "stg_first_model.sql"


def _sql() -> str:
    return SQL_PATH.read_text()


def test_file_exists_and_non_empty():
    assert SQL_PATH.exists()
    assert len(_sql()) > 100


def test_renders_with_mock_context():
    """The model should render without errors using the mock dbt context."""
    rendered = render_jinja(_sql())
    # Mock returns source('ethereum','raw_transactions') -> DB.public.ethereum_raw_transactions
    assert "DB.public" in rendered
    assert "value_eth" in rendered
    assert "eth" in rendered.lower()


def test_references_source_function():
    """Staging models must use {{ source() }}, not {{ ref() }}."""
    assert "source(" in _sql(), "demo must show {{ source() }} usage"


def test_author_signature():
    s = _sql()
    assert "Prem Vishnoi" in s
    assert "pvishnoi@avilx.com" in s
    assert "pvilx.com" not in s, "typo `pvilx.com` found"


def test_uses_config_block():
    """Staging models should set `{{ config(materialized='view') }}`."""
    assert "config(" in _sql() and "materialized" in _sql()
