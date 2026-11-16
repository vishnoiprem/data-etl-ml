"""The four detectors, and the guards that keep them honest.

Each detector has a *decoy* case: something that looks like a finding
but is not. Those are the tests that matter most, because a detector
that cries wolf is worse than one that finds nothing — a reader who
learns to ignore the output stops reading it.
"""

from __future__ import annotations

from datetime import date

import pytest

from aws_cost_analyzer.config import Thresholds
from aws_cost_analyzer.detectors import access, allocation, growth, lifecycle
from aws_cost_analyzer.models import CostRecord
from aws_cost_analyzer.pricing import default_card


def _record(
    period: str,
    amount: float,
    *,
    group: tuple[str, ...] = ("Amazon Simple Storage Service",),
    service: str = "Amazon Simple Storage Service",
    estimated: bool = False,
) -> CostRecord:
    year, month = (int(p) for p in period.split("-"))
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return CostRecord(
        period_start=start,
        period_end=end,
        granularity="MONTHLY",
        service=service,
        region="ap-southeast-1",
        group=group,
        amount=amount,
        estimated=estimated,
    )


# --------------------------------------------------------------------------- #
# D1 — growth
# --------------------------------------------------------------------------- #


class TestGrowth:
    def test_a_bucket_that_grew_is_found(self):
        records = [
            _record("2026-08", 100.0, group=("s3", "bucket-a")),
            _record("2026-09", 110.0, group=("s3", "bucket-a")),
            _record("2026-10", 200.0, group=("s3", "bucket-a")),
        ]
        findings = growth.detect_growth(records, Thresholds(), group_index=1)
        assert len(findings) == 1
        assert findings[0].target == "bucket-a"

    def test_a_stable_bucket_is_not_found(self):
        records = [
            _record("2026-08", 100.0, group=("s3", "bucket-a")),
            _record("2026-09", 102.0, group=("s3", "bucket-a")),
            _record("2026-10", 98.0, group=("s3", "bucket-a")),
        ]
        assert growth.detect_growth(records, Thresholds(), group_index=1) == []

    def test_a_decoy_that_doubled_to_nothing_is_not_found(self):
        # The classic false positive: a huge relative move on a tiny
        # amount. $3 doubling is not a story.
        records = [
            _record("2026-08", 3.0, group=("s3", "tiny")),
            _record("2026-09", 4.0, group=("s3", "tiny")),
            _record("2026-10", 12.0, group=("s3", "tiny")),
        ]
        assert growth.detect_growth(records, Thresholds(), group_index=1) == []

    def test_a_decoy_that_moved_a_lot_but_stayed_small_is_not_found(self):
        records = [
            _record("2026-08", 20.0, group=("s3", "small")),
            _record("2026-09", 30.0, group=("s3", "small")),
            _record("2026-10", 40.0, group=("s3", "small")),
        ]
        findings = growth.detect_growth(records, Thresholds(), group_index=1)
        assert findings == []

    def test_a_measured_growth_passes_the_double_threshold(self):
        records = [
            _record("2026-08", 100.0, group=("s3", "bucket-a")),
            _record("2026-09", 110.0, group=("s3", "bucket-a")),
            _record("2026-10", 200.0, group=("s3", "bucket-a")),
        ]
        findings = growth.detect_growth(records, Thresholds(), group_index=1)
        assert findings[0].cost_impact_basis == "measured"
        # The baseline is the trailing median (105), not the previous
        # month (110) — a single unusual month should not define "normal".
        assert findings[0].cost_impact == pytest.approx(95.0)

    def test_the_growth_is_measured_against_the_trailing_median(self):
        # 100, 110, 200 -> median of (100, 110) is 105.
        records = [
            _record("2026-08", 100.0, group=("s3", "bucket-a")),
            _record("2026-09", 110.0, group=("s3", "bucket-a")),
            _record("2026-10", 200.0, group=("s3", "bucket-a")),
        ]
        findings = growth.detect_growth(records, Thresholds(), group_index=1)
        assert findings[0].details["baseline"] == pytest.approx(105.0)

    def test_a_new_target_is_found_on_the_absolute_floor_alone(self):
        # There is no percentage for something that did not exist.
        records = [
            _record("2026-09", 100.0, group=("s3", "existing")),
            _record("2026-10", 75.0, group=("s3", "brand-new")),
        ]
        findings = growth.detect_growth(records, Thresholds(), group_index=1)
        targets = {f.target for f in findings}
        assert "brand-new" in targets

    def test_a_target_above_its_own_trailing_max_is_noted(self):
        records = [
            _record("2026-07", 50.0, group=("s3", "bucket-a")),
            _record("2026-08", 60.0, group=("s3", "bucket-a")),
            _record("2026-09", 70.0, group=("s3", "bucket-a")),
            _record("2026-10", 500.0, group=("s3", "bucket-a")),
        ]
        findings = growth.detect_growth(records, Thresholds(), group_index=1)
        assert findings[0].details["above_own_trailing_max"]

    def test_the_id_is_stable_across_runs(self):
        records = [
            _record("2026-08", 100.0, group=("s3", "bucket-a")),
            _record("2026-09", 110.0, group=("s3", "bucket-a")),
            _record("2026-10", 200.0, group=("s3", "bucket-a")),
        ]
        first = growth.detect_growth(records, Thresholds(), group_index=1)
        second = growth.detect_growth(records, Thresholds(), group_index=1)
        assert first[0].id == second[0].id

    def test_the_id_has_no_timestamp_in_it(self):
        records = [
            _record("2026-08", 100.0, group=("s3", "bucket-a")),
            _record("2026-10", 200.0, group=("s3", "bucket-a")),
        ]
        findings = growth.detect_growth(records, Thresholds(), group_index=1)
        assert "2026-11" not in findings[0].id
        assert "T" not in findings[0].id


