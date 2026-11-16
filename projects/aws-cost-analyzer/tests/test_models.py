"""The data model: records, evidence, findings, and the basis vocabulary."""

from __future__ import annotations

from datetime import date

import pytest

from aws_cost_analyzer.models import (
    BASES,
    MEASURED,
    MODELLED,
    SAVINGS_BASIS_MODELLED,
    SAVINGS_BASIS_NOT_QUANTIFIED,
    UPPER_BOUND,
    CostRecord,
    Evidence,
    Finding,
    severity_for,
)


def _record(**kwargs) -> CostRecord:
    defaults = dict(
        period_start=date(2026, 5, 1),
        period_end=date(2026, 6, 1),
        granularity="MONTHLY",
        service="Amazon Simple Storage Service",
        region="ap-southeast-1",
        group=("Amazon Simple Storage Service",),
        amount=123.45,
    )
    defaults.update(kwargs)
    return CostRecord(**defaults)


class TestCostRecord:
    def test_a_monthly_record_is_complete(self):
        assert _record().is_complete_month

    def test_a_partial_month_is_not_complete(self):
        # June 1 to June 15 — a partial period.
        record = _record(period_start=date(2026, 6, 1), period_end=date(2026, 6, 15))
        assert not record.is_complete_month

    def test_a_daily_record_is_always_complete(self):
        record = _record(
            period_start=date(2026, 6, 1),
            period_end=date(2026, 6, 2),
            granularity="DAILY",
        )
        assert record.is_complete_month

    def test_the_period_label_is_the_month(self):
        assert _record().period_label == "2026-05"

    def test_the_group_is_a_tuple_not_a_dict(self):
        # A GroupBy=[SERVICE] layout and a GroupBy=[SERVICE, TAG] layout
        # are different dimension spaces.
        assert isinstance(_record().group, tuple)
        assert isinstance(_record(group=("S3", "Data")).group, tuple)

    def test_it_round_trips_through_a_dict(self):
        original = _record(tags={"TagKey": "Data"})
        restored = CostRecord.from_dict(original.to_dict())
        assert restored == original

    def test_the_round_trip_keeps_the_group_a_tuple(self):
        restored = CostRecord.from_dict(_record(group=("S3", "Data")).to_dict())
        assert restored.group == ("S3", "Data")


class TestFinding:
    def _finding(self, **kwargs) -> Finding:
        defaults = dict(
            id="growth:s3:bucket-a",
            detector="growth",
            title="Bucket a grew",
            severity="medium",
            summary="Bucket a grew by 40%.",
            target="bucket-a",
            cost_impact=120.0,
            cost_impact_basis=MEASURED,
        )
        defaults.update(kwargs)
        return Finding(**defaults)

    def test_it_rejects_an_unknown_basis(self):
        with pytest.raises(ValueError, match="cost_impact_basis"):
            self._finding(cost_impact_basis="probably")

    def test_it_accepts_the_three_known_bases(self):
        for basis in BASES:
            assert self._finding(cost_impact_basis=basis).cost_impact_basis == basis

    def test_a_saving_with_no_basis_is_rejected(self):
        # There is no such thing as a savings figure with no provenance.
        with pytest.raises(ValueError, match="savings_basis"):
            self._finding(savings_estimate=50.0, savings_basis="")

    def test_a_saving_must_carry_a_known_basis(self):
        with pytest.raises(ValueError, match="savings_basis"):
            self._finding(savings_estimate=50.0, savings_basis="measured")

    def test_the_two_savings_bases_are_accepted(self):
        for basis in (SAVINGS_BASIS_MODELLED, SAVINGS_BASIS_NOT_QUANTIFIED):
            assert self._finding(savings_basis=basis).savings_basis == basis

    def test_it_round_trips_through_a_dict(self):
        original = self._finding(
            evidence=[
                Evidence(
                    metric="monthly_spend",
                    value=120.0,
                    unit="USD",
                    source="cost_explorer",
                    period="2026-10",
                )
            ],
            savings_estimate=40.0,
            savings_basis=SAVINGS_BASIS_MODELLED,
        )
        restored = Finding.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.cost_impact == original.cost_impact
        assert restored.cost_impact_basis == original.cost_impact_basis
        assert restored.evidence[0].source == "cost_explorer"
        assert restored.savings_basis == SAVINGS_BASIS_MODELLED

    def test_a_modelled_finding_needs_volume_evidence(self):
        without = self._finding(cost_impact_basis=MODELLED, evidence=[])
        assert not without.has_volume_evidence

        with_volume = self._finding(
            cost_impact_basis=MODELLED,
            evidence=[
                Evidence(
                    metric="storage_gb",
                    value=100.0,
                    unit="GB",
                    source="cloudwatch",
                    period="2026-10",
                )
            ],
        )
        assert with_volume.has_volume_evidence


class TestSeverity:
    def test_a_large_measured_impact_is_high(self):
        assert severity_for(5000, MEASURED) == "high"

    def test_a_mid_measured_impact_is_medium(self):
        assert severity_for(500, MEASURED) == "medium"

    def test_a_small_measured_impact_is_low(self):
        assert severity_for(20, MEASURED) == "low"

    def test_an_upper_bound_can_never_be_high(self):
        # It is a ceiling on something we could not measure. It might be
        # worth nothing at all.
        assert severity_for(100000, UPPER_BOUND) == "low"

    def test_a_modelled_impact_can_be_high(self):
        # Modelled is weaker than measured but not that weak — it is a
        # real volume times a real rate.
        assert severity_for(5000, MODELLED) == "high"
