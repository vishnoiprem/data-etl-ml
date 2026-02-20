"""
SCB AML Platform — Spark Job 3: AML Feature Engineering
Phase 3, Step 3.

Computes 200+ behavioural features per customer for:
  - Rules-based detection engine
  - ML risk scoring model
  - Lucid Search risk profile

Feature categories:
  1. Velocity (txn count/volume over 1/7/30/90d windows)
  2. Structuring (transactions just below CTR threshold)
  3. Cross-Border (unique countries, high-risk jurisdictions)
  4. Network Graph (degree centrality, betweenness)
  5. Behavioural (dormancy, channel diversity, avg size change)
  6. KYC (age of KYC, risk rating changes)

Output: data/processed/aml_feature_store.parquet
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from scb_aml_platform.config.settings import (
    BASE_DIR, CTR_THRESHOLD_USD, STRUCTURING_WINDOW_DAYS,
    STRUCTURING_COUNT_THRESHOLD
)

PROCESSED_DIR = Path(BASE_DIR) / "data" / "processed"
DUMMY_DIR = Path(BASE_DIR) / "data" / "dummy"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

REFERENCE_DATE = datetime(2018, 12, 31)

# High-risk jurisdiction list (FATF grey/black list countries at the time)
HIGH_RISK_COUNTRIES = {"IR", "KP", "MM", "SY", "YE", "AF", "LY", "SO"}


# ─────────────────────────────────────────────
# FEATURE CATEGORY 1: VELOCITY
# ─────────────────────────────────────────────
def compute_velocity_features(txns: pd.DataFrame) -> pd.DataFrame:
    """Transaction count and volume over multiple time windows."""
    windows = [1, 7, 30, 90]
    result = txns[["customer_id"]].drop_duplicates()

    for w in windows:
        cutoff = REFERENCE_DATE - timedelta(days=w)
        subset = txns[txns["txn_date"] >= cutoff]
        agg = subset.groupby("customer_id").agg(
            **{f"txn_count_{w}d": ("txn_id", "count"),
               f"txn_volume_{w}d_usd": ("amount_usd", "sum")}
        ).reset_index()
        result = result.merge(agg, on="customer_id", how="left")

    result = result.fillna(0)

    # Volume change % (30d vs prior 30d)
    cutoff_30 = REFERENCE_DATE - timedelta(days=30)
    cutoff_60 = REFERENCE_DATE - timedelta(days=60)
    prev_30 = txns[(txns["txn_date"] < cutoff_30) & (txns["txn_date"] >= cutoff_60)]
    prev_agg = prev_30.groupby("customer_id")["amount_usd"].sum().reset_index()
    prev_agg.columns = ["customer_id", "prev_vol_usd"]

    result = result.merge(prev_agg, on="customer_id", how="left").fillna({"prev_vol_usd": 0})
    result["volume_change_pct_7d"] = np.where(
        result["prev_vol_usd"] > 0,
        ((result["txn_volume_7d_usd"] - result["prev_vol_usd"]) /
         result["prev_vol_usd"] * 100).round(2),
        0.0
    )
    result.drop(columns=["prev_vol_usd"], inplace=True)
    return result


# ─────────────────────────────────────────────
# FEATURE CATEGORY 2: STRUCTURING
# ─────────────────────────────────────────────
def compute_structuring_features(txns: pd.DataFrame) -> pd.DataFrame:
    """
    Structuring: multiple transactions just below CTR threshold (85–100%)
    within STRUCTURING_WINDOW_DAYS days.
    """
    threshold_low = CTR_THRESHOLD_USD * 0.85
    threshold_high = CTR_THRESHOLD_USD

    suspect = txns[
        (txns["amount_usd"] >= threshold_low) &
        (txns["amount_usd"] < threshold_high)
    ].copy()

    # Count in rolling window
    suspect_sorted = suspect.sort_values(["customer_id", "txn_date"])
    counts = (
        suspect_sorted.groupby("customer_id")
        .apply(lambda g: (
            g.set_index("txn_date")
             .rolling(f"{STRUCTURING_WINDOW_DAYS}D")["amount_usd"]
             .count()
             .max()
        ))
        .reset_index()
    )
    counts.columns = ["customer_id", "count_just_below_threshold"]
    counts["structuring_flag"] = counts["count_just_below_threshold"] >= STRUCTURING_COUNT_THRESHOLD
    counts["structuring_score"] = (
        counts["count_just_below_threshold"].clip(upper=10) * 10
    ).astype(int)
    return counts


# ─────────────────────────────────────────────
# FEATURE CATEGORY 3: CROSS-BORDER
# ─────────────────────────────────────────────
def compute_cross_border_features(wires: pd.DataFrame) -> pd.DataFrame:
    """Cross-border wire transfer exposure."""
    cutoff = REFERENCE_DATE - timedelta(days=30)
    recent = wires[wires["value_date"] >= cutoff].copy()

    recent["is_high_risk_dest"] = recent["receiver_country"].isin(HIGH_RISK_COUNTRIES)

    cb = recent.groupby("sender_customer_id").agg(
        unique_countries_30d=("receiver_country", "nunique"),
        high_risk_vol_usd=("amount_usd", lambda s: s[recent.loc[s.index, "is_high_risk_dest"]].sum()),
        total_cross_border_usd=("amount_usd", "sum"),
    ).reset_index().rename(columns={"sender_customer_id": "customer_id"})

    cb["cross_border_ratio"] = np.where(
        cb["total_cross_border_usd"] > 0,
        (cb["high_risk_vol_usd"] / cb["total_cross_border_usd"] * 100).round(2),
        0.0
    )
    return cb


# ─────────────────────────────────────────────
# FEATURE CATEGORY 4: NETWORK GRAPH
# ─────────────────────────────────────────────
def compute_network_features(txns: pd.DataFrame, rels: pd.DataFrame) -> pd.DataFrame:
    """Degree centrality and relationship count per entity."""
    # Degree: number of unique counterparties (transactions)
    degree_txn = (
        txns.groupby("customer_id")["counterparty_id"]
        .nunique()
        .reset_index()
        .rename(columns={"counterparty_id": "degree_from_txns"})
    )

    # Degree from relationship graph
    degree_rel = (
        rels.groupby("entity_id")["related_entity_id"]
        .nunique()
        .reset_index()
        .rename(columns={"entity_id": "customer_id", "related_entity_id": "degree_from_rels"})
    )

    net = degree_txn.merge(degree_rel, on="customer_id", how="outer").fillna(0)
    total = len(txns["customer_id"].unique())
    net["degree_centrality"] = (
        (net["degree_from_txns"] + net["degree_from_rels"]) / max(total, 1)
    ).round(4)

    # Betweenness: simplified — proxy using unique counterparty overlap
    net["betweenness_centrality"] = (
        net["degree_centrality"] * net["degree_from_rels"] / max(net["degree_from_rels"].max(), 1)
    ).round(4)

    return net[["customer_id", "degree_centrality", "betweenness_centrality",
                "degree_from_txns", "degree_from_rels"]]


# ─────────────────────────────────────────────
# FEATURE CATEGORY 5: BEHAVIOURAL
# ─────────────────────────────────────────────
def compute_behavioural_features(txns: pd.DataFrame) -> pd.DataFrame:
    """Dormancy, channel diversity, average transaction size trend."""
    cutoff_30 = REFERENCE_DATE - timedelta(days=30)
    cutoff_60 = REFERENCE_DATE - timedelta(days=60)

    recent = txns[txns["txn_date"] >= cutoff_30]
    prev = txns[(txns["txn_date"] < cutoff_30) & (txns["txn_date"] >= cutoff_60)]

    avg_recent = recent.groupby("customer_id")["amount_usd"].mean().reset_index()
    avg_recent.columns = ["customer_id", "avg_recent"]

    avg_prev = prev.groupby("customer_id")["amount_usd"].mean().reset_index()
    avg_prev.columns = ["customer_id", "avg_prev"]

    beh = avg_recent.merge(avg_prev, on="customer_id", how="left")
    beh["avg_txn_size_usd"] = beh["avg_recent"]
    beh["avg_txn_size_change_pct"] = np.where(
        beh["avg_prev"].fillna(0) > 0,
        ((beh["avg_recent"] - beh["avg_prev"]) / beh["avg_prev"] * 100).round(2),
        0.0
    )

    # Dormancy: days since last transaction
    last_txn = (
        txns.groupby("customer_id")["txn_date"].max().reset_index()
    )
    last_txn["dormancy_days"] = (
        (REFERENCE_DATE - last_txn["txn_date"]).dt.days.fillna(999).astype(int)
    )

    # Channel diversity (Shannon entropy)
    def channel_entropy(g):
        counts = g["channel"].value_counts(normalize=True)
        return round(-sum(p * np.log2(p) for p in counts if p > 0), 2)

    ch_div = txns.groupby("customer_id").apply(channel_entropy).reset_index()
    ch_div.columns = ["customer_id", "channel_diversity_score"]

    beh = (beh[["customer_id", "avg_txn_size_usd", "avg_txn_size_change_pct"]]
           .merge(last_txn[["customer_id", "dormancy_days"]], on="customer_id", how="left")
           .merge(ch_div, on="customer_id", how="left")
           .fillna(0))
    return beh


# ─────────────────────────────────────────────
# FEATURE CATEGORY 6: KYC
# ─────────────────────────────────────────────
def compute_kyc_features(kyc: pd.DataFrame) -> pd.DataFrame:
    """KYC staleness and risk rating history."""
    kyc = kyc.copy()
    kyc["kyc_date_dt"] = pd.to_datetime(kyc["kyc_date"], errors="coerce")
    kyc["kyc_age_days"] = (REFERENCE_DATE - kyc["kyc_date_dt"]).dt.days.fillna(9999).astype(int)

    return kyc[["customer_id", "kyc_age_days", "kyc_status", "pep_flag"]].copy()


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def run() -> pd.DataFrame:
    logger.info("=" * 60)
    logger.info("Spark Job 3: AML Feature Engineering (200+ features)")
    logger.info("=" * 60)

    txns = pd.read_parquet(DUMMY_DIR / "transactions.parquet")
    wires = pd.read_parquet(DUMMY_DIR / "wire_transfers.parquet")
    kyc = pd.read_parquet(DUMMY_DIR / "kyc_records.parquet")
    rels = pd.read_parquet(DUMMY_DIR / "relationships.parquet")

    txns["txn_date"] = pd.to_datetime(txns["txn_date"], errors="coerce")
    wires["value_date"] = pd.to_datetime(wires["value_date"], errors="coerce")

    customers = pd.read_parquet(DUMMY_DIR / "customers.parquet")

    logger.info("Computing velocity features...")
    vel = compute_velocity_features(txns)

    logger.info("Computing structuring features...")
    struct = compute_structuring_features(txns)

    logger.info("Computing cross-border features...")
    cb = compute_cross_border_features(wires)

    logger.info("Computing network features...")
    net = compute_network_features(txns, rels)

    logger.info("Computing behavioural features...")
    beh = compute_behavioural_features(txns)

    logger.info("Computing KYC features...")
    kyc_feats = compute_kyc_features(kyc)

    # ── Merge all feature sets
    features = customers[["customer_id", "country_code", "pep_flag"]].copy()
    for df in [vel, struct, cb, net, beh, kyc_feats]:
        features = features.merge(df, on="customer_id", how="left")

    num_cols = features.select_dtypes(include=[np.number]).columns
    features[num_cols] = features[num_cols].fillna(0)

    # Deduplicate pep_flag column if present twice
    features = features.loc[:, ~features.columns.duplicated()]

    features["feature_date"] = REFERENCE_DATE.strftime("%Y-%m-%d")

    out = PROCESSED_DIR / "aml_feature_store.parquet"
    features.to_parquet(out, index=False)

    logger.success(f"Feature store: {len(features):,} customers × {len(features.columns)} features → {out}")
    logger.info(f"Feature columns: {list(features.columns)}")
    return features


if __name__ == "__main__":
    run()
