#!/usr/bin/env python3
"""
sample_data.py — generate the deterministic dataset for the course.

The data is deterministic (``SEED = 42``) and deliberately imperfect.
It contains every mistake the chapters talk about, so the validation
gate has something real to catch:

    * **duplicate order lines** — a re-delivered event, which inflates
      every additive measure;
    * **a customer with no matching customer row** — a foreign key that
      does not resolve, so a left join shows a blank label;
    * **a null ``product_id``** — an optional dimension that is
      sometimes absent;
    * **a day with no orders** — the gap the date spine has to fill;
    * **a negative revenue row** — a legitimate refund;
    * **a stale day** — the newest rows stop before "today", so the
      freshness check fires.

Usage:

    python resources/sample_data.py --output-dir ./sample_data
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

#: The seed. Everything below is derived from it, so the dataset is
#: identical on every machine and every run.
SEED = 42

#: The number of customers.
CUSTOMERS = 120

#: The number of products.
PRODUCTS = 40

#: The number of order lines.
ORDER_LINES = 900

#: The first date in the dataset.
START_DATE = date(2026, 1, 1)

#: The number of days in the dataset.
DAYS = 180

REGIONS = ("AMER", "EMEA", "APAC", "LATAM")
CHANNELS = ("web", "app", "store", "partner")
STATUSES = ("placed", "shipped", "delivered", "cancelled", "returned")
SEGMENTS = ("enterprise", "mid-market", "smb", "consumer")
CATEGORIES = ("accessories", "hardware", "software", "services")
SUPPLIERS = tuple(f"supplier_{i:02d}" for i in range(1, 9))
COUNTRIES = (
    "US", "CA", "GB", "DE", "FR", "BR", "IN", "JP", "AU", "ZA",
)


def _weighted_dates(rng: random.Random, count: int, days: int) -> list[date]:
    """Pick order dates with a weekly rhythm.

    Business data is not uniform: weekends are quieter, and the last
    week of the quarter is busier. A flat random distribution produces a
    dataset that looks fake in a chart.

    Args:
        rng: The random generator.
        count: How many dates to produce.
        days: The width of the window, in days.

    Returns:
        The chosen dates.
    """
    dates: list[date] = []
    for _ in range(count):
        offset = rng.randrange(days)
        candidate = START_DATE + timedelta(days=offset)
        if candidate.weekday() >= 5 and rng.random() < 0.65:
            offset = (offset + 2) % days
            candidate = START_DATE + timedelta(days=offset)
        dates.append(candidate)
    return dates


def build_customers(rng: random.Random) -> list[dict[str, object]]:
    """Build the customers table.

    Args:
        rng: The random generator.

    Returns:
        The customer rows.
    """
    rows: list[dict[str, object]] = []
    for index in range(1, CUSTOMERS + 1):
        signup = START_DATE - timedelta(days=rng.randrange(0, 900))
        rows.append(
            {
                "customer_id": f"c{index:04d}",
                "name": f"Customer {index:04d}",
                "segment": rng.choice(SEGMENTS),
                "country": rng.choice(COUNTRIES),
                "signup_date": signup.isoformat(),
                "lifetime_value": round(rng.uniform(0, 25000), 2),
            }
        )
    return rows


def build_products(rng: random.Random) -> list[dict[str, object]]:
    """Build the products table.

    Args:
        rng: The random generator.

    Returns:
        The product rows.
    """
    rows: list[dict[str, object]] = []
    for index in range(1, PRODUCTS + 1):
        cost = round(rng.uniform(5, 400), 2)
        rows.append(
            {
                "product_id": f"p{index:04d}",
                "name": f"Product {index:04d}",
                "category": rng.choice(CATEGORIES),
                "supplier": rng.choice(SUPPLIERS),
                "cost": cost,
                "list_price": round(cost * rng.uniform(1.2, 3.0), 2),
            }
        )
    return rows


def build_order_lines(
    rng: random.Random,
    customers: list[dict[str, object]],
    products: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Build the order-line fact table.

    Args:
        rng: The random generator.
        customers: The customers, for the foreign key.
        products: The products, for the foreign key.

    Returns:
        The order-line rows.
    """
    customer_ids = [str(c["customer_id"]) for c in customers]
    product_rows = list(products)
    dates = _weighted_dates(rng, ORDER_LINES, DAYS)

    rows: list[dict[str, object]] = []
    for index in range(1, ORDER_LINES + 1):
        product = rng.choice(product_rows)
        unit_price = float(product["list_price"])
        quantity = rng.randrange(1, 6)
        amount = round(unit_price * quantity, 2)
        cost = round(float(product["cost"]) * quantity, 2)
        margin = round(amount - cost, 2)
        customer_id = rng.choice(customer_ids)
        rows.append(
            {
                "order_id": f"o{(index - 1) // 2 + 1:05d}",
                "line_id": f"ol{index:06d}",
                "customer_id": customer_id,
                "product_id": str(product["product_id"]),
                "quantity": quantity,
                "unit_price": unit_price,
                "total_amount": amount,
                "margin_amount": margin,
                "region": rng.choice(REGIONS),
                "channel": rng.choice(CHANNELS),
                "status": rng.choices(
                    STATUSES, weights=(15, 20, 50, 8, 7)
                )[0],
                "product_category": str(product["category"]),
                "created_at": dates[index - 1].isoformat(),
            }
        )

    # --- The deliberate imperfections -----------------------------------
    #
    # Each of these is a mistake the chapters explain, and each one is
    # caught by a specific check in `project/core/validate.py`.

    # 1. A duplicated order line — a re-delivered event. This inflates
    #    every additive measure by exactly the size of the duplicate.
    rows.append(dict(rows[10]))

    # 2. A foreign key that does not resolve — the customer row has not
    #    landed yet. A left join will show a blank label.
    rows[50]["customer_id"] = "c9999"

    # 3. A null product id — an optional dimension that is sometimes
    #    absent.
    rows[77]["product_id"] = None

    # 4. A legitimate refund — negative revenue.
    rows[120]["total_amount"] = -round(abs(float(rows[120]["total_amount"])), 2)
    rows[120]["margin_amount"] = -round(
        abs(float(rows[120]["margin_amount"])), 2
    )
    rows[120]["status"] = "returned"

    # 5. A stale pipeline — the extract stopped three days before the
    #    end of the range, so the freshness check fires. This is what a
    #    broken extract looks like from the dashboard's point of view:
    #    a flat line at the end, not an error.
    stale_cutoff = (START_DATE + timedelta(days=DAYS - 4)).isoformat()
    for row in rows:
        if str(row["created_at"]) > stale_cutoff:
            row["created_at"] = stale_cutoff

    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    """Write rows to a CSV file.

    Args:
        path: The destination path.
        rows: The rows.

    Returns:
        None.
    """
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_ndjson(path: Path, rows: list[dict[str, object]]) -> None:
    """Write rows to a newline-delimited JSON file.

    Args:
        path: The destination path.
        rows: The rows.

    Returns:
        None.
    """
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, default=str) + "\n")


