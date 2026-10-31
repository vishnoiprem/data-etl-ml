"""
Tests for Spark Job 4: Sanctions & PEP Screening.

The synthetic generator now produces a sanctions_list.parquet with
Ivan Petrov, Mohammed Al-Rahman, Kim Song. These tests pin:
  - The screening job runs to completion
  - It writes screening_alerts.parquet
  - PEP relationship inference flags associated entities
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(HERE))

from scb_aml_platform.data.dummy.generate_dummy_data import main as _gen  # noqa: E402
from scb_aml_platform.spark.screening.job4_sanctions_pep_screening import run  # noqa: E402
from scb_aml_platform.config.settings import BASE_DIR  # noqa: E402

DUMMY_DIR = Path(BASE_DIR) / "data" / "dummy"
PROCESSED_DIR = Path(BASE_DIR) / "data" / "processed"


@pytest.fixture(scope="module", autouse=True)
def _generate():
    _gen()
    yield


def test_sanctions_list_parquet_exists():
    assert (DUMMY_DIR / "sanctions_list.parquet").exists()
    sl = pd.read_parquet(DUMMY_DIR / "sanctions_list.parquet")
    assert "entity_name" in sl.columns
    assert "name_variants" in sl.columns
    # Synthetic generator includes Ivan Petrov, Mohammed Al-Rahman, Kim Song
    names = sl["entity_name"].tolist()
    assert any("Petrov" in n for n in names)


def test_screening_runs_to_completion():
    out = PROCESSED_DIR / "screening_alerts.parquet"
    alerts = run()
    assert out.exists()
    assert "screening_id" in alerts.columns
    assert "customer_id" in alerts.columns
    assert "match_score" in alerts.columns
    # PEP inference should have produced at least one alert
    assert len(alerts) > 0


def test_screening_score_in_valid_range():
    alerts = run()
    assert alerts["match_score"].between(0, 100).all()
