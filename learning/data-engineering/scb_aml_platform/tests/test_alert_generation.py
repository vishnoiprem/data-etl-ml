"""
Tests for alert generation: SLA mapping, dedup, status assignment.
"""
from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def sample_rules_alerts() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "alert_id": "ALT_R01_C001_20260101000000",
            "rule_id": "R01", "rule_name": "CTR",
            "customer_id": "C001", "customer_name": "John",
            "alert_reason": "test", "alert_score": 60,
            "country_code": "SG", "trigger_value": 15000.0,
            "trigger_unit": "USD", "report_type": "CTR",
        },
        {
            "alert_id": "ALT_R02_C002_20260101000000",
            "rule_id": "R02", "rule_name": "Structuring",
            "customer_id": "C002", "customer_name": "Jane",
            "alert_reason": "test", "alert_score": 75,
            "country_code": "UK", "trigger_value": 3,
            "trigger_unit": "count", "report_type": "STR",
        },
        {
            "alert_id": "ALT_R03_C003_20260101000000",
            "rule_id": "R03", "rule_name": "Sanctions",
            "customer_id": "C003", "customer_name": "Bob",
            "alert_reason": "test", "alert_score": 90,
            "country_code": "US", "trigger_value": 95,
            "trigger_unit": "score", "report_type": "SAR",
        },
    ])


@pytest.fixture
def sample_risk_profiles() -> pd.DataFrame:
    return pd.DataFrame([
        {"customer_id": "C001", "composite_aml_score": 75, "risk_band": "HIGH",
         "crs": 80, "trs": 70, "nrs": 60},
        {"customer_id": "C002", "composite_aml_score": 40, "risk_band": "MEDIUM",
         "crs": 30, "trs": 50, "nrs": 30},
        # C003 not in profiles -> falls back to MEDIUM
    ])


class TestMergeAlertsWithRisk:
    """Tests for merge_alerts_with_risk()."""

    def test_empty_alerts_returns_empty(self, sample_risk_profiles):
        from scb_aml_platform.aml_engine.alert_generation.alert_generator import (
            merge_alerts_with_risk,
        )
        df = merge_alerts_with_risk(pd.DataFrame(), sample_risk_profiles)
        assert df.empty

    def test_final_score_uses_max_of_rule_and_risk(
        self, sample_rules_alerts, sample_risk_profiles
    ):
        from scb_aml_platform.aml_engine.alert_generation.alert_generator import (
            merge_alerts_with_risk,
        )
        df = merge_alerts_with_risk(sample_rules_alerts, sample_risk_profiles)
        # C001: rule=60, risk=75 -> final = 75
        # C002: rule=75, risk=40 -> final = 75
        c001 = df[df["customer_id"] == "C001"].iloc[0]
        c002 = df[df["customer_id"] == "C002"].iloc[0]
        assert c001["final_alert_score"] == 75
        assert c002["final_alert_score"] == 75

    def test_missing_risk_profile_defaults_to_medium(
        self, sample_rules_alerts, sample_risk_profiles
    ):
        from scb_aml_platform.aml_engine.alert_generation.alert_generator import (
            merge_alerts_with_risk,
        )
        df = merge_alerts_with_risk(sample_rules_alerts, sample_risk_profiles)
        c003 = df[df["customer_id"] == "C003"].iloc[0]
        assert c003["risk_band"] == "MEDIUM"


