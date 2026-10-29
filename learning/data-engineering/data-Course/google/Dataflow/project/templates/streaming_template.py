#!/usr/bin/env python3
"""
streaming_template.py — a Dataflow flex template for the streaming pipeline.

This template reads from a Pub/Sub topic, groups events into fixed windows,
and writes the per-region, per-window totals to Cloud Storage and optionally
to BigQuery.

A streaming flex template differs from a batch one in two ways:

    * it must set `--streaming` when the job is launched
    * the sink must tolerate repeated updates, because a window can be
      written more than once when late data arrives

Usage:
    gcloud dataflow flex-template build streaming_template.py \
        --project YOUR_PROJECT_ID --region us-central1 \
        --image gcr.io/YOUR_PROJECT_ID/dataflow/streaming-template:latest \
        --temp-location gs://YOUR_BUCKET/tmp

    gcloud dataflow jobs run dataflow-streaming-template \
        --project YOUR_PROJECT_ID --region us-central1 \
        --streaming \
        --image gcr.io/YOUR_PROJECT_ID/dataflow/streaming-template:latest \
        --temp-location gs://YOUR_BUCKET/tmp \
        --topic YOUR_PROJECT_ID.your_topic \
        --output gs://YOUR_BUCKET/streaming \
        --window-seconds 3600
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import apache_beam as beam  # noqa: E402
from apache_beam.io.gcp.pubsub import ReadFromPubSub  # noqa: E402
from apache_beam.io.textio import WriteToText  # noqa: E402
from apache_beam.options.pipeline_options import PipelineOptions  # noqa: E402
from apache_beam.transforms.window import FixedWindows  # noqa: E402
from apache_beam.transforms.trigger import (  # noqa: E402
    AccumulationMode,
    AfterWatermark,
)

from transforms import format_summary_csv, parse_event_payload  # noqa: E402

log = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the template's own arguments.

    Args:
        argv: Argument list. Defaults to `sys.argv[1:]`.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--topic", required=True, help="Pub/Sub topic to read from")
    parser.add_argument("--subscription", default=None, help="Optional subscription")
    parser.add_argument("--output", required=True, help="Output path prefix")
    parser.add_argument(
        "--bigquery-table",
        default=None,
        help="Optional BigQuery table, e.g. project.dataset.table",
    )
    parser.add_argument(
        "--window-seconds", type=int, default=3600, help="Fixed window width"
    )
    args, unknown = parser.parse_known_args(argv)
    if unknown:
        log.info("ignoring unrecognised arguments: %s", unknown)
    return args


def parse_event(payload: bytes) -> dict | None:
    """Parse one Pub/Sub payload into an event dict.

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


def build_pipeline(
    pipeline: beam.Pipeline,
    *,
    topic: str,
    subscription: str | None = None,
    output_path: str,
    bigquery_table: str | None = None,
    window_seconds: int = 3600,
) -> None:
    """Build the streaming windowed aggregation.

    Args:
        pipeline: The pipeline to add transforms to.
        topic: The Pub/Sub topic to read from.
        subscription: Optional subscription to read from.
        output_path: The output path prefix.
        bigquery_table: Optional BigQuery table.
        window_seconds: The fixed window width.
    """
    events = pipeline | "ReadPubSub" >> ReadFromPubSub(
        topic=topic, subscription=subscription
    )

    parsed = events | "ParseEvents" >> beam.Map(parse_event)

    windowed = parsed | "ApplyWindow" >> beam.WindowInto(
        FixedWindows(size=window_seconds),
        trigger=AfterWatermark(),
        accumulation_mode=AccumulationMode.ACCUMULATING,
    )

    counts = (
        windowed
        | "KeyByRegion" >> beam.Map(lambda event: (event["region"], 1))
        | "CountEvents" >> beam.combiners.Count.PerKey()
    )

    rows = counts | "FormatCsv" >> beam.Map(
        lambda item: format_summary_csv(
            {"region": item[0], "order_count": item[1], "revenue_eur": 0.0}
        )
    )

    rows | "WriteOutput" >> WriteToText(
        output_path,
        header="region,order_count,revenue_eur",
        num_shards=1,
        shard_name_template="",
    )

    if bigquery_table:
        rows | "WriteBigQuery" >> beam.io.WriteToBigQuery(
            bigquery_table,
            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
        )


def run(argv: list[str] | None = None) -> int:
    """Run the template.

    Args:
        argv: Argument list. Defaults to `sys.argv[1:]`.

    Returns:
        The process exit code.
    """
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    options = PipelineOptions(sys.argv[1:])

    with beam.Pipeline(options=options) as pipeline:
        build_pipeline(
            pipeline,
            topic=args.topic,
            subscription=args.subscription,
            output_path=args.output,
            bigquery_table=args.bigquery_table,
            window_seconds=args.window_seconds,
        )

    log.info("template run finished successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
