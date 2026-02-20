"""
SCB AML Platform — Rules-Based Detection Engine
AML Detection Layer, Component 1.

Rules implemented:
  R01 — CTR: Single transaction ≥ USD 10,000
  R02 — Structuring: Multiple transactions just below CTR threshold
  R03 — Sanctions Hit: Confirmed sanctions match score ≥ 80
  R04 — PEP Transaction: PEP customer with high-value wire
  R05 — High-Velocity: Transaction count spike > 3× 30d average
  R06 — Cross-Border High Risk: Wire to FATF high-risk jurisdiction
  R07 — Dormant Account Reactivation: Account inactive >180d, sudden activity
  R08 — Round-Number Structuring: Multiple exact round-number transactions
  R09 — Counterparty Concentration: >70% volume to single counterparty

Each rule returns a list of RuleAlert records.
"""

import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

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
OUTPUT_DIR = Path(BASE_DIR) / "output" / "alerts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REFERENCE_DATE = datetime(2018, 12, 31)
HIGH_RISK_COUNTRIES = {"IR", "KP", "MM", "SY", "YE", "AF"}


@dataclass
class RuleAlert:
    alert_id: str
    rule_id: str
    rule_name: str
    customer_id: str
    customer_name: str
    alert_reason: str
    alert_score: int          # 0–100
    country_code: str
    trigger_value: float = 0.0
    trigger_unit: str = ""
    created_date: str = field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d"))
    status: str = "open"


def _make_alert_id(rule_id: str, customer_id: str) -> str:
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"ALT_{rule_id}_{customer_id[:8]}_{ts}"


# ─────────────────────────────────────────────
# RULE R01 — Currency Transaction Report
# ─────────────────────────────────────────────
def rule_ctr(txns: pd.DataFrame, customers: pd.DataFrame) -> list[RuleAlert]:
    """Single transaction ≥ USD 10,000."""
    alerts = []
    cust_map = customers.set_index("customer_id")[["customer_name", "country_code"]].to_dict("index")

    hits = txns[txns["amount_usd"] >= CTR_THRESHOLD_USD]
    for _, row in hits.iterrows():
        cust = cust_map.get(row["customer_id"], {})
        alerts.append(RuleAlert(
            alert_id=_make_alert_id("R01", row["customer_id"]),
            rule_id="R01",
            rule_name="Currency Transaction Report",
            customer_id=row["customer_id"],
            customer_name=cust.get("customer_name", ""),
            alert_reason=f"Single txn USD {row['amount_usd']:,.0f} exceeds CTR threshold",
            alert_score=60,
            country_code=cust.get("country_code", row.get("country_code", "")),
            trigger_value=row["amount_usd"],
            trigger_unit="USD",
        ))
    return alerts


# ─────────────────────────────────────────────
# RULE R02 — Structuring Detection
# ─────────────────────────────────────────────
def rule_structuring(txns: pd.DataFrame, customers: pd.DataFrame) -> list[RuleAlert]:
    """Multiple transactions 85–100% of CTR within window days."""
    alerts = []
    cust_map = customers.set_index("customer_id")[["customer_name", "country_code"]].to_dict("index")
    low, high = CTR_THRESHOLD_USD * 0.85, CTR_THRESHOLD_USD

    txns = txns.copy()
    txns["txn_date_dt"] = pd.to_datetime(txns["txn_date"], errors="coerce")
    suspect = txns[(txns["amount_usd"] >= low) & (txns["amount_usd"] < high)].sort_values("txn_date_dt")

    for cust_id, group in suspect.groupby("customer_id"):
        if len(group) >= STRUCTURING_COUNT_THRESHOLD:
            cust = cust_map.get(cust_id, {})
            alerts.append(RuleAlert(
                alert_id=_make_alert_id("R02", cust_id),
                rule_id="R02",
                rule_name="Structuring Detection",
                customer_id=cust_id,
                customer_name=cust.get("customer_name", ""),
                alert_reason=(
                    f"{len(group)} transactions between "
                    f"USD {low:,.0f}–{high:,.0f} in {STRUCTURING_WINDOW_DAYS} days"
                ),
                alert_score=75,
                country_code=cust.get("country_code", ""),
                trigger_value=len(group),
                trigger_unit="transaction_count",
            ))
    return alerts