# --------------------------------------------------------------------------- #
# D2 — access
# --------------------------------------------------------------------------- #


#: The real S3 server access log format is not Common Log Format:
#:
#:     bucket_owner bucket [time] remote_ip requester request_id operation "key" HTTP/1.1 status bytes ...
#:
#: The operation is ``REST.GET.OBJECT``-style, and the key is quoted.
LOG_SAMPLE = """
79a1b2c3d4e5f6g7h8i9 sample-bucket [06/Feb/2026:00:00:01 +0000] 1.2.3.4 arn:aws:iam::1:u abc REST.GET.OBJECT "logs/2026-02-01.log" HTTP/1.1 200 1048576 123 - 123 12 34 56
79a1b2c3d4e5f6g7h8i9 sample-bucket [06/Feb/2026:00:00:02 +0000] 1.2.3.4 arn:aws:iam::1:u abc REST.GET.OBJECT "logs/2026-02-02.log" HTTP/1.1 200 1048576 123 - 123 12 34 56
79a1b2c3d4e5f6g7h8i9 sample-bucket [06/Feb/2026:00:00:03 +0000] 1.2.3.4 arn:aws:iam::1:u abc REST.GET.OBJECT "logs/2026-02-03.log" HTTP/1.1 200 1048576 123 - 123 12 34 56
79a1b2c3d4e5f6g7h8i9 sample-bucket [06/Feb/2026:00:00:04 +0000] 1.2.3.4 arn:aws:iam::1:u abc REST.GET.OBJECT "data/report.csv" HTTP/1.1 200 512 123 - 123 12 34 56
79a1b2c3d4e5f6g7h8i9 sample-bucket [06/Feb/2026:00:00:05 +0000] 1.2.3.4 arn:aws:iam::1:u abc REST.GET.OBJECT "data/report2.csv" HTTP/1.1 200 512 123 - 123 12 34 56
79a1b2c3d4e5f6g7h8i9 sample-bucket [06/Feb/2026:00:00:06 +0000] 1.2.3.4 arn:aws:iam::1:u abc REST.GET.OBJECT "data/report3.csv" HTTP/1.1 200 512 123 - 123 12 34 56
"""

