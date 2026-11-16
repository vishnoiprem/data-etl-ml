"""The report — and specifically, that every figure shows its basis."""

from __future__ import annotations

import json

import pytest

from aws_cost_analyzer.models import MEASURED, MODELLED, UPPER_BOUND, Evidence, Finding
from aws_cost_analyzer.report import (
    ReportContext,
    format_basis,
    format_money,
    render_text,
    to_json,
    totals_by_basis,
    totals_by_detector,
    write_json_report,
    write_text_report,
)


def _finding(
    *,
    detector: str = "growth",
    target: str = "analytics-raw",
    impact: float = 2000.0,
    basis: str = MEASURED,
    savings: float = 0.0,
    savings_basis: str = "",
    severity: str = "high",
) -> Finding:
    return Finding(
        id=f"{detector}:{target}:2026-10",
        detector=detector,
        title=f"{target} grew",
        severity=severity,
        summary=f"{target} cost ${impact:,.2f} in 2026-10.",
        target=target,
        cost_impact=impact,
        cost_impact_basis=basis,
        savings_estimate=savings,
        savings_basis=savings_basis,
        evidence=[
            Evidence(
                metric="monthly_spend",
                value=impact,
                unit="USD",
                source="cost_explorer",
                period="2026-10",
            )
        ],
        confidence=1.0,
        recommendation="Look at the volume.",
    )


class TestFormatting:
    def test_money_has_a_thousands_separator(self):
        assert format_money(1234.5) == "$1,234.50"

    def test_zero_money_is_still_a_dollar_figure(self):
        assert format_money(0) == "$0.00"

    @pytest.mark.parametrize(
        ("basis", "expected"),
        [
            (MEASURED, "measured"),
            (MODELLED, "modelled"),
            (UPPER_BOUND, "upper bound"),
        ],
    )
    def test_each_basis_has_its_own_label(self, basis, expected):
        finding = _finding(basis=basis)
        assert expected in format_basis(finding)

    def test_measured_and_modelled_do_not_read_the_same(self):
        assert format_basis(_finding(basis=MEASURED)) != format_basis(_finding(basis=MODELLED))


class TestTheTextReport:
    def test_it_shows_the_window(self):
        context = ReportContext(region="ap-southeast-1", start="2026-05-01", end="2026-10-31")
        text = render_text([], context)
        assert "ap-southeast-1" in text
        assert "2026-05-01" in text

    def test_it_shows_the_basis_of_every_figure(self):
        findings = [
            _finding(basis=MEASURED),
            _finding(detector="lifecycle", target="b2", basis=MODELLED),
            _finding(detector="access", target="b3", basis=UPPER_BOUND),
        ]
        text = render_text(findings, ReportContext(region="ap-southeast-1"))
        assert "measured" in text
        assert "modelled" in text
        assert "upper bound" in text

    def test_it_never_says_savings(self):
        findings = [_finding(savings=500.0, savings_basis="modelled_from_rate_card")]
        text = render_text(findings, ReportContext()).lower()
        assert "savings" not in text

    def test_it_says_avoidable_cost_at_the_observed_volume(self):
        findings = [_finding(savings=500.0, savings_basis="modelled_from_rate_card")]
        text = render_text(findings, ReportContext()).lower()
        assert "observed volume" in text

    def test_it_names_the_excluded_periods(self):
        context = ReportContext(excluded_periods=["2026-10"])
        text = render_text([], context)
        assert "2026-10" in text
        assert "excluded" in text.lower()

    def test_it_states_a_region_mismatch(self):
        context = ReportContext(
            region="ap-southeast-1",
            rate_card_region="us-east-1",
            rate_card_checked_on="2026-11-16",
        )
        text = render_text([], context)
        assert "us-east-1" in text
        assert "ap-southeast-1" in text

    def test_it_does_not_mention_a_mismatch_when_the_regions_match(self):
        context = ReportContext(region="us-east-1", rate_card_region="us-east-1")
        text = render_text([], context)
        assert "indicative, not authoritative" not in text

    def test_it_says_when_there_are_no_findings(self):
        text = render_text([], ReportContext())
        assert "Nothing crossed the thresholds" in text

    def test_it_shows_the_evidence(self):
        text = render_text([_finding()], ReportContext())
        assert "monthly_spend" in text
        assert "cost_explorer" in text

    def test_it_shows_the_recommendation(self):
        text = render_text([_finding()], ReportContext())
        assert "Look at the volume." in text

    def test_it_says_the_model_cannot_change_a_finding(self):
        text = render_text([], ReportContext(router_name="stub"))
        assert "cannot change a finding" in text


class TestTheJsonReport:
    def test_it_is_valid_json(self):
        data = to_json([_finding()], ReportContext())
        json.dumps(data)

    def test_it_carries_every_finding(self):
        data = to_json([_finding(), _finding(target="other")], ReportContext())
        assert len(data["findings"]) == 2

    def test_it_keeps_the_bases_apart(self):
        findings = [
            _finding(basis=MEASURED, impact=100.0),
            _finding(detector="lifecycle", target="b2", basis=MODELLED, impact=50.0),
            _finding(detector="access", target="b3", basis=UPPER_BOUND, impact=25.0),
        ]
        data = to_json(findings, ReportContext())
        totals = data["totals_by_basis"]
        assert totals["measured"] == 100.0
        assert totals["modelled"] == 50.0
        assert totals["upper_bound"] == 25.0

    def test_the_totals_by_detector_are_correct(self):
        findings = [
            _finding(detector="growth", impact=100.0),
            _finding(detector="growth", target="b2", impact=50.0),
            _finding(detector="lifecycle", target="b3", impact=25.0),
        ]
        totals = totals_by_detector(findings)
        assert totals["growth"] == 150.0
        assert totals["lifecycle"] == 25.0

    def test_it_carries_the_excluded_periods(self):
        data = to_json([], ReportContext(excluded_periods=["2026-10"]))
        assert data["excluded_periods"] == ["2026-10"]

    def test_it_carries_the_router_name(self):
        data = to_json([], ReportContext(router_name="stub"))
        assert data["router"] == "stub"

    def test_the_spend_is_marked_as_measured(self):
        data = to_json([], ReportContext(total_spend=1234.0))
        assert data["total_spend_basis"] == "measured"


class TestWriting:
    def test_the_text_report_is_written(self, tmp_path):
        path = tmp_path / "report.txt"
        write_text_report([_finding()], ReportContext(), path)
        assert "analytics-raw" in path.read_text()

    def test_the_json_report_is_written(self, tmp_path):
        path = tmp_path / "report.json"
        write_json_report([_finding()], ReportContext(), path)
        assert json.loads(path.read_text())["finding_count"] == 1

    def test_the_parent_directory_is_created(self, tmp_path):
        path = tmp_path / "nested" / "deeper" / "report.json"
        write_json_report([], ReportContext(), path)
        assert path.exists()


def test_totals_by_basis_is_empty_for_no_findings():
    assert totals_by_basis([]) == {}
