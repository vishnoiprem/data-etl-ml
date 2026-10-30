#!/usr/bin/env python3
"""
local_bi.py — the local BI engine.

This is the tool that lets the course *run*. It loads the sample data,
builds the semantic layer, aggregates it the way a Looker explore would,
validates it, and writes the results out — all locally, with no GCP
account, no Looker instance and no bill.

Subcommands:

    ``query``     — aggregate the fact table and print the result
    ``describe``  — print the semantic layer: models, measures,
                    dimensions, joins, grains
    ``explores``  — list the explores and their fan-out risk
    ``validate``  — run the validation gate over the data
    ``lookml``    — render the semantic layer as LookML
    ``spine``     — fill the gaps in the fact table with a date spine

Usage:
    python project/local_bi.py query \
        --input ./sample_data/orders.csv \
        --dimensions region \
        --measures total_revenue,distinct_orders
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Sequence

CORE = Path(__file__).resolve().parent / "core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from date_helpers import (  # noqa: E402
    build_date_spine,
    fill_missing_periods,
    truncate_date,
)
from lookml import render_explore, render_view  # noqa: E402
from model import (  # noqa: E402
    Explore,
    Model,
    aggregate,
    build_customer_model,
    build_explores,
    build_product_model,
    build_sales_model,
)
from validate import validate_dataset  # noqa: E402


def load_rows(path: Path) -> list[dict[str, Any]]:
    """Load rows from a CSV or NDJSON file.

    Args:
        path: The file to read.

    Returns:
        The rows, as dictionaries.

    Raises:
        ValueError: If the file format is not recognised.
    """
    if path.suffix == ".ndjson" or path.suffix == ".jsonl":
        rows: list[dict[str, Any]] = []
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                text = line.strip()
                if text:
                    rows.append(json.loads(text))
        return rows

    if path.suffix == ".csv":
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    raise ValueError(
        f"cannot read {path.suffix!r} files; use .csv or .ndjson"
    )


def all_models() -> dict[str, Model]:
    """Build every model the course defines.

    Returns:
        The models, keyed by name.
    """
    return {
        "orders": build_sales_model(),
        "customers": build_customer_model(),
        "products": build_product_model(),
    }


def _numeric(value: Any) -> Any:
    """Coerce a numeric-looking string to a number.

    CSV files carry every value as a string. The measures need numbers.

    Args:
        value: The value.

    Returns:
        The number, or the original value.
    """
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return float(text) if "." in text else int(text)
        except ValueError:
            return value
    return value


def _coerce_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Coerce the numeric-looking fields in a set of rows.

    Args:
        rows: The rows.

    Returns:
        The coerced rows.
    """
    coerced: list[dict[str, Any]] = []
    for row in rows:
        coerced.append({k: _numeric(v) for k, v in row.items()})
    return coerced


def cmd_query(args: argparse.Namespace) -> int:
    """Run an aggregate query.

    Args:
        args: The parsed arguments.

    Returns:
        The exit code.
    """
    models = all_models()
    model = models.get(args.model)
    if model is None:
        print(
            f"unknown model {args.model!r}; expected one of "
            f"{sorted(models)}",
            file=sys.stderr,
        )
        return 2

    rows = _coerce_rows(load_rows(Path(args.input)))
    dimensions = [d for d in (args.dimensions or "").split(",") if d]
    measures = [m for m in (args.measures or "").split(",") if m]

    if not measures:
        print("an aggregate query needs at least one measure", file=sys.stderr)
        return 2

    try:
        result = aggregate(model, rows, dimensions, measures)
    except KeyError as exc:
        print(f"unknown field: {exc}", file=sys.stderr)
        return 2

    if args.format == "csv":
        text = result.to_csv()
    elif args.format == "json":
        text = json.dumps(result.to_dicts(), indent=2, default=str)
    else:
        widths = {}
        for column in result.columns:
            widths[column] = max(
                len(column),
                max(
                    (len(str(row.to_dict().get(column, ""))) for row in result.rows),
                    default=0,
                ),
            )
        lines = [
            "  ".join(column.ljust(widths[column]) for column in result.columns),
            "  ".join("-" * widths[column] for column in result.columns),
        ]
        for row in result.rows:
            values = row.to_dict()
            lines.append(
                "  ".join(
                    str(values.get(column, "")).ljust(widths[column])
                    for column in result.columns
                )
            )
        text = "\n".join(lines)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
        print(f"Wrote {out_path}")
    else:
        print(text)

    return 0


