"""The Cost Explorer normalizer.

This is the most important test file in the project. A normalizer that
drops a group under-counts the bill, and every downstream finding is
then wrong in a way that no unit test of a detector would catch. So the
assertions here are about *exact* row counts, *exact* payload equality
and *exact* error recording — not about "some records came out".
"""

from __future__ import annotations

import json

import pytest

from aws_cost_analyzer.ce_normalizer import (
    describe_group,
    merge_pages,
    normalize_cost_and_usage,
    normalize_with_resources,
    paginate,
    records_from_json,
    records_to_json,
)

SERVICE_GROUP = [{"Type": "DIMENSION", "Key": "SERVICE"}]
TAG_GROUP = [
    {"Type": "DIMENSION", "Key": "SERVICE"},
    {"Type": "TAG", "Key": "user:Data"},
]


class TestRowCounts:
    def test_one_record_per_period_per_group(self, ce_service_payload):
        result = normalize_cost_and_usage(ce_service_payload, group_definitions=SERVICE_GROUP)
        assert len(result.records) == 6

    def test_the_row_count_is_exact_not_approximate(self, ce_service_payload):
        # Six periods, one group each. If the normalizer dropped or
        # duplicated a row the total would be wrong, and the bill would
        # be wrong.
        result = normalize_cost_and_usage(ce_service_payload, group_definitions=SERVICE_GROUP)
        assert len(result.records) == len(ce_service_payload["ResultsByTime"])

    def test_a_tag_group_produces_one_record_per_tag_value(self, ce_tag_payload):
        result = normalize_cost_and_usage(ce_tag_payload, group_definitions=TAG_GROUP)
        assert len(result.records) == 3

    def test_the_total_is_the_sum_of_the_amounts(self, ce_service_payload):
        result = normalize_cost_and_usage(ce_service_payload, group_definitions=SERVICE_GROUP)
        expected = sum(
            float(row["Groups"][0]["Metrics"]["UnblendedCost"]["Amount"])
            for row in ce_service_payload["ResultsByTime"]
        )
        assert result.total_amount == pytest.approx(expected)


class TestAmounts:
    def test_an_amount_is_parsed_from_its_string(self, ce_service_payload):
        result = normalize_cost_and_usage(ce_service_payload, group_definitions=SERVICE_GROUP)
        assert result.records[0].amount == pytest.approx(1234.56)

    def test_an_unparseable_amount_is_an_error_not_a_zero(self, ce_malformed_payload):
        # Coercing to 0.0 would erase a cost without telling anyone, and
        # a missing month looks exactly like a cheap month.
        result = normalize_cost_and_usage(ce_malformed_payload, group_definitions=SERVICE_GROUP)
        assert any("not-a-number" in error for error in result.errors)

    def test_the_bad_row_is_dropped_not_zeroed(self, ce_malformed_payload):
        result = normalize_cost_and_usage(ce_malformed_payload, group_definitions=SERVICE_GROUP)
        amounts = [r.amount for r in result.records]
        assert 0.0 not in amounts
        assert len(result.records) == 2

    def test_a_bad_period_is_an_error(self, ce_malformed_payload):
        result = normalize_cost_and_usage(ce_malformed_payload, group_definitions=SERVICE_GROUP)
        assert any("not-a-date" in error for error in result.errors)

    def test_the_good_rows_survive_a_bad_neighbour(self, ce_malformed_payload):
        result = normalize_cost_and_usage(ce_malformed_payload, group_definitions=SERVICE_GROUP)
        assert {r.amount for r in result.records} == {100.0, 250.0}


class TestPeriods:
    def test_the_period_label_is_the_month(self, ce_service_payload):
        result = normalize_cost_and_usage(ce_service_payload, group_definitions=SERVICE_GROUP)
        assert result.periods_seen == [
            "2026-05",
            "2026-06",
            "2026-07",
            "2026-08",
            "2026-09",
            "2026-10",
        ]

    def test_an_estimated_period_is_marked(self, ce_service_payload):
        result = normalize_cost_and_usage(ce_service_payload, group_definitions=SERVICE_GROUP)
        assert result.estimated_periods == ["2026-10"]

    def test_the_record_carries_the_estimated_flag(self, ce_service_payload):
        result = normalize_cost_and_usage(ce_service_payload, group_definitions=SERVICE_GROUP)
        by_label = {r.period_label: r for r in result.records}
        assert by_label["2026-10"].estimated
        assert not by_label["2026-05"].estimated

    def test_the_period_end_is_the_exclusive_bound(self, ce_service_payload):
        # AWS reports End as the exclusive bound. The May period runs
        # 2026-05-01 .. 2026-06-01, not .. 2026-05-31.
        result = normalize_cost_and_usage(ce_service_payload, group_definitions=SERVICE_GROUP)
        may = next(r for r in result.records if r.period_label == "2026-05")
        assert may.period_start.isoformat() == "2026-05-01"
        assert may.period_end.isoformat() == "2026-06-01"

    def test_a_complete_month_is_complete(self, ce_service_payload):
        result = normalize_cost_and_usage(ce_service_payload, group_definitions=SERVICE_GROUP)
        assert all(r.is_complete_month for r in result.records)


