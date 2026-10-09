"""dbt-style SQL transformations.

This module implements five dbt-style models as Python functions
that run SQL against a :class:`common.QueryRunner`:

  * ``stg_orders``        — staging for the raw ``orders`` table
  * ``stg_users``         — staging for the raw ``users`` table
  * ``int_orders_with_user`` — intermediate join
  * ``fct_orders_daily``  — daily fact aggregation
  * ``dim_users_scd2``    — SCD2 dimension

Each function is *idempotent*: running it twice produces the same
result. The staging models use ``CREATE TABLE IF NOT EXISTS``;
the downstream models use ``CREATE OR REPLACE TABLE``.

The model SQL is intentionally explicit (no Jinja, no ``ref``)
so it can be read top-to-bottom by someone who has never used
dbt.

Author: Prem Vishnoi <prem.vishnoi@example.com>
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from common import QueryRunner, Table, Column, create_table_sqlite


# ---- ddl helpers ------------------------------------------------------


def _ensure_seed_tables(q: QueryRunner) -> None:
    """Create and seed the raw tables that the models read from.

    Called automatically by ``build_all`` if the tables don't
    exist. Useful for tests.
    """
    raw_orders = Table("raw_orders", [
        Column("order_id", "INTEGER", primary_key=True),
        Column("user_id", "INTEGER", nullable=False),
        Column("order_date", "TEXT", nullable=False),
        Column("total", "REAL", nullable=False),
        Column("status", "TEXT", nullable=False),
    ])
    raw_users = Table("raw_users", [
        Column("id", "INTEGER", primary_key=True),
        Column("name", "TEXT", nullable=False),
        Column("email", "TEXT", nullable=False),
        Column("country", "TEXT", nullable=False),
        Column("signup_date", "TEXT", nullable=False),
        Column("updated_at", "TEXT", nullable=False),
    ])
    q.execute(create_table_sqlite(raw_orders))
    q.execute(create_table_sqlite(raw_users))

    # Only seed if the table is empty (idempotent re-runs).
    existing = q.query_one("SELECT COUNT(*) AS n FROM raw_orders")["n"]
    if existing:
        return

    # Seed deterministic sample data. The exact numbers are
    # unimportant; we just need enough variety to exercise
    # the joins and aggregations.
    sample_orders = [
        # (order_id, user_id, order_date, total, status)
        (1, 1, "2024-01-15T10:00:00Z", 50.00, "paid"),
        (2, 1, "2024-01-20T11:00:00Z", 30.00, "shipped"),
        (3, 2, "2024-01-21T12:00:00Z", 75.00, "delivered"),
        (4, 3, "2024-01-22T13:00:00Z", 22.00, "cancelled"),
        (5, 2, "2024-01-22T14:00:00Z", 18.00, "paid"),
        (6, 4, "2024-01-23T15:00:00Z", 99.00, "pending"),
        (7, 1, "2024-01-23T16:00:00Z", 12.00, "refunded"),
    ]
    q.executemany(
        "INSERT INTO raw_orders VALUES (?, ?, ?, ?, ?)",
        sample_orders,
    )

    sample_users = [
        # (id, name, email, country, signup_date, updated_at)
        (1, "Alice", "alice@x.com", "US", "2022-03-01", "2024-01-01T00:00:00Z"),
        (2, "Bob",   "bob@x.com",   "UK", "2022-05-15", "2024-01-01T00:00:00Z"),
        (3, "Carol", "carol@x.com", "DE", "2023-01-20", "2024-01-01T00:00:00Z"),
        (4, "Dan",   "dan@x.com",   "US", "2023-08-12", "2024-01-01T00:00:00Z"),
    ]
    q.executemany(
        "INSERT INTO raw_users VALUES (?, ?, ?, ?, ?, ?)",
        sample_users,
    )


# ---- the five models -------------------------------------------------


def _create_or_replace(q: QueryRunner, table: str, select_sql: str) -> None:
    """Drop ``table`` if it exists, then ``CREATE TABLE AS select_sql``.

    SQLite doesn't support ``CREATE OR REPLACE TABLE``, so we
    simulate it with DROP + CREATE. The dbt equivalent is
    ``{{ config(materialized='table') }}`` with a full refresh.
    """
    q.execute(f'DROP TABLE IF EXISTS "{table}"')
    q.execute(f"CREATE TABLE \"{table}\" AS {select_sql}")


def stg_orders(q: QueryRunner) -> int:
    """Staging model for orders: rename, type, no business logic."""
    _create_or_replace(
        q,
        "stg_orders",
        """
        SELECT
          CAST(order_id AS INTEGER) AS order_id,
          CAST(user_id AS INTEGER) AS user_id,
          CAST(order_date AS TEXT) AS order_date,
          CAST(total AS REAL) AS total,
          CAST(status AS TEXT) AS status
        FROM raw_orders
        """,
    )
    return q.query_one("SELECT COUNT(*) AS n FROM stg_orders")["n"]


def stg_users(q: QueryRunner) -> int:
    """Staging model for users: rename, type, no business logic."""
    _create_or_replace(
        q,
        "stg_users",
        """
        SELECT
          CAST(id AS INTEGER) AS id,
          CAST(name AS TEXT) AS name,
          CAST(email AS TEXT) AS email,
          CAST(country AS TEXT) AS country,
          CAST(signup_date AS TEXT) AS signup_date,
          CAST(updated_at AS TEXT) AS updated_at
        FROM raw_users
        """,
    )
    return q.query_one("SELECT COUNT(*) AS n FROM stg_users")["n"]


def int_orders_with_user(q: QueryRunner) -> int:
    """Intermediate model: orders joined to users."""
    _create_or_replace(
        q,
        "int_orders_with_user",
        """
        SELECT
          o.order_id,
          o.user_id,
          o.order_date,
          DATE(o.order_date) AS order_day,
          o.total,
          o.status,
          u.email,
          u.country,
          u.signup_date
        FROM stg_orders o
        LEFT JOIN stg_users u ON o.user_id = u.id
        """,
    )
    return q.query_one("SELECT COUNT(*) AS n FROM int_orders_with_user")["n"]


def fct_orders_daily(q: QueryRunner) -> int:
    """Fact model: daily revenue by country. Grain: (order_day, country)."""
    _create_or_replace(
        q,
        "fct_orders_daily",
        """
        SELECT
          order_day,
          country,
          COUNT(*) AS order_count,
          COUNT(DISTINCT user_id) AS unique_buyers,
          SUM(total) AS revenue
        FROM int_orders_with_user
        WHERE status IN ('paid', 'shipped', 'delivered')
        GROUP BY 1, 2
        """,
    )
    return q.query_one("SELECT COUNT(*) AS n FROM fct_orders_daily")["n"]


def dim_users_scd2(q: QueryRunner) -> int:
    """SCD2 dimension for users. Grain: (user_id, valid_from)."""
    _create_or_replace(
        q,
        "dim_users_scd2",
        """
        WITH base AS (
          SELECT
            id AS user_id,
            name,
            email,
            country,
            signup_date,
            updated_at
          FROM stg_users
        ),
        with_lead AS (
          SELECT
            user_id,
            name,
            email,
            country,
            signup_date,
            updated_at AS valid_from,
            LEAD(updated_at) OVER (
              PARTITION BY user_id ORDER BY updated_at
            ) AS next_valid_from
          FROM base
        )
        SELECT
          user_id,
          name,
          email,
          country,
          signup_date,
          valid_from,
          COALESCE(next_valid_from, '9999-12-31') AS valid_to,
          CASE WHEN next_valid_from IS NULL THEN 1 ELSE 0 END AS is_current
        FROM with_lead
        """,
    )
    return q.query_one("SELECT COUNT(*) AS n FROM dim_users_scd2")["n"]


# ---- orchestration ---------------------------------------------------


def build_all(q: QueryRunner) -> Dict[str, int]:
    """Build all five models in dependency order.

    Returns a dict of model name → row count.
    """
    _ensure_seed_tables(q)
    counts: Dict[str, int] = {}
    counts["stg_orders"] = stg_orders(q)
    counts["stg_users"] = stg_users(q)
    counts["int_orders_with_user"] = int_orders_with_user(q)
    counts["fct_orders_daily"] = fct_orders_daily(q)
    counts["dim_users_scd2"] = dim_users_scd2(q)
    return counts
