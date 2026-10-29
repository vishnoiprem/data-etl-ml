#!/usr/bin/env python3
"""
sample_data.py — generate the sample data the Dataflow course exercises use.

Creates deterministic CSV, NDJSON, and Parquet files, then (optionally)
uploads them to a Cloud Storage bucket.

The generator is seeded, so every run produces byte-identical output. That
matters for a course: the expected outputs printed in the chapters stay
correct no matter when you run them.

Usage:
    python resources/sample_data.py --output-dir ./sample_data
    python resources/sample_data.py --output-dir ./sample_data --upload gs://YOUR_BUCKET/staging
    python resources/sample_data.py --orders 50000 --events 200000
    python resources/sample_data.py --output-dir ./sample_data --hot-key-rate 0.5
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
CURRENCIES = {"EUR": 1.0, "USD": 0.92, "GBP": 1.17, "JPY": 0.0064}
STATUSES = ["active", "complete", "cancelled", "refunded"]
EVENT_TYPES = ["page_view", "click", "add_to_cart", "purchase", "search", "scroll"]
PRODUCTS = [f"p{i:04d}" for i in range(200)]
SEED = 42

ORDER_FIELDS = [
    "order_id",
    "customer_id",
    "order_ts",
    "region",
    "channel",
    "currency",
    "status",
    "amount",
    "product_id",
]

EVENT_FIELDS = [
    "event_id",
    "user_id",
    "event_ts",
    "event_type",
    "product_id",
    "region",
    "value",
]


# --------------------------------------------------------------------------
# Generators
# --------------------------------------------------------------------------


def generate_orders(
    n: int,
    target_date: date,
    *,
    hot_key_rate: float = 0.0,
    rng: random.Random | None = None,
) -> list[dict]:
    """Generate a deterministic set of orders.

    Args:
        n: Number of orders to generate.
        target_date: The calendar day the orders are spread across.
        hot_key_rate: Fraction of orders assigned to a single "hot" customer.
            Used to demonstrate skew in the CombinePerKey chapter. 0.0 means
            an even spread.
        rng: Optional random generator, for reproducible skewed samples.

    Returns:
        A list of order dicts with the keys in ORDER_FIELDS.
    """
    rng = rng or random.Random(SEED)
    rows: list[dict] = []
    base_ts = datetime(
        target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc
    )

    for i in range(n):
        order_id = f"o{i:08d}"
        if hot_key_rate > 0 and rng.random() < hot_key_rate:
            customer_id = "c000001"  # the hot key
        else:
            customer_id = f"c{rng.randint(2, 5000):06d}"
        offset = timedelta(seconds=rng.randint(0, 86_399))
        order_ts = base_ts + offset
        currency = rng.choice(list(CURRENCIES))
        rows.append(
            {
                "order_id": order_id,
                "customer_id": customer_id,
                "order_ts": order_ts.isoformat(),
                "region": rng.choice(REGIONS),
                "channel": rng.choice(CHANNELS),
                "currency": currency,
                "status": rng.choice(STATUSES),
                "amount": round(rng.uniform(5.0, 950.0), 2),
                "product_id": rng.choice(PRODUCTS),
            }
        )
    return rows


def generate_events(
    n: int,
    target_date: date,
    *,
    late_events: int = 0,
    rng: random.Random | None = None,
) -> list[dict]:
    """Generate a deterministic set of clickstream events.

    Args:
        n: Number of events to generate.
        target_date: The calendar day the events are spread across.
        late_events: How many events to backdate well past the window they
            belong to. These exercise the allowed-lateness and late-data
            handling in the streaming module.
        rng: Optional random generator.

    Returns:
        A list of event dicts with the keys in EVENT_FIELDS.
    """
    rng = rng or random.Random(SEED + 1)
    rows: list[dict] = []
    base_ts = datetime(
        target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc
    )

    for i in range(n):
        offset = timedelta(seconds=rng.randint(0, 86_399))
        event_ts = base_ts + offset

        # The tail of the list holds deliberately late events: they belong to
        # the very start of the day but are stamped hours afterwards.
        if late_events and i >= n - late_events:
            event_ts = base_ts + timedelta(hours=23, minutes=59)

        rows.append(
            {
                "event_id": f"e{i:08d}",
                "user_id": f"u{rng.randint(1, 5000):06d}",
                "event_ts": event_ts.isoformat(),
                "event_type": rng.choice(EVENT_TYPES),
                "product_id": rng.choice(PRODUCTS),
                "region": rng.choice(REGIONS),
                "value": round(rng.uniform(0.0, 120.0), 2),
            }
        )
    return rows


def generate_malformed_rows(count: int = 5) -> list[str]:
    """Generate rows that deliberately fail validation.

    These are what the DLQ chapter needs: a pipeline that rejects bad input
    must have bad input to reject.
    """
    return [
        "not-an-order,missing-fields,garbage",
        "o99999999,c000001,not-a-timestamp,EMEA,web,EUR,complete,not-a-number,p0001",
        "o99999998,c000002,2026-01-01T00:00:00+00:00,UNKNOWN_REGION,web,EUR,complete,100.00,p0002",
        "o99999997,c000003,2026-01-01T00:00:00+00:00,EMEA,web,XYZ,complete,100.00,p0003",
        ",,,,",
    ][:count]


def generate_reference_data() -> dict[str, dict]:
    """Generate the small reference table used as a Beam side input.

    A side input is a lookup small enough to fit in memory and broadcast to
    every worker. Product metadata is the canonical example.
    """
    return {
        pid: {
            "product_id": pid,
            "category": f"cat-{pid[-2:]}",
            "unit_cost": round(3.0 + (int(pid[1:]) % 50), 2),
            "active": True,
        }
        for pid in PRODUCTS[:50]
    }


# --------------------------------------------------------------------------
# Writers
# --------------------------------------------------------------------------


def write_csv(rows: list[dict], path: Path, fields: list[str]) -> None:
    """Write rows to a CSV file with a header row."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    log.info("wrote %s (%d rows)", path, len(rows))


