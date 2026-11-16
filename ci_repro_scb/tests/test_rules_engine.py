"""
Tests for the AML rules engine.

Covers all 6 rules with synthetic data. Uses the fixtures from
conftest.py (sample_customers, sample_transactions, sample_wires,
sample_screening, sample_features).
"""
from __future__ import annotations

from scb_aml_platform.aml_engine.rules.rules_engine import (
    RuleAlert,
    aggregate_alerts,
    rule_ctr,
    rule_high_risk_xborder,
    rule_pep_transaction,
    rule_sanctions_hit,
    rule_structuring,
    rule_velocity_spike,
)


class TestRuleCTR:
    """R01: single transaction >= USD 10,000."""

    def test_detects_threshold_breach(self, sample_transactions, sample_customers):
        alerts = rule_ctr(sample_transactions, sample_customers)
        amounts = [a.trigger_value for a in alerts]
        assert 15000.0 in amounts

    def test_ignores_sub_threshold(self, sample_customers):
        import pandas as pd
        small_txns = pd.DataFrame([
            {"customer_id": "C001", "amount_usd": 9500.0, "txn_date": "2018-11-01"},
        ])
        alerts = rule_ctr(small_txns, sample_customers)
        assert alerts == []

    def test_alert_score_is_60(self, sample_transactions, sample_customers):
        alerts = rule_ctr(sample_transactions, sample_customers)
        assert all(a.alert_score == 60 for a in alerts)

    def test_alert_id_is_unique_per_alert(self, sample_transactions, sample_customers):
        alerts = rule_ctr(sample_transactions, sample_customers)
        ids = [a.alert_id for a in alerts]
        assert len(ids) == len(set(ids)), "alert_ids must be unique"


class TestRuleStructuring:
    """R02: 3+ transactions 85-100% of CTR in window days."""

    def test_detects_3_suspect_transactions(
        self, sample_transactions, sample_customers
    ):
        alerts = rule_structuring(sample_transactions, sample_customers)
        cust_ids = [a.customer_id for a in alerts]
        assert "C001" in cust_ids

    def test_ignores_lone_suspect(self, sample_customers):
        import pandas as pd
        lone = pd.DataFrame([
            {"customer_id": "C001", "amount_usd": 9500.0, "txn_date": "2018-11-01"},
        ])
        alerts = rule_structuring(lone, sample_customers)
        assert alerts == []


class TestRuleSanctions:
    """R03: sanctions match score >= 80."""

    def test_detects_high_score(self, sample_screening):
        alerts = rule_sanctions_hit(sample_screening)
        assert len(alerts) == 1
        assert alerts[0].customer_id == "C001"
        assert alerts[0].alert_score == 90

    def test_ignores_low_score(self, sample_customers):
        import pandas as pd
        low = pd.DataFrame([
            {
                "customer_id": "C001", "customer_name": "X",
                "matched_list_source": "OFAC", "matched_entity_name": "Y",
                "match_score": 30, "country_code": "SG",
            },
        ])
        alerts = rule_sanctions_hit(low)
        assert alerts == []


class TestRulePEPHVWire:
    """R04: PEP customer wire >= USD 50,000."""

    def test_detects_pep_large_wire(self, sample_wires, sample_customers):
        alerts = rule_pep_transaction(sample_wires, sample_customers)
        assert any(a.customer_id == "C001" for a in alerts)

    def test_ignores_non_pep(self, sample_wires):
        import pandas as pd
        non_pep = pd.DataFrame([
            {
                "customer_id": "C002", "customer_name": "Jane",
                "pep_flag": "N", "pep_grade": None,
                "country_code": "UK", "risk_rating": "low",
            },
        ])
        alerts = rule_pep_transaction(sample_wires, non_pep)
        assert alerts == []


class TestRuleVelocity:
    """R05: 7d count > 3x 30d daily average."""

    def test_detects_spike(self, sample_features, sample_customers):
        # C001 has txn_count_7d=21, txn_count_30d=30, ratio = 21/7 / 1.0 = 3.0 -> at threshold
        alerts = rule_velocity_spike(sample_features, sample_customers)
        cust_ids = [a.customer_id for a in alerts]
        assert "C001" in cust_ids

    def test_ignores_normal(self, sample_customers):
        import pandas as pd
        normal = pd.DataFrame([
            {
                "customer_id": "C001", "txn_count_7d": 5, "txn_count_30d": 30,
            },
        ])
        alerts = rule_velocity_spike(normal, sample_customers)
        assert alerts == []


class TestRuleHighRiskXBorder:
    """R06: wire to FATF high-risk jurisdiction."""

    def test_detects_ir_wire(self, sample_wires, sample_customers):
        alerts = rule_high_risk_xborder(sample_wires, sample_customers)
        # IR is in HIGH_RISK_COUNTRIES
        assert any(a.customer_id == "C001" for a in alerts)

    def test_ignores_safe_country(self, sample_customers):
        import pandas as pd
        safe = pd.DataFrame([
            {
                "wire_id": "W002", "sender_customer_id": "C001",
                "sender_country": "SG", "receiver_customer_id": "C002",
                "receiver_country": "JP", "amount_usd": 1000.0,
                "value_date": "2018-11-01",
            },
        ])
        alerts = rule_high_risk_xborder(safe, sample_customers)
        assert alerts == []


class TestAggregateAlerts:
    """aggregate_alerts() — DataFrame conversion + dedup."""

    def test_empty_list_returns_empty_df(self):
        df = aggregate_alerts([])
        assert df.empty

    def test_dedupes_by_customer_and_rule(self, sample_customers):
        # Two CTR alerts for same customer -> should be deduped
        alerts = [
            RuleAlert(
                alert_id="A1", rule_id="R01", rule_name="CTR",
                customer_id="C001", customer_name="John",
                alert_reason="x", alert_score=60, country_code="SG",
            ),
            RuleAlert(
                alert_id="A2", rule_id="R01", rule_name="CTR",
                customer_id="C001", customer_name="John",
                alert_reason="y", alert_score=70, country_code="SG",
            ),
        ]
        df = aggregate_alerts(alerts)
        # Only one row per (customer, rule) — keep the higher score
        assert len(df) == 1
        assert df.iloc[0]["alert_score"] == 70

    def test_assigns_report_type(self, sample_customers):
        alerts = [
            RuleAlert(
                alert_id="A1", rule_id="R01", rule_name="CTR",
                customer_id="C001", customer_name="John",
                alert_reason="x", alert_score=60, country_code="SG",
            ),
            RuleAlert(
                alert_id="A2", rule_id="R02", rule_name="Structuring",
                customer_id="C002", customer_name="Jane",
                alert_reason="y", alert_score=75, country_code="UK",
            ),
        ]
        df = aggregate_alerts(alerts)
        rule_to_type = dict(zip(df["rule_id"], df["report_type"], strict=True))
        assert rule_to_type["R01"] == "CTR"
        assert rule_to_type["R02"] == "STR"
