#!/usr/bin/env python3
"""
sample_data.py — generate the sample dataset the GCP course exercises use.

Creates deterministic CSV and NDJSON files. The generator is seeded, so
every run produces byte-identical output. That matters for a course: the
expected outputs printed in the chapters and notebooks stay correct no
matter when you run them.

The dataset is a day of clickstream-style events spread across 24 hours
and four regions, plus a set of deliberately malformed rows that
exercise the dead-letter path.

Usage:
    python resources/sample_data.py --output-dir ./sample_data
    python resources/sample_data.py --output-dir ./sample_data --events 50000
    python resources/sample_data.py --output-dir ./sample_data --malformed 12
    python resources/sample_data.py --output-dir ./sample_data --hot-key-rate 0.25
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

REGIONS = ["EMEA", "AMER", "APAC", "LATAM"]
CHANNELS = ["web", "mobile", "store"]
CURRENCIES = ["EUR", "USD", "GBP", "JPY"]
EVENT_TYPES = ["order", "refund", "page_view", "signup"]
SEED = 42

EVENT_FIELDS = [
    "event_id",
    "user_id",
    "event_ts",
    "event_type",
    "region",
    "channel",
    "currency",
    "amount",
]

#: The number of events in the default dataset.
DEFAULT_EVENTS = 4800

#: The calendar day the events are spread across.
DEFAULT_DATE = "2026-01-15"

#: The hour the day starts at, in UTC.
START_HOUR = 0


# --------------------------------------------------------------------------
# Generators
# --------------------------------------------------------------------------


def generate_events(
    n: int,
    target_date: date,
    *,
    hot_key_rate: float = 0.0,
    rng: random.Random | None = None,
) -> list[dict]:
    """Generate a deterministic set of events.

    Args:
        n: Number of events to generate.
        target_date: The calendar day the events are spread across.
        hot_key_rate: Fraction of events assigned to a single "hot" user
            key. Used to demonstrate downstream skew. 0.0 means an even
            spread.
        rng: Optional random generator, for reproducible skewed samples.

    Returns:
        A list of event dicts with the keys in EVENT_FIELDS.
    """
    rng = rng or random.Random(SEED)
    rows: list[dict] = []
    base_ts = datetime(
        target_date.year,
        target_date.month,
        target_date.day,
        START_HOUR,
        tzinfo=timezone.utc,
    )

    for i in range(n):
        event_id = f"e{i:08d}"
        if hot_key_rate > 0 and rng.random() < hot_key_rate:
            user_id = "u000001"  # the hot key
        else:
            user_id = f"u{rng.randint(2, 5000):06d}"
        offset = timedelta(seconds=rng.randint(0, 86_399))
        event_ts = base_ts + offset
        event_type = rng.choice(EVENT_TYPES)
        currency = rng.choice(CURRENCIES)
        rows.append(
            {
                "event_id": event_id,
                "user_id": user_id,
                "event_ts": event_ts.isoformat(),
                "event_type": event_type,
                "region": rng.choice(REGIONS),
                "channel": rng.choice(CHANNELS),
                "currency": currency,
                "amount": round(rng.uniform(5.0, 950.0), 2),
            }
        )
    return rows


def generate_malformed_rows(count: int = 12) -> list[str]:
    """Generate rows that deliberately fail validation.

    These are what the dead-letter path needs: a pipeline that rejects
    bad input must have bad input to reject.

    The base list contains **one row per reject reason code** the
    project defines, so every reason appears exactly once and the
    reject counts are assertable.

    Args:
        count: How many rows to return. Counts above the base length
            repeat the base rows; counts below it take a prefix.

    Returns:
        Malformed CSV lines.
    """
    base = [
        # wrong_field_count
        "not-an-event,missing-fields,garbage",
        # bad_amount
        "e99999999,u000001,not-a-timestamp,order,EMEA,web,EUR,not-a-number",
        # unknown_region
        "e99999998,u000002,2026-01-15T00:00:00+00:00,order,UNKNOWN_REGION,web,EUR,100.00",
        # unknown_channel
        "e99999997,u000003,2026-01-15T00:00:00+00:00,order,EMEA,telepathy,EUR,100.00",
        # unknown_currency
        "e99999996,u000004,2026-01-15T00:00:00+00:00,order,EMEA,web,XYZ,100.00",
        # unknown_event_type
        "e99999995,u000005,2026-01-15T00:00:00+00:00,teleport,EMEA,web,EUR,100.00",
        # missing_event_id
        ",u000006,2026-01-15T00:00:00+00:00,order,EMEA,web,EUR,100.00",
        # missing_user_id
        "e99999994,,2026-01-15T00:00:00+00:00,order,EMEA,web,EUR,100.00",
        # negative_amount
        "e99999993,u000007,2026-01-15T00:00:00+00:00,order,EMEA,web,EUR,-50.00",
        # bad_timestamp (well-formed otherwise)
        "e99999992,u000008,15-01-2026 10:00,order,EMEA,web,EUR,100.00",
        # unknown_region (a second one, to show a repeated reason)
        "e99999991,u000009,2026-01-15T00:00:00+00:00,signup,MARS,web,EUR,100.00",
        # bad_amount (a second one)
        "e99999990,u000010,2026-01-15T00:00:00+00:00,order,EMEA,web,NaN",
    ]
    if count <= len(base):
        return base[:count]
    extra = []
    for i in range(count - len(base)):
        extra.append(base[i % len(base)])
    return base + extra


def generate_reference_data() -> dict[str, dict]:
    """Generate the small reference table used as a lookup.

    In a deployed pipeline this arrives as a BigQuery table and is
    joined in; the local pipeline loads the same data from JSON.
    """
    return {
        f"r{i:03d}": {
            "region_code": f"r{i:03d}",
            "country": f"Country-{i:02d}",
            "tier": "gold" if i % 3 == 0 else "standard",
        }
        for i in range(50)
    }


# --------------------------------------------------------------------------
# Writers
# --------------------------------------------------------------------------


def write_csv(rows: list[dict], path: Path, fields: list[str]) -> None:
    """Write rows to a CSV file with a header row.

    Args:
        rows: The rows to write.
        path: The destination path.
        fields: The column order.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    log.info("wrote %s (%d rows)", path, len(rows))


