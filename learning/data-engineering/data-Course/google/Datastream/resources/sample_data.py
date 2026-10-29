#!/usr/bin/env python3
"""
sample_data.py — generate the sample data the Datastream course exercises use.

Creates deterministic change events and Kafka messages, then (optionally)
uploads them to a Cloud Storage bucket.

The generator is seeded, so every run produces byte-identical output. That
matters for a course: the expected outputs printed in the chapters stay
correct no matter when you run them.

Usage:
    python resources/sample_data.py --output-dir ./sample_data
    python resources/sample_data.py --output-dir ./sample_data --changes 5000
    python resources/sample_data.py --output-dir ./sample_data --upload gs://YOUR_BUCKET/staging
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

log = logging.getLogger(__name__)

REGIONS = ["EMEA", "AMER", "APAC", "LATAM"]
CHANNELS = ["web", "mobile", "store"]
CURRENCIES = ["EUR", "USD", "GBP", "JPY"]
STATUSES = ["active", "complete", "cancelled", "refunded"]
PRODUCTS = [f"p{i:04d}" for i in range(200)]
SEED = 42

CUSTOMER_FIELDS = [
    "customer_id",
    "first_name",
    "last_name",
    "email",
    "region",
    "tier",
    "created_at",
]

TRANSACTION_FIELDS = [
    "transaction_id",
    "customer_id",
    "amount",
    "currency",
    "product_id",
    "channel",
    "timestamp",
]


# --------------------------------------------------------------------------
# Generators
# --------------------------------------------------------------------------


def generate_customers(n: int, rng: random.Random) -> list[dict]:
    """Generate the base customer rows.

    Args:
        n: Number of customers.
        rng: The seeded random generator.

    Returns:
        A list of customer dicts with the keys in CUSTOMER_FIELDS.
    """
    first_names = ["Ada", "Grace", "Alan", "Edsger", "Barbara", "Linus", "Katherine", "Tim"]
    last_names = ["Lovelace", "Hopper", "Turing", "Dijkstra", "Liskov", "Torvalds", "Johnson", "Berners"]
    tiers = ["bronze", "silver", "gold", "platinum"]

    rows = []
    for i in range(n):
        rows.append(
            {
                "customer_id": f"c{i:06d}",
                "first_name": rng.choice(first_names),
                "last_name": rng.choice(last_names),
                "email": f"customer{i:06d}@example.com",
                "region": rng.choice(REGIONS),
                "tier": rng.choice(tiers),
                "created_at": "2026-01-01T00:00:00+00:00",
            }
        )
    return rows


def build_change_events(
    customers: list[dict],
    rng: random.Random,
    *,
    update_rate: float = 0.35,
    delete_rate: float = 0.10,
) -> list[dict]:
    """Turn a set of base rows into a realistic change-event stream.

    The stream has a deliberate shape, because the shape is the lesson:

    * every customer starts with an `INSERT`;
    * some are then `UPDATE`d, sometimes several times, with the `before`
      image showing the *previous* state — which is what proves the merge
      is working;
    * some are `DELETE`d, with the `before` image carrying the last known
      state;
    * a few events are duplicated, so the pipeline's idempotency is
      exercised;
    * one event is malformed, so the rejection path is exercised.

    Args:
        customers: The base rows.
        rng: The seeded random generator.
        update_rate: Fraction of rows that receive at least one update.
        delete_rate: Fraction of rows that are eventually deleted.

    Returns:
        The change events, in order.
    """
    events: list[dict] = []
    base_ts = datetime(2026, 1, 15, tzinfo=timezone.utc)

    for index, customer in enumerate(customers):
        # 1. The insert.
        insert_ts = base_ts + timedelta(seconds=index)
        events.append(
            {
                "op": "INSERT",
                "before": None,
                "after": dict(customer),
                "sourceTimestamp": insert_ts.isoformat(),
                "serverTimestamp": insert_ts.isoformat(),
            }
        )

        current = dict(customer)

        # 2. Zero or more updates.
        if rng.random() < update_rate:
            for update_index in range(rng.randint(1, 3)):
                before = dict(current)
                current["tier"] = rng.choice(["bronze", "silver", "gold", "platinum"])
                current["region"] = rng.choice(REGIONS)
                update_ts = (
                    base_ts
                    + timedelta(seconds=index)
                    + timedelta(minutes=update_index + 1)
                )
                events.append(
                    {
                        "op": "UPDATE",
                        "before": before,
                        "after": dict(current),
                        "sourceTimestamp": update_ts.isoformat(),
                        "serverTimestamp": update_ts.isoformat(),
                    }
                )

        # 3. A delete, for some fraction of rows.
        if rng.random() < delete_rate:
            delete_ts = base_ts + timedelta(seconds=index, minutes=30)
            events.append(
                {
                    "op": "DELETE",
                    "before": dict(current),
                    "after": None,
                    "sourceTimestamp": delete_ts.isoformat(),
                    "serverTimestamp": delete_ts.isoformat(),
                }
            )

    # 4. Duplicates — the same event delivered twice. A merge must be
    #    idempotent, and this is how we prove it.
    duplicates = [dict(event) for event in events[::37]]
    events.extend(duplicates)

    # 5. One malformed event, so the rejection path is exercised.
    events.append(
        {
            "op": "UPDATE",
            "before": None,
            "after": {"email": "no-key@example.com"},
            "sourceTimestamp": base_ts.isoformat(),
            "serverTimestamp": base_ts.isoformat(),
        }
    )

    # The stream is ordered by source timestamp, because that is the order
    # a real stream delivers it in — and because the merge depends on it.
    events.sort(key=lambda e: (e.get("sourceTimestamp") or "", e.get("op") or ""))
    return events


def generate_transactions(n: int, rng: random.Random) -> list[dict]:
    """Generate Kafka-style transaction messages.

    Args:
        n: Number of transactions.
        rng: The seeded random generator.

    Returns:
        A list of transaction dicts with the keys in TRANSACTION_FIELDS.
    """
    base_ts = datetime(2026, 1, 15, tzinfo=timezone.utc)
    rows = []
    for i in range(n):
        offset = timedelta(seconds=rng.randint(0, 86_399))
        rows.append(
            {
                "transaction_id": f"t{i:08d}",
                "customer_id": f"c{rng.randint(0, 999):06d}",
                "amount": round(rng.uniform(1.0, 800.0), 2),
                "currency": rng.choice(CURRENCIES),
                "product_id": rng.choice(PRODUCTS),
                "channel": rng.choice(CHANNELS),
                "timestamp": (base_ts + offset).isoformat(),
            }
        )
    return rows


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
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    log.info("wrote %s (%d rows)", path, len(rows))


def write_ndjson(rows: list[dict], path: Path) -> None:
    """Write rows to a newline-delimited JSON file.

    Args:
        rows: The rows to write.
        path: The destination path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
    log.info("wrote %s (%d rows)", path, len(rows))


