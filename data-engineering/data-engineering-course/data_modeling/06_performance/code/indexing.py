"""Indexing strategies — B-tree, bitmap, partial.

This module benchmarks the three indexing strategies on a
sample fact table and demonstrates the tradeoffs. It also
shows how to build each type of index using the
`common.schema` helper.

What this module covers:

  * B-tree indexes — the default in most warehouses.
    Best for high-cardinality columns and range queries.
  * Bitmap indexes — best for low-cardinality columns
    (e.g., country, status). Note: SQLite doesn't
    natively support bitmap indexes, so we simulate the
    pattern with multiple single-column indexes.
  * Partial indexes — only index rows matching a WHERE
    clause. Best for sparse data ("only index active
    users," "only index recent orders").

The benchmarks are *not* asserted on timing — the
asserts are on the *correctness* of the results. The
timing prints are for inspection.

Author: Prem Vishnoi <prem.vishnoi@example.com>
"""

from __future__ import annotations

import time
from typing import Dict, List

from common import Column, QueryRunner, Table


# ---- schema --------------------------------------------------------------


def _build_schema(q: QueryRunner, n: int = 50_000) -> None:
    """Build a sample fact_orders table with N rows."""
    import random

    dim_customer = Table("dim_customer", [
        Column("customer_key", "INTEGER", primary_key=True),
        Column("country", "TEXT", nullable=False),
    ])
    fact_orders = Table("fact_orders", [
        Column("order_key", "INTEGER", primary_key=True),
        Column("customer_key", "INTEGER", nullable=False,
               references="dim_customer(customer_key)"),
        Column("date_key", "INTEGER", nullable=False),
        Column("status", "TEXT", nullable=False),
        Column("amount", "REAL", nullable=False),
    ])
    q.execute(dim_customer.to_ddl())
    q.execute(fact_orders.to_ddl())

    # Seed customers with low-cardinality country (10 values).
    countries = ["US", "UK", "DE", "FR", "IN", "JP",
                 "BR", "CA", "AU", "MX"]
    customers = [(i + 1, countries[i % len(countries)])
                 for i in range(1000)]
    q.executemany(
        "INSERT INTO dim_customer VALUES (?, ?)", customers
    )

    # Seed orders.
    statuses = ["pending", "paid", "shipped", "delivered", "cancelled"]
    rng = random.Random(42)
    orders = []
    for i in range(1, n + 1):
        orders.append((
            i,
            rng.randint(1, 1000),
            20240101 + (i % 365),
            statuses[i % len(statuses)],
            round(rng.uniform(10.0, 500.0), 2),
        ))
    q.executemany(
        "INSERT INTO fact_orders VALUES (?, ?, ?, ?, ?)", orders
    )


# ---- no index baseline ---------------------------------------------------


def benchmark_no_index(q: QueryRunner) -> Dict[str, float]:
    """Baseline: no secondary indexes, just the PK."""
    _build_schema(q)
    # Query 1: filter by status (low cardinality).
    t0 = time.perf_counter()
    res1 = q.query_all(
        "SELECT COUNT(*) AS n FROM fact_orders WHERE status = 'paid'"
    )
    t1 = time.perf_counter() - t0

    # Query 2: filter by date (high cardinality).
    t0 = time.perf_counter()
    res2 = q.query_all(
        "SELECT COUNT(*) AS n FROM fact_orders WHERE date_key = 20240301"
    )
    t2 = time.perf_counter() - t0

    return {
        "by_status_ms": t1 * 1000,
        "by_date_ms": t2 * 1000,
        "by_status_count": res1[0]["n"],
        "by_date_count": res2[0]["n"],
    }


# ---- B-tree index --------------------------------------------------------


