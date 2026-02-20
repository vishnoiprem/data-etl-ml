"""
SCB AML Platform — Risk Scoring Engine
AML Detection Layer, Component 2.

Computes three composite risk scores per customer:
  CRS — Customer Risk Score   (KYC + PEP + demographics)
  TRS — Transaction Risk Score (behavioural + velocity + structuring)
  NRS — Network Risk Score     (counterparty graph + cross-border)

Final composite AML Score = 0.35*CRS + 0.40*TRS + 0.25*NRS (0–100)
Risk bands:
  0–30  LOW
  31–60 MEDIUM
  61–80 HIGH
  81–100 CRITICAL

Output: data/processed/customer_risk_profiles.parquet
"""

import sys
from pathlib import Path

import pandas as pd
import numpy as np
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from scb_aml_platform.config.settings import (
    BASE_DIR, RISK_LOW_MAX, RISK_MEDIUM_MAX, RISK_HIGH_MIN
)

PROCESSED_DIR = Path(BASE_DIR) / "data" / "processed"
DUMMY_DIR = Path(BASE_DIR) / "data" / "dummy"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# CRS — Customer Risk Score
# ─────────────────────────────────────────────
def compute_crs(customers: pd.DataFrame, kyc: pd.DataFrame) -> pd.DataFrame:
    """
    CRS components:
      - Base risk rating:  low=10, medium=40, high=80
      - PEP flag:          +20 for PEP-A, +15 PEP-B, +10 PEP-C
      - KYC staleness:     +10 if >365 days, +20 if >730 days
      - ID verified:       -5 if verified
      - KYC status:        +10 if expired or pending
    """
    df = customers.merge(
        kyc[["customer_id", "kyc_age_days", "kyc_status",
             "id_verified", "pep_flag"]].rename(columns={"pep_flag": "kyc_pep"}),
        on="customer_id", how="left"
    )

    # Base
    df["crs"] = df["risk_rating"].map({"low": 10, "medium": 40, "high": 80}).fillna(10)

    # PEP modifier
    pep_grade_mod = {"A": 20, "B": 15, "C": 10}
    df["pep_mod"] = df.apply(
        lambda r: pep_grade_mod.get(str(r.get("pep_grade", "")), 0)
        if r["pep_flag"] == "Y" else 0,
        axis=1
    )
    df["crs"] = (df["crs"] + df["pep_mod"]).clip(upper=100)

    # KYC staleness
    df["kyc_age_days"] = df["kyc_age_days"].fillna(999)
    df["kyc_stale"] = np.where(df["kyc_age_days"] > 730, 20,
                      np.where(df["kyc_age_days"] > 365, 10, 0))
    df["crs"] = (df["crs"] + df["kyc_stale"]).clip(upper=100)

    # KYC status penalty
    df["kyc_status_mod"] = df["kyc_status"].map(
        {"expired": 10, "pending": 5, "verified": -5}
    ).fillna(0)
    df["crs"] = (df["crs"] + df["kyc_status_mod"]).clip(lower=0, upper=100).astype(int)

    return df[["customer_id", "crs"]]


# ─────────────────────────────────────────────
# TRS — Transaction Risk Score
# ─────────────────────────────────────────────
def compute_trs(features: pd.DataFrame) -> pd.DataFrame:
    """
    TRS components from feature store:
      - Volume change spike:   +20 if >200%, +10 if >100%
      - Structuring score:     direct contribution (0–40)
      - Dormancy flag:         +15 if dormant >180d then reactivated
      - Avg txn size change:   +10 if >300% increase
      - Volume 30d tier:       graduated contribution
    """
    if features.empty:
        return pd.DataFrame(columns=["customer_id", "trs"])

    f = features.copy()

    trs = pd.Series(0, index=f.index, dtype=float)

    # Volume spike
    vc = f.get("volume_change_pct_7d", pd.Series(0, index=f.index)).fillna(0)
    trs += np.where(vc > 200, 20, np.where(vc > 100, 10, 0))

    # Structuring
    struct = f.get("structuring_score", pd.Series(0, index=f.index)).fillna(0)
    trs += (struct * 0.4).clip(upper=40)

    # Dormancy reactivation
    dormancy = f.get("dormancy_days", pd.Series(0, index=f.index)).fillna(0)
    txn_7d = f.get("txn_count_7d", pd.Series(0, index=f.index)).fillna(0)
    trs += np.where((dormancy > 180) & (txn_7d > 5), 15, 0)

    # Avg txn size spike
    atsc = f.get("avg_txn_size_change_pct", pd.Series(0, index=f.index)).fillna(0)
    trs += np.where(atsc > 300, 10, 0)

    # Volume tier
    vol_30 = f.get("txn_volume_30d_usd", pd.Series(0, index=f.index)).fillna(0)
    trs += np.where(vol_30 > 1_000_000, 15,
           np.where(vol_30 > 100_000, 10,
           np.where(vol_30 > 10_000, 5, 0)))

    f["trs"] = trs.clip(0, 100).astype(int)
    return f[["customer_id", "trs"]]


