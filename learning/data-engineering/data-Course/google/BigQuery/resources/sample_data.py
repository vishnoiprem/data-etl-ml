#!/usr/bin/env python3
"""
sample_data.py — generate the sample data the course exercises use.

Creates deterministic CSV, NDJSON, and Parquet files, then (optionally)
uploads them to a Cloud Storage bucket.

Usage:
    python resources/sample_data.py --output-dir ./sample_data
    python resources/sample_data.py --output-dir ./sample_data --upload gs://YOUR_BUCKET/staging
    python resources/sample_data.py --orders 50000 --events 200000
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    HAS_PYARROW = True
except ImportError:  # pragma: no cover
    HAS_PYARROW = False

REGIONS = ["EMEA", "AMER", "APAC", "LATAM"]
CHANNELS = ["web", "mobile", "store"]
CURRENCIES = {"EUR": 1.0, "USD": 0.92, "GBP": 1.17, "JPY": 0.0064}
STATUSES = ["active", "complete", "cancelled", "refunded"]
EVENT_TYPES = ["page_view", "click", "add_to_cart", "purchase", "search", "scroll"]
PRODUCTS = [f"p{i:04d}" for i in range(200)]
SEED = 42


def generate_orders(n: int, target_date: date) -> list[dict]:
    """Generate a deterministic set of orders."""
    rng = random.Random(SEED)
    rows = []
    base_ts = datetime(target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc)

    for i in range(n):
        order_id = f"o{i:08d}"
        customer_id = f"c{rng.randint(1, 5000):06d}"
        offset = timedelta(seconds=rng.randint(0, 86_399))
        order_ts = base_ts + offset
        currency = rng.choice(list(CURRENCIES))
        channel = rng.choices(CHANNELS, weights=[45, 35, 20])[0]
        line_count = rng.randint(1, 6)
        amount = round(rng.uniform(5, 900), 2)

        rows.append(
            {
                "order_id": order_id,
                "customer_id": customer_id,
                "order_ts": order_ts.isoformat().replace("+00:00", "Z"),
                "order_date": target_date.isoformat(),
                "channel": channel,
                "region": rng.choice(REGIONS),
                "currency": currency,
                "amount_local": f"{amount:.2f}",
                "status": rng.choices(STATUSES, weights=[55, 35, 7, 3])[0],
                "line_count": line_count,
            }
        )
    return rows


def generate_events(n: int, target_date: date) -> list[dict]:
    """Generate a deterministic set of clickstream events."""
    rng = random.Random(SEED + 1)
    rows = []
    base_ts = datetime(target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc)

    for i in range(n):
        event_type = rng.choices(EVENT_TYPES, weights=[30, 25, 10, 8, 20, 7])[0]
        offset = timedelta(seconds=rng.randint(0, 86_399))
        event_ts = base_ts + offset
        amount = round(rng.uniform(1, 300), 2) if event_type == "purchase" else None

        rows.append(
            {
                "event_id": f"e{i:09d}",
                "user_id": f"u{rng.randint(1, 20000):06d}",
                "event_type": event_type,
                "event_ts": event_ts.isoformat().replace("+00:00", "Z"),
                "event_date": target_date.isoformat(),
                "amount": f"{amount:.2f}" if amount is not None else "",
                "props": json.dumps(
                    {
                        "device": rng.choice(["mobile", "desktop", "tablet"]),
                        "campaign": f"cmp_{rng.randint(1, 20):03d}",
                    },
                    separators=(",", ":"),
                ),
            }
        )
    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"  ✓ {path}  ({path.stat().st_size / 1024:.1f} KB)")


def write_ndjson(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, separators=(",", ":")) + "\n")
    print(f"  ✓ {path}  ({path.stat().st_size / 1024:.1f} KB)")


def write_parquet(rows: list[dict], path: Path) -> None:
    if not HAS_PARROW:
        print(f"  ! skipping {path} (pyarrow not installed)")
        return

    path.parent.mkdir(parents=True, exist_ok=True)

    schema = pa.schema(
        [
            pa.field("order_id", pa.string()),
            pa.field("customer_id", pa.string()),
            pa.field("order_ts", pa.timestamp("us", tz="UTC")),
            pa.field("order_date", pa.date32()),
            pa.field("channel", pa.string()),
            pa.field("region", pa.string()),
            pa.field("currency", pa.string()),
            pa.field("amount_local", pa.decimal128(12, 2)),
            pa.field("status", pa.string()),
            pa.field("line_count", pa.int64()),
        ]
    )

    table = pa.Table.from_pylist(
        [
            {
                **r,
                "order_ts": datetime.fromisoformat(r["order_ts"].replace("Z", "+00:00")),
                "order_date": date.fromisoformat(r["order_date"]),
                "amount_local": r["amount_local"],
            }
            for r in rows
        ],
        schema=schema,
    )
    pq.write_table(table, path, compression="zstd")
    print(f"  ✓ {path}  ({path.stat().st_size / 1024:.1f} KB)")


def write_fx_rates(target_date: date, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["rate_date", "currency", "rate_to_eur", "source"])
        for currency, rate in CURRENCIES.items():
            writer.writerow([target_date.isoformat(), currency, f"{rate:.6f}", "ecb"])
    print(f"  ✓ {path}")


def write_products(path: Path) -> None:
    rng = random.Random(SEED + 2)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["product_id", "product_name", "category", "list_price"])
        categories = ["electronics", "apparel", "home", "grocery", "toys", "sports"]
        for pid in PRODUCTS:
            writer.writerow(
                [
                    pid,
                    f"Product {pid}",
                    rng.choice(categories),
                    f"{rng.uniform(5, 500):.2f}",
                ]
            )
    print(f"  ✓ {path}")


def upload(local_dir: Path, gs_uri: str) -> None:
    try:
        from google.cloud import storage
    except ImportError:
        print("! google-cloud-storage not installed — skipping upload")
        return

    bucket = storage.Client().bucket(gs_uri.replace("gs://", "").split("/")[0])
    prefix = gs_uri.replace(f"gs://{bucket.name}", "").strip("/")

    for path in sorted(local_dir.rglob("*")):
        if path.is_file():
            rel = path.relative_to(local_dir).as_posix()
            blob = bucket.blob(f"{prefix}/{rel}" if prefix else rel)
            blob.upload_from_filename(str(path), content_type="text/csv")
            print(f"  ↑ gs://{bucket.name}/{prefix}/{rel}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="./sample_data")
    parser.add_argument("--date", default="2026-01-15")
    parser.add_argument("--orders", type=int, default=10_000)
    parser.add_argument("--events", type=int, default=50_000)
    parser.add_argument("--upload", default=None, metavar="GS_URI")
    args = parser.parse_args()

    target_date = date.fromisoformat(args.date)
    out = Path(args.output_dir)
    stamp = target_date.strftime("%Y%m%d")

    print(f"Generating sample data for {target_date} into {out}\n")

    print("Orders:")
    orders = generate_orders(args.orders, target_date)
    write_csv(orders, out / "orders" / f"orders_{stamp}.csv")
    write_ndjson(orders, out / "orders" / f"orders_{stamp}.ndjson")
    write_parquet(orders, out / "orders" / f"orders_{stamp}.parquet")

    print("\nEvents:")
    events = generate_events(args.events, target_date)
    write_csv(events, out / "events" / f"events_{stamp}.csv")
    write_ndjson(events, out / "events" / f"events_{stamp}.ndjson")

    print("\nReference:")
    write_fx_rates(target_date, out / "reference" / f"fx_rates_{stamp}.csv")
    write_products(out / "reference" / "products.csv")

    if args.upload:
        print(f"\nUploading to {args.upload}:")
        upload(out, args.upload)

    print("\nDone. Load with:")
    print(f"  bq load --source_format=CSV --skip_leading_rows=1 --replace \\")
    print(f"    YOUR_PROJECT_ID:curated.orders \\")
    print(f"    gs://YOUR_BUCKET/staging/orders/orders_{stamp}.csv")


if __name__ == "__main__":
    main()
