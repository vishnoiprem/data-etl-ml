"""Snapshots: writing, reading, and the complete-period guard."""

from __future__ import annotations

import json

import pytest

from aws_cost_analyzer.ce_normalizer import normalize_cost_and_usage
from aws_cost_analyzer.models import CostRecord
from aws_cost_analyzer.snapshots import (
    KIND_COST_RECORDS,
    Snapshot,
    latest_snapshot,
    list_snapshots,
    period_range,
    read_snapshot,
    snapshot_from_result,
    snapshot_label,
    write_snapshot,
)

SERVICE_GROUP = [{"Type": "DIMENSION", "Key": "SERVICE"}]


def _snapshot(records: list[CostRecord], **kwargs) -> Snapshot:
    defaults = dict(
        kind=KIND_COST_RECORDS,
        region="ap-southeast-1",
        start="2026-05-01",
        end="2026-10-31",
        granularity="MONTHLY",
        records=records,
        periods_seen=[r.period_label for r in records],
        estimated_periods=[r.period_label for r in records if r.estimated],
    )
    defaults.update(kwargs)
    return Snapshot(**defaults)


class TestRoundTrip:
    def test_a_snapshot_round_trips(self, tmp_path, ce_service_payload):
        result = normalize_cost_and_usage(ce_service_payload, group_definitions=SERVICE_GROUP)
        snapshot = snapshot_from_result(
            result,
            region="ap-southeast-1",
            start="2026-05-01",
            end="2026-10-31",
            group_definitions=SERVICE_GROUP,
        )
        path = write_snapshot(snapshot, tmp_path)
        restored = read_snapshot(path)
        assert restored.records == snapshot.records
        assert restored.region == snapshot.region

    def test_the_file_is_valid_json(self, tmp_path, ce_service_payload):
        result = normalize_cost_and_usage(ce_service_payload, group_definitions=SERVICE_GROUP)
        snapshot = snapshot_from_result(result)
        path = write_snapshot(snapshot, tmp_path)
        assert json.loads(path.read_text())["snapshot_version"] == 1

    def test_the_errors_are_kept(self, tmp_path, ce_malformed_payload):
        result = normalize_cost_and_usage(ce_malformed_payload, group_definitions=SERVICE_GROUP)
        snapshot = snapshot_from_result(result)
        path = write_snapshot(snapshot, tmp_path)
        assert len(read_snapshot(path).errors) == 2


class TestCompleteRecords:
    def test_an_estimated_month_is_excluded(self, ce_service_payload):
        result = normalize_cost_and_usage(ce_service_payload, group_definitions=SERVICE_GROUP)
        snapshot = snapshot_from_result(result)
        # October is estimated in the fixture.
        assert len(snapshot.complete_records) == 5

    def test_an_estimated_month_is_named(self, ce_service_payload):
        result = normalize_cost_and_usage(ce_service_payload, group_definitions=SERVICE_GROUP)
        snapshot = snapshot_from_result(result)
        assert snapshot.excluded_periods == ["2026-10"]

    def test_a_partial_month_is_excluded(self):
        from datetime import date

        record = CostRecord(
            period_start=date(2026, 10, 1),
            period_end=date(2026, 10, 15),
            granularity="MONTHLY",
            service="Amazon Simple Storage Service",
            region="ap-southeast-1",
            group=("Amazon Simple Storage Service",),
            amount=100.0,
        )
        snapshot = _snapshot([record], periods_seen=["2026-10"])
        assert snapshot.complete_records == []
        assert snapshot.excluded_periods == ["2026-10"]

    def test_a_complete_month_is_kept(self):
        from datetime import date

        record = CostRecord(
            period_start=date(2026, 9, 1),
            period_end=date(2026, 10, 1),
            granularity="MONTHLY",
            service="Amazon Simple Storage Service",
            region="ap-southeast-1",
            group=("Amazon Simple Storage Service",),
            amount=100.0,
        )
        snapshot = _snapshot([record], periods_seen=["2026-09"])
        assert len(snapshot.complete_records) == 1
        assert snapshot.excluded_periods == []


class TestListing:
    def test_snapshots_are_listed_newest_first(self, tmp_path):
        first = write_snapshot(_snapshot([], taken_at="2026-11-01T00:00:00Z"), tmp_path)
        second = write_snapshot(_snapshot([], taken_at="2026-11-02T00:00:00Z"), tmp_path)
        found = list_snapshots(tmp_path)
        assert set(found) == {first, second}

    def test_the_latest_snapshot_is_found(self, tmp_path):
        write_snapshot(_snapshot([], taken_at="2026-11-01T00:00:00Z"), tmp_path)
        write_snapshot(_snapshot([], taken_at="2026-11-02T00:00:00Z"), tmp_path)
        assert latest_snapshot(tmp_path).taken_at == "2026-11-02T00:00:00Z"

    def test_a_missing_directory_is_not_an_error(self, tmp_path):
        assert list_snapshots(tmp_path / "nope") == []
        assert latest_snapshot(tmp_path / "nope") is None

    def test_the_latest_can_be_filtered_by_kind(self, tmp_path):
        write_snapshot(_snapshot([], taken_at="2026-11-01T00:00:00Z"), tmp_path)
        write_snapshot(
            _snapshot([], kind="raw_payload", taken_at="2026-11-02T00:00:00Z"), tmp_path
        )
        assert latest_snapshot(tmp_path, kind=KIND_COST_RECORDS).taken_at == "2026-11-01T00:00:00Z"


class TestPeriodRange:
    def test_the_range_covers_the_window(self):
        assert period_range("2026-05-01", "2026-10-31") == [
            "2026-05",
            "2026-06",
            "2026-07",
            "2026-08",
            "2026-09",
            "2026-10",
        ]

    def test_the_range_rolls_over_the_year(self):
        assert period_range("2025-11-01", "2026-02-28") == [
            "2025-11",
            "2025-12",
            "2026-01",
            "2026-02",
        ]

    def test_a_single_month_range(self):
        assert period_range("2026-05-01", "2026-05-31") == ["2026-05"]


class TestLabel:
    def test_the_label_says_what_the_snapshot_holds(self, ce_service_payload):
        result = normalize_cost_and_usage(ce_service_payload, group_definitions=SERVICE_GROUP)
        snapshot = snapshot_from_result(result, region="ap-southeast-1")
        label = snapshot_label(snapshot)
        assert "ap-southeast-1" in label
        assert "6 records" in label


def test_snapshot_from_result_keeps_the_group_definitions(ce_service_payload):
    result = normalize_cost_and_usage(ce_service_payload, group_definitions=SERVICE_GROUP)
    snapshot = snapshot_from_result(result, group_definitions=SERVICE_GROUP)
    assert snapshot.group_definitions == SERVICE_GROUP


@pytest.mark.parametrize("kind", ["cost_records", "raw_payload"])
def test_both_kinds_round_trip(tmp_path, kind):
    snapshot = _snapshot([], kind=kind)
    path = write_snapshot(snapshot, tmp_path)
    assert read_snapshot(path).kind == kind
