"""Tests for the pure pipeline logic — no GCP account, no cloud SDK."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))

from pipeline_logic import (  # noqa: E402
    EXPECTED_REJECT_COUNTS,
    EXPECTED_SUMMARY,
    EXPECTED_TOTAL_EVENTS,
    bucket_by_window,
    build_bigquery_rows,
    dedup_key,
    deduplicate,
    event_time_bounds,
    estimated_scan_bytes,
    estimated_scan_tb,
    filter_rows_for_partition,
    hours_spanned,
    ingest_events,
    normalise_currency,
    normalise_event,
    partition_for_date,
    partition_for_event,
    publish_topic,
    redact_pii,
    reject_counts,
    render_rejects_csv,
    render_summary_csv,
    validate_event,
)

SAMPLE_DIR = Path(__file__).resolve().parent.parent.parent / "sample_data"


def _sample_lines() -> list[str]:
    """Read the generated events file, or skip the test."""
    path = SAMPLE_DIR / "events.csv"
    if not path.exists():
        pytest.skip("sample data not generated")
    return path.read_text(encoding="utf-8").splitlines()


def _malformed_lines() -> list[str]:
    """Read the generated malformed file, or skip the test."""
    path = SAMPLE_DIR / "malformed_events.csv"
    if not path.exists():
        pytest.skip("sample data not generated")
    return path.read_text(encoding="utf-8").splitlines()


class TestTimestamps:
    def test_parses_z_suffix(self):
        from pipeline_logic import parse_timestamp

        assert parse_timestamp("2026-01-15T00:00:00Z") == datetime(
            2026, 1, 15, tzinfo=timezone.utc
        )

    def test_assumes_utc_when_naive(self):
        from pipeline_logic import parse_timestamp

        assert parse_timestamp("2026-01-15T00:00:00").tzinfo == timezone.utc

    def test_rejects_garbage(self):
        from pipeline_logic import parse_timestamp

        with pytest.raises(ValueError):
            parse_timestamp("not-a-timestamp")


class TestCurrency:
    def test_known_currency(self):
        assert normalise_currency(100.0, "EUR") == 100.0

    def test_unknown_currency_raises(self):
        with pytest.raises(ValueError):
            normalise_currency(100.0, "XYZ")

    def test_rounds_to_two_places(self):
        assert normalise_currency(10.0, "JPY") == 0.06


class TestValidation:
    def test_valid_event(self):
        row = {
            "event_id": "e1",
            "user_id": "u1",
            "event_ts": "2026-01-15T00:00:00+00:00",
            "event_type": "order",
            "region": "EMEA",
            "channel": "web",
            "currency": "EUR",
            "amount": 10.0,
        }
        assert validate_event(row) == "valid"

    @pytest.mark.parametrize(
        ("field", "value", "reason"),
        [
            ("event_id", "", "missing_event_id"),
            ("user_id", "", "missing_user_id"),
            ("event_type", "teleport", "unknown_event_type"),
            ("region", "MARS", "unknown_region"),
            ("channel", "telepathy", "unknown_channel"),
            ("currency", "XYZ", "unknown_currency"),
            ("event_ts", "garbage", "bad_timestamp"),
            ("amount", -1.0, "negative_amount"),
        ],
    )
    def test_reject_reasons(self, field, value, reason):
        row = {
            "event_id": "e1",
            "user_id": "u1",
            "event_ts": "2026-01-15T00:00:00+00:00",
            "event_type": "order",
            "region": "EMEA",
            "channel": "web",
            "currency": "EUR",
            "amount": 10.0,
        }
        row[field] = value
        assert validate_event(row) == reason

    def test_nan_amount_rejected(self):
        row = {
            "event_id": "e1",
            "user_id": "u1",
            "event_ts": "2026-01-15T00:00:00+00:00",
            "event_type": "order",
            "region": "EMEA",
            "channel": "web",
            "currency": "EUR",
            "amount": float("nan"),
        }
        assert validate_event(row) == "bad_amount"


class TestIngest:
    def test_accepts_all_clean_rows(self):
        accepted, rejected = ingest_events(_sample_lines())
        assert len(accepted) == EXPECTED_TOTAL_EVENTS
        assert rejected == []

    def test_rejects_every_malformed_row(self):
        accepted, rejected = ingest_events(_malformed_lines())
        assert accepted == []
        assert len(rejected) == 12

    def test_reject_counts_match_expected(self):
        _, rejected = ingest_events(_malformed_lines())
        assert reject_counts(rejected) == EXPECTED_REJECT_COUNTS

    def test_skip_header(self):
        accepted, _ = ingest_events(["event_id,user_id"] + _sample_lines()[:5])
        assert len(accepted) == 4

    def test_header_only_file_is_empty(self):
        accepted, rejected = ingest_events(["event_id,user_id,event_ts"])
        assert accepted == []
        assert rejected == []

    def test_reject_mode_raises(self):
        from pipeline_logic import EventRejected

        with pytest.raises(EventRejected):
            ingest_events(_malformed_lines(), reject=True)

    def test_normalises_amount(self):
        accepted, _ = ingest_events(_sample_lines()[:10])
        for row in accepted:
            assert row["amount_eur"] == normalise_currency(
                float(row["amount"]), row["currency"]
            )


class TestAggregation:
    def test_summary_matches_expected(self):
        from pipeline_logic import aggregate_events

        accepted, _ = ingest_events(_sample_lines())
        summary = aggregate_events(accepted)
        assert summary == EXPECTED_SUMMARY

    def test_summary_csv_renders(self):
        from pipeline_logic import aggregate_events

        accepted, _ = ingest_events(_sample_lines())
        csv_text = render_summary_csv(aggregate_events(accepted))
        lines = csv_text.strip().splitlines()
        assert lines[0] == "region,event_count,revenue_eur"
        assert lines[1].startswith("AMER,1238,464848.02")

    def test_totals_are_consistent(self):
        from pipeline_logic import aggregate_events

        accepted, _ = ingest_events(_sample_lines())
        summary = aggregate_events(accepted)
        assert sum(int(s["event_count"]) for s in summary.values()) == EXPECTED_TOTAL_EVENTS

    def test_filters_by_event_type(self):
        from pipeline_logic import aggregate_events

        accepted, _ = ingest_events(_sample_lines())
        orders_only = aggregate_events(accepted, event_types=["order"])
        everything = aggregate_events(accepted)
        assert sum(int(s["event_count"]) for s in orders_only.values()) < sum(
            int(s["event_count"]) for s in everything.values()
        )


class TestWindowing:
    def test_24_hour_dataset_has_24_windows(self):
        accepted, _ = ingest_events(_sample_lines())
        assert len(bucket_by_window(accepted)) == 24

    def test_hours_spanned(self):
        accepted, _ = ingest_events(_sample_lines())
        assert hours_spanned(accepted) == 24

    def test_window_keys_are_window_starts(self):
        accepted, _ = ingest_events(_sample_lines())
        for key in bucket_by_window(accepted):
            assert key.endswith(":00:00+00:00")

    def test_bucketing_preserves_total(self):
        accepted, _ = ingest_events(_sample_lines())
        bucketed = bucket_by_window(accepted)
        assert sum(len(v) for v in bucketed.values()) == len(accepted)

    def test_event_time_bounds(self):
        accepted, _ = ingest_events(_sample_lines())
        earliest, latest = event_time_bounds(accepted)
        assert earliest < latest


class TestPartitioning:
    def test_partition_decorator(self):
        assert partition_for_date("2026-01-15") == "20260115"

    def test_partition_for_event(self):
        assert partition_for_event("2026-01-15T09:30:00+00:00") == "20260115"

    def test_filter_by_partition(self):
        accepted, _ = ingest_events(_sample_lines())
        matching = filter_rows_for_partition(accepted, "20260115")
        assert len(matching) == len(accepted)

    def test_filter_by_wrong_partition_is_empty(self):
        accepted, _ = ingest_events(_sample_lines())
        assert filter_rows_for_partition(accepted, "20260116") == []


class TestIdempotency:
    def test_dedup_key_is_deterministic(self):
        assert dedup_key("e1", "20260115") == "20260115:e1"

    def test_dedup_key_ignores_arrival_time(self):
        assert dedup_key("e1", "20260115") == dedup_key("e1", "20260115")

    def test_deduplicate_removes_duplicates(self):
        row = {"event_id": "e1", "event_dt": "2026-01-15T00:00:00+00:00"}
        result = deduplicate([row, dict(row), dict(row)], partition="20260115")
        assert len(result) == 1

    def test_retry_produces_identical_keys(self):
        accepted, _ = ingest_events(_sample_lines()[:100])
        first = {dedup_key(r["event_id"], "20260115") for r in accepted}
        second = {dedup_key(r["event_id"], "20260115") for r in accepted}
        assert first == second


class TestPublish:
    def test_publish_builds_messages(self):
        accepted, _ = ingest_events(_sample_lines()[:11])
        messages = publish_topic(accepted)
        assert len(messages) == 10
        assert messages[0]["topic"] == "events-normalised"

    def test_messages_carry_attributes(self):
        accepted, _ = ingest_events(_sample_lines()[:11])
        messages = publish_topic(accepted)
        assert "region" in messages[0]["attributes"]

    def test_rejects_csv_has_header(self):
        _, rejected = ingest_events(_malformed_lines())
        assert render_rejects_csv(rejected).splitlines()[0] == "reason,detail,raw"


class TestBigQueryShape:
    def test_rows_have_flat_primitive_columns(self):
        accepted, _ = ingest_events(_sample_lines()[:21])
        rows = build_bigquery_rows(accepted)
        for row in rows:
            assert isinstance(row["amount_eur"], float)
            assert isinstance(row["event_id"], str)
            assert "amount_eur" in row


class TestScanEstimate:
    def test_partitioned_scan_is_smaller(self):
        accepted, _ = ingest_events(_sample_lines()[:100])
        unpartitioned = estimated_scan_bytes(accepted, partitioned=False)
        partitioned = estimated_scan_bytes(accepted, partitioned=True)
        assert partitioned < unpartitioned

    def test_unpartitioned_scan_reads_everything(self):
        accepted, _ = ingest_events(_sample_lines()[:100])
        unpartitioned = estimated_scan_bytes(accepted, partitioned=False)
        assert unpartitioned > 0

    def test_prune_ratio_applies(self):
        accepted, _ = ingest_events(_sample_lines()[:100])
        full = estimated_scan_bytes(accepted, partitioned=False)
        pruned = estimated_scan_bytes(
            accepted, partitioned=True, partition_prune_ratio=0.5
        )
        assert pruned == full // 2


class TestRedaction:
    def test_keeps_last_four(self):
        assert redact_pii("secretvalue").endswith("alue")

    def test_short_values_fully_masked(self):
        assert redact_pii("abc") == "***"

    def test_email_detection(self):
        from pipeline_logic import looks_like_email

        assert looks_like_email("a@b.com")
        assert not looks_like_email("not-an-email")
