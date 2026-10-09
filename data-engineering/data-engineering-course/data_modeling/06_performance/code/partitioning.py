"""Partitioning strategies — range, hash, list.

This module demonstrates the three partitioning strategies
on a sample fact table:

  * Range partitioning — by date_key, by amount bucket.
    Best for time-series queries.
  * Hash partitioning — by customer_key, by order_id.
    Best for even distribution of writes.
  * List partitioning — by country, by status.
    Best for categorical access patterns.

Note: SQLite doesn't have native partitioning, so we
simulate the pattern with separate tables (one per
partition) and a UNION ALL view. The tradeoffs and
patterns are the same as in a real warehouse.

Author: Prem Vishnoi <prem.vishnoi@example.com>
"""

from __future__ import annotations

import time
from typing import Dict

from common import Column, QueryRunner, Table


def _build_range_partitions(q: QueryRunner) -> None:
    """Build a range-partitioned fact table.

    Three partitions: 2024-Q1, 2024-Q2, 2024-Q3, 2024-Q4.
    Each is a separate table; a UNION ALL view stitches
    them back together.
    """
    fact_q1 = Table("fact_orders_2024_q1", [
        Column("order_key", "INTEGER", primary_key=True),
        Column("customer_key", "INTEGER", nullable=False),
        Column("date_key", "INTEGER", nullable=False),
        Column("amount", "REAL", nullable=False),
    ])
    fact_q2 = Table("fact_orders_2024_q2", [
        Column("order_key", "INTEGER", primary_key=True),
        Column("customer_key", "INTEGER", nullable=False),
        Column("date_key", "INTEGER", nullable=False),
        Column("amount", "REAL", nullable=False),
    ])
    fact_q3 = Table("fact_orders_2024_q3", [
        Column("order_key", "INTEGER", primary_key=True),
        Column("customer_key", "INTEGER", nullable=False),
        Column("date_key", "INTEGER", nullable=False),
        Column("amount", "REAL", nullable=False),
    ])
    fact_q4 = Table("fact_orders_2024_q4", [
        Column("order_key", "INTEGER", primary_key=True),
        Column("customer_key", "INTEGER", nullable=False),
        Column("date_key", "INTEGER", nullable=False),
        Column("amount", "REAL", nullable=False),
    ])
    for t in (fact_q1, fact_q2, fact_q3, fact_q4):
        q.execute(t.to_ddl())

    # Seed each partition with 1k rows.
    import random
    rng = random.Random(42)
    for q_name, q_start, q_end in [
        ("fact_orders_2024_q1", 20240101, 20240331),
        ("fact_orders_2024_q2", 20240401, 20240630),
        ("fact_orders_2024_q3", 20240701, 20240930),
        ("fact_orders_2024_q4", 20241001, 20241231),
    ]:
        rows = []
        for i in range(1, 1001):
            date_key = rng.randint(q_start, q_end)
            rows.append((
                (hash(q_name) % 1_000_000) + i,
                rng.randint(1, 1000),
                date_key,
                round(rng.uniform(10.0, 500.0), 2),
            ))
        q.executemany(
            f"INSERT INTO {q_name} VALUES (?, ?, ?, ?)", rows
        )

    # The union view.
    q.execute("""
        CREATE VIEW fact_orders AS
        SELECT * FROM fact_orders_2024_q1
        UNION ALL
        SELECT * FROM fact_orders_2024_q2
        UNION ALL
        SELECT * FROM fact_orders_2024_q3
        UNION ALL
        SELECT * FROM fact_orders_2024_q4
    """)


def benchmark_range_partition(
    q: QueryRunner, use_pruning: bool
) -> Dict[str, float]:
    """Benchmark range-partitioned fact with/without pruning.

    Pruning means the query only scans the relevant
    partition. Without pruning, the query scans all four
    partitions. The benchmark is on a date-range filter.
    """
    _build_range_partitions(q)
    if use_pruning:
        # Pruning: query only the relevant partition.
        sql = (
            "SELECT COUNT(*) AS n, SUM(amount) AS total "
            "FROM fact_orders_2024_q1 "
            "WHERE date_key BETWEEN 20240201 AND 20240228"
        )
    else:
        # No pruning: query the full union view.
        sql = (
            "SELECT COUNT(*) AS n, SUM(amount) AS total "
            "FROM fact_orders "
            "WHERE date_key BETWEEN 20240201 AND 20240228"
        )
    t0 = time.perf_counter()
    res = q.query_all(sql)
    return {
        "scan_ms": (time.perf_counter() - t0) * 1000,
        "rows": res[0]["n"],
        "total": res[0]["total"],
    }


# ---- hash partitioning ---------------------------------------------------