def cmd_describe(args: argparse.Namespace) -> int:
    """Print the semantic layer.

    Args:
        args: The parsed arguments.

    Returns:
        The exit code.
    """
    models = all_models()

    for model in models.values():
        print(f"Model: {model.name}")
        print(f"  label        : {model.label}")
        print(f"  table        : {model.table}")
        print(f"  grain        : {model.grain}")
        print(f"  primary key  : {model.primary_key}")
        print(f"  description  : {model.description}")
        print()
        print("  Measures:")
        for measure in model.measures:
            additive = "additive" if measure.is_additive else "non-additive"
            print(
                f"    {measure.name:24} {measure.aggregation:14} "
                f"{additive:14} {measure.description}"
            )
        print()
        print("  Dimensions:")
        for dimension in model.dimensions:
            timeframe = (
                f" [{', '.join(dimension.timeframe)}]"
                if dimension.timeframe
                else ""
            )
            print(
                f"    {dimension.name:24} {dimension.type:10}{timeframe}"
            )
        print()
        if model.joins:
            print("  Joins:")
            for join in model.joins:
                risk = "FAN-OUT" if join.causes_fan_out else "safe"
                print(
                    f"    {join.name:24} {join.type:14} {risk:8} "
                    f"{join.foreign_key} -> {join.to_model}.{join.primary_key}"
                )
            print()
    return 0