def upload_to_gcs(local_dir: Path, gcs_uri: str) -> None:
    """Upload the generated files to a Cloud Storage bucket.

    Args:
        local_dir: The local directory to upload.
        gcs_uri: The `gs://` destination.

    Raises:
        SystemExit: If the storage client library is missing.
    """
    try:
        from google.cloud import storage  # type: ignore[import-not-found]
    except ImportError as exc:
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
        bucket.blob(blob_name).upload_from_filename(str(local_file))
        log.info("uploaded %s -> gs://%s/%s", local_file, bucket_name, blob_name)


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        argv: The argument list, or None to read from `sys.argv`.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output-dir", default="./sample_data", help="Local output directory")
    parser.add_argument("--customers", type=int, default=200, help="Number of customers")
    parser.add_argument("--changes", type=int, default=500, help="Number of Kafka transactions")
    parser.add_argument(
        "--date", default="2026-01-15", help="Target date (YYYY-MM-DD) for the records"
    )
    parser.add_argument("--upload", default=None, help="Optional gs:// destination")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Generate the sample dataset.

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

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(SEED)

    customers = generate_customers(args.customers, rng)
    write_csv(customers, output_dir / "customers.csv", CUSTOMER_FIELDS)
    write_ndjson(customers, output_dir / "customers.ndjson")

    events = build_change_events(customers, rng)
    write_ndjson(events, output_dir / "changes.ndjson")

    transactions = generate_transactions(args.changes, rng)
    write_ndjson(transactions, output_dir / "transactions.ndjson")

    summary = {
        "customers": len(customers),
        "change_events": len(events),
        "transactions": len(transactions),
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