def write_ndjson(rows: list[dict], path: Path) -> None:
    """Write rows as newline-delimited JSON.

    Args:
        rows: The rows to write.
        path: The destination path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    log.info("wrote %s (%d rows)", path, len(rows))


def write_text_lines(lines: list[str], path: Path) -> None:
    """Write plain lines to a text file, one per line.

    Args:
        lines: The lines to write.
        path: The destination path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log.info("wrote %s (%d lines)", path, len(lines))


def upload_to_gcs(local_dir: Path, gcs_uri: str) -> None:
    """Upload the generated files to a Cloud Storage bucket.

    Requires google-cloud-storage and valid application-default
    credentials.

    Args:
        local_dir: The local directory to upload.
        gcs_uri: The ``gs://`` destination.
    """
    try:
        from google.cloud import storage
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "google-cloud-storage is not installed. "
            "Install it with: pip install google-cloud-storage"
        ) from exc

    client = storage.Client()
    bucket_name = gcs_uri.removeprefix("gs://").split("/")[0]
    bucket = client.bucket(bucket_name)
    prefix = gcs_uri.removeprefix("gs://").split("/", 1)[1] if "/" in gcs_uri else ""

    for local_file in sorted(local_dir.rglob("*")):
        if not local_file.is_file():
            continue
        relative = local_file.relative_to(local_dir).as_posix()
        blob_name = f"{prefix.rstrip('/')}/{relative}".lstrip("/")
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(str(local_file))
        log.info("uploaded %s -> gs://%s/%s", local_file, bucket_name, blob_name)


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        argv: The argument list, or None for ``sys.argv``.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output-dir", default="./sample_data", help="Local output directory")
    parser.add_argument(
        "--events", type=int, default=DEFAULT_EVENTS, help="Number of events"
    )
    parser.add_argument(
        "--date", default=DEFAULT_DATE, help="Target date (YYYY-MM-DD) for the events"
    )
    parser.add_argument(
        "--hot-key-rate",
        type=float,
        default=0.0,
        help="Fraction of events sent to one hot user key (0.0-1.0)",
    )
    parser.add_argument(
        "--malformed", type=int, default=12, help="Number of malformed rows to include"
    )
    parser.add_argument("--upload", default=None, help="Optional gs:// destination")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Generate the sample dataset.

    Args:
        argv: The argument list, or None for ``sys.argv``.

    Returns:
        The process exit code.
    """
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(SEED)
    events = generate_events(
        args.events, target_date, hot_key_rate=args.hot_key_rate, rng=rng
    )

    write_csv(events, output_dir / "events.csv", EVENT_FIELDS)
    write_ndjson(events, output_dir / "events.ndjson")
    write_text_lines(
        generate_malformed_rows(args.malformed), output_dir / "malformed_events.csv"
    )
    write_ndjson(
        list(generate_reference_data().values()), output_dir / "region_reference.ndjson"
    )

    summary = {
        "events": len(events),
        "malformed_rows": len(generate_malformed_rows(args.malformed)),
        "reference_rows": len(generate_reference_data()),
        "target_date": args.date,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    log.info("sample data ready in %s", output_dir.resolve())
    log.info("summary: %s", summary)

    if args.upload:
        upload_to_gcs(output_dir, args.upload)
        log.info("uploaded to %s", args.upload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