#: A scanner that LISTs the bucket. LISTs are billed at $0.005 per
#: 1,000 — about ten times a GET — so this is the expensive pattern.
LOG_SCANNER = """
79a1b2c3d4e5f6g7h8i9 scan-bucket [06/Feb/2026:00:00:01 +0000] 1.2.3.4 arn:aws:iam::1:u abc REST.GET.BUCKET "" HTTP/1.1 200 1024 123 - 123 12 34 56
79a1b2c3d4e5f6g7h8i9 scan-bucket [06/Feb/2026:00:00:02 +0000] 1.2.3.4 arn:aws:iam::1:u abc REST.GET.BUCKET "" HTTP/1.1 200 1024 123 - 123 12 34 56
79a1b2c3d4e5f6g7h8i9 scan-bucket [06/Feb/2026:00:00:03 +0000] 1.2.3.4 arn:aws:iam::1:u abc REST.GET.BUCKET "" HTTP/1.1 200 1024 123 - 123 12 34 56
79a1b2c3d4e5f6g7h8i9 scan-bucket [06/Feb/2026:00:00:04 +0000] 1.2.3.4 arn:aws:iam::1:u abc REST.GET.OBJECT "archive/old-1.bin" HTTP/1.1 200 1024 123 - 123 12 34 56
"""


class TestAccess:
    def test_the_log_is_parsed(self):
        log = access.parse_access_log(LOG_SAMPLE)
        assert log.total_requests == 6

    def test_the_requests_are_grouped_by_prefix(self):
        log = access.parse_access_log(LOG_SAMPLE)
        assert log.by_prefix["sample-bucket"]["logs"] == 3
        assert log.by_prefix["sample-bucket"]["data"] == 3

    def test_a_bucket_get_is_counted_as_a_list(self):
        log = access.parse_access_log(
            'owner b [06/Feb/2026:00:00:01 +0000] 1.2.3.4 arn:x abc REST.GET.BUCKET "" HTTP/1.1 200 10 1 - 1 2 3 4\n'
        )
        assert log.by_request_type["LIST"] == 1
        assert "GET" not in log.by_request_type

    def test_error_responses_are_not_counted(self):
        log = access.parse_access_log(
            'owner b [06/Feb/2026:00:00:01 +0000] 1.2.3.4 arn:x abc REST.GET.OBJECT "x" HTTP/1.1 404 0 1 - 1 2 3 4\n'
        )
        assert log.total_requests == 0

    def test_the_coverage_ratio_is_the_log_over_cloudwatch(self):
        assert access.coverage_ratio(100, 100.0) == pytest.approx(1.0)
        assert access.coverage_ratio(50, 100.0) == pytest.approx(0.5)

    def test_a_zero_cloudwatch_count_gives_no_coverage(self):
        assert access.coverage_ratio(100, 0.0) == 0.0

    def test_a_dominant_prefix_is_found(self):
        # A scanner that LISTs the bucket. LISTs are billed at $0.005
        # per 1,000 — about ten times a GET — so 6,000,000 LISTs is
        # roughly $30 and clears the $25 floor.
        #
        # The log is scaled by repetition, which is what a real scanner
        # produces; the counts are what the detector reads.
        log = access.parse_access_log(LOG_SCANNER)
        log.by_prefix["scan-bucket"]["(root)"] = 6_000_000
        log.by_request_type["LIST"] = 6_000_000
        log.total_requests = 6_000_000
        findings = access.detect_access_patterns(
            log, {"scan-bucket": 6_000_000.0}, Thresholds(), default_card()
        )
        assert findings
        assert findings[0].details["prefix"] in {"(root)", "archive"}

    def test_a_list_heavy_scanner_is_noted_as_such(self):
        log = access.parse_access_log(LOG_SCANNER)
        log.by_prefix["scan-bucket"]["(root)"] = 6_000_000
        log.by_request_type["LIST"] = 6_000_000
        log.total_requests = 6_000_000
        findings = access.detect_access_patterns(
            log, {"scan-bucket": 6_000_000.0}, Thresholds(), default_card()
        )
        assert findings
        assert findings[0].details["list_request_share"] > 0.5

    def test_a_tiny_amount_of_traffic_is_not_worth_a_finding(self):
        log = access.parse_access_log(LOG_SAMPLE)
        findings = access.detect_access_patterns(
            log, {"sample-bucket": 600.0}, Thresholds(), default_card()
        )
        # 6 requests cost a fraction of a cent — below the $25 floor.
        assert findings == []

    def test_the_coverage_is_checked_against_cloudwatch(self):
        log = access.parse_access_log(LOG_SAMPLE)
        # The log saw 6 requests; CloudWatch counted 100. The coverage
        # is 6%, so the finding cannot be presented as complete.
        findings = access.detect_access_patterns(
            log, {"sample-bucket": 100.0}, Thresholds(), default_card()
        )
        if findings:
            assert findings[0].confidence <= 0.5

    def test_a_complete_log_keeps_full_confidence(self):
        log = access.parse_access_log(LOG_SAMPLE * 100)
        findings = access.detect_access_patterns(
            log, {"sample-bucket": 600.0}, Thresholds(), default_card()
        )
        if findings:
            assert findings[0].confidence == 1.0

    def test_a_small_traffic_target_is_not_found(self):
        log = access.parse_access_log(LOG_SAMPLE)
        findings = access.detect_access_patterns(
            log, {"sample-bucket": 600.0}, Thresholds(), default_card()
        )
        # 6 requests cost a fraction of a cent — below the $25 floor.
        assert findings == []

    def test_logging_being_off_is_reported(self):
        findings = access.detect_logging_disabled(
            ["bucket-a"], Thresholds(), default_card(), monthly_spend=500.0
        )
        assert len(findings) == 1
        assert findings[0].details["problem"] == "access_logging_disabled"

    def test_logging_being_off_costs_nothing_it_cannot_measure(self):
        findings = access.detect_logging_disabled(
            ["bucket-a"], Thresholds(), default_card(), monthly_spend=500.0
        )
        assert findings[0].cost_impact_basis == "upper_bound"
        assert findings[0].cost_impact == 0.0


