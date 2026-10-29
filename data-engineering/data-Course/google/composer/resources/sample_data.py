#!/usr/bin/env python3
"""
sample_data.py — generate the sample dataset the Composer course exercises use.

Creates deterministic CSV and NDJSON files. The generator is seeded, so
every run produces byte-identical output. That matters for a course: the
expected outputs printed in the chapters and notebooks stay correct no
matter when you run them.

Usage:
    python resources/sample_data.py --output-dir ./sample_data
    python resources/sample_data.py --output-dir ./sample_data --orders 50000
    python resources/sample_data.py --output-dir ./sample_data --malformed 50
    python resources/sample_data.py --output-dir ./sample_data --upload gs://YOUR_BUCKET/staging
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
STATUSES = ["active", "complete", "cancelled", "refunded"]
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

#: The expected per-region result for the default 5000-order dataset.
#: The notebooks and chapters assert against this, so it must stay exact.
EXPECTED_SUMMARY = {
    "AMER": {"order_count": 318, "revenue_eur": 113592.19},
    "APAC": {"order_count": 285, "revenue_eur": 108194.92},
    "EMEA": {"order_count": 322, "revenue_eur": 118423.22},
    "LATAM": {"order_count": 320, "revenue_eur": 110646.18},
}


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
            Used to demonstrate downstream skew. 0.0 means an even spread.
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
        currency = rng.choice(CURRENCIES)
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


def generate_malformed_rows(count: int = 9) -> list[str]:
    """Generate rows that deliberately fail validation.

    These are what the dead-letter path needs: a pipeline that rejects bad
    input must have bad input to reject.

    The base list contains **one row per reject reason code** the project
    defines, plus one row that is valid but not revenue-bearing (its
    status is ``cancelled``). That last row is deliberate: it proves the
    validator *accepts* rows it does not count as revenue, which is the
    distinction between "invalid" and "not revenue-bearing".

    With every reason code appearing exactly once, the reject counts are
    all 1 — which is what makes the dead-letter path assertable.

    Args:
        count: How many rows to return. Counts above the base length
            repeat the base rows; counts below it take a prefix, which
            may not cover every reason code.

    Returns:
        Malformed CSV lines.
    """
    base = [
        # wrong_field_count
        "not-an-order,missing-fields,garbage",
        # bad_amount
        "o99999999,c000001,not-a-timestamp,EMEA,web,EUR,complete,not-a-number,p0001",
        # unknown_region
        "o99999998,c000002,2026-01-01T00:00:00+00:00,UNKNOWN_REGION,web,EUR,complete,100.00,p0002",
        # unknown_currency
        "o99999997,c000003,2026-01-01T00:00:00+00:00,EMEA,web,XYZ,complete,100.00,p0003",
        # missing_order_id
        ",c000004,2026-01-01T00:00:00+00:00,EMEA,web,EUR,complete,100.00,p0004",
        # missing_customer_id
        "o99999996,,2026-01-01T00:00:00+00:00,EMEA,web,EUR,complete,100.00,p0006",
        # negative_amount
        "o99999995,c000005,2026-01-01T00:00:00+00:00,EMEA,web,EUR,complete,-50.00,p0005",
        # unknown_status
        "o99999994,c000006,2026-01-01T00:00:00+00:00,EMEA,web,EUR,unknown_status,100.00,p0006",
        # VALID, but `cancelled` — accepted by the validator, then
        # excluded from the revenue because it does not bear revenue.
        "o99999993,c000007,2026-01-01T00:00:00+00:00,EMEA,web,EUR,cancelled,100.00,p0007",
    ]
    if count <= len(base):
        return base[:count]
    # Repeat with varied ids to reach the requested count.
    extra = []
    for i in range(count - len(base)):
        extra.append(base[i % len(base)])
    return base + extra


def generate_reference_data() -> dict[str, dict]:
    """Generate the small reference table used as a lookup.

    In the DAG this arrives as a BigQuery table and is joined in; the
    local runner loads the same data from JSON.
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

    Requires google-cloud-storage and valid application-default credentials.

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
    parser.add_argument("--orders", type=int, default=5000, help="Number of orders")
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
        "--malformed", type=int, default=9, help="Number of malformed rows to include"
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
    orders = generate_orders(
        args.orders, target_date, hot_key_rate=args.hot_key_rate, rng=rng
    )

    write_csv(orders, output_dir / "orders.csv", ORDER_FIELDS)
    write_ndjson(orders, output_dir / "orders.ndjson")
    write_text_lines(
        generate_malformed_rows(args.malformed), output_dir / "malformed_orders.csv"
    )
    write_ndjson(
        list(generate_reference_data().values()), output_dir / "product_reference.ndjson"
    )

    summary = {
        "orders": len(orders),
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
