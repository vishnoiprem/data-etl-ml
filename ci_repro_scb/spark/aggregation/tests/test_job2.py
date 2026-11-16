"""
Tests for Spark Job 2: Transaction Aggregation.

Covers three regression bugs that crashed job2 on the synthetic data:
  - load_data() used `value_date`; generator writes `wire_date`
  - compute_cross_border_flows() used `sender_country` (missing on synth)
  - run()'s nlargest crashed if summary was empty
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(HERE))

from scb_aml_platform.data.dummy.generate_dummy_data import main as _gen  # noqa: E402
from scb_aml_platform.spark.aggregation.job2_transaction_aggregation import (  # noqa: E402
    load_data, compute_cross_border_flows, run,
)
from scb_aml_platform.config.settings import BASE_DIR  # noqa: E402

DUMMY_DIR = Path(BASE_DIR) / "data" / "dummy"
PROCESSED_DIR = Path(BASE_DIR) / "data" / "processed"


@pytest.fixture(scope="module", autouse=True)
def _generate():
    _gen()
    yield


def test_load_data_normalizes_wire_date_to_value_date():
    """load_data() must produce wires with a `value_date` column even
    when the source parquet only has `wire_date`."""
    txns, wires, entities = load_data()
    assert "value_date" in wires.columns
    assert pd.api.types.is_datetime64_any_dtype(wires["value_date"])


def test_compute_cross_border_flows_runs_without_sender_country():
    """Cross-border used to read `sender_country`, which the synth
    generator does not produce. Now it uses receiver_country against
    a high-risk destination set."""
    _, wires, _ = load_data()
    cb = compute_cross_border_flows(wires)
    assert "cross_border_count" in cb.columns
    assert "cross_border_vol_usd" in cb.columns
    assert "unique_receiver_countries" in cb.columns
    assert (cb["cross_border_vol_usd"] >= 0).all()


def test_run_end_to_end_writes_summary():
    out = PROCESSED_DIR / "agg_customer_txn_summary.parquet"
    summary = run()
    assert out.exists(), "summary parquet not written"
    assert "customer_id" in summary.columns
    assert "volume_usd_30d" in summary.columns
    assert len(summary) > 0


def test_run_does_not_crash_on_empty_top_n(monkeypatch):
    """run() previously crashed with KeyError on `volume_usd_30d` if
    the window was empty. Now it guards."""
    import scb_aml_platform.spark.aggregation.job2_transaction_aggregation as j2

    # Force window_agg to return an empty frame for 30d
    real = j2.window_agg

    def empty_agg(*args, **kwargs):
        result = real(*args, **kwargs)
        if kwargs.get("window_days") == 30 or (
            len(args) >= 5 and args[4] == 30
        ):
            return result.iloc[0:0]
        return result

    monkeypatch.setattr(j2, "window_agg", empty_agg)
    # Should not raise
    j2.run()
