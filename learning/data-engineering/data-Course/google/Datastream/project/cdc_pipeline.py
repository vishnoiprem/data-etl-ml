#!/usr/bin/env python3
"""
cdc_pipeline.py — replay a change-event stream into a local table.

This is the course's end-to-end runnable pipeline. It reads change events
from an NDJSON file, applies them with the merge semantics from `cdc.py`,
and writes the resulting table out as CSV and JSON.

It runs with **no GCP account, no credentials and no bill**, because the
interesting part of Datastream — the merge — is pure logic. The part that
needs GCP is the *transport*: reading the source's write-ahead log and
writing change events into BigQuery.

Usage:
    python project/cdc_pipeline.py \\
        --input ./sample_data/changes.ndjson \\
        --output ./out/customers \\
        --merge-keys customer_id

    python project/cdc_pipeline.py \\
        --input ./sample_data/changes.ndjson \\
        --output ./out/customers \\
        --merge-keys customer_id \\
        --verbose
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cdc import CdcState, iter_change_events  # noqa: E402

log = logging.getLogger("cdc_pipeline")

DEFAULT_MERGE_KEYS = ("customer_id",)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        argv: The argument list, or None to read from `sys.argv`.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input", required=True, help="NDJSON file of change events")
    parser.add_argument("--output", required=True, help="Output prefix (without extension)")
    parser.add_argument(
        "--merge-keys",
        default=",".join(DEFAULT_MERGE_KEYS),
        help="Comma-separated merge key columns",
    )
    parser.add_argument(
        "--audit",
        default=None,
        help="Optional path for the change-event audit log",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser.parse_args(argv)


def build_state(
    events: list[dict],
    merge_keys: list[str],
) -> CdcState:
    """Apply a list of change events to a fresh table.

    Args:
        events: The raw change events.
        merge_keys: The merge key columns.

    Returns:
        The resulting table state.
    """
    state = CdcState(merge_keys=merge_keys)
    state.apply_events(events)
    return state


def write_outputs(
    state: CdcState,
    output_prefix: Path,
    columns: list[str],
) -> tuple[Path, Path]:
    """Write the table out as CSV and JSON.

    Args:
        state: The table state.
        output_prefix: The output path, without an extension.
        columns: The column order for the CSV.

    Returns:
        The (csv_path, json_path) that were written.
    """
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    rows = state.snapshot()

    csv_path = output_prefix.with_suffix(".csv")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    json_path = output_prefix.with_suffix(".json")
    json_path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")

    return csv_path, json_path


def collect_columns(events: list[dict]) -> list[str]:
    """Work out the union of columns across all change events.

    The order is deterministic: merge keys first (so the file reads
    naturally), then every other column in first-seen order.

    Args:
        events: The raw change events.

    Returns:
        The column names.
    """
    seen: dict[str, None] = {}
    for event in events:
        data = event.get("data") if isinstance(event.get("data"), dict) else event
        for image_key in ("before", "after"):
            image = data.get(image_key)
            if isinstance(image, dict):
                for column in image:
                    seen.setdefault(column, None)
    return list(seen)


def main(argv: list[str] | None = None) -> int:
    """Run the pipeline.

    Args:
        argv: The argument list, or None to read from `sys.argv`.

    Returns:
        The process exit code.
    """
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    merge_keys = [k.strip() for k in args.merge_keys.split(",") if k.strip()]
    if not merge_keys:
        log.error("no merge keys given")
        return 2

    input_path = Path(args.input)
    if not input_path.exists():
        log.error("input file not found: %s", input_path)
        return 2

    events = list(iter_change_events(str(input_path)))
    log.info("read %d change events from %s", len(events), input_path)

    state = build_state(events, merge_keys)

    columns = merge_keys + [c for c in collect_columns(events) if c not in merge_keys]
    csv_path, json_path = write_outputs(state, Path(args.output), columns)

    print()
    print("CDC replay summary")
    print("-" * 52)
    print(f"  events read          : {len(events)}")
    print(f"  rows in table        : {state.row_count()}")
    print(f"  changes applied      : {state.applied_count}")
    print(f"  events skipped       : {state.skipped_count}")
    if state.skipped_reasons:
        print("  skip reasons:")
        for reason, count in sorted(state.skipped_reasons.items()):
            print(f"    {reason:<26}: {count}")
    print(f"  csv output           : {csv_path}")
    print(f"  json output          : {json_path}")
    print()

    if args.audit:
        audit_path = Path(args.audit)
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit_path.write_text(
            json.dumps(
                {
                    "events_read": len(events),
                    "rows": state.row_count(),
                    "applied": state.applied_count,
                    "skipped": state.skipped_count,
                    "skipped_reasons": state.skipped_reasons,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        log.info("audit log written to %s", audit_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
