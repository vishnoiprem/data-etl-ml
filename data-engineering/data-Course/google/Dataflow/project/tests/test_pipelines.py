"""
test_pipelines.py — integration tests that run the pipelines on the Direct Runner.

These tests exercise the real Beam transforms, including the ones that are
easy to get subtly wrong: windowing, triggers, late data, and the combiner's
merge behaviour.

The modern `beam.testing.TestPipeline` API is used here. The older
`PTest` style is deprecated and has different semantics.

Usage:
    python3 -m pytest project/tests/test_pipelines.py -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

apache_beam = pytest.importorskip("apache_beam", reason="apache-beam is not installed")

import apache_beam as beam  # noqa: E402
from apache_beam.io.textio import ReadFromText  # noqa: E402
from apache_beam.testing.test_pipeline import TestPipeline  # noqa: E402
from apache_beam.testing.util import assert_that, equal_to  # noqa: E402
from apache_beam.utils.windowed_value import WindowedValue  # noqa: E402
from apache_beam.transforms.window import FixedWindows  # noqa: E402
from apache_beam.transforms.trigger import (  # noqa: E402
    AccumulationMode,
    AfterCount,
    AfterWatermark,
)

from conftest import beam_test_options  # noqa: E402
from transforms import (  # noqa: E402
    RevenueByRegionFn,
    to_summary_row,
)

ORDER_LINES = [
    "o1,c1,2026-01-15T10:00:00+00:00,EMEA,web,EUR,complete,100.00,p1",
    "o2,c2,2026-01-15T11:00:00+00:00,EMEA,web,USD,complete,200.00,p2",
    "o3,c3,2026-01-15T12:00:00+00:00,AMER,web,EUR,complete,50.00,p3",
    "o4,c4,2026-01-15T13:00:00+00:00,AMER,web,EUR,cancelled,999.00,p4",
    "o5,c5,2026-01-15T14:00:00+00:00,EMEA,web,GBP,complete,100.00,p5",
]


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _orders(lines: list[str], pipeline: beam.Pipeline):
    """Build a PCollection of (region, order) pairs from raw CSV lines.

    Args:
        lines: The raw CSV lines.
        pipeline: The pipeline to attach the source to.

    Returns:
        A PCollection of (region, order) pairs.
    """
    from transforms import ParseOrderFn

    return (
        pipeline
        | "Create" >> beam.Create(lines)
        | "Parse" >> beam.ParDo(ParseOrderFn())
        | "KeyByRegion" >> beam.Map(lambda order: (order["region"], order))
    )



def _windowed_values(expected: list[tuple]):
    """Build a matcher that compares the values, not the windows.

    With `use_global_window=False` the elements arrive as `WindowedValue`
    objects. Comparing them directly against plain tuples fails, because
    the window has a start, an end, and a timestamp.

    This matcher unwraps the value and compares only the payload. The
    window boundaries are deliberately not checked: they depend on the
    timestamps in the test data, and what the test is really about is
    *how many* firings happened and *what* each contained.

    Args:
        expected: The expected values, in any order.

    Returns:
        A Beam matcher.
    """

    def _compare(actual):
        unwrapped = [
            item.value if hasattr(item, "value") else item for item in actual
        ]
        return sorted(unwrapped, key=repr) == sorted(expected, key=repr)

    return _compare


# --------------------------------------------------------------------------
# Combiner tests
# --------------------------------------------------------------------------


class TestRevenueCombiner:
    """The `RevenueByRegionFn` combiner."""

    def test_sums_revenue_per_region(self):
        """Revenue is aggregated per region.

        The combiner itself does no filtering — it counts every order it
        is given. Status filtering happens upstream in the pipeline, which
        is what the `test_filtered_statuses` test covers. Here the
        cancelled order is included, so AMER counts 2.
        """
        with TestPipeline(options=beam_test_options()) as pipeline:
            result = (
                _orders(ORDER_LINES, pipeline)
                | "Revenue" >> beam.CombinePerKey(RevenueByRegionFn())
                | "ToRows" >> beam.Map(to_summary_row)
            )
            assert_that(
                result,
                equal_to(
                    [
                        # EMEA = EUR 100 + USD 200 x 0.92 (184) + GBP 100 x 1.17 (117)
                        {"region": "EMEA", "order_count": 3, "revenue_eur": 401.0},
                        # AMER = EUR 50 + cancelled EUR 999
                        {"region": "AMER", "order_count": 2, "revenue_eur": 1049.0},
                    ]
                ),
            )

    def test_merge_is_order_independent(self):
        """The combiner gives the same answer however the inputs are merged.

        This is the property that makes a `CombineFn` scalable: Beam merges
        partial accumulators from different workers in an arbitrary order.

        Two accumulators are built from *disjoint* halves of the input, so
        merging them must equal the total — regardless of the order the
        halves were accumulated in.
        """
        orders = [
            {"amount": 10.0, "currency": "EUR"},
            {"amount": 20.0, "currency": "EUR"},
            {"amount": 30.0, "currency": "EUR"},
        ]
        combiner = RevenueByRegionFn()

        left = combiner.create_accumulator()
        for order in orders[:2]:
            left = combiner.add_input(left, order)

        right = combiner.create_accumulator()
        for order in reversed(orders[2:]):
            right = combiner.add_input(right, order)

        merged = combiner.merge_accumulators([left, right])
        assert combiner.extract_output(merged) == {
            "order_count": 3,
            "revenue_eur": 60.0,
        }

    def test_empty_accumulator(self):
        """A fresh accumulator extracts to zero, not to an error."""
        combiner = RevenueByRegionFn()
        assert combiner.extract_output(combiner.create_accumulator()) == {
            "order_count": 0,
            "revenue_eur": 0.0,
        }


# --------------------------------------------------------------------------
# Windowing tests
# --------------------------------------------------------------------------


class TestWindowing:
    """Fixed windows, triggers, and late data."""

    def test_fixed_window_groups_by_time(self):
        """Events in different windows produce different groups.

        The first two events fall in the 10:00 hour window and the third
        in the 11:00 hour window, so there are two groups: one of size 2
        and one of size 1.
        """
        events = [
            ("2026-01-15T10:05:00+00:00", 10.0),
            ("2026-01-15T10:55:00+00:00", 20.0),
            ("2026-01-15T11:05:00+00:00", 30.0),
        ]

        with TestPipeline(options=beam_test_options()) as pipeline:
            result = (
                pipeline
                | "Create" >> beam.Create(events)
                | "WithTimestamps" >> beam.Map(
                    lambda pair: (
                        beam.window.Timestamp(
                            _to_epoch(pair[0])
                        ),
                        pair[1],
                    )
                )
                | "Window" >> beam.WindowInto(FixedWindows(3600))
                | "KeyByRegion" >> beam.Map(lambda pair: ("all", pair[1]))
                | "Count" >> beam.combiners.Count.PerKey()
            )
            assert_that(
                result,
                _windowed_values([("all", 2), ("all", 1)]),
                use_global_window=False,
            )

    def test_accumulating_mode_emits_running_total(self):
        """ACCUMULATING emits the window total each time it fires."""
        events = [(f"2026-01-15T10:0{i}:00+00:00", 1.0) for i in range(5)]

        with TestPipeline(options=beam_test_options()) as pipeline:
            result = (
                pipeline
                | "Create" >> beam.Create(events)
                | "WithTimestamps" >> beam.Map(
                    lambda pair: (
                        beam.window.Timestamp(_to_epoch(pair[0])),
                        pair[1],
                    )
                )
                | "Window" >> beam.WindowInto(
                    FixedWindows(3600),
                    trigger=AfterCount(2),
                    accumulation_mode=AccumulationMode.ACCUMULATING,
                )
                | "KeyByRegion" >> beam.Map(lambda pair: ("all", pair[1]))
                | "Count" >> beam.combiners.Count.PerKey()
            )
            # With accumulation, the counts are 2, 4, 5 — the running
            # total — rather than the deltas 2, 2, 1.
            assert_that(
                result,
                _windowed_values([("all", 2), ("all", 4), ("all", 5)]),
                use_global_window=False,
            )

    def test_discarding_mode_emits_deltas(self):
        """DISCARDING emits only what arrived since the last firing."""
        events = [(f"2026-01-15T10:0{i}:00+00:00", 1.0) for i in range(5)]

        with TestPipeline(options=beam_test_options()) as pipeline:
            result = (
                pipeline
                | "Create" >> beam.Create(events)
                | "WithTimestamps" >> beam.Map(
                    lambda pair: (
                        beam.window.Timestamp(_to_epoch(pair[0])),
                        pair[1],
                    )
                )
                | "Window" >> beam.WindowInto(
                    FixedWindows(3600),
                    trigger=AfterCount(2),
                    accumulation_mode=AccumulationMode.DISCARDING,
                )
                | "KeyByRegion" >> beam.Map(lambda pair: ("all", pair[1]))
                | "Count" >> beam.combiners.Count.PerKey()
            )
            # With discarding, the counts are the deltas 2, 2, 1.
            assert_that(
                result,
                _windowed_values([("all", 2), ("all", 2), ("all", 1)]),
                use_global_window=False,
            )


# --------------------------------------------------------------------------
# Pipeline-level tests
# --------------------------------------------------------------------------


class TestBatchPipeline:
    """The batch pipeline built by `batch_pipeline.build_pipeline`."""

    def test_end_to_end_revenue_summary(self, tmp_path):
        """The pipeline reads orders and writes the per-region summary."""
        from batch_pipeline import build_pipeline

        input_file = tmp_path / "orders.csv"
        input_file.write_text("\n".join(ORDER_LINES) + "\n", encoding="utf-8")
        output_prefix = tmp_path / "summary"

        with TestPipeline(options=beam_test_options()) as pipeline:
            build_pipeline(
                pipeline,
                input_path=str(input_file),
                output_path=str(output_prefix),
            )

        # The sink writes one sharded file plus the header.
        output_files = sorted(tmp_path.glob("summary*"))
        assert output_files, "the pipeline produced no output file"

        contents = "\n".join(f.read_text(encoding="utf-8") for f in output_files)
        assert "region,order_count,revenue_eur" in contents
        assert "EMEA,3,401.0" in contents
        assert "AMER,1,50.0" in contents

    def test_filtered_statuses(self, tmp_path):
        """Only the requested statuses are counted."""
        from batch_pipeline import build_pipeline

        input_file = tmp_path / "orders.csv"
        input_file.write_text("\n".join(ORDER_LINES) + "\n", encoding="utf-8")
        output_prefix = tmp_path / "summary_active"

        with TestPipeline(options=beam_test_options()) as pipeline:
            build_pipeline(
                pipeline,
                input_path=str(input_file),
                output_path=str(output_prefix),
                statuses=("complete", "cancelled"),
            )

        output_files = sorted(tmp_path.glob("summary_active*"))
        contents = "\n".join(f.read_text(encoding="utf-8") for f in output_files)
        # The cancelled order (999.00) is now included in AMER.
        assert "AMER,2,1049.0" in contents

    def test_side_input_enrichment_does_not_change_the_totals(self, tmp_path):
        """Enriching with a product reference leaves the revenue unchanged.

        The reference table is a side input, so it is broadcast to every
        worker rather than shuffled. The regression this guards against is
        a side input that is *silently* not applied — Beam runs the
        pipeline to completion and writes plausible-looking output either
        way.
        """
        from batch_pipeline import build_pipeline

        input_file = tmp_path / "orders.csv"
        input_file.write_text("\n".join(ORDER_LINES) + "\n", encoding="utf-8")

        reference_file = tmp_path / "reference.ndjson"
        reference_file.write_text(
            "\n".join(
                [
                    json.dumps({"product_id": "p1", "category": "widgets"}),
                    json.dumps({"product_id": "p2", "category": "gadgets"}),
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        output_prefix = tmp_path / "summary_enriched"
        with TestPipeline(options=beam_test_options()) as pipeline:
            build_pipeline(
                pipeline,
                input_path=str(input_file),
                output_path=str(output_prefix),
                reference_path=str(reference_file),
            )

        output_files = sorted(tmp_path.glob("summary_enriched*"))
        contents = "\n".join(f.read_text(encoding="utf-8") for f in output_files)
        # The revenue is identical to the unenriched run.
        assert "EMEA,3,401.0" in contents
        assert "AMER,1,50.0" in contents

    def test_side_input_lookup_miss_is_not_fatal(self):
        """An order with no matching product still counts.

        A missing dimension row must not drop the order — that would
        silently change the revenue totals. The order is counted and
        labelled "unknown".
        """
        from batch_pipeline import _enrich_with_category

        reference = {"p1": {"product_id": "p1", "category": "widgets"}}

        hit = _enrich_with_category({"product_id": "p1"}, reference)
        assert hit["category"] == "widgets"

        miss = _enrich_with_category({"product_id": "missing"}, reference)
        assert miss["category"] == "unknown"


# --------------------------------------------------------------------------
# Streaming pipeline tests
# --------------------------------------------------------------------------

#: Two events in different hours, one region, deliberately **out of
#: chronological order** in the file — the second line's `event_ts` is
#: earlier than the first line's. If the pipeline windows on arrival time
#: rather than event time, both events land in one window; if it windows on
#: event time, they land in two windows.
EVENT_LINES = [
    json.dumps(
        {
            "event_id": "e1",
            "user_id": "u1",
            "event_ts": "2026-01-15T10:30:00+00:00",
            "event_type": "click",
            "product_id": "p1",
            "region": "EMEA",
            "value": 10.0,
        }
    ),
    json.dumps(
        {
            "event_id": "e2",
            "user_id": "u2",
            "event_ts": "2026-01-15T12:30:00+00:00",
            "event_type": "click",
            "product_id": "p2",
            "region": "EMEA",
            "value": 20.0,
        }
    ),
]


class TestStreamingPipeline:
    """The windowed aggregation built by `streaming_pipeline`."""

    def test_events_land_in_separate_event_time_windows(self, tmp_path):
        """Events are windowed by event time, not by arrival time.

        This is the regression test for the most subtle bug the course
        project can have: forgetting to stamp elements with their event-time
        timestamps. The pipeline still produces the right *totals*, so the
        bug is invisible until you look at the per-window output — where
        every event collapses into a single window.
        """
        from streaming_pipeline import build_streaming_pipeline

        input_file = tmp_path / "events.ndjson"
        input_file.write_text("\n".join(EVENT_LINES) + "\n", encoding="utf-8")
        output_prefix = tmp_path / "streaming"

        with TestPipeline(options=beam_test_options()) as pipeline:
            events = pipeline | "Read" >> ReadFromText(str(input_file))
            build_streaming_pipeline(
                pipeline,
                events=events,
                output_path=str(output_prefix),
                window_seconds=3600,
            )

        output_files = sorted(tmp_path.glob("streaming*"))
        assert output_files, "the pipeline produced no output file"

        contents = "\n".join(f.read_text(encoding="utf-8") for f in output_files)
        rows = [
            line
            for line in contents.splitlines()
            if line and not line.startswith("region,")
        ]

        # Two events, two hours apart, two windows — one row per window.
        assert len(rows) == 2, (
            f"expected one row per event-time window, got {len(rows)}: {rows}"
        )
        # Each window holds exactly one event, with that event's own value.
        assert sorted(rows) == ["EMEA,1,10.0", "EMEA,1,20.0"], rows

    def test_malformed_events_are_dropped_not_fatal(self, tmp_path):
        """A malformed payload is dropped instead of failing the pipeline."""
        from streaming_pipeline import build_streaming_pipeline

        input_file = tmp_path / "events.ndjson"
        input_file.write_text(
            "\n".join(["not json at all"] + EVENT_LINES) + "\n", encoding="utf-8"
        )
        output_prefix = tmp_path / "streaming_malformed"

        with TestPipeline(options=beam_test_options()) as pipeline:
            events = pipeline | "Read" >> ReadFromText(str(input_file))
            build_streaming_pipeline(
                pipeline,
                events=events,
                output_path=str(output_prefix),
                window_seconds=3600,
            )

        output_files = sorted(tmp_path.glob("streaming_malformed*"))
        contents = "\n".join(f.read_text(encoding="utf-8") for f in output_files)
        # The two good events are counted; the bad one is gone.
        assert "EMEA,1,10.0" in contents
        assert "EMEA,1,20.0" in contents
        assert "not json" not in contents


def _to_epoch(timestamp: str) -> float:
    """Convert an ISO timestamp to epoch seconds.

    Args:
        timestamp: The ISO-8601 timestamp.

    Returns:
        The epoch seconds as a float.
    """
    from transforms import parse_timestamp

    return float(parse_timestamp(timestamp).timestamp())
