"""Materialized views and pre-aggregation.

This module demonstrates the *pattern* of pre-aggregation:
compute the expensive aggregate once, store it, and serve
the result from the stored table on subsequent queries.

In SQLite, materialized views don't exist natively, so
we simulate the pattern with a regular table that the
loader populates. In a real warehouse (Snowflake,
BigQuery, Redshift), you'd use the native MATERIALIZED
VIEW support.

The two patterns covered:

  * Pre-aggregated rollup tables — built from a fact
    table, refreshed on a schedule.
  * Pre-joined "wide" tables — denormalized for fast
    reads at the cost of storage.

The benchmarks compare query latency against the raw
fact table.

Author: Prem Vishnoi <prem.vishnoi@example.com>
"""

from __future__ import annotations

import time
from typing import Dict, List

from common import Column, QueryRunner, Table


def _build_raw_fact(q: QueryRunner, n: int = 50_000) -> None:
    """Build a sample fact table with N rows."""
    import random
    rng = random.Random(42)
    dim_customer = Table("dim_customer", [
        Column("customer_key", "INTEGER", primary_key=True),
        Column("country", "TEXT", nullable=False),
    ])
    fact = Table("fact_orders", [
        Column("order_key", "INTEGER", primary_key=True),
        Column("customer_key", "INTEGER", nullable=False,
               references="dim_customer(customer_key)"),
        Column("date_key", "INTEGER", nullable=False),
        Column("amount", "REAL", nullable=False),
    ])
    q.execute(dim_customer.to_ddl())
    q.execute(fact.to_ddl())

    countries = ["US", "UK", "DE", "FR", "IN",
                 "JP", "BR", "CA", "AU", "MX"]
    q.executemany(
        "INSERT INTO dim_customer VALUES (?, ?)",
        [(i + 1, countries[i % len(countries)]) for i in range(1000)],
    )
    orders = []
    for i in range(1, n + 1):
        orders.append((
            i,
            rng.randint(1, 1000),
            20240101 + (i % 365),
            round(rng.uniform(10.0, 500.0), 2),
        ))
    q.executemany(
        "INSERT INTO fact_orders VALUES (?, ?, ?, ?)", orders
    )


# ---- baseline: query the raw fact ---------------------------------------


def benchmark_raw_aggregate(q: QueryRunner) -> Dict[str, float]:
    """Run the aggregate against the raw fact table."""
    _build_raw_fact(q)
    t0 = time.perf_counter()
    res = q.query_all(
        """
        SELECT c.country, d.month,
               COUNT(*) AS n, SUM(f.amount) AS total
        FROM fact_orders f
        JOIN dim_customer c ON f.customer_key = c.customer_key
        JOIN (SELECT date_key, (date_key / 100) % 100 AS month
              FROM (SELECT DISTINCT date_key FROM fact_orders)) d
          ON f.date_key = d.date_key
        GROUP BY c.country, d.month
        """
    )
    return {
        "query_ms": (time.perf_counter() - t0) * 1000,
        "rows": len(res),
    }


# ---- pre-aggregated rollup ----------------------------------------------


def _build_country_month_rollup(q: QueryRunner) -> None:
    """Build a pre-aggregated rollup table.

    The rollup has one row per (country, month) with the
    pre-computed count and total.
    """
    rollup = Table("agg_country_month", [
        Column("country", "TEXT", primary_key=False, nullable=False),
        Column("month", "INTEGER", nullable=False),
        Column("n", "INTEGER", nullable=False),
        Column("total", "REAL", nullable=False),
    ])
    q.execute(rollup.to_ddl())

    # Build the rollup by aggregating the fact.
    q.execute("""
        INSERT INTO agg_country_month (country, month, n, total)
        SELECT c.country,
               (f.date_key / 100) % 100 AS month,
               COUNT(*) AS n,
               SUM(f.amount) AS total
        FROM fact_orders f
        JOIN dim_customer c ON f.customer_key = c.customer_key
        GROUP BY c.country, month
    """)


def benchmark_rollup_query(q: QueryRunner) -> Dict[str, float]:
    """Query against the pre-aggregated rollup."""
    _build_raw_fact(q)
    _build_country_month_rollup(q)
    t0 = time.perf_counter()
    res = q.query_all(
        "SELECT country, month, n, total "
        "FROM agg_country_month ORDER BY country, month"
    )
    return {
        "query_ms": (time.perf_counter() - t0) * 1000,
        "rows": len(res),
    }


# ---- pre-joined wide table ----------------------------------------------


def _build_wide_table(q: QueryRunner) -> None:
    """Build a pre-joined wide table.

    The wide table has the columns the analyst needs
    already joined, so queries don't need to join.
    """
    wide = Table("wide_orders", [
        Column("order_key", "INTEGER", primary_key=True),
        Column("customer_key", "INTEGER", nullable=False),
        Column("country", "TEXT", nullable=False),
        Column("date_key", "INTEGER", nullable=False),
        Column("month", "INTEGER", nullable=False),
        Column("amount", "REAL", nullable=False),
    ])
    q.execute(wide.to_ddl())
    q.execute("""
        INSERT INTO wide_orders
        SELECT f.order_key, f.customer_key, c.country,
               f.date_key, (f.date_key / 100) % 100 AS month,
               f.amount
        FROM fact_orders f
        JOIN dim_customer c ON f.customer_key = c.customer_key
    """)


def benchmark_wide_query(q: QueryRunner) -> Dict[str, float]:
    """Query against the pre-joined wide table."""
    _build_raw_fact(q)
    _build_wide_table(q)
    t0 = time.perf_counter()
    res = q.query_all(
        "SELECT country, month, COUNT(*) AS n, SUM(amount) AS total "
        "FROM wide_orders GROUP BY country, month "
        "ORDER BY country, month"
    )
    return {
        "query_ms": (time.perf_counter() - t0) * 1000,
        "rows": len(res),
    }


# ---- refresh workflow ---------------------------------------------------


def refresh_rollup(q: QueryRunner) -> int:
    """Refresh the rollup table from the fact table.

    Returns the number of rows in the rollup after refresh.
    """
    # Truncate and re-insert.
    q.execute("DELETE FROM agg_country_month")
    q.execute("""
        INSERT INTO agg_country_month (country, month, n, total)
        SELECT c.country,
               (f.date_key / 100) % 100 AS month,
               COUNT(*) AS n,
               SUM(f.amount) AS total
        FROM fact_orders f
        JOIN dim_customer c ON f.customer_key = c.customer_key
        GROUP BY c.country, month
    """)
    return q.query_one(
        "SELECT COUNT(*) AS n FROM agg_country_month"
    )["n"]


# ---- demo ----------------------------------------------------------------


if __name__ == "__main__":
    print("Pre-aggregation benchmarks on 50k fact_orders rows:\n")
    for label, fn in [
        ("raw aggregate (join + group by)", benchmark_raw_aggregate),
        ("rollup (pre-aggregated country × month)", benchmark_rollup_query),
        ("wide (pre-joined orders)", benchmark_wide_query),
    ]:
        with QueryRunner(":memory:") as q:
            res = fn(q)
            print(
                f"[{label}]  "
                f"query={res['query_ms']:.2f}ms  "
                f"rows={res['rows']}"
            )
    print()
    # Demonstrate refresh.
    with QueryRunner(":memory:") as q:
        _build_raw_fact(q)
        _build_country_month_rollup(q)
        n = refresh_rollup(q)
        print(f"Rollup refresh returned {n} rows.")
