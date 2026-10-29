"""Tests for 06_unstructured_data / parse_json.sql and flatten_array.sql."""
from __future__ import annotations

from pathlib import Path

import pytest

from conftest import parse_sql_statements

HERE = Path(__file__).resolve().parent
PARSE_FILE = HERE / "parse_json.sql"
FLATTEN_FILE = HERE / "flatten_array.sql"


@pytest.fixture(scope="module")
def parse_text() -> str:
    return PARSE_FILE.read_text()


@pytest.fixture(scope="module")
def flatten_text() -> str:
    return FLATTEN_FILE.read_text()


# ── parse_json.sql ──────────────────────────────────────────────────────
def test_parse_uses_variant_type(parse_text):
    assert "VARIANT" in parse_text.upper()


def test_parse_uses_parse_json(parse_text):
    assert "PARSE_JSON" in parse_text.upper()


def test_parse_uses_dot_navigation(parse_text):
    """Snowflake's `payload:user.id` style is the masterclass headline."""
    assert "payload:" in parse_text


def test_parse_uses_get_path(parse_text):
    assert "GET_PATH" in parse_text.upper()


def test_parse_uses_typeof_and_array_size(parse_text):
    upper = parse_text.upper()
    assert "TYPEOF"  in upper
    assert "ARRAY_SIZE" in upper


def test_parse_creates_typed_table(parse_text):
    assert "CREATE OR REPLACE TABLE" in parse_text.upper()
    assert "RAW_EVENTS_TYPED" in parse_text


def test_parse_parses_cleanly(parse_text):
    stmts = parse_sql_statements(parse_text)
    assert len(stmts) >= 6


# ── flatten_array.sql ──────────────────────────────────────────────────
def test_flatten_uses_lateral_flatten(flatten_text):
    assert "LATERAL FLATTEN" in flatten_text.upper()


def test_flatten_uses_outer_true(flatten_text):
    assert "OUTER => TRUE" in flatten_text.upper() or "OUTER=TRUE" in flatten_text.upper()


def test_flatten_creates_normalised_table(flatten_text):
    assert "ORDER_ITEMS" in flatten_text
    assert "CREATE OR REPLACE TABLE" in flatten_text.upper()


def test_flatten_handles_nested_arrays(flatten_text):
    """Two-level LATERAL FLATTEN (shipments → lines) is in the demo."""
    assert "LATERAL FLATTEN" in flatten_text.upper()
    # Count occurrences: there should be 3 (orders->shipments, shipments->lines, lines baseline)
    assert flatten_text.upper().count("LATERAL FLATTEN") >= 2


def test_flatten_uses_value_keyword(flatten_text):
    assert "f.VALUE" in flatten_text or "VALUE:" in flatten_text
