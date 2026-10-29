"""
test_transforms.py — unit tests for the pure half of `transforms.py`.

These tests deliberately do **not** import Apache Beam. They must pass on a
machine where `apache-beam` has never been installed, which is what makes
them a fast feedback loop while you are learning.

The pure logic covers the rules that actually decide whether a record is
good, a timestamp lands in the right window, and a currency conversion is
correct — the parts most likely to be quietly wrong in production.

Usage:
    python3 -m pytest project/tests/test_transforms.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from transforms import (  # noqa: E402
    CURRENCY_TO_EUR,
    build_revenue_summary,
    dedup_key,
    flatten_csv_header,
    is_valid_order,
    normalise_currency,
    parse_event_payload,
    parse_order_line,
    parse_timestamp,
    try_parse_order_line,
    window_key,
)

VALID_ORDER = {
    "order_id": "o00000001",
    "customer_id": "c000042",
    "order_ts": "2026-01-15T10:30:00+00:00",
    "region": "EMEA",
    "channel": "web",
    "currency": "EUR",
    "status": "complete",
    "amount": 100.0,
    "product_id": "p0042",
}

VALID_ORDER_LINE = (
    "o00000001,c000042,2026-01-15T10:30:00+00:00,EMEA,web,EUR,complete,100.0,p0042"
)


# --------------------------------------------------------------------------
# normalise_currency
# --------------------------------------------------------------------------


class TestNormaliseCurrency:
    """Currency conversion into EUR."""

    def test_euro_is_identity(self):
        """EUR converts to itself."""
        assert normalise_currency(100.0, "EUR") == 100.0

    def test_gbp_conversion(self):
        """GBP converts at the static rate."""
        assert normalise_currency(100.0, "GBP") == 117.0

    def test_usd_conversion(self):
        """USD converts at the static rate."""
        assert normalise_currency(100.0, "USD") == 92.0

    def test_jpy_conversion(self):
        """JPY converts at the static rate, rounded to two decimals."""
        assert normalise_currency(100.0, "JPY") == 0.64

    def test_case_insensitive(self):
        """A lowercase currency code still resolves."""
        assert normalise_currency(100.0, "eur") == 100.0

    def test_unknown_currency_raises(self):
        """An unknown currency is a hard error."""
        with pytest.raises(ValueError, match="unknown currency"):
            normalise_currency(100.0, "XYZ")

    def test_every_rate_converts_to_eur(self):
        """Every configured currency has a usable rate."""
        for currency in CURRENCY_TO_EUR:
            assert normalise_currency(10.0, currency) >= 0


# --------------------------------------------------------------------------
# parse_timestamp
# --------------------------------------------------------------------------


class TestParseTimestamp:
    """ISO-8601 timestamp parsing."""

    def test_parses_offset_timestamp(self):
        """An explicit offset is honoured."""
        parsed = parse_timestamp("2026-01-15T10:30:00+00:00")
        assert parsed.year == 2026
        assert parsed.month == 1
        assert parsed.day == 15
        assert parsed.hour == 10
        assert parsed.minute == 30

    def test_z_suffix_accepted(self):
        """A trailing Z is equivalent to a +00:00 offset."""
        assert parse_timestamp("2026-01-15T10:30:00Z") == parse_timestamp(
            "2026-01-15T10:30:00+00:00"
        )

    def test_naive_timestamp_assumed_utc(self):
        """A timestamp without an offset is interpreted as UTC."""
        parsed = parse_timestamp("2026-01-15T10:30:00")
        assert parsed.tzinfo is not None
        assert parsed.utcoffset().total_seconds() == 0

    def test_offset_converted_to_utc(self):
        """A non-UTC offset is normalised to UTC."""
        parsed = parse_timestamp("2026-01-15T10:30:00+05:00")
        assert parsed.hour == 5
        assert parsed.utcoffset().total_seconds() == 0

    def test_invalid_timestamp_raises(self):
        """Garbage raises a ValueError."""
        with pytest.raises(ValueError, match="invalid timestamp"):
            parse_timestamp("not-a-timestamp")


# --------------------------------------------------------------------------
# is_valid_order
# --------------------------------------------------------------------------


class TestIsValidOrder:
    """Business-rule validation of order rows."""

    def test_valid_order_passes(self):
        """A well-formed order is accepted."""
        assert is_valid_order(VALID_ORDER) is True

    @pytest.mark.parametrize(
        "field,value",
        [
            ("order_id", ""),
            ("customer_id", ""),
            ("region", "UNKNOWN_REGION"),
            ("status", "weird"),
            ("currency", "XYZ"),
            ("order_ts", "not-a-timestamp"),
            ("amount", "not-a-number"),
            ("amount", -5.0),
        ],
    )
    def test_invalid_field_rejected(self, field, value):
        """A bad value in any validated field rejects the row."""
        row = dict(VALID_ORDER)
        row[field] = value
        assert is_valid_order(row) is False


# --------------------------------------------------------------------------
# parse_order_line / try_parse_order_line
# --------------------------------------------------------------------------


class TestParseOrderLine:
    """CSV line parsing."""

    def test_parses_valid_line(self):
        """A well-formed line parses into a dict."""
        row = parse_order_line(VALID_ORDER_LINE)
        assert row["order_id"] == "o00000001"
        assert row["customer_id"] == "c000042"
        assert row["region"] == "EMEA"
        assert row["amount"] == 100.0

    def test_amount_is_float(self):
        """The amount field is coerced to a float."""
        row = parse_order_line(VALID_ORDER_LINE)
        assert isinstance(row["amount"], float)

    def test_trailing_newline_tolerated(self):
        """A trailing newline does not break parsing."""
        assert parse_order_line(VALID_ORDER_LINE + "\n")["order_id"] == "o00000001"

    def test_wrong_field_count_raises(self):
        """A short line is a parse error."""
        with pytest.raises(ValueError, match="malformed order line"):
            parse_order_line("o1,c2,too,few")

    def test_non_numeric_amount_returns_none(self):
        """A non-numeric amount makes the line unparseable."""
        line = VALID_ORDER_LINE.replace("100.0", "not-a-number")
        assert try_parse_order_line(line) is None

    def test_empty_line_returns_none(self):
        """An empty line is skipped, not parsed."""
        assert try_parse_order_line("   ") is None

    def test_malformed_returns_none_not_raises(self):
        """try_parse never raises for bad input."""
        assert try_parse_order_line("garbage") is None


# --------------------------------------------------------------------------
# parse_event_payload
# --------------------------------------------------------------------------


class TestParseEventPayload:
    """Pub/Sub message payload parsing."""

    def test_parses_bytes_payload(self):
        """Bytes payloads are decoded and parsed."""
        payload = (
            b'{"event_id":"e1","user_id":"u1","event_ts":"2026-01-15T10:00:00+00:00",'
            b'"event_type":"click","product_id":"p1","region":"EMEA","value":10.5}'
        )
        event = parse_event_payload(payload)
        assert event["event_id"] == "e1"
        assert event["value"] == 10.5

    def test_parses_str_payload(self):
        """String payloads are parsed directly."""
        payload = (
            '{"event_id":"e1","user_id":"u1","event_ts":"2026-01-15T10:00:00+00:00",'
            '"event_type":"click","product_id":"p1","region":"EMEA","value":10.5}'
        )
        assert parse_event_payload(payload)["event_id"] == "e1"

    def test_invalid_json_raises(self):
        """Invalid JSON is a hard error."""
        with pytest.raises(ValueError, match="not valid JSON"):
            parse_event_payload(b"not json")

    def test_non_object_raises(self):
        """A JSON array is not an event."""
        with pytest.raises(ValueError, match="not a JSON object"):
            parse_event_payload(b"[1, 2, 3]")

    def test_missing_field_raises(self):
        """A payload missing required fields is rejected."""
        with pytest.raises(ValueError, match="missing fields"):
            parse_event_payload(b'{"event_id":"e1"}')

    def test_non_numeric_value_raises(self):
        """A non-numeric value is rejected."""
        payload = (
            '{"event_id":"e1","user_id":"u1","event_ts":"2026-01-15T10:00:00+00:00",'
            '"event_type":"click","product_id":"p1","region":"EMEA","value":"abc"}'
        )
        with pytest.raises(ValueError, match="non-numeric value"):
            parse_event_payload(payload)


# --------------------------------------------------------------------------
# build_revenue_summary
# --------------------------------------------------------------------------


class TestBuildRevenueSummary:
    """Pure twin of the Beam revenue combiner."""

    def test_empty_input(self):
        """No rows produce no regions."""
        assert build_revenue_summary([]) == {}

    def test_sums_per_region(self):
        """Revenue is summed per region, not globally."""
        rows = [
            {**VALID_ORDER, "region": "EMEA", "amount": 100.0},
            {**VALID_ORDER, "region": "EMEA", "amount": 50.0},
            {**VALID_ORDER, "region": "AMER", "amount": 25.0},
        ]
        summary = build_revenue_summary(rows)
        assert summary["EMEA"]["revenue_eur"] == 150.0
        assert summary["EMEA"]["order_count"] == 2
        assert summary["AMER"]["revenue_eur"] == 25.0
        assert summary["AMER"]["order_count"] == 1

    def test_only_complete_status_counted(self):
        """Cancelled and refunded orders are excluded by default."""
        rows = [
            {**VALID_ORDER, "status": "complete", "amount": 100.0},
            {**VALID_ORDER, "status": "cancelled", "amount": 500.0},
            {**VALID_ORDER, "status": "refunded", "amount": 300.0},
        ]
        summary = build_revenue_summary(rows)
        assert summary["EMEA"]["revenue_eur"] == 100.0
        assert summary["EMEA"]["order_count"] == 1

    def test_status_filter_is_configurable(self):
        """The status filter can be widened."""
        rows = [
            {**VALID_ORDER, "status": "active", "amount": 100.0},
            {**VALID_ORDER, "status": "complete", "amount": 50.0},
        ]
        summary = build_revenue_summary(rows, statuses=("active", "complete"))
        assert summary["EMEA"]["revenue_eur"] == 150.0
        assert summary["EMEA"]["order_count"] == 2

    def test_invalid_rows_skipped(self):
        """Invalid rows never reach the aggregation."""
        rows = [VALID_ORDER, {**VALID_ORDER, "region": "BAD"}, {**VALID_ORDER, "amount": "x"}]
        summary = build_revenue_summary(rows)
        assert summary["EMEA"]["order_count"] == 1
        assert "BAD" not in summary

    def test_currency_conversion_applied(self):
        """Amounts in other currencies are converted to EUR."""
        rows = [{**VALID_ORDER, "currency": "GBP", "amount": 100.0}]
        summary = build_revenue_summary(rows)
        assert summary["EMEA"]["revenue_eur"] == 117.0

    def test_result_is_rounded(self):
        """The revenue figure is rounded to two decimals."""
        rows = [{**VALID_ORDER, "currency": "JPY", "amount": 333.0}]
        summary = build_revenue_summary(rows)
        assert summary["EMEA"]["revenue_eur"] == 2.13


# --------------------------------------------------------------------------
# dedup_key and window_key
# --------------------------------------------------------------------------


class TestDedupKey:
    """Deduplication key derivation."""

    def test_uses_event_id(self):
        """The event id is the dedup key."""
        assert dedup_key({"event_id": "e42"}) == "e42"

    def test_falls_back_to_user_id(self):
        """Without an event id, the user id is used."""
        assert dedup_key({"user_id": "u7"}) == "u7"

    def test_is_stable_across_calls(self):
        """The same event always produces the same key."""
        event = {"event_id": "e42", "user_id": "u7"}
        assert dedup_key(event) == dedup_key(event)


class TestWindowKey:
    """Window index derivation."""

    def test_same_window_same_key(self):
        """Two events in the same hour land in the same window."""
        a = window_key({"event_ts": "2026-01-15T10:05:00+00:00"}, 3600)
        b = window_key({"event_ts": "2026-01-15T10:55:00+00:00"}, 3600)
        assert a == b

    def test_different_window_different_key(self):
        """Events in different hours land in different windows."""
        a = window_key({"event_ts": "2026-01-15T10:05:00+00:00"}, 3600)
        b = window_key({"event_ts": "2026-01-15T11:05:00+00:00"}, 3600)
        assert a != b

    def test_window_boundaries_are_exact(self):
        """The window index is an exact division, not a rounded one."""
        first = window_key({"event_ts": "2026-01-15T00:00:00+00:00"}, 3600)
        last = window_key({"event_ts": "2026-01-15T00:59:59+00:00"}, 3600)
        next_window = window_key({"event_ts": "2026-01-15T01:00:00+00:00"}, 3600)
        assert first == last
        assert next_window == first + 1

    def test_invalid_window_width_raises(self):
        """A non-positive window width is an error."""
        with pytest.raises(ValueError, match="must be positive"):
            window_key({"event_ts": "2026-01-15T10:00:00+00:00"}, 0)


# --------------------------------------------------------------------------
# flatten_csv_header
# --------------------------------------------------------------------------


class TestFlattenCsvHeader:
    """Column union for ragged row sets."""

    def test_union_of_keys(self):
        """Every key across rows appears exactly once."""
        rows = [{"a": 1, "b": 2}, {"b": 3, "c": 4}]
        assert list(flatten_csv_header(rows)) == ["a", "b", "c"]

    def test_first_seen_order_preserved(self):
        """Column order follows first appearance."""
        rows = [{"z": 1}, {"a": 2}]
        assert list(flatten_csv_header(rows)) == ["z", "a"]

    def test_empty_rows(self):
        """No rows means no columns."""
        assert list(flatten_csv_header([])) == []