def benchmark_btree_index(q: QueryRunner) -> Dict[str, float]:
    """B-tree on `date_key` and `status`."""
    _build_schema(q)
    q.execute(
        'CREATE INDEX IF NOT EXISTS idx_orders_date '
        'ON fact_orders (date_key)'
    )
    q.execute(
        'CREATE INDEX IF NOT EXISTS idx_orders_status '
        'ON fact_orders (status)'
    )

    t0 = time.perf_counter()
    res1 = q.query_all(
        "SELECT COUNT(*) AS n FROM fact_orders WHERE status = 'paid'"
    )
    t1 = time.perf_counter() - t0

    t0 = time.perf_counter()
    res2 = q.query_all(
        "SELECT COUNT(*) AS n FROM fact_orders WHERE date_key = 20240301"
    )
    t2 = time.perf_counter() - t0

    return {
        "by_status_ms": t1 * 1000,
        "by_date_ms": t2 * 1000,
        "by_status_count": res1[0]["n"],
        "by_date_count": res2[0]["n"],
    }


# ---- bitmap-style (multiple single-column indexes) ----------------------


def benchmark_bitmap_style(q: QueryRunner) -> Dict[str, float]:
    """Bitmap-style: one index per low-cardinality value.

    SQLite doesn't have native bitmap indexes, but the
    *pattern* is "one index per distinct low-card value."
    In a real warehouse (Snowflake, Redshift, Oracle),
    this is a single bitmap index; in SQLite, it's
    multiple single-column indexes that the planner
    combines.
    """
    _build_schema(q)
    # One index per status value.
    for status in ("pending", "paid", "shipped",
                   "delivered", "cancelled"):
        q.execute(
            f"CREATE INDEX IF NOT EXISTS idx_orders_status_"
            f"{status} ON fact_orders (order_key) "
            f"WHERE status = '{status}'"
        )

    t0 = time.perf_counter()
    res1 = q.query_all(
        "SELECT COUNT(*) AS n FROM fact_orders WHERE status = 'paid'"
    )
    t1 = time.perf_counter() - t0

    # Date query is unchanged.
    t0 = time.perf_counter()
    res2 = q.query_all(
        "SELECT COUNT(*) AS n FROM fact_orders WHERE date_key = 20240301"
    )
    t2 = time.perf_counter() - t0

    return {
        "by_status_ms": t1 * 1000,
        "by_date_ms": t2 * 1000,
        "by_status_count": res1[0]["n"],
        "by_date_count": res2[0]["n"],
    }


# ---- partial index -------------------------------------------------------


def benchmark_partial_index(q: QueryRunner) -> Dict[str, float]:
    """Partial index: only index `status = 'paid'` rows.

    The pattern: only the most-queried subset is indexed.
    Saves index storage and update cost.
    """
    _build_schema(q)
    q.execute(
        "CREATE INDEX IF NOT EXISTS idx_orders_paid_only "
        "ON fact_orders (date_key, amount) WHERE status = 'paid'"
    )

    # This query benefits from the partial index.
    t0 = time.perf_counter()
    res1 = q.query_all(
        "SELECT COUNT(*) AS n FROM fact_orders "
        "WHERE status = 'paid' AND date_key = 20240301"
    )
    t1 = time.perf_counter() - t0

    # This query does not benefit (status != 'paid').
    t0 = time.perf_counter()
    res2 = q.query_all(
        "SELECT COUNT(*) AS n FROM fact_orders "
        "WHERE status = 'cancelled' AND date_key = 20240301"
    )
    t2 = time.perf_counter() - t0

    return {
        "by_paid_date_ms": t1 * 1000,
        "by_cancelled_date_ms": t2 * 1000,
        "by_paid_date_count": res1[0]["n"],
        "by_cancelled_date_count": res2[0]["n"],
    }


# ---- demo ----------------------------------------------------------------


if __name__ == "__main__":
    print("Indexing benchmarks on 50k fact_orders rows:")
    print()
    for label, fn in [
        ("no index", benchmark_no_index),
        ("B-tree on date_key + status", benchmark_btree_index),
        ("bitmap-style (5 partial indexes per status)",
         benchmark_bitmap_style),
        ("partial index (status='paid' only)",
         benchmark_partial_index),
    ]:
        with QueryRunner(":memory:") as q:
            res = fn(q)
            print(f"[{label}]")
            for k, v in res.items():
                if k.endswith("_ms"):
                    print(f"   {k:<25} = {v:8.2f} ms")
                else:
                    print(f"   {k:<25} = {v}")
            print()