def main() -> int:
    """Generate the dataset.

    Returns:
        0 on success.
    """
    parser = argparse.ArgumentParser(
        description="Generate the deterministic dataset for the course."
    )
    parser.add_argument(
        "--output-dir",
        default="./sample_data",
        help="Where to write the dataset (default: ./sample_data)",
    )
    args = parser.parse_args()

    rng = random.Random(SEED)

    customers = build_customers(rng)
    products = build_products(rng)
    orders = build_order_lines(rng, customers, products)

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)

    write_csv(output / "customers.csv", customers)
    write_csv(output / "products.csv", products)
    write_csv(output / "orders.csv", orders)
    write_ndjson(output / "orders.ndjson", orders)

    latest = max(str(row["created_at"]) for row in orders)
    print("Sample data generated")
    print("----------------------------------------------------")
    print(f"  customers          : {len(customers)}")
    print(f"  products           : {len(products)}")
    print(f"  order lines        : {len(orders)}")
    print(f"  distinct orders    : {len({r['order_id'] for r in orders})}")
    print(f"  date range         : {START_DATE} to {latest}")
    print(f"  output directory   : {output}")
    print()
    print("  The dataset contains deliberate imperfections:")
    print("    - 1 duplicated order line (a re-delivered event)")
    print("    - 1 unresolved customer_id (c9999)")
    print("    - 1 null product_id")
    print("    - 1 negative revenue row (a refund)")
    print("    - days with no orders at all")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