# --------------------------------------------------------------------------- #
# D3 — lifecycle
# --------------------------------------------------------------------------- #


class TestLifecycle:
    def _samples(self, days_old: int, size_kb: int = 1024, count: int = 10):
        today = date(2026, 11, 1)
        return [
            lifecycle.ObjectSample(
                key=f"data/file-{i}.bin",
                size_bytes=size_kb * 1024,
                last_modified=date.fromordinal(today.toordinal() - days_old),
            )
            for i in range(count)
        ]

    def test_a_bucket_with_no_rules_is_a_finding(self):
        findings = lifecycle.detect_lifecycle(
            "bucket-a", [], self._samples(200), 100.0, Thresholds(), default_card(),
            today=date(2026, 11, 1),
        )
        assert len(findings) == 1
        assert findings[0].details["problem"] == "no_lifecycle_configuration"

    def test_a_mis_scoped_rule_is_a_different_finding(self):
        rules = [
            lifecycle.LifecycleRule(
                id="r1", prefix="logs/", transitions=[("GLACIER_IR", 90)]
            )
        ]
        findings = lifecycle.detect_lifecycle(
            "bucket-a", rules, self._samples(200), 100.0, Thresholds(), default_card(),
            today=date(2026, 11, 1),
        )
        problems = {f.details.get("problem") for f in findings}
        assert "mis_scoped_rule" in problems

    def test_a_rule_that_covers_the_objects_is_not_mis_scoped(self):
        rules = [
            lifecycle.LifecycleRule(
                id="r1", prefix="data/", transitions=[("GLACIER_IR", 90)]
            )
        ]
        findings = lifecycle.detect_lifecycle(
            "bucket-a", rules, self._samples(200), 100.0, Thresholds(), default_card(),
            today=date(2026, 11, 1),
        )
        problems = {f.details.get("problem") for f in findings}
        assert "mis_scoped_rule" not in problems

    def test_an_early_transition_is_a_finding(self):
        rules = [
            lifecycle.LifecycleRule(
                id="r1", prefix="data/", transitions=[("GLACIER_IR", 30)]
            )
        ]
        findings = lifecycle.detect_lifecycle(
            "bucket-a", rules, self._samples(200), 100.0, Thresholds(), default_card(),
            today=date(2026, 11, 1),
        )
        problems = {f.details.get("problem") for f in findings}
        assert "early_transition" in problems

    def test_a_transition_at_the_aws_minimum_is_fine(self):
        rules = [
            lifecycle.LifecycleRule(
                id="r1", prefix="data/", transitions=[("GLACIER_IR", 90)]
            )
        ]
        findings = lifecycle.detect_lifecycle(
            "bucket-a", rules, self._samples(200), 100.0, Thresholds(), default_card(),
            today=date(2026, 11, 1),
        )
        problems = {f.details.get("problem") for f in findings}
        assert "early_transition" not in problems

    def test_young_objects_are_not_proposed_for_a_cold_class(self):
        findings = lifecycle.detect_lifecycle(
            "bucket-a",
            [lifecycle.LifecycleRule(id="r1", prefix="", transitions=[])],
            self._samples(10),
            100.0,
            Thresholds(),
            default_card(),
            today=date(2026, 11, 1),
        )
        problems = {f.details.get("problem") for f in findings}
        assert "cold_class_opportunity" not in problems

    def test_small_objects_are_not_proposed_for_a_cold_class(self):
        # Under 128 KB they are billed at the tier minimum, so moving
        # them saves nothing.
        findings = lifecycle.detect_lifecycle(
            "bucket-a",
            [lifecycle.LifecycleRule(id="r1", prefix="", transitions=[])],
            self._samples(200, size_kb=10),
            100.0,
            Thresholds(),
            default_card(),
            today=date(2026, 11, 1),
        )
        problems = {f.details.get("problem") for f in findings}
        assert "cold_class_opportunity" not in problems

    def test_old_large_objects_are_proposed_for_a_cold_class(self):
        findings = lifecycle.detect_lifecycle(
            "bucket-a",
            [lifecycle.LifecycleRule(id="r1", prefix="", transitions=[])],
            self._samples(200, size_kb=10240, count=100),
            1000.0,
            Thresholds(),
            default_card(),
            today=date(2026, 11, 1),
        )
        problems = {f.details.get("problem") for f in findings}
        assert "cold_class_opportunity" in problems

    def test_a_cold_class_saving_is_modelled_not_measured(self):
        findings = lifecycle.detect_lifecycle(
            "bucket-a",
            [lifecycle.LifecycleRule(id="r1", prefix="", transitions=[])],
            self._samples(200, size_kb=10240, count=100),
            1000.0,
            Thresholds(),
            default_card(),
            today=date(2026, 11, 1),
        )
        cold = next(f for f in findings if f.details.get("problem") == "cold_class_opportunity")
        assert cold.cost_impact_basis == "modelled"
        assert cold.savings_basis == "modelled_from_rate_card"

    def test_a_cold_class_saving_carries_a_volume_evidence(self):
        findings = lifecycle.detect_lifecycle(
            "bucket-a",
            [lifecycle.LifecycleRule(id="r1", prefix="", transitions=[])],
            self._samples(200, size_kb=10240, count=100),
            1000.0,
            Thresholds(),
            default_card(),
            today=date(2026, 11, 1),
        )
        cold = next(f for f in findings if f.details.get("problem") == "cold_class_opportunity")
        assert cold.has_volume_evidence

    def test_an_empty_sample_is_reported_as_insufficient(self):
        findings = lifecycle.detect_lifecycle(
            "bucket-a",
            [lifecycle.LifecycleRule(id="r1", prefix="", transitions=[])],
            [],
            100.0,
            Thresholds(),
            default_card(),
            today=date(2026, 11, 1),
        )
        assert findings[0].details["problem"] == "insufficient_sample"

    def test_the_rules_are_parsed_from_an_s3_response(self):
        rules = lifecycle.parse_lifecycle_rules(
            {
                "Rules": [
                    {
                        "ID": "r1",
                        "Status": "Enabled",
                        "Filter": {"Prefix": "logs/"},
                        "Transitions": [{"Days": 90, "StorageClass": "GLACIER_IR"}],
                        "Expiration": {"Days": 365},
                    }
                ]
            }
        )
        assert rules[0].prefix == "logs/"
        assert rules[0].transitions == [("GLACIER_IR", 90)]
        assert rules[0].expiration_days == 365

    def test_no_configuration_parses_to_no_rules(self):
        assert lifecycle.parse_lifecycle_rules(None) == []


