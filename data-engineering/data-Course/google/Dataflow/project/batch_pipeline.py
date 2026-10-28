#!/usr/bin/env python3
"""
batch_pipeline.py — a batch ETL pipeline built with Apache Beam.

The pipeline reads order records, validates them, converts currency into EUR,
and aggregates revenue per region. It writes the result to a CSV output path.

The **same code** runs locally on the Direct Runner and on Dataflow. The only
difference between a local run and a cloud run is the path prefix and the
`--runner` flag:

    # Local, no credentials, no bill
    python project/batch_pipeline.py --runner DirectRunner \
        --input ./sample_data/orders.csv --output ./out/summary

    # Cloud
    python project/batch_pipeline.py --runner DataflowRunner \
        --project my-project --region us-central1 \
        --input gs://my-bucket/orders.csv --output gs://my-bucket/summary \
        --staging_location gs://my-bucket/staging \
        --temp_location gs://my-bucket/temp

Usage:
    python project/batch_pipeline.py --help
    python project/batch_pipeline.py --input ./sample_data/orders.csv
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import apache_beam as beam  # noqa: E402
from apache_beam.io.textio import ReadFromText, WriteToText  # noqa: E402
from apache_beam.options.pipeline_options import PipelineOptions  # noqa: E402

from beam_options import (  # noqa: E402
    apply_dataflow_defaults,
    build_options,
    is_local,
    pipeline_options_summary,
    resolve_runner,
)
from transforms import (  # noqa: E402
    ParseOrderFn,
    RevenueByRegionFn,
    format_summary_csv,
    to_summary_row,
    write_summary_to_csv,
)

log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

DEFAULT_INPUT = "./sample_data/orders.csv"
DEFAULT_OUTPUT = "./out/summary"
DEFAULT_TABLE = "orders_by_region"


# --------------------------------------------------------------------------
# Pipeline
# --------------------------------------------------------------------------


def build_pipeline(
    pipeline: beam.Pipeline,
    *,
    input_path: str = DEFAULT_INPUT,
    output_path: str = DEFAULT_OUTPUT,
    bigquery_table: str | None = None,
    statuses: tuple[str, ...] = ("complete",),
    reference_path: str | None = None,
) -> None:
    """Build the batch revenue pipeline.

    The pipeline is assembled as a directed graph of PTransforms:

        ReadFromText
            -> ParseOrderFn (ParDo)
            -> Filter (status in `statuses`)
            -> CombinePerKey(RevenueByRegionFn) keyed by region
            -> Map to a flat row
            -> WriteToText (CSV) and optionally WriteToBigQuery

    Args:
        pipeline: The pipeline to add transforms to.
        input_path: The input CSV path, local or gs://.
        output_path: The output path prefix, local or gs://.
        bigquery_table: Optional fully-qualified BigQuery table
            (`project.dataset.table`). When set, the summary is also written
            to BigQuery.
        statuses: Which order statuses count toward revenue.
        reference_path: Optional path to a product reference file. When set,
            it is loaded as a Beam side input and used to enrich each order
            with its product category.
    """
    lines = pipeline | "ReadOrders" >> ReadFromText(input_path)

    orders = lines | "ParseOrders" >> beam.ParDo(ParseOrderFn())

    if reference_path:
        # `AsDict` builds a `{product_id: row}` lookup on each worker, so
        # the enrichment below is an O(1) dictionary hit per order.
        #
        # `AsIter` would also work, but it hands the function a *list*,
        # and a lookup against that list is a linear scan — O(orders ×
        # products) comparisons across the whole job. With 1,206 products
        # and ~20,000 orders that is roughly 24 million string comparisons
        # for a lookup table that fits in memory in milliseconds.
        reference = (
            pipeline
            | "ReadReference" >> ReadFromText(reference_path)
            | "ParseReference" >> beam.Map(_parse_reference_line)
            | "KeyByProductId" >> beam.Map(
                lambda row: (row["product_id"], row)
            )
        )
        orders = orders | "EnrichWithCategory" >> beam.Map(
            _enrich_with_category, reference=beam.pvalue.AsDict(reference)
        )

    completed = orders | "KeepCompletedOrders" >> beam.Filter(
        lambda order: order["status"] in statuses
    )

    keyed = completed | "KeyByRegion" >> beam.Map(
        lambda order: (order["region"], order)
    )

    summary = keyed | "RevenueByRegion" >> beam.CombinePerKey(RevenueByRegionFn())

    rows = summary | "ToFlatRow" >> beam.Map(to_summary_row)

    rows | "FormatCsv" >> beam.Map(format_summary_csv) | "WriteSummaryCsv" >> WriteToText(
        output_path,
        header="region,order_count,revenue_eur",
        num_shards=1,
        shard_name_template="",
    )

    if bigquery_table:
        # `WRITE_TRUNCATE`, not `WRITE_APPEND`. This sink writes a
        # **full-refresh aggregate** — one row per region summarising the
        # whole input. Appending would leave the previous run's rows in the
        # table and double-count every order on the next run. Truncating
        # makes the write idempotent: re-running the job overwrites the
        # table with the same content rather than adding to it.
        rows | "WriteSummaryBigQuery" >> beam.io.WriteToBigQuery(
            bigquery_table,
            write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
        )


def _parse_reference_line(line: str) -> dict[str, str]:
    """Parse one line of the product reference file.

    The reference file is a tiny JSON-per-line lookup table. It is small
    enough to read as a side input.

    Args:
        line: One JSON object.

    Returns:
        The reference dict.
    """
    import json

    text = line.strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        log.warning("skipping malformed reference line: %.80s", line)
        return {}


def _enrich_with_category(order: dict, reference: dict[str, dict]) -> dict:
    """Attach a product category to an order using a side input.

    The side input is a `{product_id: row}` mapping, so the lookup is an
    O(1) dictionary hit rather than a linear scan over the table.

    A lookup miss is **not** an error. The order still counts; it just
    gets the "unknown" category. Silently dropping unmatched orders
    would change the revenue totals, which is worse than a visible
    "unknown" bucket.

    Args:
        order: The order dict.
        reference: The product reference table, keyed by product id.

    Returns:
        The order dict, with a "category" key added.
    """
    product_id = order.get("product_id")
    row = reference.get(product_id)
    order["category"] = row.get("category", "unknown") if row else "unknown"
    return order


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
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Input CSV path")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output path prefix")
    parser.add_argument(
        "--bigquery-table",
        default=None,
        help="Optional BigQuery table, e.g. my-project.my_dataset.orders_by_region",
    )
    parser.add_argument(
        "--reference",
        default=None,
        help="Optional product reference file used as a side input",
    )
    parser.add_argument(
        "--statuses",
        default="complete",
        help="Comma-separated order statuses to include",
    )
    parser.add_argument("--runner", default=None, help="Beam runner to use")
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


def run(argv: list[str] | None = None) -> int:
    """Build and run the pipeline.

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

    # Beam parses the raw argument list itself, including flags this
    # script's own parser does not know about. Passing the full argv lets
    # `--runner`, `--job_name`, `--streaming` and every other Beam option
    # work without this script re-declaring them.
    raw_argv = list(argv) if argv is not None else sys.argv[1:]
    options = build_options(raw_argv)

    # Explicit command line values win over the options object. Only set an
    # attribute when the options object actually declares it — `PipelineOptions`
    # raises `AttributeError` for unknown names, and the Dataflow-specific
    # options are only present on the `DataflowOptions` subclass.
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
    log.info("input=%s output=%s", args.input, args.output)

    statuses = tuple(s.strip() for s in args.statuses.split(",") if s.strip())

    with beam.Pipeline(options=options) as pipeline:
        build_pipeline(
            pipeline,
            input_path=args.input,
            output_path=args.output,
            bigquery_table=args.bigquery_table,
            statuses=statuses,
            reference_path=args.reference,
        )

    log.info("pipeline finished successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
