"""
Tests for the alert generation engine.

End-to-end smoke test: rules engine → risk scoring → alert generator.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(HERE))

from scb_aml_platform.data.dummy.generate_dummy_data import main as _gen  # noqa: E402
from scb_aml_platform.aml_engine.alert_generation.alert_generator import (  # noqa: E402
    merge_alerts_with_risk, classify_and_file, run,
)
from scb_aml_platform.aml_engine.rules.rules_engine import run as rules_run  # noqa: E402
from scb_aml_platform.aml_engine.risk_scoring.risk_scoring_engine import run as risk_run  # noqa: E402
from scb_aml_platform.config.settings import BASE_DIR  # noqa: E402

DUMMY_DIR = Path(BASE_DIR) / "data" / "dummy"
PROCESSED_DIR = Path(BASE_DIR) / "data" / "processed"
ALERTS_DIR = Path(BASE_DIR) / "output" / "alerts"


@pytest.fixture(scope="module", autouse=True)
def _setup():
    _gen()
    rules_run()
    risk_run()
    yield


def test_rules_engine_wrote_alerts():
    assert (ALERTS_DIR / "rules_alerts.parquet").exists()


def test_risk_scoring_wrote_profiles():
    assert (PROCESSED_DIR / "customer_risk_profiles.parquet").exists()


def test_alert_generator_end_to_end():
    """Full pipeline: rules + risk → alerts."""
    out = ALERTS_DIR / "aml_alert_master.parquet"
    alerts = run()
    assert out.exists()
    assert len(alerts) > 0
    assert "alert_id" in alerts.columns
    assert "customer_id" in alerts.columns
    assert "alert_type" in alerts.columns
    assert "status" in alerts.columns


def test_merge_alerts_with_risk_handles_empty_risk():
    """merge_alerts_with_risk must work when risk_profiles is empty
    (uses default fallback)."""
    rules_alerts = pd.DataFrame([
        {"customer_id": "C1", "rule_id": "R01", "alert_score": 80,
         "report_type": "STR", "country_code": "SG"}
    ])
    risk_profiles = pd.DataFrame()
    merged = merge_alerts_with_risk(rules_alerts, risk_profiles)
    assert "composite_aml_score" in merged.columns
    assert "risk_band" in merged.columns
    # Should have inherited alert_score since risk_profiles is empty
    assert merged["composite_aml_score"].iloc[0] == 80
    assert merged["risk_band"].iloc[0] == "MEDIUM"


def test_classify_and_file_assigns_alert_id():
    rules_alerts = pd.DataFrame([
        {"customer_id": "C1", "rule_id": "R01", "alert_score": 80,
         "report_type": "STR", "country_code": "SG"}
    ])
    risk = pd.DataFrame([
        {"customer_id": "C1", "composite_aml_score": 90, "risk_band": "CRITICAL",
         "crs": 90, "trs": 90, "nrs": 90}
    ])
    merged = merge_alerts_with_risk(rules_alerts, risk)
    filed = classify_and_file(merged)
    assert "alert_id" in filed.columns
    assert filed["alert_id"].iloc[0].startswith("ALT_")
    assert filed["status"].iloc[0] == "escalated"