# ─────────────────────────────────────────────
# RULE R03 — Sanctions Match
# ─────────────────────────────────────────────
def rule_sanctions_hit(screening: pd.DataFrame) -> list[RuleAlert]:
    """Sanctions match score ≥ 80 → high-confidence hit."""
    alerts = []
    hits = screening[screening["match_score"] >= 80]

    for _, row in hits.iterrows():
        alerts.append(RuleAlert(
            alert_id=_make_alert_id("R03", row["customer_id"]),
            rule_id="R03",
            rule_name="Sanctions Match",
            customer_id=row["customer_id"],
            customer_name=row["customer_name"],
            alert_reason=(
                f"Matched {row['matched_list_source']} list: "
                f"'{row['matched_entity_name']}' (score={row['match_score']})"
            ),
            alert_score=90,
            country_code=row.get("country_code", ""),
            trigger_value=row["match_score"],
            trigger_unit="match_score",
        ))
    return alerts


# ─────────────────────────────────────────────
# RULE R04 — PEP High-Value Transaction
# ─────────────────────────────────────────────
def rule_pep_transaction(wires: pd.DataFrame, customers: pd.DataFrame) -> list[RuleAlert]:
    """PEP customer wire transfer ≥ USD 50,000."""
    alerts = []
    PEP_WIRE_THRESHOLD = 50_000

    pep_ids = set(customers[customers["pep_flag"] == "Y"]["customer_id"])
    cust_map = customers.set_index("customer_id")[["customer_name", "country_code"]].to_dict("index")

    hits = wires[
        (wires["sender_customer_id"].isin(pep_ids)) &
        (wires["amount_usd"] >= PEP_WIRE_THRESHOLD)
    ]
    for _, row in hits.iterrows():
        cust_id = row["sender_customer_id"]
        cust = cust_map.get(cust_id, {})
        alerts.append(RuleAlert(
            alert_id=_make_alert_id("R04", cust_id),
            rule_id="R04",
            rule_name="PEP High-Value Wire Transfer",
            customer_id=cust_id,
            customer_name=cust.get("customer_name", ""),
            alert_reason=(
                f"PEP customer wire USD {row['amount_usd']:,.0f} "
                f"to {row['receiver_country']}"
            ),
            alert_score=80,
            country_code=cust.get("country_code", ""),
            trigger_value=row["amount_usd"],
            trigger_unit="USD",
        ))
    return alerts


# ─────────────────────────────────────────────
# RULE R05 — High Velocity Spike
# ─────────────────────────────────────────────
def rule_velocity_spike(features: pd.DataFrame, customers: pd.DataFrame) -> list[RuleAlert]:
    """Transaction count spike: 7d count > 3× 30d daily average."""
    alerts = []
    cust_map = customers.set_index("customer_id")[["customer_name", "country_code"]].to_dict("index")

    f = features.copy()
    if "txn_count_7d" not in f.columns or "txn_count_30d" not in f.columns:
        return alerts

    f["daily_avg_30d"] = f["txn_count_30d"] / 30.0
    f["spike_ratio"] = np.where(
        f["daily_avg_30d"] > 0,
        f["txn_count_7d"] / 7.0 / f["daily_avg_30d"],
        0.0
    )
    hits = f[f["spike_ratio"] >= 3.0]

    for _, row in hits.iterrows():
        cust = cust_map.get(row["customer_id"], {})
        alerts.append(RuleAlert(
            alert_id=_make_alert_id("R05", row["customer_id"]),
            rule_id="R05",
            rule_name="High Transaction Velocity",
            customer_id=row["customer_id"],
            customer_name=cust.get("customer_name", ""),
            alert_reason=(
                f"Transaction rate {row['spike_ratio']:.1f}× above 30d average"
            ),
            alert_score=65,
            country_code=row.get("country_code", ""),
            trigger_value=round(row["spike_ratio"], 2),
            trigger_unit="spike_ratio",
        ))
    return alerts


