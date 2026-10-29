"""
test_pipeline_logic.py — tests for the pure business logic.

These tests need **no Airflow and no GCP account**. They run in well under
a second, which is the whole point of keeping the logic in
``core/pipeline_logic.py`` instead of inside the DAG files.

If you ever find yourself unable to test a rule because the code lives in
a DAG file, that is a design smell, not a tooling problem.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from pipeline_logic import (
    REJECT_BAD_AMOUNT,
    REJECT_BAD_TIMESTAMP,
    REJECT_MISSING_CUSTOMER_ID,
    REJECT_MISSING_ORDER_ID,
    REJECT_NEGATIVE_AMOUNT,
    REJECT_UNKNOWN_CURRENCY,
    REJECT_UNKNOWN_REGION,
    REJECT_UNKNOWN_STATUS,
    REJECT_WRONG_FIELD_COUNT,
    RowRejected,
    build_bigquery_rows,
    classify_row,
    dedup_key,
    filter_rows_for_partition,
    format_timestamp,
    gcs_object_path,
    is_valid_order,
    logical_date_window,
    normalise_currency,
    partition_for_date,
    parse_order_line,
    parse_timestamp,
    render_rejects_csv,
    render_summary_csv,
    reject_counts,
    should_run_full_load,
    summarise_by_region,
    transform_orders,
    try_parse_order_line,
)

VALID_ROW = {
    "order_id": "o1",
    "customer_id": "c1",
    "order_ts": "2026-01-15T10:00:00+00:00",
    "region": "EMEA",
    "channel": "web",
    "currency": "EUR",
    "status": "complete",
    "amount": 100.0,
    "product_id": "p1",
}


# --------------------------------------------------------------------------
# Currency conversion
# --------------------------------------------------------------------------


class TestNormaliseCurrency:
    """Tests for :func:`normalise_currency`."""

    def test_eur_is_identity(self):
        assert normalise_currency(100.0, "EUR") == 100.0

    def test_converts_usd(self):
        assert normalise_currency(100.0, "USD") == 92.0

    def test_is_case_insensitive(self):
        assert normalise_currency(100.0, "usd") == normalise_currency(100.0, "USD")

    def test_rounds_to_two_decimals(self):
        assert normalise_currency(33.333, "GBP") == round(33.333 * 1.17, 2)

    def test_unknown_currency_raises(self):
        with pytest.raises(ValueError, match="unknown currency"):
            normalise_currency(100.0, "XYZ")


# --------------------------------------------------------------------------
# Timestamps
# --------------------------------------------------------------------------


class TestParseTimestamp:
    """Tests for :func:`parse_timestamp`."""

    def test_parses_iso_with_offset(self):
        parsed = parse_timestamp("2026-01-15T10:00:00+00:00")
        assert parsed.year == 2026 and parsed.month == 1 and parsed.day == 15

    def test_parses_z_suffix(self):
        parsed = parse_timestamp("2026-01-15T10:00:00Z")
        assert parsed.tzinfo is not None

    def test_naive_timestamp_assumed_utc(self):
        parsed = parse_timestamp("2026-01-15T10:00:00")
        assert parsed.tzinfo == timezone.utc

    def test_converts_to_utc(self):
        parsed = parse_timestamp("2026-01-15T12:00:00+02:00")
        assert parsed.hour == 10

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="invalid timestamp"):
            parse_timestamp("not-a-timestamp")

    def test_format_round_trips(self):
        original = "2026-01-15T10:00:00+00:00"
        assert format_timestamp(parse_timestamp(original)) == original


# --------------------------------------------------------------------------
# Row classification
# --------------------------------------------------------------------------


class TestClassifyRow:
    """Tests for :func:`classify_row`."""

    def test_valid_row(self):
        assert classify_row(dict(VALID_ROW)) == "valid"

    def test_missing_order_id(self):
        row = {**VALID_ROW, "order_id": ""}
        assert classify_row(row) == REJECT_MISSING_ORDER_ID

    def test_missing_customer_id(self):
        row = {**VALID_ROW, "customer_id": ""}
        assert classify_row(row) == REJECT_MISSING_CUSTOMER_ID

    def test_unknown_region(self):
        row = {**VALID_ROW, "region": "MARS"}
        assert classify_row(row) == REJECT_UNKNOWN_REGION

    def test_unknown_status(self):
        row = {**VALID_ROW, "status": "teleported"}
        assert classify_row(row) == REJECT_UNKNOWN_STATUS

    def test_unknown_currency(self):
        row = {**VALID_ROW, "currency": "XYZ"}
        assert classify_row(row) == REJECT_UNKNOWN_CURRENCY

    def test_bad_timestamp(self):
        row = {**VALID_ROW, "order_ts": "yesterday"}
        assert classify_row(row) == REJECT_BAD_TIMESTAMP

    def test_bad_amount(self):
        row = {**VALID_ROW, "amount": "not-a-number"}
        assert classify_row(row) == REJECT_BAD_AMOUNT

    def test_negative_amount(self):
        row = {**VALID_ROW, "amount": -1.0}
        assert classify_row(row) == REJECT_NEGATIVE_AMOUNT

    def test_nan_amount(self):
        row = {**VALID_ROW, "amount": float("nan")}
        assert classify_row(row) == REJECT_BAD_AMOUNT

    def test_is_valid_order_matches_classify(self):
        assert is_valid_order(dict(VALID_ROW)) is True
        assert is_valid_order({**VALID_ROW, "region": "MARS"}) is False


# --------------------------------------------------------------------------
# Parsing lines
# --------------------------------------------------------------------------


class TestParseOrderLine:
    """Tests for the line-level parsers."""

    def test_parses_a_good_line(self):
        row = parse_order_line(
            "o1,c2,2026-01-15T00:00:00+00:00,EMEA,web,EUR,complete,10.5,p1"
        )
        assert row["order_id"] == "o1"
        assert row["amount"] == 10.5

    def test_malformed_line_returns_none(self):
        assert try_parse_order_line("too,few,fields") is None

    def test_empty_line_returns_none(self):
        assert try_parse_order_line("   ") is None

    def test_parse_raises_on_malformed(self):
        with pytest.raises(ValueError):
            parse_order_line("garbage")


# --------------------------------------------------------------------------
# Transform
# --------------------------------------------------------------------------


class TestTransformOrders:
    """Tests for :func:`transform_orders`."""

    def test_splits_valid_and_rejected(self, order_lines):
        """Every data row ends up in exactly one of the two buckets.

        Note that rows with a non-revenue status (cancelled, active,
        refunded) are *valid* but not revenue-bearing, so they appear in
        neither bucket by default. Pass ``statuses=`` to include them.
        """
        accepted, rejected = transform_orders(order_lines)
        assert accepted
        # The clean orders.csv contains no malformed rows — those live in
        # a separate file precisely so the two cases can be tested apart.
        assert rejected == []

        # Re-running with every status counts every valid row.
        all_accepted, all_rejected = transform_orders(
            order_lines, statuses=("active", "complete", "cancelled", "refunded")
        )
        data_rows = [
            line
            for line in order_lines
            if line.strip() and not line.lower().startswith("order_id,")
        ]
        assert len(all_accepted) + len(all_rejected) == len(data_rows)

    def test_skips_header(self):
        accepted, rejected = transform_orders(
            ["order_id,customer_id,order_ts,region,channel,currency,status,amount,product_id"]
        )
        assert accepted == [] and rejected == []

    def test_blank_lines_are_ignored(self):
        accepted, rejected = transform_orders(["", "   ", "\n"])
        assert accepted == [] and rejected == []

    def test_adds_amount_eur(self):
        line = "o1,c2,2026-01-15T00:00:00+00:00,EMEA,web,USD,complete,100,p1"
        accepted, _ = transform_orders([line])
        assert accepted[0]["amount_eur"] == 92.0

    def test_non_revenue_status_excluded(self):
        line = "o1,c2,2026-01-15T00:00:00+00:00,EMEA,web,EUR,cancelled,100,p1"
        accepted, rejected = transform_orders([line])
        assert accepted == []
        assert rejected == []

    def test_reject_mode_raises(self):
        line = "bad,line"
        with pytest.raises(RowRejected):
            transform_orders([line], reject=True)

    def test_rejected_rows_carry_a_reason(self):
        accepted, rejected = transform_orders(["o1,c2,not-a-date,EMEA,web,EUR,complete,1,p1"])
        assert rejected[0]["reason"] == REJECT_BAD_TIMESTAMP

    def test_wrong_field_count_reason(self):
        _, rejected = transform_orders(["a,b,c,d,e,f,g,h,i,j,k"])
        assert rejected[0]["reason"] == REJECT_WRONG_FIELD_COUNT


# --------------------------------------------------------------------------
# Aggregation and rendering
# --------------------------------------------------------------------------


class TestSummariseByRegion:
    """Tests for :func:`summarise_by_region`."""

    def test_empty_input(self):
        assert summarise_by_region([]) == {}

    def test_groups_by_region(self):
        rows = [
            {"region": "EMEA", "amount_eur": 10.0},
            {"region": "EMEA", "amount_eur": 5.0},
            {"region": "AMER", "amount_eur": 1.0},
        ]
        summary = summarise_by_region(rows)
        assert summary["EMEA"]["order_count"] == 2
        assert summary["EMEA"]["revenue_eur"] == 15.0
        assert summary["AMER"]["order_count"] == 1

    def test_rounds_revenue(self):
        rows = [{"region": "EMEA", "amount_eur": 0.1}, {"region": "EMEA", "amount_eur": 0.2}]
        assert summarise_by_region(rows)["EMEA"]["revenue_eur"] == 0.3


class TestRenderSummaryCsv:
    """Tests for :func:`render_summary_csv`."""

    def test_has_header(self):
        assert render_summary_csv({}).splitlines()[0] == "region,order_count,revenue_eur"

    def test_sorted_by_region(self):
        summary = {
            "LATAM": {"order_count": 1, "revenue_eur": 1.0},
            "AMER": {"order_count": 2, "revenue_eur": 2.0},
        }
        lines = render_summary_csv(summary).splitlines()
        assert lines[1].startswith("AMER")
        assert lines[2].startswith("LATAM")

    def test_two_decimal_places(self):
        summary = {"EMEA": {"order_count": 1, "revenue_eur": 1.5}}
        assert render_summary_csv(summary).splitlines()[1] == "EMEA,1,1.50"


class TestRejectCounts:
    """Tests for :func:`reject_counts`."""

    def test_counts_by_reason(self):
        rejected = [{"reason": "a"}, {"reason": "a"}, {"reason": "b"}]
        assert reject_counts(rejected) == {"a": 2, "b": 1}

    def test_empty(self):
        assert reject_counts([]) == {}

    def test_render_rejects_csv_has_header(self):
        assert render_rejects_csv([]).splitlines()[0] == "reason,detail,raw"


# --------------------------------------------------------------------------
# Data interval semantics
# --------------------------------------------------------------------------


class TestLogicalDateWindow:
    """Tests for :func:`logical_date_window`.

    The half-open interval ``[start, end)`` is the single most important
    convention in a daily Airflow pipeline, and it is where off-by-one
    bugs live.
    """

    def test_single_day_is_half_open(self):
        start, end = logical_date_window("2026-01-15")
        assert start == "2026-01-15"
        assert end == "2026-01-16"

    def test_seven_day_window(self):
        start, end = logical_date_window("2026-01-15", data_interval_days=7)
        assert start == "2026-01-15"
        assert end == "2026-01-22"

    def test_include_end_makes_it_inclusive(self):
        start, end = logical_date_window("2026-01-15", include_end=True)
        assert end == "2026-01-15"

    def test_month_boundary(self):
        start, end = logical_date_window("2026-01-31")
        assert end == "2026-02-01"

    def test_accepts_full_timestamp(self):
        start, end = logical_date_window("2026-01-15T03:00:00+00:00")
        assert start == "2026-01-15" and end == "2026-01-16"

    def test_partition_matches_window_start(self):
        start, _ = logical_date_window("2026-01-15")
        assert partition_for_date("2026-01-15") == start.replace("-", "")


class TestPartitionFiltering:
    """Tests for :func:`filter_rows_for_partition`."""

    def test_keeps_matching_rows(self):
        rows = [
            {"order_dt": "2026-01-15T10:00:00+00:00"},
            {"order_dt": "2026-01-16T10:00:00+00:00"},
        ]
        matched = filter_rows_for_partition(rows, "20260115")
        assert len(matched) == 1
        assert matched[0]["order_dt"].startswith("2026-01-15")

    def test_empty_result(self):
        assert filter_rows_for_partition([{"order_dt": "2026-01-16T00:00:00+00:00"}], "20260115") == []

    def test_rows_without_timestamp_are_dropped(self):
        assert filter_rows_for_partition([{"order_id": "o1"}], "20260115") == []


# --------------------------------------------------------------------------
# Branching
# --------------------------------------------------------------------------


class TestShouldRunFullLoad:
    """Tests for :func:`should_run_full_load`.

    The boundary is the interesting part — this is exactly where a
    branch bug hides.
    """

    def test_below_threshold(self):
        assert should_run_full_load(999, 1000) is False

    def test_at_threshold_is_incremental(self):
        assert should_run_full_load(1000, 1000) is False

    def test_above_threshold_is_full(self):
        assert should_run_full_load(1001, 1000) is True

    def test_zero_threshold(self):
        assert should_run_full_load(1, 0) is True


# --------------------------------------------------------------------------
# Idempotency and paths
# --------------------------------------------------------------------------


class TestDedupKey:
    """Tests for :func:`dedup_key`."""

    def test_is_deterministic(self):
        assert dedup_key("o1", "20260115") == dedup_key("o1", "20260115")

    def test_differs_by_partition(self):
        assert dedup_key("o1", "20260115") != dedup_key("o1", "20260116")

    def test_includes_order_id(self):
        assert "o1" in dedup_key("o1", "20260115")


class TestGcsObjectPath:
    """Tests for :func:`gcs_object_path`."""

    def test_with_prefix(self):
        assert gcs_object_path("b", "orders", "f.csv") == "gs://b/orders/f.csv"

    def test_without_prefix(self):
        assert gcs_object_path("b", "", "f.csv") == "gs://b/f.csv"

    def test_strips_slashes(self):
        assert gcs_object_path("b", "/orders/", "f.csv") == "gs://b/orders/f.csv"


class TestBuildBigQueryRows:
    """Tests for :func:`build_bigquery_rows`."""

    def test_shape(self):
        rows = build_bigquery_rows([{**VALID_ROW, "amount_eur": 100.0}])
        assert len(rows) == 1
        assert rows[0]["amount"] == 100.0
        assert rows[0]["amount_eur"] == 100.0
        assert "load_ts" not in rows[0]


# --------------------------------------------------------------------------
# End-to-end on the real sample dataset
# --------------------------------------------------------------------------


class TestEndToEnd:
    """End-to-end tests against the deterministic sample dataset."""

    def test_expected_summary_matches_documented_values(self, order_lines):
        """The published per-region summary must match exactly.

        The chapters and notebooks print these numbers. If this test
        fails, the published outputs are wrong and must be regenerated.
        """
        accepted, _ = transform_orders(order_lines)
        summary = summarise_by_region(accepted)

        assert summary["AMER"] == {"order_count": 318, "revenue_eur": 113592.19}
        assert summary["APAC"] == {"order_count": 285, "revenue_eur": 108194.92}
        assert summary["EMEA"] == {"order_count": 322, "revenue_eur": 118423.22}
        assert summary["LATAM"] == {"order_count": 320, "revenue_eur": 110646.18}

    def test_total_order_count(self, order_lines):
        accepted, _ = transform_orders(order_lines)
        assert len(accepted) == 1245

    def test_pipeline_is_deterministic(self, order_lines):
        """Running the pipeline twice must produce identical output.

        This is what makes a DAG re-runnable and its result auditable.
        """
        first = render_summary_csv(summarise_by_region(transform_orders(order_lines)[0]))
        second = render_summary_csv(summarise_by_region(transform_orders(order_lines)[0]))
        assert first == second

    def test_accepted_plus_rejected_accounts_for_all_rows(self, order_lines):
        """No row is silently dropped.

        With every status accepted, the accepted and rejected lists must
        account for every data row in the file — this is the property
        that catches a pipeline quietly losing data.
        """
        accepted, rejected = transform_orders(
            order_lines, statuses=("active", "complete", "cancelled", "refunded")
        )
        data_rows = [
            line
            for line in order_lines
            if line.strip() and not line.lower().startswith("order_id,")
        ]
        assert len(accepted) + len(rejected) == len(data_rows)
