#!/usr/bin/env python3
"""
batch_template.py — a Dataflow flex template for the batch revenue pipeline.

A **flex template** is a Python file that Dataflow executes on the worker.
It is the modern way to deploy a Beam pipeline to Dataflow: you upload the
file once, then launch it with `gcloud dataflow jobs run` and a set of
runtime arguments.

The template deliberately keeps its own arguments separate from Beam's, so
the same file works both as a template and as a local script.

Usage:
    # Build the template image and stage it
    gcloud dataflow flex-template build batch_template.py \
        --project YOUR_PROJECT_ID --region us-central1 \
        --image gcr.io/YOUR_PROJECT_ID/dataflow/batch-template:latest \
        --temp-location gs://YOUR_BUCKET/tmp

    # Run it
    gcloud dataflow jobs run dataflow-batch-template \
        --project YOUR_PROJECT_ID --region us-central1 \
        --image gcr.io/YOUR_PROJECT_ID/dataflow/batch-template:latest \
        --temp-location gs://YOUR_BUCKET/tmp \
        --input gs://YOUR_BUCKET/orders.csv \
        --output gs://YOUR_BUCKET/summary \
        --bigquery-table YOUR_PROJECT_ID.your_dataset.orders_by_region
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import apache_beam as beam  # noqa: E402
from apache_beam.io.textio import ReadFromText, WriteToText  # noqa: E402
from apache_beam.options.pipeline_options import PipelineOptions  # noqa: E402

from transforms import (  # noqa: E402
    ParseOrderFn,
    RevenueByRegionFn,
    format_summary_csv,
    to_summary_row,
)

log = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the template's own arguments.

    Args:
        argv: Argument list. Defaults to `sys.argv[1:]`.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input", required=True, help="Input CSV path")
    parser.add_argument("--output", required=True, help="Output path prefix")
    parser.add_argument(
        "--bigquery-table",
        default=None,
        help="Optional BigQuery table, e.g. project.dataset.table",
    )
    parser.add_argument(
        "--statuses", default="complete", help="Comma-separated statuses to include"
    )
    args, unknown = parser.parse_known_args(argv)
    if unknown:
        log.info("ignoring unrecognised arguments: %s", unknown)
    return args


def build_pipeline(
    pipeline: beam.Pipeline,
    *,
    input_path: str,
    output_path: str,
    bigquery_table: str | None = None,
    statuses: tuple[str, ...] = ("complete",),
) -> None:
    """Build the revenue pipeline for the flex template.

    Args:
        pipeline: The pipeline to add transforms to.
        input_path: The input CSV path.
        output_path: The output path prefix.
        bigquery_table: Optional BigQuery table.
        statuses: Which order statuses count toward revenue.
    """
    orders = (
        pipeline
        | "ReadOrders" >> ReadFromText(input_path)
        | "ParseOrders" >> beam.ParDo(ParseOrderFn())
    )

    completed = orders | "KeepCompletedOrders" >> beam.Filter(
        lambda order: order["status"] in statuses
    )

    summary = (
        completed
        | "KeyByRegion" >> beam.Map(lambda order: (order["region"], order))
        | "RevenueByRegion" >> beam.CombinePerKey(RevenueByRegionFn())
        | "ToFlatRow" >> beam.Map(to_summary_row)
    )

    summary | "FormatCsv" >> beam.Map(format_summary_csv) | "WriteSummary" >> WriteToText(
        output_path,
        header="region,order_count,revenue_eur",
        num_shards=1,
        shard_name_template="",
    )

    if bigquery_table:
        summary | "WriteBigQuery" >> beam.io.WriteToBigQuery(
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

    statuses = tuple(s.strip() for s in args.statuses.split(",") if s.strip())
    options = PipelineOptions(sys.argv[1:])

    with beam.Pipeline(options=options) as pipeline:
        build_pipeline(
            pipeline,
            input_path=args.input,
            output_path=args.output,
            bigquery_table=args.bigquery_table,
            statuses=statuses,
        )

    log.info("template run finished successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