def _build_hash_partitions(q: QueryRunner) -> None:
    """Build a hash-partitioned fact table.

    Four partitions, hashed by customer_key mod 4. Each
    partition has ~1/4 of the data.
    """
    import random
    rng = random.Random(42)
    for shard in range(4):
        t = Table(f"fact_orders_shard_{shard}", [
            Column("order_key", "INTEGER", primary_key=True),
            Column("customer_key", "INTEGER", nullable=False),
            Column("date_key", "INTEGER", nullable=False),
            Column("amount", "REAL", nullable=False),
        ])
        q.execute(t.to_ddl())

    rows_per_shard = {i: [] for i in range(4)}
    for i in range(1, 4001):
        cust = rng.randint(1, 1000)
        shard = cust % 4
        rows_per_shard[shard].append((
            i,
            cust,
            20240101 + (i % 365),
            round(rng.uniform(10.0, 500.0), 2),
        ))
    for shard, rows in rows_per_shard.items():
        q.executemany(
            f"INSERT INTO fact_orders_shard_{shard} "
            f"VALUES (?, ?, ?, ?)",
            rows,
        )

    q.execute("""
        CREATE VIEW fact_orders AS
        SELECT * FROM fact_orders_shard_0
        UNION ALL SELECT * FROM fact_orders_shard_1
        UNION ALL SELECT * FROM fact_orders_shard_2
        UNION ALL SELECT * FROM fact_orders_shard_3
    """)


def benchmark_hash_partition(
    q: QueryRunner, use_pruning: bool
) -> Dict[str, float]:
    """Benchmark hash-partitioned fact with/without pruning.

    Pruning: query only the relevant shard.
    No pruning: query the full view.
    """
    _build_hash_partitions(q)
    if use_pruning:
        # Hash-pruning requires the caller to know which
        # shard to query (they apply the same hash).
        target_customer = 42
        target_shard = target_customer % 4
        sql = (
            f"SELECT COUNT(*) AS n, SUM(amount) AS total "
            f"FROM fact_orders_shard_{target_shard} "
            f"WHERE customer_key = {target_customer}"
        )
    else:
        sql = (
            "SELECT COUNT(*) AS n, SUM(amount) AS total "
            "FROM fact_orders WHERE customer_key = 42"
        )
    t0 = time.perf_counter()
    res = q.query_all(sql)
    return {
        "scan_ms": (time.perf_counter() - t0) * 1000,
        "rows": res[0]["n"],
        "total": res[0]["total"],
    }


# ---- list partitioning ---------------------------------------------------


def _build_list_partitions(q: QueryRunner) -> None:
    """Build a list-partitioned fact table by country."""
    import random
    rng = random.Random(42)
    countries = {
        "amer": ["US", "CA", "MX", "BR"],
        "emea": ["UK", "DE", "FR", "AU"],
        "apac": ["IN", "JP"],
    }
    for region, _ in countries.items():
        t = Table(f"fact_orders_{region}", [
            Column("order_key", "INTEGER", primary_key=True),
            Column("customer_key", "INTEGER", nullable=False),
            Column("country", "TEXT", nullable=False),
            Column("amount", "REAL", nullable=False),
        ])
        q.execute(t.to_ddl())

    rows_per_region = {r: [] for r in countries}
    for i in range(1, 4001):
        country = rng.choice(
            countries["amer"] + countries["emea"] + countries["apac"]
        )
        region = next(
            r for r, cs in countries.items() if country in cs
        )
        rows_per_region[region].append((
            i, rng.randint(1, 1000), country,
            round(rng.uniform(10.0, 500.0), 2),
        ))
    for region, rows in rows_per_region.items():
        q.executemany(
            f"INSERT INTO fact_orders_{region} "
            f"VALUES (?, ?, ?, ?)",
            rows,
        )

    q.execute("""
        CREATE VIEW fact_orders AS
        SELECT * FROM fact_orders_amer
        UNION ALL SELECT * FROM fact_orders_emea
        UNION ALL SELECT * FROM fact_orders_apac
    """)


def benchmark_list_partition(
    q: QueryRunner, use_pruning: bool
) -> Dict[str, float]:
    """Benchmark list-partitioned fact with/without pruning."""
    _build_list_partitions(q)
    if use_pruning:
        sql = (
            "SELECT COUNT(*) AS n, SUM(amount) AS total "
            "FROM fact_orders_amer WHERE country = 'US'"
        )
    else:
        sql = (
            "SELECT COUNT(*) AS n, SUM(amount) AS total "
            "FROM fact_orders WHERE country = 'US'"
        )
    t0 = time.perf_counter()
    res = q.query_all(sql)
    return {
        "scan_ms": (time.perf_counter() - t0) * 1000,
        "rows": res[0]["n"],
        "total": res[0]["total"],
    }


# ---- demo ----------------------------------------------------------------


if __name__ == "__main__":
    print("Partitioning benchmarks:\n")
    print("Range partitioning (4 quarterly partitions):")
    for pruning in (False, True):
        with QueryRunner(":memory:") as q:
            res = benchmark_range_partition(q, use_pruning=pruning)
            print(
                f"   pruning={pruning}  "
                f"scan={res['scan_ms']:.2f}ms  "
                f"rows={res['rows']}"
            )

    print("\nHash partitioning (4 shards, mod 4):")
    for pruning in (False, True):
        with QueryRunner(":memory:") as q:
            res = benchmark_hash_partition(q, use_pruning=pruning)
            print(
                f"   pruning={pruning}  "
                f"scan={res['scan_ms']:.2f}ms  "
                f"rows={res['rows']}"
            )

    print("\nList partitioning (3 regions):")
    for pruning in (False, True):
        with QueryRunner(":memory:") as q:
            res = benchmark_list_partition(q, use_pruning=pruning)
            print(
                f"   pruning={pruning}  "
                f"scan={res['scan_ms']:.2f}ms  "
                f"rows={res['rows']}"
            )