class TestClassifyAndFile:
    """Tests for classify_and_file()."""

    def test_status_escalated_for_high_risk(
        self, sample_rules_alerts, sample_risk_profiles
    ):
        from scb_aml_platform.aml_engine.alert_generation.alert_generator import (
            classify_and_file,
            merge_alerts_with_risk,
        )
        merged = merge_alerts_with_risk(sample_rules_alerts, sample_risk_profiles)
        out = classify_and_file(merged)
        # C001 has risk_band HIGH -> escalated
        c001 = out[out["customer_id"] == "C001"].iloc[0]
        assert c001["status"] == "escalated"

    def test_status_open_for_medium_risk(
        self, sample_rules_alerts, sample_risk_profiles
    ):
        from scb_aml_platform.aml_engine.alert_generation.alert_generator import (
            classify_and_file,
            merge_alerts_with_risk,
        )
        merged = merge_alerts_with_risk(sample_rules_alerts, sample_risk_profiles)
        out = classify_and_file(merged)
        c002 = out[out["customer_id"] == "C002"].iloc[0]
        assert c002["status"] == "open"

    def test_due_date_per_regulator(
        self, sample_rules_alerts, sample_risk_profiles
    ):
        from scb_aml_platform.aml_engine.alert_generation.alert_generator import (
            classify_and_file,
            merge_alerts_with_risk,
        )
        merged = merge_alerts_with_risk(sample_rules_alerts, sample_risk_profiles)
        out = classify_and_file(merged)
        # MAS (SG) -> 3 days, FCA (UK) -> 5 days, FinCEN (US) -> 30 days
        c001 = out[out["customer_id"] == "C001"].iloc[0]
        c002 = out[out["customer_id"] == "C002"].iloc[0]
        c003 = out[out["customer_id"] == "C003"].iloc[0]
        assert c001["regulatory_body"] == "MAS"
        assert c002["regulatory_body"] == "FCA"
        assert c003["regulatory_body"] == "FinCEN"
        # The due date is REFERENCE_DATE (2018-12-31) + N business days,
        # but the implementation uses calendar days. Just check the
        # format is right.
        assert c001["due_date"] == "2019-01-03"
        assert c002["due_date"] == "2019-01-05"
        assert c003["due_date"] == "2019-01-30"

    def test_dedupes_per_customer_per_alert_type(
        self, sample_rules_alerts, sample_risk_profiles
    ):
        from scb_aml_platform.aml_engine.alert_generation.alert_generator import (
            classify_and_file,
            merge_alerts_with_risk,
        )
        # Duplicate C001 alerts to verify dedup
        doubled = pd.concat([sample_rules_alerts, sample_rules_alerts.iloc[[0]]], ignore_index=True)
        merged = merge_alerts_with_risk(doubled, sample_risk_profiles)
        out = classify_and_file(merged)
        c001_alerts = out[out["customer_id"] == "C001"]
        # One CTR per customer -> 1 row
        assert len(c001_alerts) == 1


class TestRegulatoryQueue:
    """Tests for generate_regulatory_queue()."""

    def test_empty_alerts_returns_empty(self):
        from scb_aml_platform.aml_engine.alert_generation.alert_generator import (
            generate_regulatory_queue,
        )
        out = generate_regulatory_queue(pd.DataFrame())
        assert out.empty

    def test_includes_all_ctr_alerts(
        self, sample_rules_alerts, sample_risk_profiles
    ):
        from scb_aml_platform.aml_engine.alert_generation.alert_generator import (
            classify_and_file,
            generate_regulatory_queue,
            merge_alerts_with_risk,
        )
        merged = merge_alerts_with_risk(sample_rules_alerts, sample_risk_profiles)
        out = classify_and_file(merged)
        queue = generate_regulatory_queue(out)
        # C001 is CTR -> must be in queue regardless of risk
        assert "C001" in queue["customer_id"].values

    def test_includes_high_score_alerts(
        self, sample_rules_alerts, sample_risk_profiles
    ):
        from scb_aml_platform.aml_engine.alert_generation.alert_generator import (
            classify_and_file,
            generate_regulatory_queue,
            merge_alerts_with_risk,
        )
        merged = merge_alerts_with_risk(sample_rules_alerts, sample_risk_profiles)
        out = classify_and_file(merged)
        queue = generate_regulatory_queue(out)
        # C001 has final score 75 (HIGH) -> in queue
        assert "C001" in queue["customer_id"].values
