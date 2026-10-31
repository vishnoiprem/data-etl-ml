"""
Tests for the entity resolution pipeline (Job 1).

Before the dummy data generator was fixed, this job crashed with
KeyError: 'id_number' on the first run. These tests pin the contract:
  - All required customer columns are produced (id_type, id_number,
    name_local_script)
  - The full pipeline runs to completion
  - Shared id_numbers across countries collapse into one golden entity
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(HERE))

from scb_aml_platform.data.dummy.generate_dummy_data import (  # noqa: E402
    main as _gen, DUMMY_DIR,
)


@pytest.fixture(scope="module", autouse=True)
def _generate():
    _gen()
    yield


REQUIRED_CUSTOMER_COLS = [
    "customer_id", "customer_name", "nationality", "country_code",
    "date_of_birth", "pep_flag", "pep_grade", "risk_rating",
    "id_type", "id_number", "name_local_script", "onboarded_date",
]


@pytest.mark.parametrize("col", REQUIRED_CUSTOMER_COLS)
def test_customers_have_required_column(col):
    """Every column the entity resolution / risk scoring jobs read
    must exist on the customers table."""
    customers = pd.read_parquet(DUMMY_DIR / "customers.parquet")
    assert col in customers.columns, f"missing {col} on customers.parquet"


def test_full_entity_resolution_runs():
    """End-to-end: Pass 1 (exact ID) + Pass 2 (fuzzy) + Pass 3 (phonetic)
    must all complete and produce a non-empty entity_master."""
    from scb_aml_platform.spark.entity_resolution.job1_entity_resolution import run
    master = run()
    assert not master.empty
    assert "golden_entity_id" in master.columns
    # The synthetic data intentionally shares some id_numbers across
    # countries, so unique golden IDs should be < customer count.
    customers = pd.read_parquet(DUMMY_DIR / "customers.parquet")
    assert master["golden_entity_id"].nunique() < len(customers)


def test_shared_id_collapses_to_single_golden():
    """Records sharing an id_number must share a golden_entity_id."""
    from scb_aml_platform.spark.entity_resolution.job1_entity_resolution import (
        pass1_exact_id, make_golden_id,
    )
    customers = pd.read_parquet(DUMMY_DIR / "customers.parquet")
    # Find a shared id_number
    shared = (
        customers[customers["id_number"].str.startswith("SHARED_", na=False)]
    )
    if shared.empty:
        pytest.skip("no shared id_numbers in this dataset")
    shared_id = shared["id_number"].iloc[0]
    group = customers[customers["id_number"] == shared_id]
    # After pass 1, all should have the same golden_entity_id
    df = pass1_exact_id(customers)
    group_after = df[df["id_number"] == shared_id]
    assert group_after["golden_entity_id"].nunique() == 1
