"""The registry: running all four detectors together."""

from __future__ import annotations

from datetime import date

from aws_cost_analyzer.config import Settings
from aws_cost_analyzer.detectors import lifecycle
from aws_cost_analyzer.detectors.registry import AnalysisInput, dedupe, run_all
from aws_cost_analyzer.models import CostRecord
from aws_cost_analyzer.pricing import default_card


def _record(period: str, amount: float, group: tuple[str, ...]) -> CostRecord:
    year, month = (int(p) for p in period.split("-"))
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return CostRecord(
        period_start=start,
        period_end=end,
        granularity="MONTHLY",
        service="Amazon Simple Storage Service",
        region="ap-southeast-1",
        group=group,
        amount=amount,
    )


class TestRunning:
    def test_an_empty_input_produces_no_findings(self):
        findings = run_all(AnalysisInput(), Settings(), default_card())
        assert findings == []

    def test_a_growing_bucket_is_found(self):
        records = [
            _record("2026-08", 100.0, ("Amazon Simple Storage Service", "bucket-a")),
            _record("2026-09", 110.0, ("Amazon Simple Storage Service", "bucket-a")),
            _record("2026-10", 200.0, ("Amazon Simple Storage Service", "bucket-a")),
        ]
        findings = run_all(
            AnalysisInput(records=records, resource_group_index=1), Settings(), default_card()
        )
        assert any(f.detector == "growth" for f in findings)

    def test_the_findings_are_sorted_by_severity(self):
        records = [
            _record("2026-08", 100.0, ("Amazon Simple Storage Service", "bucket-a")),
            _record("2026-09", 110.0, ("Amazon Simple Storage Service", "bucket-a")),
            _record("2026-10", 200.0, ("Amazon Simple Storage Service", "bucket-a")),
        ]
        findings = run_all(
            AnalysisInput(records=records, resource_group_index=1), Settings(), default_card()
        )
        order = {"high": 0, "medium": 1, "low": 2}
        severities = [order[f.severity] for f in findings]
        assert severities == sorted(severities)

    def test_one_failing_detector_does_not_sink_the_run(self):
        # A detector that raises must not hide the findings of the
        # ones that work.
        data = AnalysisInput(
            records=[
                _record("2026-08", 100.0, ("Amazon Simple Storage Service", "bucket-a")),
                _record("2026-10", 200.0, ("Amazon Simple Storage Service", "bucket-a")),
            ],
            resource_group_index=1,
        )
        # A rule with a transition that is not a (class, days) pair
        # blows up the lifecycle detector's unpacking. The sample is
        # needed so the detector gets past its early-return paths.
        data.lifecycle_rules = {"bucket-a": [lifecycle.LifecycleRule(id="bad", transitions=[1])]}
        data.object_samples = {
            "bucket-a": [
                lifecycle.ObjectSample(
                    key="data/a.bin", size_bytes=1024 * 1024, last_modified=date(2026, 1, 1)
                )
            ]
        }
        data.today = date(2026, 11, 1)

        findings = run_all(data, Settings(), default_card())
        assert any(f.detector == "growth" for f in findings)
        assert any("lifecycle detector failed" in note for note in data.notes)

    def test_the_ids_are_stable_across_runs(self):
        records = [
            _record("2026-08", 100.0, ("Amazon Simple Storage Service", "bucket-a")),
            _record("2026-10", 200.0, ("Amazon Simple Storage Service", "bucket-a")),
        ]
        data = AnalysisInput(records=records, resource_group_index=1)
        first = run_all(data, Settings(), default_card())
        second = run_all(data, Settings(), default_card())
        assert [f.id for f in first] == [f.id for f in second]

    def test_the_ids_are_unique(self):
        records = [
            _record("2026-08", 100.0, ("Amazon Simple Storage Service", "bucket-a")),
            _record("2026-09", 110.0, ("Amazon Simple Storage Service", "bucket-a")),
            _record("2026-10", 200.0, ("Amazon Simple Storage Service", "bucket-a")),
        ]
        findings = run_all(
            AnalysisInput(records=records, resource_group_index=1), Settings(), default_card()
        )
        ids = [f.id for f in findings]
        assert len(ids) == len(set(ids))


class TestDedupe:
    def test_a_duplicate_id_is_dropped(self):
        records = [
            _record("2026-08", 100.0, ("Amazon Simple Storage Service", "bucket-a")),
            _record("2026-10", 200.0, ("Amazon Simple Storage Service", "bucket-a")),
        ]
        findings = run_all(
            AnalysisInput(records=records, resource_group_index=1), Settings(), default_card()
        )
        assert len(dedupe(findings)) == len(findings)

    def test_a_manually_duplicated_finding_is_dropped(self):
        from aws_cost_analyzer.models import MEASURED, Finding

        finding = Finding(
            id="growth:bucket-a:2026-10",
            detector="growth",
            title="t",
            severity="low",
            summary="s",
            target="bucket-a",
            cost_impact=1.0,
            cost_impact_basis=MEASURED,
        )
        assert len(dedupe([finding, finding])) == 1
