"""
Tests for the synthetic data generator.

The generator is what makes the rest of the platform runnable on a fresh
checkout. Before it existed, `pipeline_orchestrator.py` step 0 crashed
with `ModuleNotFoundError: scb_aml_platform.data.dummy.generate_dummy_data`,
which made every downstream test fail at the import stage.

These tests verify:
  - All 5 expected parquets are written
  - Manifest is written and parses
  - Re-running is idempotent (deterministic seed)
  - Customer coverage spans all 15 countries
  - At least one PEP exists (so the PEP-wire rule is exercisable)
  - Transactions have some rows over the CTR threshold (so the CTR
    rule is exercisable)
"""

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(HERE))

from scb_aml_platform.config.settings import (  # noqa: E402
    BASE_DIR, COUNTRIES, CTR_THRESHOLD_USD,
)
from scb_aml_platform.data.dummy.generate_dummy_data import (  # noqa: E402
    main as gen_main, DUMMY_DIR,
)


@pytest.fixture(scope="module", autouse=True)
def _generate_once():
    """Run the generator once for the test module."""
    gen_main()
    yield


REQUIRED_PARQUETS = [
    "customers.parquet",
    "transactions.parquet",
    "wire_transfers.parquet",
    "relationships.parquet",
    "kyc_records.parquet",
    "sanctions_list.parquet",
    "accounts.parquet",
]


@pytest.mark.parametrize("filename", REQUIRED_PARQUETS)
def test_all_required_parquets_exist(filename):
    """Every parquet the platform depends on must be produced."""
    assert (DUMMY_DIR / filename).exists(), f"missing {filename}"


def test_manifest_written_and_valid():
    manifest_path = DUMMY_DIR / "manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text())
    assert manifest["all_synthetic"] is True
    assert "seed" in manifest
    assert set(COUNTRIES).issubset(set(manifest["countries"]))
    for key in ("customers", "transactions", "wire_transfers", "relationships"):
        assert key in manifest["counts"]
        assert manifest["counts"][key] > 0


def test_customers_cover_all_15_countries():
    customers = pd.read_parquet(DUMMY_DIR / "customers.parquet")
    covered = set(customers["country_code"].unique())
    missing = set(COUNTRIES) - covered
    assert not missing, f"countries with zero customers: {missing}"


def test_at_least_one_pep_exists():
    customers = pd.read_parquet(DUMMY_DIR / "customers.parquet")
    pep_count = int((customers["pep_flag"] == "Y").sum())
    assert pep_count >= 1, "no PEPs — the PEP-wire rule R04 won't fire"


def test_at_least_some_transactions_over_ctr():
    """The CTR rule (R01) flags txns ≥ CTR_THRESHOLD_USD. Without any
    such txns in the synthetic data, the rule is untestable."""
    txns = pd.read_parquet(DUMMY_DIR / "transactions.parquet")
    over_ctr = int((txns["amount_usd"] >= CTR_THRESHOLD_USD).sum())
    assert over_ctr >= 1, (
        f"no txns ≥ CTR_THRESHOLD_USD ({CTR_THRESHOLD_USD:,}) — "
        f"R01 will never fire on this dataset"
    )


def test_kyc_records_match_customer_count():
    """KYC is 1:1 with customers (one KYC record per customer)."""
    customers = pd.read_parquet(DUMMY_DIR / "customers.parquet")
    kyc = pd.read_parquet(DUMMY_DIR / "kyc_records.parquet")
    assert len(kyc) == len(customers)


def test_wires_have_sender_and_amount():
    """R04 (PEP wire ≥ 50k) needs both sender_customer_id and amount_usd."""
    wires = pd.read_parquet(DUMMY_DIR / "wire_transfers.parquet")
    assert "sender_customer_id" in wires.columns
    assert "amount_usd" in wires.columns
    assert wires["amount_usd"].notna().all()
    assert (wires["amount_usd"] > 0).all()


def test_deterministic_rerun():
    """Re-running with the same seed should produce identical customers.

    This protects against hidden nondeterminism (e.g. random.seed() in
    the wrong order) that would make regression tests flaky.
    """
    before = pd.read_parquet(DUMMY_DIR / "customers.parquet")
    gen_main()
    after = pd.read_parquet(DUMMY_DIR / "customers.parquet")
    assert (before["customer_id"].tolist() == after["customer_id"].tolist())
    assert (before["customer_name"].tolist() == after["customer_name"].tolist())
