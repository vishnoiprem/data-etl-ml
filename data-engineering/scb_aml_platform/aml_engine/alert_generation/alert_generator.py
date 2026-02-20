"""
SCB AML Platform — Alert Generation Engine
AML Detection Layer, Component 3.

Merges rules-based alerts and risk scores to generate final
regulatory filing queue:
  STR  — Suspicious Transaction Report (MAS SG, HKMA, RBI, etc.)
  SAR  — Suspicious Activity Report (FinCEN US)
  CTR  — Currency Transaction Report

Alert prioritisation:
  1. Merge rules alerts + risk score profiles
  2. Escalate alerts where composite_aml_score ≥ 61 (HIGH band)
  3. Assign due dates based on regulatory SLA per country
  4. Output regulatory filing queue

Output: output/alerts/aml_alert_master.parquet
        output/reports/regulatory_filing_queue.csv
"""

import sys
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from scb_aml_platform.config.settings import (
    BASE_DIR, REGULATORS, RISK_HIGH_MIN
)

PROCESSED_DIR = Path(BASE_DIR) / "data" / "processed"
OUTPUT_ALERTS = Path(BASE_DIR) / "output" / "alerts"
OUTPUT_REPORTS = Path(BASE_DIR) / "output" / "reports"
OUTPUT_ALERTS.mkdir(parents=True, exist_ok=True)
OUTPUT_REPORTS.mkdir(parents=True, exist_ok=True)

# Regulatory SLA (business days from detection to filing)
REGULATORY_SLA = {
    "MAS": 3, "FCA": 5, "FinCEN": 30, "HKMA": 5,
    "RBI": 7, "BNM": 5, "CBUAE": 3, "FSC": 5,
    "BOT": 5, "FSC_TW": 5, "CBK": 7, "CBN": 7,
    "SBP": 7, "BB": 7, "PBOC": 5, "DEFAULT": 5
}

REFERENCE_DATE = datetime(2018, 12, 31)


def _make_alert_id(customer_id: str, alert_type: str) -> str:
    h = hashlib.md5(f"{customer_id}{alert_type}".encode()).hexdigest()[:8].upper()
    return f"ALT_{alert_type}_{h}"


def _due_date(country: str, created: datetime) -> str:
    regulator = REGULATORS.get(country, "DEFAULT")
    sla_days = REGULATORY_SLA.get(regulator, REGULATORY_SLA["DEFAULT"])
    return (created + timedelta(days=sla_days)).strftime("%Y-%m-%d")


