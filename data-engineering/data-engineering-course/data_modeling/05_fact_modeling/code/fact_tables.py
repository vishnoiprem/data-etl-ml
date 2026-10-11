"""The four fact-table types, with builder functions for each.

A *fact* is a measurement. But not all facts are the same
shape. The Kimball taxonomy gives us four types:

  1. Transactional — one row per event.
  2. Periodic snapshot — one row per (entity, time period).
  3. Accumulating snapshot — one row per lifecycle, with
     columns for each milestone date.
  4. Factless fact — one row per event, but with no numeric
     measures; the fact exists to record the occurrence.

Each builder function in this module creates a working
SQLite example of one type, with sample data.

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""

from __future__ import annotations

from typing import List

from common import Column, QueryRunner, Table


# ---- 1. Transactional fact ----------------------------------------------


def build_transactional_fact(q: QueryRunner) -> List[str]:
    """Transactional fact: one row per event.

    Use when: each event is a discrete, atomic action that
    happens at a moment in time (an order, a click, a
    payment). The fact is append-only; no row is ever
    updated.

    Example: `fact_order_items` from the e-commerce schema
    (Module 03). One row per order line item.
    """
    dim_customer = Table("dim_customer", [
        Column("customer_key", "INTEGER", primary_key=True),
        Column("customer_id", "INTEGER", nullable=False),
        Column("name", "TEXT"),
    ])
    dim_product = Table("dim_product", [
        Column("product_key", "INTEGER", primary_key=True),
        Column("product_id", "INTEGER", nullable=False),
        Column("name", "TEXT"),
    ])
    dim_date = Table("dim_date", [
        Column("date_key", "INTEGER", primary_key=True),
        Column("date", "TEXT", nullable=False),
        Column("month", "INTEGER"),
        Column("year", "INTEGER"),
    ])
    fact = Table("fact_sales_transactional", [
        Column("txn_key", "INTEGER", primary_key=True),
        Column("customer_key", "INTEGER", nullable=False,
               references="dim_customer(customer_key)"),
        Column("product_key", "INTEGER", nullable=False,
               references="dim_product(product_key)"),
        Column("date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("quantity", "INTEGER", nullable=False),
        Column("unit_price", "REAL", nullable=False),
        Column("gross_amount", "REAL", nullable=False),
        Column("discount_amount", "REAL", nullable=False, default="0"),
        Column("net_amount", "REAL", nullable=False),
    ])
    tables = [dim_customer, dim_product, dim_date, fact]
    for t in tables:
        q.execute(t.to_ddl())

    q.executemany(
        "INSERT INTO dim_customer VALUES (?,?,?)",
        [(1, 101, "Alice"), (2, 102, "Bob")],
    )
    q.executemany(
        "INSERT INTO dim_product VALUES (?,?,?)",
        [(1, 201, "Widget"), (2, 202, "Gadget")],
    )
    q.executemany(
        "INSERT INTO dim_date VALUES (?,?,?,?)",
        [
            (20240101, "2024-01-01", 1, 2024),
            (20240115, "2024-01-15", 1, 2024),
            (20240201, "2024-02-01", 2, 2024),
        ],
    )
    q.executemany(
        "INSERT INTO fact_sales_transactional VALUES (?,?,?,?,?,?,?,?,?)",
        [
            (1, 1, 1, 20240101, 2, 50.0, 100.0, 0.0, 100.0),
            (2, 1, 2, 20240115, 1, 75.0, 75.0, 5.0, 70.0),
            (3, 2, 1, 20240201, 3, 50.0, 150.0, 0.0, 150.0),
        ],
    )
    return [t.name for t in tables]


# ---- 2. Periodic snapshot fact -----------------------------------------


def build_periodic_snapshot_fact(q: QueryRunner) -> List[str]:
    """Periodic snapshot: one row per (entity, time period).

    Use when: you need to know the state of an entity at
    regular intervals (a customer's MRR at end of each
    month, a product's inventory at end of each week, a
    user's follower count at end of each day).

    The grain is one row per (entity, period). The fact is
    *rebuilt* each period — the previous period's row stays
    but a new one is appended.

    Example: `fact_subscriptions_monthly` from the
    subscription SaaS schema (Lesson 09). One row per
    customer-month.
    """
    dim_customer = Table("dim_customer", [
        Column("customer_key", "INTEGER", primary_key=True),
        Column("customer_id", "INTEGER", nullable=False),
        Column("name", "TEXT"),
    ])
    dim_plan = Table("dim_plan", [
        Column("plan_key", "INTEGER", primary_key=True),
        Column("plan_id", "INTEGER", nullable=False),
        Column("name", "TEXT"),
    ])
    dim_date = Table("dim_date", [
        Column("date_key", "INTEGER", primary_key=True),
        Column("date", "TEXT", nullable=False),
        Column("month", "INTEGER"),
        Column("year", "INTEGER"),
    ])
    fact = Table("fact_subscription_monthly_snapshot", [
        Column("snapshot_key", "INTEGER", primary_key=True),
        Column("customer_key", "INTEGER", nullable=False,
               references="dim_customer(customer_key)"),
        Column("plan_key", "INTEGER", nullable=False,
               references="dim_plan(plan_key)"),
        Column("period_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("mrr", "REAL", nullable=False, default="0"),
        Column("is_active", "INTEGER", nullable=False, default="0"),
        Column("is_new", "INTEGER", nullable=False, default="0"),
        Column("is_churned", "INTEGER", nullable=False, default="0"),
    ])
    tables = [dim_customer, dim_plan, dim_date, fact]
    for t in tables:
        q.execute(t.to_ddl())

    q.executemany(
        "INSERT INTO dim_customer VALUES (?,?,?)",
        [(1, 101, "Alice"), (2, 102, "Bob"), (3, 103, "Carol")],
    )
    q.executemany(
        "INSERT INTO dim_plan VALUES (?,?,?)",
        [(1, 1, "free"), (2, 2, "pro"), (3, 3, "enterprise")],
    )
    q.executemany(
        "INSERT INTO dim_date VALUES (?,?,?,?)",
        [
            (20240131, "2024-01-31", 1, 2024),
            (20240229, "2024-02-29", 2, 2024),
            (20240331, "2024-03-31", 3, 2024),
        ],
    )
    q.executemany(
        "INSERT INTO fact_subscription_monthly_snapshot "
        "VALUES (?,?,?,?,?,?,?,?)",
        [
            # Alice: pro Jan, pro Feb, churned Mar
            (1, 1, 2, 20240131, 50.0, 1, 0, 0),
            (2, 1, 2, 20240229, 50.0, 1, 0, 0),
            (3, 1, 1, 20240331, 0.0, 0, 0, 1),
            # Bob: free Jan, upgraded to pro Feb, pro Mar
            (4, 2, 1, 20240131, 0.0, 1, 1, 0),
            (5, 2, 2, 20240229, 50.0, 1, 0, 0),
            (6, 2, 2, 20240331, 50.0, 1, 0, 0),
            # Carol: new pro Mar
            (7, 3, 2, 20240331, 50.0, 1, 1, 0),
        ],
    )
    return [t.name for t in tables]


# ---- 3. Accumulating snapshot fact --------------------------------------


def build_accumulating_snapshot_fact(q: QueryRunner) -> List[str]:
    """Accumulating snapshot: one row per lifecycle.

    Use when: each entity has a *known* lifecycle with
    distinct milestones (an order: ordered → paid → shipped
    → delivered; a job application: applied → screened →
    interviewed → offered → hired). The fact has one row per
    entity, and the columns are updated as the entity
    progresses.

    Example: a `fact_order_lifecycle` table with columns for
    each milestone date. When the order ships, the
    `ship_date_key` is set. When it delivers, the
    `delivery_date_key` is set.
    """
    dim_customer = Table("dim_customer", [
        Column("customer_key", "INTEGER", primary_key=True),
        Column("customer_id", "INTEGER", nullable=False),
        Column("name", "TEXT"),
    ])
    dim_date = Table("dim_date", [
        Column("date_key", "INTEGER", primary_key=True),
        Column("date", "TEXT", nullable=False),
    ])
    fact = Table("fact_order_accumulating_snapshot", [
        Column("order_key", "INTEGER", primary_key=True),
        Column("order_id", "INTEGER", nullable=False),
        Column("customer_key", "INTEGER", nullable=False,
               references="dim_customer(customer_key)"),
        # Each milestone date is a role-playing dim_date FK.
        Column("order_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("paid_date_key", "INTEGER",
               references="dim_date(date_key)"),
        Column("ship_date_key", "INTEGER",
               references="dim_date(date_key)"),
        Column("delivery_date_key", "INTEGER",
               references="dim_date(date_key)"),
        # Lag measures (computed at load time).
        Column("days_to_pay", "INTEGER"),
        Column("days_to_ship", "INTEGER"),
        Column("days_to_deliver", "INTEGER"),
        # Total order amount (set once at order time).
        Column("total_amount", "REAL", nullable=False),
    ])
    tables = [dim_customer, dim_date, fact]
    for t in tables:
        q.execute(t.to_ddl())

    q.executemany(
        "INSERT INTO dim_customer VALUES (?,?,?)",
        [(1, 101, "Alice"), (2, 102, "Bob")],
    )
    q.executemany(
        "INSERT INTO dim_date VALUES (?,?)",
        [
            (20240101, "2024-01-01"),
            (20240102, "2024-01-02"),
            (20240103, "2024-01-03"),
            (20240105, "2024-01-05"),
            (20240108, "2024-01-08"),
            (20240110, "2024-01-10"),
        ],
    )
    q.executemany(
        "INSERT INTO fact_order_accumulating_snapshot "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        [
            # Order 1: ordered Jan 1, paid Jan 2, shipped Jan 3,
            # delivered Jan 5. Lag: 1d to pay, 1d to ship,
            # 2d to deliver.
            (1, 1001, 1, 20240101, 20240102, 20240103, 20240105,
             1, 1, 2, 100.0),
            # Order 2: ordered Jan 3, paid Jan 5, shipped Jan 8,
            # delivered Jan 10. Lag: 2d to pay, 3d to ship,
            # 2d to deliver.
            (2, 1002, 2, 20240103, 20240105, 20240108, 20240110,
             2, 3, 2, 50.0),
            # Order 3: ordered Jan 5, paid Jan 8, in transit
            # (not yet delivered).
            (3, 1003, 1, 20240105, 20240108, 20240110, None,
             3, 2, None, 75.0),
        ],
    )
    return [t.name for t in tables]


# ---- 4. Factless fact table ---------------------------------------------


def build_factless_fact(q: QueryRunner) -> List[str]:
    """Factless fact: one row per event, no numeric measures.

    Use when: you need to record *that* an event happened, not
    measure it. Common cases:

    * Attendance: "user X attended event Y on date Z."
    * Coverage: "store S had product P in stock on date D."
    * Promotion eligibility: "user X was eligible for promo Y
      on date Z."

    The fact has only FKs and flags; the "measure" is the
    *existence* of the row.
    """
    dim_user = Table("dim_user", [
        Column("user_key", "INTEGER", primary_key=True),
        Column("user_id", "INTEGER", nullable=False),
        Column("name", "TEXT"),
    ])
    dim_event = Table("dim_event", [
        Column("event_key", "INTEGER", primary_key=True),
        Column("event_id", "INTEGER", nullable=False),
        Column("event_name", "TEXT", nullable=False),
    ])
    dim_date = Table("dim_date", [
        Column("date_key", "INTEGER", primary_key=True),
        Column("date", "TEXT", nullable=False),
    ])
    fact = Table("fact_attendance_factless", [
        Column("attendance_key", "INTEGER", primary_key=True),
        Column("user_key", "INTEGER", nullable=False,
               references="dim_user(user_key)"),
        Column("event_key", "INTEGER", nullable=False,
               references="dim_event(event_key)"),
        Column("date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
    ])
    tables = [dim_user, dim_event, dim_date, fact]
    for t in tables:
        q.execute(t.to_ddl())

    q.executemany(
        "INSERT INTO dim_user VALUES (?,?,?)",
        [
            (1, 101, "Alice"),
            (2, 102, "Bob"),
            (3, 103, "Carol"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_event VALUES (?,?,?)",
        [
            (1, 201, "Yoga class"),
            (2, 202, "Spin class"),
            (3, 203, "Pilates class"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_date VALUES (?,?)",
        [
            (20240115, "2024-01-15"),
            (20240116, "2024-01-16"),
            (20240117, "2024-01-17"),
        ],
    )
    q.executemany(
        "INSERT INTO fact_attendance_factless VALUES (?,?,?,?)",
        [
            (1, 1, 1, 20240115),  # Alice attended Yoga on Jan 15
            (2, 1, 2, 20240116),  # Alice attended Spin on Jan 16
            (3, 2, 1, 20240115),  # Bob attended Yoga on Jan 15
            (4, 2, 3, 20240117),  # Bob attended Pilates on Jan 17
            (5, 3, 2, 20240116),  # Carol attended Spin on Jan 16
        ],
    )
    return [t.name for t in tables]


# ---- demo ----------------------------------------------------------------


if __name__ == "__main__":
    print("Building 4 fact-table types...\n")
    for name, fn in [
        ("transactional", build_transactional_fact),
        ("periodic snapshot", build_periodic_snapshot_fact),
        ("accumulating snapshot", build_accumulating_snapshot_fact),
        ("factless", build_factless_fact),
    ]:
        with QueryRunner(":memory:") as q:
            tables = fn(q)
            print(f"[{name}]  tables: {tables}")
            for tn in tables:
                if tn.startswith("fact_"):
                    rows = q.query_all(f"SELECT * FROM {tn} LIMIT 1")
                    print(f"   {tn} sample: {rows[0]}")
        print()