class TestGroupKeys:
    def test_the_group_is_a_positional_tuple(self, ce_tag_payload):
        result = normalize_cost_and_usage(ce_tag_payload, group_definitions=TAG_GROUP)
        assert result.records[0].group == ("Amazon Simple Storage Service", "Data")

    def test_the_two_dimensions_stay_distinct(self, ce_tag_payload):
        # A GroupBy=[SERVICE] layout and a GroupBy=[SERVICE, TAG] layout
        # are different dimension spaces. Flattening them would make a
        # tag value indistinguishable from a service name.
        result = normalize_cost_and_usage(ce_tag_payload, group_definitions=TAG_GROUP)
        assert all(len(r.group) == 2 for r in result.records)

    def test_a_service_group_has_one_element(self, ce_service_payload):
        result = normalize_cost_and_usage(ce_service_payload, group_definitions=SERVICE_GROUP)
        assert all(len(r.group) == 1 for r in result.records)

    def test_the_service_is_read_from_the_first_key(self, ce_service_payload):
        result = normalize_cost_and_usage(ce_service_payload, group_definitions=SERVICE_GROUP)
        assert all(r.service == "Amazon Simple Storage Service" for r in result.records)

    def test_the_service_is_the_default_when_the_group_is_not_service(self, ce_tag_payload):
        result = normalize_cost_and_usage(
            ce_tag_payload,
            group_definitions=TAG_GROUP,
            default_service="Amazon Simple Storage Service",
        )
        assert all(r.service == "Amazon Simple Storage Service" for r in result.records)

    def test_the_group_is_labelled_from_the_definitions(self):
        label = describe_group(["Amazon Simple Storage Service", "Data"], TAG_GROUP)
        assert "service=Amazon Simple Storage Service" in label
        assert "user:data=Data" in label

    def test_a_group_without_definitions_is_labelled_by_its_keys(self):
        assert describe_group(["S3", "Data"], None) == "S3/Data"


class TestPagination:
    def test_every_page_is_followed(self, ce_pages):
        def fetch(token):
            return ce_pages[0] if token is None else ce_pages[1] if token == "page2token" else ce_pages[2]

        pages = paginate(fetch)
        assert len(pages) == 3

    def test_the_last_page_has_no_token(self, ce_pages):
        def fetch(token):
            return ce_pages[0] if token is None else ce_pages[1] if token == "page2token" else ce_pages[2]

        pages = paginate(fetch)
        assert "NextPageToken" not in pages[-1]

    def test_pagination_stops_when_the_server_stops_issuing_tokens(self, ce_pages):
        calls = []

        def fetch(token):
            calls.append(token)
            # The server hands back a token forever, but the client
            # must stop when the page has no token of its own.
            page = dict(ce_pages[0])
            if len(calls) >= 3:
                page.pop("NextPageToken")
            return page

        pages = paginate(fetch, max_pages=10)
        assert len(pages) == 3
        assert len(calls) == 3

    def test_merging_concatenates_the_periods(self, ce_pages):
        merged = merge_pages(ce_pages)
        assert len(merged["ResultsByTime"]) == 3

    def test_merging_keeps_the_group_definitions(self, ce_pages):
        merged = merge_pages(ce_pages)
        assert merged["GroupDefinitions"] == SERVICE_GROUP

    def test_a_merged_payload_normalizes_to_the_right_row_count(self, ce_pages):
        merged = merge_pages(ce_pages)
        result = normalize_cost_and_usage(merged, group_definitions=SERVICE_GROUP)
        assert len(result.records) == 3

    def test_the_merged_total_is_the_sum_of_the_pages(self, ce_pages):
        merged = merge_pages(ce_pages)
        result = normalize_cost_and_usage(merged, group_definitions=SERVICE_GROUP)
        assert result.total_amount == pytest.approx(60.0)

    def test_pagination_refuses_to_run_forever(self):
        def fetch(token):
            return {"NextPageToken": "always-more", "ResultsByTime": []}

        with pytest.raises(RuntimeError, match="did not terminate"):
            paginate(fetch, max_pages=3)


class TestWithResources:
    def test_the_resource_becomes_the_last_group_element(self, ce_with_resources_payload):
        result = normalize_with_resources(
            ce_with_resources_payload, group_definitions=SERVICE_GROUP
        )
        assert result.records[0].group == ("Amazon Simple Storage Service", "growth-bucket")

    def test_each_month_is_a_separate_record(self, ce_with_resources_payload):
        result = normalize_with_resources(
            ce_with_resources_payload, group_definitions=SERVICE_GROUP
        )
        assert len(result.records) == 2
        assert {r.period_label for r in result.records} == {"2026-09", "2026-10"}

    def test_the_amounts_are_attributed_to_the_resource(self, ce_with_resources_payload):
        result = normalize_with_resources(
            ce_with_resources_payload, group_definitions=SERVICE_GROUP
        )
        by_period = {r.period_label: r.amount for r in result.records}
        assert by_period["2026-09"] == pytest.approx(900.0)
        assert by_period["2026-10"] == pytest.approx(1500.0)


class TestSerialisation:
    def test_records_round_trip(self, ce_service_payload):
        result = normalize_cost_and_usage(ce_service_payload, group_definitions=SERVICE_GROUP)
        restored = records_from_json(records_to_json(result.records, result))
        assert restored == result.records

    def test_the_serialised_payload_is_valid_json(self, ce_service_payload):
        result = normalize_cost_and_usage(ce_service_payload, group_definitions=SERVICE_GROUP)
        data = json.loads(records_to_json(result.records, result))
        assert len(data["records"]) == 6

    def test_the_errors_travel_with_the_snapshot(self, ce_malformed_payload):
        result = normalize_cost_and_usage(ce_malformed_payload, group_definitions=SERVICE_GROUP)
        data = json.loads(records_to_json(result.records, result))
        assert len(data["errors"]) == 2

    def test_the_estimated_periods_travel_with_the_snapshot(self, ce_service_payload):
        result = normalize_cost_and_usage(ce_service_payload, group_definitions=SERVICE_GROUP)
        data = json.loads(records_to_json(result.records, result))
        assert data["estimated_periods"] == ["2026-10"]
