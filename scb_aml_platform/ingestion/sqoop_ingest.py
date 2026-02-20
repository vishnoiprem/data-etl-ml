"""
SCB AML Platform — Sqoop Batch Ingestion Simulator
Simulates Sqoop incremental imports from Oracle/DB2 source systems
into the HDFS Raw Landing Zone.

In production: sqoop import --connect jdbc:oracle:thin:@host --incremental lastmodified
Here: reads dummy Parquet files and writes partitioned ORC-like Parquet
      to the local HDFS simulation directory.
"""

import sys
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from scb_aml_platform.config.settings import (
    DUMMY_DIR, HDFS_ROOT, COUNTRIES, HDFS_PARTITION_TEMPLATE
)

DUMMY_DIR = Path(DUMMY_DIR)
HDFS_ROOT = Path(HDFS_ROOT)


def _partition_path(country: str, source: str, dt: str) -> Path:
    """Build HDFS partition path: /raw/{country}/{source}/{YYYY}/{MM}/{DD}/"""
    year, month, day = dt[:4], dt[4:6], dt[6:]
    rel = HDFS_PARTITION_TEMPLATE.format(
        country_code=country.lower(),
        source=source,
        year=year, month=month, day=day
    )
    return HDFS_ROOT / rel.lstrip("/")


def _write_partition(df: pd.DataFrame, path: Path, label: str):
    path.mkdir(parents=True, exist_ok=True)
    out = path / "part-00000.parquet"
    df.to_parquet(out, index=False)
    logger.info(f"  [{label}] {len(df):,} rows → {out}")


def ingest_customers(run_date: str):
    """Sqoop import: source_system=core_banking, table=customer_master"""
    logger.info("=== Sqoop: Ingesting customer_master ===")
    df = pd.read_parquet(DUMMY_DIR / "customers.parquet")

    for country in COUNTRIES:
        subset = df[df["country_code"] == country].copy()
        if subset.empty:
            continue
        subset["load_timestamp"] = datetime.utcnow().isoformat()
        subset["source_file"] = f"core_banking.customer_master.{run_date}"
        path = _partition_path(country, "customer_master", run_date)
        _write_partition(subset, path, f"customers/{country}")


def ingest_accounts(run_date: str):
    """Sqoop import: source_system=core_banking, table=account_master"""
    logger.info("=== Sqoop: Ingesting account_master ===")
    df = pd.read_parquet(DUMMY_DIR / "accounts.parquet")

    for country in COUNTRIES:
        subset = df[df["country_code"] == country].copy()
        if subset.empty:
            continue
        subset["load_timestamp"] = datetime.utcnow().isoformat()
        path = _partition_path(country, "account_master", run_date)
        _write_partition(subset, path, f"accounts/{country}")


def ingest_transactions(run_date: str):
    """Sqoop import: source_system=retail_banking, table=fact_transaction"""
    logger.info("=== Sqoop: Ingesting retail transactions ===")
    df = pd.read_parquet(DUMMY_DIR / "transactions.parquet")

    for country in COUNTRIES:
        subset = df[df["country_code"] == country].copy()
        if subset.empty:
            continue
        subset["load_timestamp"] = datetime.utcnow().isoformat()
        path = _partition_path(country, "fact_transaction", run_date)
        _write_partition(subset, path, f"transactions/{country}")


def ingest_wire_transfers(run_date: str):
    """Flat-file ingest: CIB SWIFT MT103/MT202 messages"""
    logger.info("=== Flat-file: Ingesting wire transfers (SWIFT) ===")
    df = pd.read_parquet(DUMMY_DIR / "wire_transfers.parquet")

    for country in COUNTRIES:
        subset = df[df["sender_country"] == country].copy()
        if subset.empty:
            continue
        subset["load_timestamp"] = datetime.utcnow().isoformat()
        path = _partition_path(country, "wire_transfer", run_date)
        _write_partition(subset, path, f"wire/{country}")


def ingest_sanctions_list(run_date: str):
    """Daily sanctions list refresh from OFAC/UN/EU feeds."""
    logger.info("=== External: Ingesting sanctions lists ===")
    df = pd.read_parquet(DUMMY_DIR / "sanctions_list.parquet")
    df["load_timestamp"] = datetime.utcnow().isoformat()
    # Sanctions list is not country-partitioned — stored in /raw/global/
    path = HDFS_ROOT / "raw" / "global" / "sanctions_list" / run_date[:4] / run_date[4:6] / run_date[6:]
    _write_partition(df, path, "sanctions_list/global")


def run_all(run_date: str = None):
    """Run full Sqoop ingestion cycle."""
    if run_date is None:
        run_date = datetime.utcnow().strftime("%Y%m%d")

    logger.info(f"Starting Sqoop ingestion run for date: {run_date}")
    ingest_customers(run_date)
    ingest_accounts(run_date)
    ingest_transactions(run_date)
    ingest_wire_transfers(run_date)
    ingest_sanctions_list(run_date)

    # Count files written
    total = sum(1 for _ in HDFS_ROOT.rglob("*.parquet"))
    logger.success(f"Ingestion complete. Total partition files: {total}")
    return run_date


if __name__ == "__main__":
    run_date = run_all()
    print(f"\nHDFS landing zone: {HDFS_ROOT}")
    print(f"Run date: {run_date}")
