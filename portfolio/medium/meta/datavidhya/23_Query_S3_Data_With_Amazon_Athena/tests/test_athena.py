"""Offline pytest suite for the Athena lab -- DuckDB, no AWS.

Asserts:
    - Database/schema creation
    - External table has 15 columns with the right types
    - Row count + payment-type distribution
    - Cash-vs-tip trap (CSH trips have zero tips)
    - Per-day distribution
    - Challenge query zone pair
    - CSV is untouched by teardown (schema-on-read guarantee)
"""
from __future__ import annotations

from typing import Any, List, Tuple

import duckdb
import pytest


def _q(db: duckdb.DuckDBPyConnection, sql: str) -> List[Tuple[Any, ...]]:
    return db.execute(sql).fetchall()


def test_database_creation_succeeds(db) -> None:
    schemas = [r[0] for r in _q(
        db, "SELECT schema_name FROM information_schema.schemata")]
    assert "taxi_db" in schemas


def test_external_table_has_fifteen_columns(db, fully_qualified_table) -> None:
    cols = _q(db, f"DESCRIBE {fully_qualified_table}")
    assert len(cols) == 15


def test_external_table_column_types(db, fully_qualified_table) -> None:
    cols = _q(db, f"DESCRIBE {fully_qualified_table}")
    types = {name: dtype.upper() for name, dtype, *_ in cols}
    assert "TIMESTAMP" in types["pickup_datetime"]
    assert "DOUBLE" in types["total_amount"]
    assert "VARCHAR" in types["payment_type"]
    assert "INT" in types["passenger_count"]


def test_count_star_returns_twentyfour(db, fully_qualified_table) -> None:
    n = _q(db, f"SELECT COUNT(*) FROM {fully_qualified_table}")[0][0]
    assert n == 24


def test_payment_type_grouping_returns_four_buckets(
        db, fully_qualified_table) -> None:
    rows = _q(db, f"""
        SELECT payment_type, COUNT(*) AS trips
        FROM {fully_qualified_table}
        GROUP BY payment_type
    """)
    assert len(rows) == 4
    seen = {r[0] for r in rows}
    assert seen == {"CRD", "CSH", "NOC", "UNK"}


def test_credit_card_trips_have_nonzero_tips(
        db, fully_qualified_table) -> None:
    avg_tip = _q(db, f"""
        SELECT AVG(tip_amount) FROM {fully_qualified_table}
        WHERE payment_type='CRD'
    """)[0][0]
    assert avg_tip > 0


def test_cash_trips_have_zero_tips(db, fully_qualified_table) -> None:
    n_zero = _q(db, f"""
        SELECT COUNT(*) FROM {fully_qualified_table}
        WHERE payment_type='CSH' AND tip_amount=0
    """)[0][0]
    n_total = _q(db, f"""
        SELECT COUNT(*) FROM {fully_qualified_table}
        WHERE payment_type='CSH'
    """)[0][0]
    assert n_zero == n_total            # ALL cash trips have zero tips
    assert n_total > 0


def test_top_pickup_zone_by_revenue(db, fully_qualified_table) -> None:
    top = _q(db, f"""
        SELECT pickup_zone, SUM(total_amount) AS revenue
        FROM {fully_qualified_table}
        GROUP BY pickup_zone
        ORDER BY revenue DESC
        LIMIT 1
    """)[0]
    assert top[0] in {"Midtown Center", "JFK Airport", "LaGuardia Airport"}
    assert top[1] > 0


def test_per_day_distribution_has_three_days(db, fully_qualified_table) -> None:
    rows = _q(db, f"""
        SELECT DATE(pickup_datetime) AS day, COUNT(*) AS trips
        FROM {fully_qualified_table}
        GROUP BY day
        ORDER BY day
    """)
    assert len(rows) == 3
    assert sum(r[1] for r in rows) == 24


def test_challenge_query_zone_pair_appears_in_top_five(
        db, fully_qualified_table) -> None:
    rows = _q(db, f"""
        SELECT pickup_zone, dropoff_zone, COUNT(*) AS trips
        FROM {fully_qualified_table}
        WHERE passenger_count > 0
        GROUP BY pickup_zone, dropoff_zone
        ORDER BY trips DESC
        LIMIT 5
    """)
    pairs = {(r[0], r[1]) for r in rows}
    # Midtown Center is the busiest pickup zone; it should pair with
    # LaGuardia, JFK, Upper East Side, or itself.
    assert any(p[0] == "Midtown Center" for p in pairs)


def test_csv_untouched_after_drop(taxi_csv_path) -> None:
    """Schema-on-read guarantee: dropping the table leaves the file alone."""
    import os
    assert os.path.isfile(taxi_csv_path)
    with open(taxi_csv_path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()
    # 1 header + 24 data rows.
    assert len(lines) == 25


def test_null_dropoff_zone_is_preserved(db, fully_qualified_table) -> None:
    n = _q(db, f"""
        SELECT COUNT(*) FROM {fully_qualified_table}
        WHERE dropoff_zone IS NULL
    """)[0][0]
    assert n == 1


def test_zero_distance_cancelled_trip_is_preserved(
        db, fully_qualified_table) -> None:
    n = _q(db, f"""
        SELECT COUNT(*) FROM {fully_qualified_table}
        WHERE trip_distance = 0
    """)[0][0]
    assert n == 1


def test_unknown_payment_type_is_preserved(db, fully_qualified_table) -> None:
    n = _q(db, f"""
        SELECT COUNT(*) FROM {fully_qualified_table}
        WHERE payment_type='UNK'
    """)[0][0]
    assert n == 1