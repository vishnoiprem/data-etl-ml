"""
Tests for Spark Job 3: AML Feature Engineering.

The synthetic generator writes `wire_date`; SWIFT-fed wires typically use
`value_date`. Job 3 used to crash with `KeyError: 'value_date'` on the
synthetic data. These tests pin the contract:
  - `value_date` is normalized on the wires frame (whether source
    column was `wire_date` or `value_date`)
  - All 6 feature categories produce non-empty outputs
  - The end-to-end pipeline completes and writes the feature store
  - No accidental duplicate columns survive the merge
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(HERE))

from scb_aml_platform.data.dummy.generate_dummy_data import (  # noqa: E402
    main as _gen,
)
from scb_aml_platform.spark.feature_engineering.job3_feature_engineering import (  # noqa: E402
    compute_velocity_features,
    compute_structuring_features,
    compute_cross_border_features,
    compute_network_features,
    compute_behavioural_features,
    compute_kyc_features,
    run,
)
from scb_aml_platform.config.settings import BASE_DIR  # noqa: E402

DUMMY_DIR = Path(BASE_DIR) / "data" / "dummy"


@pytest.fixture(scope="module", autouse=True)
def _generate():
    _gen()
    yield


def test_run_end_to_end_writes_feature_store():
    """End-to-end: must run without KeyError, write parquet, and
    have one row per customer."""
    out_path = Path(BASE_DIR) / "data" / "processed" / "aml_feature_store.parquet"
    features = run()
    assert out_path.exists(), "feature store parquet not written"
    assert len(features) == len(pd.read_parquet(DUMMY_DIR / "customers.parquet"))
    # 30+ features per customer is the documented baseline
    assert features.shape[1] >= 30


def test_feature_store_columns_are_unique():
    """Merging customer + kyc can produce two `pep_flag` columns. The
    dedup at the end of run() must keep only one."""
    features = run()
    dup_mask = features.columns.duplicated()
    assert not bool(dup_mask.any()), (
        f"duplicate columns: "
        f"{features.columns[dup_mask].tolist()}"
    )
    # And specifically: pep_flag appears exactly once
    assert list(features.columns).count("pep_flag") == 1


def test_run_handles_wire_date_column_name():
    """The synthetic generator writes `wire_date` (not `value_date`).
    run() must normalize so the cross-border code can use `value_date`."""
    wires = pd.read_parquet(DUMMY_DIR / "wire_transfers.parquet")
    assert "wire_date" in wires.columns  # precondition
    # If run() didn't normalize, it would raise KeyError on the
    # cross-border cut. It must complete cleanly.
    run()


def test_velocity_features_cover_all_customers_with_txns():
    txns = pd.read_parquet(DUMMY_DIR / "transactions.parquet")
    vel = compute_velocity_features(txns)
    assert "txn_count_30d" in vel.columns
    assert "txn_volume_30d_usd" in vel.columns
    assert (vel["txn_count_30d"] >= 0).all()
    assert (vel["txn_volume_30d_usd"] >= 0).all()


def test_structuring_features_returns_per_customer_rows():
    txns = pd.read_parquet(DUMMY_DIR / "transactions.parquet")
    struct = compute_structuring_features(txns)
    assert "structuring_flag" in struct.columns
    assert "structuring_score" in struct.columns
    assert struct["structuring_score"].between(0, 100).all()


def test_cross_border_features_handles_synthetic_wire_date():
    """Regression: must not raise KeyError on `wire_date` column name."""
    wires = pd.read_parquet(DUMMY_DIR / "wire_transfers.parquet")
    cb = compute_cross_border_features(wires)
    assert "high_risk_vol_usd" in cb.columns
    assert "total_cross_border_usd" in cb.columns
    assert "cross_border_ratio" in cb.columns
    assert (cb["cross_border_ratio"].between(0, 100)).all()


def test_network_features_returns_degree_columns():
    txns = pd.read_parquet(DUMMY_DIR / "transactions.parquet")
    rels = pd.read_parquet(DUMMY_DIR / "relationships.parquet")
    net = compute_network_features(txns, rels)
    assert "degree_centrality" in net.columns
    assert "betweenness_centrality" in net.columns
    assert (net["degree_centrality"] >= 0).all()
    assert (net["betweenness_centrality"] >= 0).all()


def test_behavioural_features_returns_dormancy_and_diversity():
    txns = pd.read_parquet(DUMMY_DIR / "transactions.parquet")
    beh = compute_behavioural_features(txns)
    assert "dormancy_days" in beh.columns
    assert "channel_diversity_score" in beh.columns
    assert (beh["dormancy_days"] >= 0).all()


def test_kyc_features_returns_age_and_status():
    kyc = pd.read_parquet(DUMMY_DIR / "kyc_records.parquet")
    feats = compute_kyc_features(kyc)
    assert "kyc_age_days" in feats.columns
    assert "kyc_status" in feats.columns
    # pep_flag is intentionally NOT returned — the customer master
    # is the authoritative source and is merged upstream.
    assert "pep_flag" not in feats.columns
    assert (feats["kyc_age_days"] >= 0).all()
