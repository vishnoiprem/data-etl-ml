"""
Tests for sqoop_ingest.

Pins two regression bugs:
  - ingest_wire_transfers used `sender_country` (not in synth wires);
    now joins to the customer master.
  - ingest_accounts used to crash on missing accounts.parquet; now
    warns and skips.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(HERE))

from scb_aml_platform.data.dummy.generate_dummy_data import main as _gen  # noqa: E402
from scb_aml_platform.ingestion.sqoop_ingest import (  # noqa: E402
    ingest_accounts, ingest_wire_transfers, run_all,
)
from scb_aml_platform.config.settings import BASE_DIR  # noqa: E402

DUMMY_DIR = Path(BASE_DIR) / "data" / "dummy"


@pytest.fixture(scope="module", autouse=True)
def _generate():
    _gen()
    yield


def test_accounts_parquet_exists():
    """The generator must now produce accounts.parquet."""
    assert (DUMMY_DIR / "accounts.parquet").exists()
    accounts = pd.read_parquet(DUMMY_DIR / "accounts.parquet")
    assert "account_id" in accounts.columns
    assert "customer_id" in accounts.columns
    assert (accounts["balance_usd"] > 0).all()


def test_ingest_accounts_runs(tmp_path, monkeypatch):
    """ingest_accounts should not crash on missing file."""
    from scb_aml_platform.ingestion import sqoop_ingest
    monkeypatch.setattr(sqoop_ingest, "DUMMY_DIR", tmp_path)
    # Should warn and return without raising
    sqoop_ingest.ingest_accounts("20260101")


def test_ingest_wire_transfers_derives_sender_country():
    """ingest_wire_transfers must not crash on missing `sender_country`."""
    # Run and verify no exception
    ingest_wire_transfers("20260101")


def test_run_all_completes(monkeypatch, tmp_path):
    """Full ingestion cycle: customers, accounts, transactions, wires, sanctions."""
    from scb_aml_platform.ingestion import sqoop_ingest

    # Use a fresh HDFS root to avoid clobbering
    monkeypatch.setattr(sqoop_ingest, "HDFS_ROOT", tmp_path / "hdfs")
    sqoop_ingest.HDFS_ROOT.mkdir(parents=True, exist_ok=True)
    run_date = sqoop_ingest.run_all("20260101")
    assert run_date == "20260101"
    # Should have written at least customers + txns + wires + sanctions
    assert any(sqoop_ingest.HDFS_ROOT.rglob("*.parquet"))
