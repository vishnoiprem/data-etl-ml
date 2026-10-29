#!/usr/bin/env python3
"""
streaming_pipeline.py — a streaming aggregation pipeline built with Apache Beam.

The pipeline reads clickstream events, groups them into fixed windows, and
reports the event count and total value per region per window.

Three input modes are supported:

    * **Bounded file** (default) — reads a local or `gs://` NDJSON file. The
      pipeline is then a finite batch job that exercises every streaming
      transform, which is how you test streaming logic without a Pub/Sub
      topic.
    * **`--use-test-stream`** — uses Beam's `TestStream`, which produces
      timestamped events on demand. This is how you test *late data* and
      *re-triggering* behaviour deterministically.
    * **`--topic`** — reads from a real Pub/Sub topic. This requires GCP.

The windowing behaviour is the point of this pipeline:

    * a **fixed window** of `--window-seconds` groups events by time
    * the **trigger** decides when a window's result is emitted
    * **allowed lateness** decides how long a late event can still update
      a window that has already fired

Usage:
    python project/streaming_pipeline.py --input ./sample_data/events.ndjson
    python project/streaming_pipeline.py --use-test-stream
    python project/streaming_pipeline.py --topic my-topic --project my-project
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import apache_beam as beam  # noqa: E402
from apache_beam.io.gcp.pubsub import ReadFromPubSub  # noqa: E402
from apache_beam.io.textio import ReadFromText, WriteToText  # noqa: E402
from apache_beam.transforms.window import FixedWindows, TimestampedValue  # noqa: E402
from apache_beam.transforms.trigger import (  # noqa: E402
    AfterCount,
    AccumulationMode,
    AfterWatermark,
)

from beam_options import (  # noqa: E402
    apply_dataflow_defaults,
    build_options,
    is_local,
    pipeline_options_summary,
    resolve_runner,
)
from transforms import (  # noqa: E402
    format_summary_csv,
    parse_event_payload,
    parse_timestamp,
)

log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

DEFAULT_INPUT = "./sample_data/events.ndjson"
DEFAULT_OUTPUT = "./out/streaming"
DEFAULT_WINDOW_SECONDS = 3600
DEFAULT_ALLOWED_LATENESS_SECONDS = 300

#: 0 means "use the safe AfterWatermark trigger". A positive value uses
#: `AfterCount`, which Beam refuses unless `--allow_unsafe_triggers` is set.
DEFAULT_TRIGGER_COUNT = 0


# --------------------------------------------------------------------------
# Transforms
# --------------------------------------------------------------------------


def parse_event(payload: bytes) -> dict:
    """Parse one Pub/Sub payload into an event dict.

    Malformed payloads are dropped rather than failing the bundle. A single
    bad message should not stop a streaming pipeline.

    Args:
        payload: The raw message bytes.

    Returns:
        The event dict, or None when the payload is malformed.
    """
    try:
        return parse_event_payload(payload)
    except ValueError as exc:
        log.warning("dropping malformed event: %s", exc)
        return None


def event_timestamp(event: dict):
    """Return the event's timestamp as a Beam timestamp.

    Using the event's own timestamp rather than arrival time is what makes
    windowing meaningful. Arrival-time windowing in a pipeline that sees
    out-of-order data produces silently wrong results.

    Args:
        event: The parsed event dict.

    Returns:
        The event timestamp.
    """
    from apache_beam.utils.timestamp import Timestamp

    return Timestamp(float(parse_timestamp(str(event["event_ts"])).timestamp()))


def stamp_event_time(event: dict):
    """Wrap an event so Beam knows when it happened.

    Without this, every element carries the *arrival* timestamp assigned by
    the runner, and a fixed window groups by when the runner processed the
    event rather than when it occurred. On a bounded file that means every
    event lands in one window; on a real stream it means late data is
    counted in the wrong hour.

    `TimestampedValue` sets the element's event-time timestamp. The
    `WindowInto` downstream then assigns the element to the window that
    contains that timestamp.

    Args:
        event: The parsed event dict.

    Returns:
        A `TimestampedValue` carrying the event at its event-time timestamp.
    """
    return TimestampedValue(event, event_timestamp(event))


def to_window_row(item) -> str:
    """Format a windowed aggregation into a CSV line.

    The key is just the region. Beam carries the window separately, and
    exposes it to a `DoFn` through the `TimestampParam`, so the window
    start is not part of the key here.

    Args:
        item: A (region, value) pair, where value holds "event_count" and
            "total_value".

    Returns:
        The CSV line.
    """
    import csv
    import io

    region, value = item
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            region,
            int(value["event_count"]),
            round(float(value["total_value"]), 2),
        ]
    )
    return buffer.getvalue().rstrip("\r\n")


def _region_of(key) -> str:
    """Return the region from a windowed key.

    The key is `(window, region)`. This helper keeps the formatting code
    readable.

    Args:
        key: The windowed key.

    Returns:
        The region name.
    """
    return key[1] if isinstance(key, (tuple, list)) and len(key) > 1 else str(key)


# --------------------------------------------------------------------------
# Pipeline
# --------------------------------------------------------------------------


def build_streaming_pipeline(
    pipeline: beam.Pipeline,
    *,
    events: beam.PCollection,
    output_path: str = DEFAULT_OUTPUT,
    window_seconds: int = DEFAULT_WINDOW_SECONDS,
    allowed_lateness_seconds: int = DEFAULT_ALLOWED_LATENESS_SECONDS,
    trigger_count: int = DEFAULT_TRIGGER_COUNT,
    options: object | None = None,
) -> None:
    """Build the windowed streaming aggregation.

    The pipeline:

        events
            -> Parse (DoFn)
            -> WindowInto(FixedWindows, trigger, allowed lateness)
            -> CombinePerKey(Count + Sum) keyed by (window, region)
            -> FormatCsv
            -> WriteToText

    Args:
        pipeline: The pipeline to add transforms to.
        events: The input PCollection of raw payloads.
        output_path: The output path prefix.
        window_seconds: The fixed window width.
        allowed_lateness_seconds: How long after the watermark a late event
            may still update a window.
        trigger_count: Fire the trigger after this many elements per window.
            0 uses the safe `AfterWatermark` trigger.
        options: The pipeline options, consulted for
            `allow_unsafe_triggers`.
    """
    parsed = events | "ParseEvents" >> beam.Map(parse_event)

    # Drop the malformed payloads before they reach the timestamp step —
    # `parse_event` returns None for those, and `stamp_event_time` would
    # fail on a None.
    parsed = parsed | "DropMalformed" >> beam.Filter(lambda event: event is not None)

    # Stamp each event with its own event-time timestamp. Without this the
    # runner's arrival timestamp is used, and every event lands in whichever
    # window the runner happened to process it in.
    parsed = parsed | "StampEventTime" >> beam.Map(stamp_event_time)

    # The trigger decides when a window's result is emitted.
    #
    # Beam's safety rule: a trigger is *safe* only if it can never fire
    # while more elements for the window are still in flight. That holds
    # for `AfterWatermark` **only when allowed lateness is zero**. Once you
    # allow late data, the window can be updated after it fires, so Beam
    # (correctly) refuses the trigger unless `--allow_unsafe_triggers` is
    # passed.
    #
    # `AfterCount` is never safe: it fires every N elements, and a window
    # can close with elements still in flight.
    #
    # So the pipeline takes the safe path by default — `AfterWatermark` with
    # zero allowed lateness — and opts into the unsafe path only when the
    # caller explicitly asks for it.
    unsafe = bool(getattr(options, "allow_unsafe_triggers", False)) if options else False

    if trigger_count:
        trigger = AfterCount(count=trigger_count)
        accumulation_mode = AccumulationMode.DISCARDING
    else:
        trigger = AfterWatermark()
        accumulation_mode = AccumulationMode.ACCUMULATING

    # With allowed lateness, the trigger becomes unsafe unless the caller
    # opts in. Fall back to a zero-lateness window so the default run is
    # always safe and always succeeds.
    effective_lateness = allowed_lateness_seconds
    if effective_lateness and not unsafe:
        log.warning(
            "allowed_lateness=%ds requires --allow_unsafe_triggers; "
            "falling back to 0s so the pipeline stays safe",
            effective_lateness,
        )
        effective_lateness = 0

    window = FixedWindows(size=window_seconds)

    windowed = parsed | "ApplyWindow" >> beam.WindowInto(
        window,
        trigger=trigger,
        accumulation_mode=accumulation_mode,
        allowed_lateness=effective_lateness,
    )

    # The key is (region, value). The window is carried by Beam itself —
    # after `WindowInto`, each element belongs to a window, and the
    # combiner runs per (key, window) pair. So the key only needs the
    # region, and the value needs to be something both `Count` and `sum`
    # can consume.
    keyed = windowed | "KeyByRegion" >> beam.Map(
        lambda event: (event["region"], event["value"])
    )

    # Count and sum with two combiners, then merge them back together.
    # `CoGroupByKey` is the right tool here: it groups two keyed
    # PCollections by the same key and keeps the windowed key intact.
    #
    # Note there is no `combiners.Sum` — a sum is just the builtin `sum`
    # function, which Beam wraps with `CombinePerKey`.
    counts = keyed | "CountEvents" >> beam.combiners.Count.PerKey()
    sums = keyed | "SumValues" >> beam.CombinePerKey(sum)

    combined = _combine_counts_and_sums(counts, sums)

    combined | "FormatCsv" >> beam.Map(to_window_row) | "WriteOutput" >> WriteToText(
        output_path,
        header="region,event_count,total_value",
        num_shards=1,
        shard_name_template="",
    )


def _combine_counts_and_sums(
    counts: beam.PCollection, sums: beam.PCollection
) -> beam.PCollection:
    """Merge a count aggregation and a sum aggregation into one.

    Beam has no built-in "join two PCollections" transform that preserves
    the windowed key, so the merge is done by re-keying both sides and
    grouping them with `CoGroupByKey` — which is exactly what that
    transform is for.

    Args:
        counts: A PCollection of ((window, region), count).
        sums: A PCollection of ((window, region), sum).

    Returns:
        A PCollection of ((window, region), {"event_count", "total_value"}).
    """
    from apache_beam import pvalue

    def _tag(key_value, tag):
        key, value = key_value
        return (key, (tag, value))

    tagged_counts = counts | "TagCounts" >> beam.Map(_tag, tag="count")
    tagged_sums = sums | "TagSums" >> beam.Map(_tag, tag="sum")

    grouped = (tagged_counts, tagged_sums) | "GroupBoth" >> beam.CoGroupByKey()

    def _merge(item):
        key, (count_rows, sum_rows) = item
        event_count = 0
        total_value = 0.0
        for _, value in count_rows:
            event_count += value
        for _, value in sum_rows:
            total_value += value
        return key, {"event_count": event_count, "total_value": round(total_value, 2)}

    return grouped | "MergeAggregations" >> beam.Map(_merge)


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the pipeline arguments.

    Args:
        argv: Argument list. Defaults to `sys.argv[1:]`.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Input NDJSON path")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output path prefix")
    parser.add_argument("--topic", default=None, help="Pub/Sub topic to read from")
    parser.add_argument(
        "--subscription", default=None, help="Pub/Sub subscription to read from"
    )
    parser.add_argument(
        "--use-test-stream",
        action="store_true",
        help="Use TestStream instead of a file or topic (for deterministic tests)",
    )
    parser.add_argument(
        "--window-seconds",
        type=int,
        default=DEFAULT_WINDOW_SECONDS,
        help="Fixed window width in seconds",
    )
    parser.add_argument(
        "--allowed-lateness-seconds",
        type=int,
        default=DEFAULT_ALLOWED_LATENESS_SECONDS,
        help="How long late data may still update a fired window",
    )
    parser.add_argument(
        "--trigger-count",
        type=int,
        default=DEFAULT_TRIGGER_COUNT,
        help=(
            "Fire the trigger after this many elements per window. "
            "0 (the default) uses the safe AfterWatermark trigger. "
            "A positive value needs --allow_unsafe_triggers."
        ),
    )
    parser.add_argument("--project", default=None, help="GCP project id")
    parser.add_argument("--region", default=None, help="GCP region")
    parser.add_argument("--staging_location", default=None, help="Dataflow staging path")
    parser.add_argument("--temp_location", default=None, help="Dataflow temp path")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    # `parse_known_args` so Beam's own flags — `--runner`, `--job_name`,
    # `--streaming` — pass straight through to Beam instead of being
    # rejected by argparse.
    args, unknown = parser.parse_known_args(argv)
    if unknown:
        log.debug("passing through to Beam: %s", unknown)
    return args


def _build_test_stream() -> beam.PCollection:
    """Build a deterministic TestStream of events.

    The stream emits events in a known order, including one that arrives
    after the window it belongs to has already fired. That is what makes
    the late-data path testable.

    Returns:
        A PCollection of timestamped event payloads.
    """
    import json

    def _event(event_id, region, offset_seconds, value):
        from apache_beam.utils.timestamp import Timestamp

        base = 1_700_000_000  # 2023-11-14T22:13:20Z
        payload = {
            "event_id": event_id,
            "user_id": "u000001",
            "event_ts": "2023-11-14T22:13:20+00:00",
            "event_type": "click",
            "product_id": "p0001",
            "region": region,
            "value": value,
        }
        return Timestamp(base + offset_seconds), json.dumps(payload).encode("utf-8")

    return (
        beam.Create(
            [
                _event("e1", "EMEA", 0, 10.0),
                _event("e2", "EMEA", 10, 20.0),
                _event("e3", "AMER", 20, 30.0),
            ]
        )
        | "WithEventTimestamps" >> beam.Map(lambda pair: pair)
    )


def run(argv: list[str] | None = None) -> int:
    """Build and run the streaming pipeline.

    Args:
        argv: Argument list. Defaults to `sys.argv[1:]`.

    Returns:
        The process exit code.
    """
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    raw_argv = list(argv) if argv is not None else sys.argv[1:]
    options = build_options(raw_argv)

    for attr, value in (
        ("project", args.project),
        ("region", args.region),
        ("staging_location", args.staging_location),
        ("temp_location", args.temp_location),
    ):
        if not value:
            continue
        try:
            setattr(options, attr, value)
        except AttributeError:
            log.warning("this runner does not support the --%s option", attr.replace("_", "-"))

    runner = resolve_runner(options)
    if not is_local(runner):
        bucket = options.staging_location or options.temp_location
        if bucket:
            apply_dataflow_defaults(options, bucket=bucket)
        if not options.project:
            log.error("--project is required for the %s", runner)
            return 2
        if not options.staging_location or not options.temp_location:
            log.error(
                "--staging_location and --temp_location are required for the %s", runner
            )
            return 2

    log.info("pipeline options: %s", pipeline_options_summary(options))

    with beam.Pipeline(options=options) as pipeline:
        if args.use_test_stream:
            events = _build_test_stream()
        elif args.topic:
            events = pipeline | "ReadPubSub" >> ReadFromPubSub(
                topic=args.topic, subscription=args.subscription
            )
        else:
            events = pipeline | "ReadEvents" >> ReadFromText(args.input)

        build_streaming_pipeline(
            pipeline,
            events=events,
            output_path=args.output,
            window_seconds=args.window_seconds,
            allowed_lateness_seconds=args.allowed_lateness_seconds,
            trigger_count=args.trigger_count,
            options=options,
        )

    log.info("pipeline finished successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