# ─────────────────────────────────────────────
# NRS — Network Risk Score
# ─────────────────────────────────────────────
def compute_nrs(features: pd.DataFrame, screening: pd.DataFrame) -> pd.DataFrame:
    """
    NRS components:
      - Degree centrality:         high centrality → hub risk
      - Unique countries 30d:      +5 per high-risk country exposure
      - Sanctions match:           +25 if score ≥ 80
      - Cross-border ratio:        +15 if >50% to high-risk
    """
    if features.empty:
        return pd.DataFrame(columns=["customer_id", "nrs"])

    f = features.copy()
    nrs = pd.Series(0, index=f.index, dtype=float)

    # Degree centrality
    dc = f.get("degree_centrality", pd.Series(0, index=f.index)).fillna(0)
    nrs += (dc * 200).clip(upper=30)  # max 30 points

    # Cross-border exposure
    cb_ratio = f.get("cross_border_ratio", pd.Series(0, index=f.index)).fillna(0)
    nrs += np.where(cb_ratio > 50, 15, np.where(cb_ratio > 20, 8, 0))

    # Unique countries
    uc = f.get("unique_countries_30d", pd.Series(0, index=f.index)).fillna(0)
    nrs += (uc * 3).clip(upper=15)

    # Sanctions match
    if not screening.empty:
        high_match = (
            screening[screening["match_score"] >= 80]
            .groupby("customer_id").size()
            .reset_index(name="sanctions_hits")
        )
        f = f.merge(high_match, on="customer_id", how="left")
        f["sanctions_hits"] = f["sanctions_hits"].fillna(0)
        nrs += np.where(f["sanctions_hits"] > 0, 25, 0)
    else:
        f["sanctions_hits"] = 0

    f["nrs"] = nrs.clip(0, 100).astype(int)
    return f[["customer_id", "nrs"]]


# ─────────────────────────────────────────────
# COMPOSITE SCORE & RISK BAND
# ─────────────────────────────────────────────
def composite_score(crs: int, trs: int, nrs: int) -> int:
    return int(round(0.35 * crs + 0.40 * trs + 0.25 * nrs))


def risk_band(score: int) -> str:
    if score <= RISK_LOW_MAX:
        return "LOW"
    elif score <= RISK_MEDIUM_MAX:
        return "MEDIUM"
    elif score <= 80:
        return "HIGH"
    return "CRITICAL"


def run() -> pd.DataFrame:
    logger.info("=" * 60)
    logger.info("Risk Scoring Engine (CRS / TRS / NRS)")
    logger.info("=" * 60)

    customers = pd.read_parquet(DUMMY_DIR / "customers.parquet")
    kyc = pd.read_parquet(DUMMY_DIR / "kyc_records.parquet")

    feature_path = PROCESSED_DIR / "aml_feature_store.parquet"
    screening_path = PROCESSED_DIR / "screening_alerts.parquet"

    features = pd.read_parquet(feature_path) if feature_path.exists() else pd.DataFrame()
    screening = pd.read_parquet(screening_path) if screening_path.exists() else pd.DataFrame()

    logger.info("Computing CRS...")
    crs_df = compute_crs(customers, kyc)

    logger.info("Computing TRS...")
    trs_df = compute_trs(features) if not features.empty else \
        pd.DataFrame({"customer_id": customers["customer_id"], "trs": 20})

    logger.info("Computing NRS...")
    nrs_df = compute_nrs(features, screening) if not features.empty else \
        pd.DataFrame({"customer_id": customers["customer_id"], "nrs": 10})

    # ── Merge
    profiles = customers[["customer_id", "customer_name", "nationality",
                           "date_of_birth", "pep_flag", "pep_grade",
                           "risk_rating", "country_code"]].copy()
    profiles = profiles.merge(crs_df, on="customer_id", how="left")
    profiles = profiles.merge(trs_df, on="customer_id", how="left")
    profiles = profiles.merge(nrs_df, on="customer_id", how="left")

    profiles[["crs", "trs", "nrs"]] = profiles[["crs", "trs", "nrs"]].fillna(10)

    profiles["composite_aml_score"] = profiles.apply(
        lambda r: composite_score(int(r["crs"]), int(r["trs"]), int(r["nrs"])),
        axis=1
    )
    profiles["risk_band"] = profiles["composite_aml_score"].apply(risk_band)

    # Score distribution
    dist = profiles["risk_band"].value_counts()
    logger.info("\nRisk Band Distribution:")
    for band, cnt in dist.items():
        logger.info(f"  {band:<10} {cnt:>6,} customers")

    # Top 10 highest risk
    top10 = profiles.nlargest(10, "composite_aml_score")[
        ["customer_id", "customer_name", "composite_aml_score", "risk_band",
         "crs", "trs", "nrs", "pep_flag", "country_code"]
    ]
    logger.info(f"\nTop 10 highest risk customers:\n{top10.to_string(index=False)}")

    out = PROCESSED_DIR / "customer_risk_profiles.parquet"
    profiles.to_parquet(out, index=False)
    logger.success(f"Risk profiles: {len(profiles):,} customers → {out}")
    return profiles


if __name__ == "__main__":
    run()