def write_ndjson(rows: list[dict], path: Path) -> None:
    """Write rows to a newline-delimited JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    log.info("wrote %s (%d rows)", path, len(rows))


def write_text_lines(lines: list[str], path: Path) -> None:
    """Write plain lines to a text file, one per line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log.info("wrote %s (%d lines)", path, len(lines))


def upload_to_gcs(local_dir: Path, gcs_uri: str) -> None:
    """Upload the generated files to a Cloud Storage bucket.

    Requires google-cloud-storage and valid application-default credentials.
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
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output-dir", default="./sample_data", help="Local output directory")
    parser.add_argument("--orders", type=int, default=5000, help="Number of orders")
    parser.add_argument("--events", type=int, default=20000, help="Number of events")
    parser.add_argument(
        "--date", default="2026-01-15", help="Target date (YYYY-MM-DD) for the records"
    )
    parser.add_argument(
        "--hot-key-rate",
        type=float,
        default=0.0,
        help="Fraction of orders sent to one hot customer key (0.0-1.0)",
    )
    parser.add_argument(
        "--late-events",
        type=int,
        default=0,
        help="Number of events backdated to simulate late data",
    )
    parser.add_argument("--upload", default=None, help="Optional gs:// destination")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Generate the sample dataset."""
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(SEED)
    orders = generate_orders(
        args.orders, target_date, hot_key_rate=args.hot_key_rate, rng=rng
    )
    events = generate_events(
        args.events, target_date, late_events=args.late_events, rng=rng
    )

    write_csv(orders, output_dir / "orders.csv", ORDER_FIELDS)
    write_ndjson(orders, output_dir / "orders.ndjson")
    write_ndjson(events, output_dir / "events.ndjson")
    write_csv(events, output_dir / "events.csv", EVENT_FIELDS)
    write_text_lines(
        generate_malformed_rows(), output_dir / "malformed_orders.csv"
    )

    reference = generate_reference_data()
    write_ndjson(
        list(reference.values()), output_dir / "product_reference.ndjson"
    )

    summary = {
        "orders": len(orders),
        "events": len(events),
        "malformed_rows": len(generate_malformed_rows()),
        "reference_rows": len(reference),
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
