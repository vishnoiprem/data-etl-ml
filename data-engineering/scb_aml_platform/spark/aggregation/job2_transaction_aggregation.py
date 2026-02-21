"""
SCB AML Platform — Spark Job 2: Transaction Aggregation
Phase 3, Step 2.

Computes per-customer aggregations at daily / weekly / monthly windows:
  - Transaction count and volume (USD)
  - Cross-border flow analysis (by country pair)
  - Counterparty frequency
  - Channel distribution

Output: data/processed/agg_customer_txn_summary.parquet
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from scb_aml_platform.config.settings import BASE_DIR

PROCESSED_DIR = Path(BASE_DIR) / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
DUMMY_DIR = Path(BASE_DIR) / "data" / "dummy"

# Reference date (end of dataset period)
REFERENCE_DATE = datetime(2018, 12, 31)


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load transactions, wire transfers, and entity master."""
    txns = pd.read_parquet(DUMMY_DIR / "transactions.parquet")
    wires = pd.read_parquet(DUMMY_DIR / "wire_transfers.parquet")

    entity_path = PROCESSED_DIR / "entity_master.parquet"
    if entity_path.exists():
        entities = pd.read_parquet(entity_path)
    else:
        entities = pd.read_parquet(DUMMY_DIR / "customers.parquet")
        entities["golden_entity_id"] = "GEI_" + entities["customer_id"]

    # Parse dates
    txns["txn_date"] = pd.to_datetime(txns["txn_date"], errors="coerce")
    wires["value_date"] = pd.to_datetime(wires["value_date"], errors="coerce")

    return txns, wires, entities


def window_agg(df: pd.DataFrame, id_col: str, amount_col: str,
               date_col: str, window_days: int, ref_date: datetime) -> pd.DataFrame:
    """Generic window aggregation for a given number of days."""
    cutoff = ref_date - timedelta(days=window_days)
    subset = df[df[date_col] >= cutoff].copy()

    agg = (
        subset.groupby(id_col)
        .agg(
            count=(amount_col, "count"),
            volume_usd=(amount_col, "sum"),
            avg_txn_usd=(amount_col, "mean"),
            max_txn_usd=(amount_col, "max"),
        )
        .reset_index()
    )
    suffix = f"_{window_days}d"
    agg.columns = [id_col] + [f"{c}{suffix}" for c in ["count", "volume_usd", "avg_txn_usd", "max_txn_usd"]]
    return agg


def compute_cross_border_flows(wires: pd.DataFrame) -> pd.DataFrame:
    """Summarise cross-border wire transfer flows per sender."""
    wires = wires.copy()
    wires["is_cross_border"] = wires["sender_country"] != wires["receiver_country"]

    cross = wires[wires["is_cross_border"]].copy()

    cb_agg = (
        cross.groupby("sender_customer_id")
        .agg(
            cross_border_count=("wire_id", "count"),
            cross_border_vol_usd=("amount_usd", "sum"),
            unique_receiver_countries=("receiver_country", "nunique"),
            avg_wire_usd=("amount_usd", "mean"),
        )
        .reset_index()
        .rename(columns={"sender_customer_id": "customer_id"})
    )
    return cb_agg


def compute_counterparty_stats(txns: pd.DataFrame) -> pd.DataFrame:
    """Counterparty diversity and frequency."""
    cp = (
        txns.groupby("customer_id")["counterparty_id"]
        .agg(unique_counterparties="nunique")
        .reset_index()
    )
    return cp


def compute_volume_velocity(txns: pd.DataFrame) -> pd.DataFrame:
    """Week-over-week volume change percentage — key structuring indicator."""
    txns = txns.copy()
    txns["week"] = txns["txn_date"].dt.isocalendar().week.astype(int)
    txns["year"] = txns["txn_date"].dt.year

    weekly = (
        txns.groupby(["customer_id", "year", "week"])["amount_usd"]
        .sum()
        .reset_index()
        .sort_values(["customer_id", "year", "week"])
    )
    weekly["prev_vol"] = weekly.groupby("customer_id")["amount_usd"].shift(1)
    weekly["volume_change_pct"] = (
        (weekly["amount_usd"] - weekly["prev_vol"]) / weekly["prev_vol"].replace(0, np.nan) * 100
    ).round(2)

    # Latest week per customer
    latest = weekly.groupby("customer_id").last().reset_index()[
        ["customer_id", "volume_change_pct"]
    ]
    return latest


def run() -> pd.DataFrame:
    logger.info("=" * 60)
    logger.info("Spark Job 2: Transaction Aggregation")
    logger.info("=" * 60)

    txns, wires, entities = load_data()
    logger.info(f"Transactions: {len(txns):,} | Wires: {len(wires):,} | Entities: {len(entities):,}")

    # ── Window aggregations
    agg_7d = window_agg(txns, "customer_id", "amount_usd", "txn_date", 7, REFERENCE_DATE)
    agg_30d = window_agg(txns, "customer_id", "amount_usd", "txn_date", 30, REFERENCE_DATE)
    agg_90d = window_agg(txns, "customer_id", "amount_usd", "txn_date", 90, REFERENCE_DATE)

    # ── Cross-border flows
    cb = compute_cross_border_flows(wires)

    # ── Counterparty stats
    cp = compute_counterparty_stats(txns)

    # ── Volume velocity
    vel = compute_volume_velocity(txns)

    # ── Normalise entity key: entity_master uses entity_id, raw customers use customer_id
    if "entity_id" in entities.columns and "customer_id" not in entities.columns:
        entities = entities.rename(columns={"entity_id": "customer_id"})

    # ── Select available columns defensively
    base_cols = ["customer_id"]
    for col in ["golden_entity_id", "customer_name", "risk_rating",
                "risk_score", "country_code", "country_codes"]:
        if col in entities.columns:
            base_cols.append(col)
    summary = entities[base_cols].copy()

    # Ensure a risk_rating-like column exists for downstream compatibility
    if "risk_rating" not in summary.columns and "risk_score" in summary.columns:
        summary["risk_rating"] = summary["risk_score"].apply(
            lambda s: "high" if s >= 70 else "medium" if s >= 40 else "low"
        )
    if "country_code" not in summary.columns and "country_codes" in summary.columns:
        summary["country_code"] = summary["country_codes"].apply(
            lambda v: v[0] if isinstance(v, list) and v else str(v)[:2]
        )

    for agg_df in [agg_7d, agg_30d, agg_90d]:
        summary = summary.merge(agg_df, on="customer_id", how="left")

    summary = summary.merge(cb, on="customer_id", how="left")
    summary = summary.merge(cp, on="customer_id", how="left")
    summary = summary.merge(vel, on="customer_id", how="left")

    # Fill nulls
    num_cols = summary.select_dtypes(include=[np.number]).columns
    summary[num_cols] = summary[num_cols].fillna(0)

    # Add aggregation date
    summary["agg_date"] = REFERENCE_DATE.strftime("%Y-%m-%d")

    out = PROCESSED_DIR / "agg_customer_txn_summary.parquet"
    summary.to_parquet(out, index=False)
    logger.success(f"Transaction aggregation: {len(summary):,} customers → {out}")

    # Quick stats
    logger.info("\nTop 5 customers by 30d volume (USD):")
    top5 = summary.nlargest(5, "volume_usd_30d")[
        ["customer_id", "customer_name", "volume_usd_30d", "cross_border_vol_usd", "risk_rating"]
    ]
    logger.info(f"\n{top5.to_string(index=False)}")

    return summary


if __name__ == "__main__":
    run()
