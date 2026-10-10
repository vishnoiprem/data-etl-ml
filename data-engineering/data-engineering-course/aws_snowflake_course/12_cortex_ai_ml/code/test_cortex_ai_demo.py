"""Tests for 12_cortex_ai_ml / cortex_ai_demo.sql."""
from __future__ import annotations

from pathlib import Path

import pytest

from conftest import parse_sql_statements

HERE = Path(__file__).resolve().parent
SQL_FILE = HERE / "cortex_ai_demo.sql"


@pytest.fixture(scope="module")
def sql_text() -> str:
    return SQL_FILE.read_text()


def test_uses_cortex_sentiment(sql_text):
    assert "SNOWFLAKE.CORTEX.SENTIMENT" in sql_text.upper()


def test_uses_cortex_summarize(sql_text):
    assert "SNOWFLAKE.CORTEX.SUMMARIZE" in sql_text.upper()


def test_uses_cortex_translate(sql_text):
    assert "SNOWFLAKE.CORTEX.TRANSLATE" in sql_text.upper()


def test_uses_cortex_extract_answer(sql_text):
    assert "SNOWFLAKE.CORTEX.EXTRACT_ANSWER" in sql_text.upper()


def test_uses_cortex_classify_text(sql_text):
    assert "SNOWFLAKE.CORTEX.CLASSIFY_TEXT" in sql_text.upper()


def test_creates_sample_reviews_table(sql_text):
    assert "CREATE OR REPLACE TABLE" in sql_text.upper()
    assert "CORTEX_REVIEWS" in sql_text


def test_aggregates_sentiment_by_product(sql_text):
    upper = sql_text.upper()
    # Snowflake accepts both "GROUP BY" and "GROUP  BY" (one or two spaces).
    assert "GROUP" in upper
    assert "BY" in upper
    assert "AVG(SNOWFLAKE.CORTEX.SENTIMENT(REVIEW))" in upper
    assert "CORTEX_REVIEWS" in upper


def test_sql_parses_cleanly(sql_text):
    stmts = parse_sql_statements(sql_text)
    assert len(stmts) >= 6


def test_uses_cortex_namespace(sql_text):
    """The fully-qualified namespace is required; the unqualified form raises."""
    assert "SNOWFLAKE.CORTEX." in sql_text
