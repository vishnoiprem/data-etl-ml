"""Tests for 19_data_sampling / sampling.sql."""
from __future__ import annotations

from pathlib import Path

import pytest

from conftest import parse_sql_statements

HERE = Path(__file__).resolve().parent
SQL_FILE = HERE / "sampling.sql"


@pytest.fixture(scope="module")
def sql_text() -> str:
    return SQL_FILE.read_text()


def test_uses_bernoulli_sampling(sql_text):
    assert "TABLESAMPLE BERNOULLI" in sql_text.upper()


def test_uses_system_sampling(sql_text):
    assert "TABLESAMPLE SYSTEM" in sql_text.upper()


def test_uses_sample_rows(sql_text):
    """`SAMPLE (N ROWS)` is exact-N, latency-friendly sampling."""
    assert "SAMPLE (1000 ROWS)" in sql_text.upper()


def test_uses_seed_for_repeatability(sql_text):
    assert "SEED" in sql_text.upper()


def test_builds_1m_row_table(sql_text):
    """The demo seeds a real table so sampling actually has something to sample."""
    assert "GENERATOR(ROWCOUNT => 1000000)" in sql_text.upper()


def test_compares_sample_to_full_aggregate(sql_text):
    """The pattern is: sample vs full aggregate — verify both branches exist."""
    assert "AVG(TOTAL_AMOUNT)" in sql_text.upper()
    assert sql_text.upper().count("AVG(TOTAL_AMOUNT)") >= 2


def test_sql_parses_cleanly(sql_text):
    stmts = parse_sql_statements(sql_text)
    assert len(stmts) >= 5
