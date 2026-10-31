"""Deterministic sample data for the Spark labs.

Two properties matter for a learning fixture:

1. **Determinism.** A fixed random seed means the same output every run, so
   a test can assert on exact numbers and a reader can follow along without
   the numbers moving under them.

2. **Realistic skew.** Uniform data hides every performance problem that
   matters. The sales fixture has one dominant region holding a large share
   of rows — the exact shape that makes a naive ``groupBy`` collapse onto a
   single executor in production.

The generator writes CSVs once and reuses them. Generating data on every
run would dominate the runtime of the small labs.
"""

from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from pathlib import Path

from sparklab import DATA_DIR

__all__ = ["SalesFixture", "ensure_sales_csv", "ensure_skew_csv", "ensure_transactions_csv"]


@dataclass(frozen=True)
class SalesFixture:
    """Paths to the generated sales fixture."""

    path: Path
    rows: int
    regions: tuple[str, ...]


_REGIONS: tuple[str, ...] = ("US", "EU", "APAC", "LATAM", "Africa")
_PRODUCTS: tuple[str, ...] = ("Laptop", "Phone", "Tablet", "Monitor", "Keyboard")

#: The weights deliberately concentrate ~60% of the rows in "US". A real
#: sales table looks like this: one big market, several small ones.
_REGION_WEIGHTS: tuple[int, ...] = (60, 20, 10, 7, 3)


def ensure_sales_csv(
    path: str | Path | None = None,
    *,
    rows: int = 100_000,
    seed: int = 42,
) -> SalesFixture:
    """Generate (or reuse) a sales CSV with a realistically skewed region key.

    The schema is: ``timestamp,region,sales_amount,product``.
    """
    target = Path(path) if path else DATA_DIR / "sales.csv"
    target.parent.mkdir(parents=True, exist_ok=True)

    if not target.exists():
        rng = random.Random(seed)
        with target.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["timestamp", "region", "sales_amount", "product"])
            for _ in range(rows):
                # 2025-01-01 .. 2025-03-31 (90 days) plus a time of day.
                day = rng.randrange(90)
                hour = rng.randrange(24)
                minute = rng.randrange(60)
                month = day // 30 + 1
                dom = day % 28 + 1
                region = rng.choices(_REGIONS, weights=_REGION_WEIGHTS, k=1)[0]
                amount = round(rng.uniform(1.0, 1000.0), 2)
                product = rng.choice(_PRODUCTS)
                writer.writerow(
                    [f"2025-{month:02d}-{dom:02d} {hour:02d}:{minute:02d}:00", region, amount, product]
                )

    return SalesFixture(path=target, rows=rows, regions=_REGIONS)


def ensure_skew_csv(
    path: str | Path | None = None,
    *,
    rows: int = 50_000,
    seed: int = 7,
) -> Path:
    """Generate a tiny user-event CSV with a deliberately hot key.

    Schema: ``user_id,event_type,event_time``.

    ``user_id=1`` receives ~80% of the rows. This is the shape that makes
    a shuffle-based aggregation hang on a single task, and it is the
    dataset the salting lab uses to make the problem measurable.
    """
    target = Path(path) if path else DATA_DIR / "skewed_events.csv"
    target.parent.mkdir(parents=True, exist_ok=True)

    if not target.exists():
        rng = random.Random(seed)
        with target.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["user_id", "event_type", "event_time"])
            for _ in range(rows):
                # 80/20 split: one hot key, a long tail of cold ones.
                if rng.random() < 0.8:
                    user_id = 1
                else:
                    user_id = rng.randrange(2, 101)
                event_type = rng.choice(["click", "view", "purchase"])
                minute = rng.randrange(0, 24 * 60)
                writer.writerow(
                    [user_id, event_type, f"2025-01-01 {minute // 60:02d}:{minute % 60:02d}:00"]
                )

    return target


def ensure_transactions_csv(
    path: str | Path | None = None,
    *,
    rows: int = 10_000,
    seed: int = 13,
) -> Path:
    """Generate a transaction log CSV.

    Schema: ``transaction_id,customer_id,amount,txn_date``.
    """
    target = Path(path) if path else DATA_DIR / "transactions.csv"
    target.parent.mkdir(parents=True, exist_ok=True)

    if not target.exists():
        rng = random.Random(seed)
        with target.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["transaction_id", "customer_id", "amount", "txn_date"])
            for i in range(rows):
                customer = f"C{rng.randrange(1, 501):04d}"
                # A long tail of small amounts plus rare large ones, so that
                # both the CTR threshold and the structuring rule have
                # something to find.
                if rng.random() < 0.02:
                    amount = round(rng.uniform(9_000, 25_000), 2)
                else:
                    amount = round(rng.uniform(1, 400), 2)
                day = rng.randrange(1, 29)
                writer.writerow([f"T{i:08d}", customer, amount, f"2025-01-{day:02d}"])

    return target