def merge_alerts_with_risk(
    rules_alerts: pd.DataFrame,
    risk_profiles: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge rules alerts with risk scores.
    If a customer has HIGH/CRITICAL risk, all their alerts are escalated.
    """
    if rules_alerts.empty:
        return pd.DataFrame()

    # Bring in composite risk score
    risk_cols = risk_profiles[
        ["customer_id", "composite_aml_score", "risk_band", "crs", "trs", "nrs"]
    ] if not risk_profiles.empty else pd.DataFrame()

    merged = rules_alerts.copy()
    if not risk_cols.empty:
        merged = merged.merge(risk_cols, on="customer_id", how="left")
        merged["composite_aml_score"] = merged["composite_aml_score"].fillna(
            merged["alert_score"]
        )
        merged["risk_band"] = merged["risk_band"].fillna("MEDIUM")
    else:
        merged["composite_aml_score"] = merged["alert_score"]
        merged["risk_band"] = "MEDIUM"

    # Use max(rule_score, composite_score) as final alert score
    merged["final_alert_score"] = merged[["alert_score", "composite_aml_score"]].max(axis=1)

    return merged


def classify_and_file(alerts: pd.DataFrame) -> pd.DataFrame:
    """
    Assign alert type, due dates, analyst queue, status.
    """
    if alerts.empty:
        return pd.DataFrame()

    df = alerts.copy()
    now = REFERENCE_DATE

    df["alert_id"] = df.apply(
        lambda r: _make_alert_id(r["customer_id"], r.get("report_type", "STR")),
        axis=1
    )
    df["alert_type"] = df.get("report_type", pd.Series("STR", index=df.index))
    df["alert_type"] = df["alert_type"].fillna("STR")

    # Determine status based on risk band
    def status(row):
        if row.get("risk_band") in ("HIGH", "CRITICAL"):
            return "escalated"
        return "open"

    df["status"] = df.apply(status, axis=1)
    df["created_date"] = now.strftime("%Y-%m-%d")
    df["due_date"] = df["country_code"].apply(
        lambda c: _due_date(c if isinstance(c, str) else "SG", now)
    )
    df["regulatory_body"] = df["country_code"].apply(
        lambda c: REGULATORS.get(c, "DEFAULT") if isinstance(c, str) else "DEFAULT"
    )

    # Assign analyst round-robin (200 analysts)
    df["assigned_analyst"] = [
        f"ANALYST_{(i % 200) + 1:03d}" for i in range(len(df))
    ]

    # De-duplicate: one alert per customer per alert_type
    df = (df.sort_values("final_alert_score", ascending=False)
          .drop_duplicates(subset=["customer_id", "alert_type"])
          .reset_index(drop=True))

    return df


def generate_regulatory_queue(alerts: pd.DataFrame) -> pd.DataFrame:
    """
    Filter escalated / high-score alerts → regulatory filing queue.
    STR filed within SLA; CTR filed same day.
    """
    if alerts.empty:
        return pd.DataFrame()

    filing = alerts[
        (alerts["final_alert_score"] >= RISK_HIGH_MIN) |
        (alerts["alert_type"] == "CTR")
    ].copy()

    filing["filing_status"] = "pending_review"
    filing["regulatory_deadline"] = filing["due_date"]

    return filing


def run() -> pd.DataFrame:
    logger.info("=" * 60)
    logger.info("Alert Generation Engine")
    logger.info("=" * 60)

    rules_path = Path(BASE_DIR) / "output" / "alerts" / "rules_alerts.parquet"
    risk_path = PROCESSED_DIR / "customer_risk_profiles.parquet"

    if not rules_path.exists():
        logger.warning("Rules alerts not found. Run the rules engine first.")
        return pd.DataFrame()

    rules_alerts = pd.read_parquet(rules_path)
    risk_profiles = pd.read_parquet(risk_path) if risk_path.exists() else pd.DataFrame()

    logger.info(f"Rules alerts: {len(rules_alerts)} | Risk profiles: {len(risk_profiles):,}")

    merged = merge_alerts_with_risk(rules_alerts, risk_profiles)
    final_alerts = classify_and_file(merged)

    logger.info(f"\nAlert Summary:")
    if not final_alerts.empty:
        logger.info(f"  Total alerts    : {len(final_alerts):,}")
        logger.info(f"  STR             : {(final_alerts['alert_type']=='STR').sum()}")
        logger.info(f"  CTR             : {(final_alerts['alert_type']=='CTR').sum()}")
        logger.info(f"  SAR             : {(final_alerts['alert_type']=='SAR').sum()}")
        logger.info(f"  Escalated       : {(final_alerts['status']=='escalated').sum()}")

    # Save alert master
    alert_out = OUTPUT_ALERTS / "aml_alert_master.parquet"
    final_alerts.to_parquet(alert_out, index=False)
    logger.success(f"Alert master → {alert_out}")

    # Regulatory filing queue
    queue = generate_regulatory_queue(final_alerts)
    if not queue.empty:
        queue_out = OUTPUT_REPORTS / "regulatory_filing_queue.csv"
        queue.to_csv(queue_out, index=False)
        logger.success(f"Regulatory queue ({len(queue)} alerts) → {queue_out}")

    return final_alerts


if __name__ == "__main__":
    run()
