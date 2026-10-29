"""
Tests for the risk scoring engine (CRS / TRS / NRS).
"""
from __future__ import annotations

import pandas as pd
import pytest


class TestCompositeScore:
    """Tests for composite_score() and risk_band()."""

    def test_composite_score_in_range(self):
        from scb_aml_platform.aml_engine.risk_scoring.risk_scoring_engine import (
            composite_score,
        )
        # Weights: 0.35 * CRS + 0.40 * TRS + 0.25 * NRS
        score = composite_score(80, 70, 60)
        # = 0.35*80 + 0.40*70 + 0.25*60 = 28 + 28 + 15 = 71
        assert 70 <= score <= 72

    def test_composite_score_with_zeros(self):
        from scb_aml_platform.aml_engine.risk_scoring.risk_scoring_engine import (
            composite_score,
        )
        assert composite_score(0, 0, 0) == 0

    def test_composite_score_caps_at_100(self):
        from scb_aml_platform.aml_engine.risk_scoring.risk_scoring_engine import (
            composite_score,
        )
        assert composite_score(100, 100, 100) == 100

    def test_risk_band_low(self):
        from scb_aml_platform.aml_engine.risk_scoring.risk_scoring_engine import (
            risk_band,
        )
        assert risk_band(0) == "LOW"
        assert risk_band(30) == "LOW"

    def test_risk_band_medium(self):
        from scb_aml_platform.aml_engine.risk_scoring.risk_scoring_engine import (
            risk_band,
        )
        assert risk_band(31) == "MEDIUM"
        assert risk_band(60) == "MEDIUM"

    def test_risk_band_high(self):
        from scb_aml_platform.aml_engine.risk_scoring.risk_scoring_engine import (
            risk_band,
        )
        assert risk_band(61) == "HIGH"
        assert risk_band(80) == "HIGH"

    def test_risk_band_critical(self):
        from scb_aml_platform.aml_engine.risk_scoring.risk_scoring_engine import (
            risk_band,
        )
        assert risk_band(81) == "CRITICAL"
        assert risk_band(100) == "CRITICAL"


class TestComputeCRS:
    """Tests for compute_crs() — KYC/PEP-driven customer risk."""

    def test_high_risk_rating_yields_high_base(self, sample_customers, sample_kyc):
        from scb_aml_platform.aml_engine.risk_scoring.risk_scoring_engine import (
            compute_crs,
        )
        df = compute_crs(sample_customers, sample_kyc)
        # C001 has risk_rating=high, pep_flag=Y, pep_grade=A
        # -> base 80 + pep 20 = 100, then KYC verified -5, then clip 0-100 = 95
        c001 = df[df["customer_id"] == "C001"].iloc[0]
        assert 90 <= c001["crs"] <= 100

    def test_low_rating_low_base(self, sample_customers, sample_kyc):
        from scb_aml_platform.aml_engine.risk_scoring.risk_scoring_engine import (
            compute_crs,
        )
        df = compute_crs(sample_customers, sample_kyc)
        # C002 has risk_rating=low, pep_flag=N -> base 10
        c002 = df[df["customer_id"] == "C002"].iloc[0]
        assert 0 <= c002["crs"] <= 20


class TestComputeTRS:
    """Tests for compute_trs() — behavioural risk from features."""

    def test_empty_features_returns_empty(self):
        from scb_aml_platform.aml_engine.risk_scoring.risk_scoring_engine import (
            compute_trs,
        )
        df = compute_trs(pd.DataFrame())
        assert df.empty
        assert list(df.columns) == ["customer_id", "trs"]

    def test_high_risk_features_produce_high_trs(self, sample_features):
        from scb_aml_platform.aml_engine.risk_scoring.risk_scoring_engine import (
            compute_trs,
        )
        df = compute_trs(sample_features)
        c001 = df[df["customer_id"] == "C001"].iloc[0]
        # C001 has: volume spike 250% (+20), structuring 60*0.4=24,
        # dormancy >180 & txn_7d>5 (+15), avg size change 350% (+10),
        # volume tier >100k (+10) -> total 79
        assert c001["trs"] >= 60

    def test_low_risk_features_produce_low_trs(self, sample_features):
        from scb_aml_platform.aml_engine.risk_scoring.risk_scoring_engine import (
            compute_trs,
        )
        df = compute_trs(sample_features)
        c002 = df[df["customer_id"] == "C002"].iloc[0]
        # C002 has nothing triggered
        assert c002["trs"] <= 10


class TestComputeNRS:
    """Tests for compute_nrs() — network risk."""

    def test_empty_features_returns_empty(self):
        from scb_aml_platform.aml_engine.risk_scoring.risk_scoring_engine import (
            compute_nrs,
        )
        df = compute_nrs(pd.DataFrame(), pd.DataFrame())
        assert df.empty

    def test_sanctions_match_increases_nrs(self, sample_features, sample_screening):
        from scb_aml_platform.aml_engine.risk_scoring.risk_scoring_engine import (
            compute_nrs,
        )
        df = compute_nrs(sample_features, sample_screening)
        c001 = df[df["customer_id"] == "C001"].iloc[0]
        # C001 has sanctions match -> +25
        # cross_border 60% -> +15
        # unique_countries 4 -> +12 (clipped 15)
        # degree 0.1 * 200 = 20 -> +20
        # total ~ 72
        assert c001["nrs"] >= 50