def cmd_explores(args: argparse.Namespace) -> int:
    """List the explores and their fan-out risk.

    Args:
        args: The parsed arguments.

    Returns:
        The exit code.
    """
    explores: list[Explore] = build_explores()
    print("Explores")
    print("----------------------------------------------------")
    for explore in explores:
        print(f"  {explore.name}")
        print(f"    base model : {explore.base_model}")
        print(f"    description: {explore.description}")
        for join in explore.joins:
            risk = (
                "FAN-OUT — measures on the far side will inflate"
                if join.causes_fan_out
                else "safe to traverse"
            )
            print(f"    join {join.name:16} {join.type:14} {risk}")
        if explore.fan_out_joins:
            print(
                "    warning: traversing a fan-out join multiplies the "
                "rows."
            )
        print()
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Run the validation gate.

    Args:
        args: The parsed arguments.

    Returns:
        1 when the validation fails, 0 otherwise.
    """
    models = all_models()
    model = models[args.model]
    rows = _coerce_rows(load_rows(Path(args.input)))

    required = [r for r in (args.required or "").split(",") if r]
    if not required:
        required = ["order_id", "customer_id", "created_at"]

    report = validate_dataset(
        rows,
        model,
        required=required,
        max_age_days=args.max_age_days,
        source=str(args.input),
    )
    print(report.to_text())

    if args.json:
        print()
        print(json.dumps(report.to_dict(), indent=2, default=str))

    return 0 if report.passed else 1


def cmd_lookml(args: argparse.Namespace) -> int:
    """Render the semantic layer as LookML.

    Args:
        args: The parsed arguments.

    Returns:
        The exit code.
    """
    models = all_models()
    chunks: list[str] = []
    for model in models.values():
        chunks.append(render_view(model))
        chunks.append("")

    if args.with_explores:
        chunks.append("")
        for explore in build_explores():
            chunks.append(render_explore(explore))
            chunks.append("")

    text = "\n".join(chunks).rstrip() + "\n"

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        print(f"Wrote {out_path}")
    else:
        print(text, end="")
    return 0


def cmd_spine(args: argparse.Namespace) -> int:
    """Fill the gaps in the fact table with a date spine.

    Args:
        args: The parsed arguments.

    Returns:
        The exit code.
    """
    rows = _coerce_rows(load_rows(Path(args.input)))
    filled = fill_missing_periods(
        rows,
        date_field=args.date_field,
        timeframe=args.timeframe,
    )

    empty = [bucket for bucket in filled if not bucket["rows"]]
    print("Date spine")
    print("----------------------------------------------------")
    print(f"  source            : {args.input}")
    print(f"  timeframe         : {args.timeframe}")
    print(f"  buckets           : {len(filled)}")
    print(f"  buckets with data : {len(filled) - len(empty)}")
    print(f"  empty buckets     : {len(empty)}")
    if empty:
        print()
        print("  The empty buckets — these are the gaps a raw chart shows:")
        for bucket in empty[: args.limit]:
            print(f"    {bucket['date'].isoformat()}")
        if len(empty) > args.limit:
            print(f"    ... and {len(empty) - args.limit} more")

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["date", "order_lines", "revenue"])
            for bucket in filled:
                revenue = sum(
                    float(row.get("total_amount") or 0)
                    for row in bucket["rows"]
                )
                writer.writerow(
                    [
                        bucket["date"].isoformat(),
                        len(bucket["rows"]),
                        round(revenue, 2),
                    ]
                )
        print()
        print(f"Wrote {out_path}")

    return 0


def cmd_spine_range(args: argparse.Namespace) -> int:
    """Print a date spine for an explicit range.

    Args:
        args: The parsed arguments.

    Returns:
        The exit code.
    """
    spine = build_date_spine(args.start, args.end)
    for row in spine:
        print(
            f"{row.date.isoformat()}  {row.year_month}  "
            f"{row.year_quarter}  week {row.week:02d}"
        )
    print()
    print(f"{len(spine)} days")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser.

    Returns:
        The parser.
    """
    parser = argparse.ArgumentParser(
        prog="local_bi.py",
        description=(
            "The local BI engine — the course's semantic layer, "
            "aggregation engine and validation gate, running offline."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    query = sub.add_parser("query", help="Aggregate the fact table")
    query.add_argument("--input", required=True, help="The data file")
    query.add_argument(
        "--model", default="orders", help="The model to query (default: orders)"
    )
    query.add_argument(
        "--dimensions", default="", help="Comma-separated dimension names"
    )
    query.add_argument(
        "--measures", default="", help="Comma-separated measure names"
    )
    query.add_argument(
        "--format",
        choices=("table", "csv", "json"),
        default="table",
        help="The output format (default: table)",
    )
    query.add_argument("--output", default="", help="Write to this file")
    query.set_defaults(func=cmd_query)

    describe = sub.add_parser(
        "describe", help="Print the semantic layer"
    )
    describe.set_defaults(func=cmd_describe)

    explores = sub.add_parser(
        "explores", help="List the explores and their fan-out risk"
    )
    explores.set_defaults(func=cmd_explores)

    validate = sub.add_parser(
        "validate", help="Run the validation gate over the data"
    )
    validate.add_argument("--input", required=True, help="The data file")
    validate.add_argument(
        "--model", default="orders", help="The model to validate"
    )
    validate.add_argument(
        "--required", default="", help="Comma-separated required fields"
    )
    validate.add_argument(
        "--max-age-days",
        type=int,
        default=2,
        help="The freshness limit in days (default: 2)",
    )
    validate.add_argument(
        "--json", action="store_true", help="Also print the report as JSON"
    )
    validate.set_defaults(func=cmd_validate)

    lookml = sub.add_parser("lookml", help="Render the semantic layer as LookML")
    lookml.add_argument("--output", default="", help="Write to this file")
    lookml.add_argument(
        "--with-explores",
        action="store_true",
        help="Include the explore blocks",
    )
    lookml.set_defaults(func=cmd_lookml)

    spine = sub.add_parser(
        "spine", help="Fill the gaps in the fact table with a date spine"
    )
    spine.add_argument("--input", required=True, help="The data file")
    spine.add_argument(
        "--date-field", default="created_at", help="The date field"
    )
    spine.add_argument(
        "--timeframe",
        default="day",
        help="The grain: day, week, month, quarter or year",
    )
    spine.add_argument("--output", default="", help="Write to this CSV file")
    spine.add_argument(
        "--limit", type=int, default=10, help="How many empty buckets to list"
    )
    spine.set_defaults(func=cmd_spine)

    spine_range = sub.add_parser(
        "spine-range", help="Print a date spine for an explicit range"
    )
    spine_range.add_argument("--start", required=True, help="The first date")
    spine_range.add_argument("--end", required=True, help="The last date")
    spine_range.set_defaults(func=cmd_spine_range)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI.

    Args:
        argv: The arguments. Defaults to ``sys.argv[1:]``.

    Returns:
        The exit code.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
