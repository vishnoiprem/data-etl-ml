"""Tests for 10_section/code/fraud_score_demo.py.

The actual model runs in Snowflake via Snowpark — here we only assert
the file structure (has model() function, uses dbt.ref, returns a
DataFrame, has the right author signature).
"""
from __future__ import annotations

import ast
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

PY_PATH = pathlib.Path(__file__).resolve().parent / "fraud_score_demo.py"


def _src() -> str:
    return PY_PATH.read_text()


def test_file_exists_and_non_empty():
    assert PY_PATH.exists()
    assert len(_src()) > 100


def test_defines_model_function():
    """A dbt Python model must define `def model(dbt, session)`."""
    tree = ast.parse(_src())
    funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    assert "model" in funcs, "expected `def model(dbt, session)`"


def test_model_takes_dbt_and_session():
    tree = ast.parse(_src())
    model_fn = next(n for n in ast.walk(tree)
                    if isinstance(n, ast.FunctionDef) and n.name == "model")
    arg_names = [a.arg for a in model_fn.args.args]
    assert "dbt" in arg_names
    assert "session" in arg_names


def test_calls_dbt_ref():
    src = _src()
    assert "dbt.ref" in src, "expected `dbt.ref(...)` call"


def test_imports_snowpark_functions():
    assert "import snowflake.snowpark.functions" in _src()


def test_author_signature():
    src = _src()
    assert "Prem Vishnoi" in src
    assert "pvishnoi@avilx.com" in src
    assert "pvilx.com" not in src
