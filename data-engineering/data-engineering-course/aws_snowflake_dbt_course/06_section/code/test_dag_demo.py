"""Tests for 06_section/code/dag_demo.sql."""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from conftest import render_jinja  # noqa: E402

SQL_PATH = pathlib.Path(__file__).resolve().parent / "dag_demo.sql"
SEED_PATH = pathlib.Path(__file__).resolve().parent / "category_seed.csv"


def _sql() -> str:
    return SQL_PATH.read_text()


def test_joins_two_models():
    """DAG demo must show a 2-model join via `{{ ref() }}`."""
    sql = _sql()
    assert sql.count("{{ ref(") >= 2, "expected 2+ ref() calls"


def test_renders_with_mock_context():
    rendered = render_jinja(_sql())
    assert "left join" in rendered.lower()
    assert "coalesce" in rendered.lower()


def test_uses_view_materialization():
    assert "view" in _sql()


def test_seed_csv_exists_and_valid():
    assert SEED_PATH.exists()
    lines = SEED_PATH.read_text().splitlines()
    assert lines[0] == "category_code,category_label"
    assert len(lines) >= 2


def test_author_signature():
    s = _sql()
    assert "Prem Vishnoi" in s
    assert "pvishnoi@avilx.com" in s
    assert "pvilx.com" not in s
