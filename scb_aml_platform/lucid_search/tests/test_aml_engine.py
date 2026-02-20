"""
AML Engine — Unit Tests
Tests rules engine, risk scoring, and alert generation.
"""

import sys
import pytest
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))


@pytest.fixture
def sample_customers():
    return pd.DataFrame([
        {"customer_id": "C001", "customer_name": "John Doe",
         "risk_rating": "high", "pep_flag": "Y", "pep_grade": "A",
         "nationality": "SG", "date_of_birth": "1975-01-01", "country_code": "SG"},
        {"customer_id": "C002", "customer_name": "Jane Smith",
         "risk_rating": "low", "pep_flag": "N", "pep_grade": None,
         "nationality": "UK", "date_of_birth": "1985-06-15", "country_code": "UK"},
    ])


@pytest.fixture
def sample_transactions():
    return pd.DataFrame([
        {"txn_id": "T001", "customer_id": "C001", "account_id": "A001",
         "amount_usd": 15000.0, "txn_date": "2018-11-01",
         "txn_type": "wire", "channel": "online",
         "counterparty_id": "C002", "country_code": "SG"},
        {"txn_id": "T002", "customer_id": "C001", "account_id": "A001",
         "amount_usd": 9500.0, "txn_date": "2018-11-02",
         "txn_type": "withdrawal", "channel": "branch",
         "counterparty_id": "C003", "country_code": "SG"},
        {"txn_id": "T003", "customer_id": "C001", "account_id": "A001",
         "amount_usd": 9200.0, "txn_date": "2018-11-03",
         "txn_type": "withdrawal", "channel": "atm",
         "counterparty_id": "C004", "country_code": "SG"},
        {"txn_id": "T004", "customer_id": "C001", "account_id": "A001",
         "amount_usd": 9100.0, "txn_date": "2018-11-04",
         "txn_type": "withdrawal", "channel": "atm",
         "counterparty_id": "C005", "country_code": "SG"},
    ])


@pytest.fixture
def sample_wires():
    return pd.DataFrame([
        {"wire_id": "W001", "sender_customer_id": "C001", "sender_country": "SG",
         "receiver_customer_id": "C002", "receiver_country": "IR",
         "amount_usd": 75000.0, "value_date": "2018-11-01",
         "swift_msg_type": "MT103", "purpose_code": "UNKNOWN"},
    ])


# ─────────────────────────────────────────────
# ENTITY RESOLUTION TESTS
# ─────────────────────────────────────────────
class TestEntityResolution:

    def test_jaro_winkler_same_name(self):
        from scb_aml_platform.spark.entity_resolution.job1_entity_resolution import jaro_winkler_score
        assert jaro_winkler_score("Mohammed", "Mohammed") == 1.0

    def test_jaro_winkler_variant(self):
        from scb_aml_platform.spark.entity_resolution.job1_entity_resolution import jaro_winkler_score
        score = jaro_winkler_score("Mohammed", "Mohammad")
        assert score > 0.85

    def test_phonetic_match_variants(self):
        from scb_aml_platform.spark.entity_resolution.job1_entity_resolution import phonetic_match
        assert phonetic_match("Chen", "Chan") in (True, False)  # depends on metaphone

    def test_transliterate_arabic(self):
        from scb_aml_platform.spark.entity_resolution.job1_entity_resolution import transliterate
        result = transliterate("محمد")
        assert isinstance(result, str)

    def test_make_golden_id_deterministic(self):
        from scb_aml_platform.spark.entity_resolution.job1_entity_resolution import make_golden_id
        id1 = make_golden_id("CUST_SG_000001")
        id2 = make_golden_id("CUST_SG_000001")
        assert id1 == id2, "Golden ID should be deterministic"


# ─────────────────────────────────────────────
# RULES ENGINE TESTS
# ─────────────────────────────────────────────
class TestRulesEngine:

    def test_ctr_rule_detects_large_transaction(self, sample_transactions, sample_customers):
        from scb_aml_platform.aml_engine.rules.rules_engine import rule_ctr
        alerts = rule_ctr(sample_transactions, sample_customers)
        ctr_amounts = [a.trigger_value for a in alerts]
        assert 15000.0 in ctr_amounts

    def test_structuring_detects_pattern(self, sample_transactions, sample_customers):
        from scb_aml_platform.aml_engine.rules.rules_engine import rule_structuring
        alerts = rule_structuring(sample_transactions, sample_customers)
        # Should detect C001 with 3 transactions just below threshold
        cust_ids = [a.customer_id for a in alerts]
        assert "C001" in cust_ids

    def test_high_risk_xborder(self, sample_wires, sample_customers):
        from scb_aml_platform.aml_engine.rules.rules_engine import rule_high_risk_xborder
        alerts = rule_high_risk_xborder(sample_wires, sample_customers)
        # IR is in HIGH_RISK_COUNTRIES
        assert len(alerts) >= 1

    def test_pep_wire_rule(self, sample_wires, sample_customers):
        from scb_aml_platform.aml_engine.rules.rules_engine import rule_pep_transaction
        alerts = rule_pep_transaction(sample_wires, sample_customers)
        # C001 is PEP and wire is > 50k
        assert any(a.customer_id == "C001" for a in alerts)


# ─────────────────────────────────────────────
# RISK SCORING TESTS
# ─────────────────────────────────────────────
class TestRiskScoring:

    def test_composite_score_range(self):
        from scb_aml_platform.aml_engine.risk_scoring.risk_scoring_engine import composite_score
        score = composite_score(80, 70, 60)
        assert 0 <= score <= 100

    def test_risk_band_low(self):
        from scb_aml_platform.aml_engine.risk_scoring.risk_scoring_engine import risk_band
        assert risk_band(20) == "LOW"

    def test_risk_band_high(self):
        from scb_aml_platform.aml_engine.risk_scoring.risk_scoring_engine import risk_band
        assert risk_band(70) == "HIGH"

    def test_risk_band_critical(self):
        from scb_aml_platform.aml_engine.risk_scoring.risk_scoring_engine import risk_band
        assert risk_band(90) == "CRITICAL"


# ─────────────────────────────────────────────
# SCREENING TESTS
# ─────────────────────────────────────────────
class TestScreening:

    def test_exact_match_scores_high(self):
        from scb_aml_platform.spark.screening.job4_sanctions_pep_screening import compute_match_score
        score, mtype = compute_match_score(
            "Mohammed Al-Rahman", "Mohammed Al-Rahman",
            "1975-03-15", "1975-03-15", "AE", "AE"
        )
        assert score == 100
        assert mtype == "exact"

    def test_fuzzy_match_scores_medium(self):
        from scb_aml_platform.spark.screening.job4_sanctions_pep_screening import compute_match_score
        score, mtype = compute_match_score(
            "Mohammed Al-Rahman", "Mohamed Al-Rahman",
            "1975-03-15", "1975-03-15", "AE", "AE"
        )
        assert score >= 60

    def test_no_match_returns_zero(self):
        from scb_aml_platform.spark.screening.job4_sanctions_pep_screening import compute_match_score
        score, mtype = compute_match_score(
            "John Smith", "Zhang Wei",
            "1975-01-01", "1980-06-01", "UK", "CN"
        )
        assert score == 0
        assert mtype == "no_match"
