"""
Tests for the Data Analyst
==========================
Run:  pytest tests/
"""

import os
import pytest
import tempfile
import pandas as pd


# =============================================================================
# UNIT TESTS (no API calls)
# =============================================================================

def test_infer_schema_basic(tmp_path):
    from dataframe_ops import infer_schema
    csv = tmp_path / "tiny.csv"
    csv.write_text("name,age,city\nAlice,30,NYC\nBob,25,LA\n")
    schema, n_rows, n_cols = infer_schema(str(csv))
    assert n_rows == 2
    assert n_cols == 3
    assert schema[0]["name"] == "name"
    assert schema[0]["dtype"] in ("object", "string")
    assert schema[1]["name"] == "age"


def test_code_validation_bans_subprocess():
    from code_executor import validate_code
    with pytest.raises(ValueError, match="Banned import"):
        validate_code("import subprocess\nsubprocess.run(['ls'])")


def test_code_validation_bans_eval():
    from code_executor import validate_code
    with pytest.raises(ValueError, match="Banned builtin"):
        validate_code("eval('1+1')")


def test_code_validation_allows_pandas():
    from code_executor import validate_code
    validate_code("import pandas as pd\nresult = df.groupby('x').sum()")


def test_visualizer_bar():
    from visualizer import pick_and_render_chart
    rows = [{"region": "US", "revenue": 100}, {"region": "EU", "revenue": 80}]
    fig = pick_and_render_chart(rows)
    assert fig is not None
    assert fig["data"][0]["type"] == "bar"


def test_visualizer_no_numeric():
    from visualizer import pick_and_render_chart
    rows = [{"name": "Alice"}, {"name": "Bob"}]
    assert pick_and_render_chart(rows) is None


# =============================================================================
# INTEGRATION TESTS (require API key)
# =============================================================================

@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
def test_end_to_end(tmp_path):
    from dataframe_ops import infer_schema, generate_pandas_code
    from code_executor import run_pandas_code

    csv = tmp_path / "sales.csv"
    csv.write_text("region,revenue\nUS,100\nEU,80\nUS,150\nEU,90\nAPAC,50\n")
    schema, n_rows, n_cols = infer_schema(str(csv))
    assert n_rows == 5

    code, cost = generate_pandas_code(
        question="What's the total revenue by region?",
        schema=schema,
        csv_path=str(csv),
        openai_api_key=os.environ["OPENAI_API_KEY"],
    )
    assert "result" in code
    assert cost > 0
    assert cost < 0.05

    rows, log = run_pandas_code(code, str(csv))
    assert len(rows) == 3
    regions = {r["region"] for r in rows}
    assert regions == {"US", "EU", "APAC"}