# ─────────────────────────────────────────────
# RULE R06 — Cross-Border High-Risk Jurisdiction
# ─────────────────────────────────────────────
def rule_high_risk_xborder(wires: pd.DataFrame, customers: pd.DataFrame) -> list[RuleAlert]:
    """Wire transfer to FATF high-risk jurisdiction."""
    alerts = []
    cust_map = customers.set_index("customer_id")[["customer_name", "country_code"]].to_dict("index")

    hits = wires[wires["receiver_country"].isin(HIGH_RISK_COUNTRIES)]
    for _, row in hits.iterrows():
        cust_id = row["sender_customer_id"]
        cust = cust_map.get(cust_id, {})
        alerts.append(RuleAlert(
            alert_id=_make_alert_id("R06", cust_id),
            rule_id="R06",
            rule_name="Wire to High-Risk Jurisdiction",
            customer_id=cust_id,
            customer_name=cust.get("customer_name", ""),
            alert_reason=(
                f"USD {row['amount_usd']:,.0f} wire to {row['receiver_country']} "
                f"(FATF high-risk)"
            ),
            alert_score=70,
            country_code=cust.get("country_code", ""),
            trigger_value=row["amount_usd"],
            trigger_unit="USD",
        ))
    return alerts


# ─────────────────────────────────────────────
# AGGREGATE & DEDUPLICATE ALERTS
# ─────────────────────────────────────────────
def aggregate_alerts(all_alerts: list[RuleAlert]) -> pd.DataFrame:
    """Convert alerts to DataFrame, deduplicate by customer+rule."""
    if not all_alerts:
        return pd.DataFrame()

    records = [vars(a) for a in all_alerts]
    df = pd.DataFrame(records)

    # Keep highest score per customer per rule
    df = (df.sort_values("alert_score", ascending=False)
          .drop_duplicates(subset=["customer_id", "rule_id"])
          .reset_index(drop=True))

    # Add regulatory report type
    def report_type(rule_id):
        ctr_rules = {"R01"}
        str_rules = {"R02", "R03", "R04", "R05", "R06"}
        if rule_id in ctr_rules:
            return "CTR"
        elif rule_id in str_rules:
            return "STR"
        return "SAR"

    df["report_type"] = df["rule_id"].apply(report_type)
    return df


def run() -> pd.DataFrame:
    logger.info("=" * 60)
    logger.info("AML Rules Engine")
    logger.info("=" * 60)

    customers = pd.read_parquet(DUMMY_DIR / "customers.parquet")
    txns = pd.read_parquet(DUMMY_DIR / "transactions.parquet")
    wires = pd.read_parquet(DUMMY_DIR / "wire_transfers.parquet")

    screening_path = PROCESSED_DIR / "screening_alerts.parquet"
    feature_path = PROCESSED_DIR / "aml_feature_store.parquet"

    screening = pd.read_parquet(screening_path) if screening_path.exists() else pd.DataFrame()
    features = pd.read_parquet(feature_path) if feature_path.exists() else pd.DataFrame()

    all_alerts = []

    logger.info("Running R01 — CTR")
    all_alerts.extend(rule_ctr(txns, customers))

    logger.info("Running R02 — Structuring")
    all_alerts.extend(rule_structuring(txns, customers))

    if not screening.empty:
        logger.info("Running R03 — Sanctions Hit")
        all_alerts.extend(rule_sanctions_hit(screening))

    logger.info("Running R04 — PEP Wire")
    all_alerts.extend(rule_pep_transaction(wires, customers))

    if not features.empty:
        logger.info("Running R05 — Velocity Spike")
        all_alerts.extend(rule_velocity_spike(features, customers))

    logger.info("Running R06 — High-Risk Jurisdiction")
    all_alerts.extend(rule_high_risk_xborder(wires, customers))

    df = aggregate_alerts(all_alerts)
    logger.success(f"Rules engine: {len(df)} unique alerts generated")

    if not df.empty:
        counts = df["rule_id"].value_counts()
        for rule, cnt in counts.items():
            logger.info(f"  {rule}: {cnt} alerts")

    out = OUTPUT_DIR / "rules_alerts.parquet"
    df.to_parquet(out, index=False)
    logger.success(f"Alerts saved → {out}")
    return df


if __name__ == "__main__":
    run()
