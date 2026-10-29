"""
Shared pytest fixtures for the SCB AML Platform test suite.

Tests run against synthetic in-memory data; no real Kafka / ES / Hive
required. Mark integration tests that need real services with
@pytest.mark.integration so they can be skipped in CI.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

# Ensure the project root (one level up) is importable as a package.
# This lets tests do `from scb_aml_platform.<x> import <y>` without
# needing a `pip install -e .` step in CI.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parent  # data-engineering/
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ─────────────────────────────────────────────────────────────────────
# Synthetic customer / transaction fixtures
# ─────────────────────────────────────────────────────────────────────
@pytest.fixture
def sample_customers() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "customer_id": "C001",
            "customer_name": "John Doe",
            "risk_rating": "high",
            "pep_flag": "Y",
            "pep_grade": "A",
            "nationality": "SG",
            "date_of_birth": "1975-01-01",
            "country_code": "SG",
        },
        {
            "customer_id": "C002",
            "customer_name": "Jane Smith",
            "risk_rating": "low",
            "pep_flag": "N",
            "pep_grade": None,
            "nationality": "UK",
            "date_of_birth": "1985-06-15",
            "country_code": "UK",
        },
    ])


@pytest.fixture
def sample_transactions() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "txn_id": "T001", "customer_id": "C001", "account_id": "A001",
            "amount_usd": 15000.0, "txn_date": "2018-11-01",
            "txn_type": "wire", "channel": "online",
            "counterparty_id": "C002", "country_code": "SG",
        },
        {
            "txn_id": "T002", "customer_id": "C001", "account_id": "A001",
            "amount_usd": 9500.0, "txn_date": "2018-11-02",
            "txn_type": "withdrawal", "channel": "branch",
            "counterparty_id": "C003", "country_code": "SG",
        },
        {
            "txn_id": "T003", "customer_id": "C001", "account_id": "A001",
            "amount_usd": 9200.0, "txn_date": "2018-11-03",
            "txn_type": "withdrawal", "channel": "atm",
            "counterparty_id": "C004", "country_code": "SG",
        },
        {
            "txn_id": "T004", "customer_id": "C001", "account_id": "A001",
            "amount_usd": 9100.0, "txn_date": "2018-11-04",
            "txn_type": "withdrawal", "channel": "atm",
            "counterparty_id": "C005", "country_code": "SG",
        },
    ])


@pytest.fixture
def sample_wires() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "wire_id": "W001", "sender_customer_id": "C001",
            "sender_country": "SG", "receiver_customer_id": "C002",
            "receiver_country": "IR", "amount_usd": 75000.0,
            "value_date": "2018-11-01", "swift_msg_type": "MT103",
            "purpose_code": "UNKNOWN",
        },
    ])


@pytest.fixture
def sample_kyc() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "customer_id": "C001",
            "kyc_date": "2017-01-01",
            "kyc_status": "verified",
            "pep_flag": "Y",
            "id_verified": True,
        },
        {
            "customer_id": "C002",
            "kyc_date": "2018-06-01",
            "kyc_status": "verified",
            "pep_flag": "N",
            "id_verified": True,
        },
    ])


@pytest.fixture
def sample_features() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "customer_id": "C001",
            "txn_count_7d": 21, "txn_count_30d": 30,
            "txn_volume_30d_usd": 50_000.0,
            "volume_change_pct_7d": 250.0,
            "structuring_score": 60.0,
            "dormancy_days": 200,
            "avg_txn_size_change_pct": 350.0,
            "degree_centrality": 0.1,
            "cross_border_ratio": 60.0,
            "unique_countries_30d": 4,
        },
        {
            "customer_id": "C002",
            "txn_count_7d": 5, "txn_count_30d": 25,
            "txn_volume_30d_usd": 5_000.0,
            "volume_change_pct_7d": 10.0,
            "structuring_score": 0.0,
            "dormancy_days": 0,
            "avg_txn_size_change_pct": 0.0,
            "degree_centrality": 0.02,
            "cross_border_ratio": 5.0,
            "unique_countries_30d": 1,
        },
    ])


@pytest.fixture
def sample_screening() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "customer_id": "C001", "customer_name": "John Doe",
            "matched_list_source": "OFAC", "matched_entity_name": "John Doe",
            "match_score": 95, "country_code": "SG",
        },
    ])