# --------------------------------------------------------------------------- #
# D4 — allocation
# --------------------------------------------------------------------------- #


class TestAllocation:
    def _tagged(self, tag: str, amounts: dict[str, float]):
        return [
            _record(period, amount, group=("Amazon Simple Storage Service", tag))
            for period, amount in amounts.items()
        ]

    def test_a_growing_tag_is_found(self):
        records = self._tagged(
            "Data", {"2026-08": 100.0, "2026-09": 110.0, "2026-10": 300.0}
        )
        findings = allocation.detect_allocation(
            records, 510.0, Thresholds(), region="ap-southeast-1"
        )
        assert len(findings) == 1
        assert findings[0].target == "Data"

    def test_a_stable_tag_is_not_found(self):
        records = self._tagged(
            "Data", {"2026-08": 100.0, "2026-09": 105.0, "2026-10": 98.0}
        )
        findings = allocation.detect_allocation(
            records, 303.0, Thresholds(), region="ap-southeast-1"
        )
        assert findings == []

    def test_a_decoy_squad_that_doubled_to_nothing_is_not_found(self):
        # $12 -> $36 is a 200% move and a rounding error.
        records = self._tagged("Data-Squad", {"2026-08": 12.0, "2026-10": 36.0})
        findings = allocation.detect_allocation(
            records, 48.0, Thresholds(), region="ap-southeast-1"
        )
        assert findings == []

    def test_the_untagged_gap_is_reported(self):
        records = self._tagged("Data", {"2026-10": 500.0})
        findings = allocation.detect_allocation(
            records, 1000.0, Thresholds(), region="ap-southeast-1"
        )
        assert any(f.details.get("problem") == "untagged_gap" for f in findings)

    def test_full_coverage_produces_no_untagged_gap(self):
        records = self._tagged("Data", {"2026-10": 1000.0})
        findings = allocation.detect_allocation(
            records, 1000.0, Thresholds(), region="ap-southeast-1"
        )
        assert not any(f.details.get("problem") == "untagged_gap" for f in findings)

    def test_incomplete_coverage_caps_the_confidence(self):
        records = self._tagged("Data", {"2026-08": 100.0, "2026-10": 200.0})
        findings = allocation.detect_allocation(
            records, 1000.0, Thresholds(), region="ap-southeast-1"
        )
        assert all(f.confidence <= 0.6 for f in findings)

    def test_complete_coverage_keeps_full_confidence(self):
        records = self._tagged("Data", {"2026-08": 100.0, "2026-10": 200.0})
        findings = allocation.detect_allocation(
            records, 300.0, Thresholds(), region="ap-southeast-1"
        )
        assert all(f.confidence == 1.0 for f in findings)

    def test_the_untagged_gap_is_measured(self):
        records = self._tagged("Data", {"2026-10": 500.0})
        findings = allocation.detect_allocation(
            records, 1000.0, Thresholds(), region="ap-southeast-1"
        )
        gap = next(f for f in findings if f.details.get("problem") == "untagged_gap")
        assert gap.cost_impact_basis == "measured"
        assert gap.cost_impact == pytest.approx(500.0)
