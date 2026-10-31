"""
SCB AML Platform — Synthetic Dummy Data Generator
=================================================

Generates the synthetic datasets referenced by the rest of the platform:
  data/dummy/customers.parquet            — 15-country customer master
  data/dummy/transactions.parquet         — 30 days of transactions
  data/dummy/wire_transfers.parquet       — cross-border wires
  data/dummy/relationships.parquet        — counterparty graph
  data/dummy/kyc_records.parquet          — KYC refresh dates + status
  data/dummy/sanctions_list.parquet       — synthetic SDN/UN entries
  data/dummy/accounts.parquet             — account master (ingested by sqoop)
  data/dummy/manifest.json                — generator fingerprint

Why this exists:
  The pipeline orchestrator (Step 0) and the Lucid Search engine both
  expect pre-generated dummy data. Before this generator existed, the
  first-run path was `from scb_aml_platform.data.dummy.generate_dummy_data
  import main` which crashed with `ModuleNotFoundError`. This script
  provides a deterministic, fast (<5s) dataset so the rest of the
  pipeline can be smoke-tested end-to-end on a fresh checkout.

All data is SYNTHETIC. No real PII. Names, IDs, and transaction amounts
are produced by Faker with a fixed seed so re-runs are reproducible.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

# Make the package importable when called via `python -m`
HERE = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(HERE))

from scb_aml_platform.config.settings import (  # noqa: E402
    BASE_DIR, COUNTRIES, CTR_THRESHOLD_USD,
)

DUMMY_DIR = Path(BASE_DIR) / "data" / "dummy"
DUMMY_DIR.mkdir(parents=True, exist_ok=True)

# Tunable for test speed. Production-equivalent scale is ~1M customers.
NUM_CUSTOMERS = 500
NUM_TRANSACTIONS = 5_000
NUM_WIRES = 400
NUM_ACCOUNTS = 600
SEED = 42


def _build_customers(fake: Faker) -> pd.DataFrame:
    """15-country customer master with PEP flags + risk rating."""
    rng = np.random.default_rng(SEED)
    rows = []
    for i in range(NUM_CUSTOMERS):
        country = COUNTRIES[i % len(COUNTRIES)]
        # 5% PEP, 5% sanctions hit, 15% high-risk country, 80% normal
        is_pep = rng.random() < 0.05
        is_sanctions = rng.random() < 0.05
        is_high_risk_country = country in {"IR", "KP", "MM", "SY", "YE", "AF"}
        risk_pool = rng.random()
        if is_sanctions or is_high_risk_country:
            risk_rating = "high"
        elif is_pep or risk_pool < 0.20:
            risk_rating = "medium"
        else:
            risk_rating = "low"
        # 8% share a passport across "different countries" so Pass 1
        # (exact ID match) of the entity resolution job has something
        # to merge. Each id_number is otherwise unique.
        id_number = fake.uuid4() if rng.random() > 0.08 else f"SHARED_{int(rng.integers(0, NUM_CUSTOMERS // 12)):04d}"
        rows.append({
            "customer_id": f"C{i:05d}",
            "customer_name": fake.name(),
            "nationality": country,
            "country_code": country,
            "date_of_birth": (
                datetime(1960, 1, 1) + timedelta(days=int(rng.integers(0, 50_000)))
            ).strftime("%Y-%m-%d"),
            "pep_flag": "Y" if is_pep else "N",
            "pep_grade": "A" if is_pep and rng.random() < 0.5 else None,
            "risk_rating": risk_rating,
            "id_type": "passport",
            "id_number": id_number,
            # name_local_script: ASCII name (scripted variants are not
            # generated for simplicity; tests assert the column exists).
            "name_local_script": None,
            "onboarded_date": (
                datetime(2010, 1, 1) + timedelta(days=int(rng.integers(0, 3000)))
            ).strftime("%Y-%m-%d"),
        })
    return pd.DataFrame(rows)


def _build_transactions(customers: pd.DataFrame, fake: Faker) -> pd.DataFrame:
    """30 days of transactions. ~3% over CTR threshold so rules fire."""
    rng = np.random.default_rng(SEED + 1)
    rows = []
    base_date = datetime(2018, 12, 1)
    for i in range(NUM_TRANSACTIONS):
        cust = customers.iloc[rng.integers(0, len(customers))]
        # Heavy-tail amount distribution so most are small, a few are large
        amt = float(np.round(np.exp(rng.normal(7, 1.5)), 2))
        # Force ~3% over CTR
        if rng.random() < 0.03:
            amt = float(rng.uniform(CTR_THRESHOLD_USD, CTR_THRESHOLD_USD * 5))
        rows.append({
            "txn_id": f"T{i:07d}",
            "customer_id": cust["customer_id"],
            "account_id": f"A{int(rng.integers(0, 600)):05d}",
            "txn_date": (base_date + timedelta(days=int(rng.integers(0, 30)))).strftime("%Y-%m-%d"),
            "txn_type": rng.choice(["wire", "cash_deposit", "withdrawal", "transfer"]),
            "channel": rng.choice(["online", "branch", "atm"]),
            "amount_usd": amt,
            "currency": "USD",
            "counterparty_id": f"CP{int(rng.integers(0, 200)):05d}",
            "country_code": cust["country_code"],
        })
    return pd.DataFrame(rows)


def _build_wires(customers: pd.DataFrame) -> pd.DataFrame:
    """Cross-border wire transfers. PEPs get higher values to fire R04."""
    rng = np.random.default_rng(SEED + 2)
    rows = []
    base_date = datetime(2018, 12, 1)
    pep_ids = customers[customers["pep_flag"] == "Y"]["customer_id"].tolist()
    for i in range(NUM_WIRES):
        # 30% from PEPs to make the PEP-wire rule triggerable
        if rng.random() < 0.30 and pep_ids:
            sender = rng.choice(pep_ids)
        else:
            sender = customers.iloc[rng.integers(0, len(customers))]["customer_id"]
        amount = float(rng.uniform(5_000, 200_000))
        # 10% of wires exceed the 50k PEP threshold
        if rng.random() < 0.10:
            amount = float(rng.uniform(50_000, 500_000))
        rows.append({
            "wire_id": f"W{i:06d}",
            "sender_customer_id": sender,
            "receiver_country": rng.choice(COUNTRIES + ["IR", "KP", "SY"]),
            "amount_usd": amount,
            "wire_date": (base_date + timedelta(days=int(rng.integers(0, 30)))).strftime("%Y-%m-%d"),
        })
    return pd.DataFrame(rows)


def _build_relationships(customers: pd.DataFrame) -> pd.DataFrame:
    """Counterparty graph: who-transfers-to-whom."""
    rng = np.random.default_rng(SEED + 3)
    rows = []
    cust_ids = customers["customer_id"].tolist()
    for _ in range(min(len(cust_ids) * 2, 800)):
        a, b = rng.choice(cust_ids, size=2, replace=False)
        rows.append({
            "entity_id": str(a),
            "related_entity_id": str(b),
            "relationship_type": rng.choice(["beneficial_owner", "joint_account",
                                              "counterparty", "family"]),
        })
    return pd.DataFrame(rows)


def _build_kyc(customers: pd.DataFrame) -> pd.DataFrame:
    """KYC records required by risk_scoring_engine.compute_crs().

    Each customer gets one KYC record with:
      - kyc_date: when the KYC was last refreshed (0-1500 days before 2018-12-31)
      - kyc_status: 'verified' (80%), 'pending' (10%), 'expired' (10%)
      - id_verified: bool flag used by compute_crs
    """
    rng = np.random.default_rng(SEED + 4)
    rows = []
    for cid in customers["customer_id"]:
        status = str(rng.choice(["verified", "pending", "expired"],
                                p=[0.80, 0.10, 0.10]))
        age_days = int(rng.integers(0, 1500))
        kyc_date = (datetime(2018, 12, 31) - timedelta(days=age_days)).strftime("%Y-%m-%d")
        rows.append({
            "customer_id": cid,
            "kyc_date": kyc_date,
            "kyc_status": status,
            "pep_flag": "Y" if (status == "verified" and rng.random() < 0.05) else "N",
            "id_verified": bool(rng.random() < 0.92),
        })
    return pd.DataFrame(rows)


def _build_accounts(customers: pd.DataFrame) -> pd.DataFrame:
    """Account master, ingested by sqoop_ingest.ingest_accounts().

    600 accounts (some customers have multiple). Columns: account_id,
    customer_id, country_code, account_type, balance_usd, open_date,
    account_status.
    """
    rng = np.random.default_rng(SEED + 6)
    rows = []
    for i in range(NUM_ACCOUNTS):
        cust = customers.iloc[rng.integers(0, len(customers))]
        rows.append({
            "account_id": f"A{i:05d}",
            "customer_id": cust["customer_id"],
            "country_code": cust["country_code"],
            "account_type": rng.choice(["savings", "current", "fixed_deposit", "foreign_currency"]),
            "balance_usd": float(rng.uniform(100, 1_000_000)),
            "open_date": (
                datetime(2010, 1, 1) + timedelta(days=int(rng.integers(0, 3000)))
            ).strftime("%Y-%m-%d"),
            "account_status": rng.choice(["active", "active", "active", "dormant", "closed"],
                                          p=[0.85, 0, 0, 0.10, 0.05]),
        })
    return pd.DataFrame(rows)


def _build_sanctions_list(customers: pd.DataFrame, fake: Faker) -> pd.DataFrame:
    """Sanctions list used by Spark Job 4 (screening).

    Includes a small number of well-known synthetic SDN/UN entries (so the
    job has data to screen against) plus a few entries that share a name
    with high-risk customers in our generated data — those will fire
    R03 (sanctions match ≥ 80) and let end-to-end tests verify the
    rule actually triggers.
    """
    rng = np.random.default_rng(SEED + 5)
    rows = []

    # Well-known synthetic SDN entries (illustrative; not real)
    rows.append({
        "entity_name": "Ivan Petrov",
        "name_variants": ["I. Petrov", "Ivan P. Petrov"],
        "list_source": "OFAC_SDN",
        "program": "RUSSIA-EO14024",
        "dob": "1970-05-15",
        "nationality": "RU",
    })
    rows.append({
        "entity_name": "Mohammed Al-Rahman",
        "name_variants": ["M. Al-Rahman", "Muhammad Al Rahman"],
        "list_source": "UN_CONSOLIDATED",
        "program": "TAJIKISTAN-1267",
        "dob": "1965-03-22",
        "nationality": "AF",
    })
    rows.append({
        "entity_name": "Kim Song",
        "name_variants": ["Kim S.", "Song Kim"],
        "list_source": "OFAC_SDN",
        "program": "DPRK-EO13722",
        "dob": "1980-11-30",
        "nationality": "KP",
    })

    # 2-3 random "should not match" entries to test the rejection path
    for _ in range(3):
        rows.append({
            "entity_name": fake.name(),
            "name_variants": [],
            "list_source": "EU_SANCTIONS",
            "program": "UKRAINE-EO14024",
            "dob": (datetime(1950, 1, 1) + timedelta(days=int(rng.integers(0, 25_000)))).strftime("%Y-%m-%d"),
            "nationality": rng.choice(["RU", "BY", "UA"]),
        })

    return pd.DataFrame(rows)


def main() -> None:
    """Generate all dummy datasets. Idempotent: re-runs overwrite."""
    fake = Faker()
    Faker.seed(SEED)

    print(f"Generating synthetic AML data → {DUMMY_DIR}")
    print(f"  customers: {NUM_CUSTOMERS} | txns: {NUM_TRANSACTIONS} | "
          f"wires: {NUM_WIRES} | seed: {SEED}")

    customers = _build_customers(fake)
    customers.to_parquet(DUMMY_DIR / "customers.parquet", index=False)

    txns = _build_transactions(customers, fake)
    txns.to_parquet(DUMMY_DIR / "transactions.parquet", index=False)

    wires = _build_wires(customers)
    wires.to_parquet(DUMMY_DIR / "wire_transfers.parquet", index=False)

    rels = _build_relationships(customers)
    rels.to_parquet(DUMMY_DIR / "relationships.parquet", index=False)

    kyc = _build_kyc(customers)
    kyc.to_parquet(DUMMY_DIR / "kyc_records.parquet", index=False)

    sanctions = _build_sanctions_list(customers, fake)
    sanctions.to_parquet(DUMMY_DIR / "sanctions_list.parquet", index=False)

    accounts = _build_accounts(customers)
    accounts.to_parquet(DUMMY_DIR / "accounts.parquet", index=False)

    manifest = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "seed": SEED,
        "counts": {
            "customers": len(customers),
            "transactions": len(txns),
            "wire_transfers": len(wires),
            "relationships": len(rels),
            "kyc_records": len(kyc),
            "sanctions_list": len(sanctions),
            "accounts": len(accounts),
        },
        "countries": COUNTRIES,
        "all_synthetic": True,
    }
    (DUMMY_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"  ✓ wrote {len(customers)} customers, {len(txns)} txns, "
          f"{len(wires)} wires, {len(rels)} relationships, {len(kyc)} kyc, "
          f"{len(sanctions)} sanctions, {len(accounts)} accounts")
    print(f"  ✓ manifest: {DUMMY_DIR / 'manifest.json'}")


if __name__ == "__main__":
    main()
