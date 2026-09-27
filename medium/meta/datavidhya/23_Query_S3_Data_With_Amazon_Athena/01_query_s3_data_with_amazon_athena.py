"""Q23: Query S3 Data with Amazon Athena    [AWS | Athena, S3, SQL, Trino]

A runnable, **offline-first** mirror of the AWS Skill Builder lab
"Query S3 Data with Amazon Athena." Six stages, seven shell scripts that
map exactly to the lab's "click in the console" steps, plus a pytest
suite that drives the same DuckDB-backed SQL. No AWS credentials needed
for verification.

How to think:
    Athena's "schema on read" model means the CSV never gets loaded into
    a database -- Athena scans the file at query time. The DDL just
    describes the columns. Offline we use DuckDB, whose
    ``read_csv_auto`` + ``CREATE TABLE … AS SELECT * FROM read_csv_auto``
    is the closest portable mirror. The SQL is intentionally Trino-
    compatible: ``CREATE DATABASE``, ``CREATE EXTERNAL TABLE``,
    ``GROUP BY`` with ``AVG``/``SUM``/``COUNT``, ``ORDER BY ... LIMIT``.

The trap:
    Athena charges per byte scanned. A query like
    ``SELECT * FROM yellow_taxi`` on the full table scans the whole CSV
    ($$$). A query that filters to ``WHERE payment_type='CRD'`` and
    selects only 3 columns scans a fraction. The lab is the first place
    you see "your table layout IS your cost" -- not a footnote.

AWS note:
    The lab pre-creates an Athena workgroup with a results location.
    ``CREATE EXTERNAL TABLE`` stores NO data; it stores a pointer to
    ``LOCATION 's3://…/taxi/'`` plus the schema. Drop the table and the
    CSV is untouched. Delete the bucket and the table is orphaned.
"""
from __future__ import annotations

import csv
import os
import sys
from typing import Any, Dict, List, Tuple

import duckdb

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE_CSV = os.path.join(HERE, "sample_data", "yellow_taxi_sample.csv")
DATABASE = "taxi_db"
TABLE = "taxi_trips"


# ============================================================ test harness
PASS, FAIL = "\u2713", "\u2717"
_results: List[Tuple[bool, str]] = []


def expect(title: str, ok: bool, detail: str = "") -> None:
    tag = PASS if ok else FAIL
    line = f"  [{tag}] {title}" + (f" -- {detail}" if detail else "")
    print(line)
    _results.append((ok, title))


def section(title: str) -> None:
    print(f"\n--- {title} ---")


# ============================================================ main
def run() -> int:
    con = duckdb.connect()                   # in-memory; equivalent to
                                              # "new Athena session"

    # ---------------------------------------------------------- stage 1
    section("Stage 1 -- inspect the S3 CSV (mirror `aws s3 cp ... | head`)")
    with open(SAMPLE_CSV, "r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)
    expect("CSV has 15 columns", len(header) == 15,
           f"got {len(header)}")
    expected_cols = ["vendor_id", "pickup_datetime", "dropoff_datetime",
                      "passenger_count", "trip_distance", "pickup_zone",
                      "dropoff_zone", "ratecode_id", "payment_type",
                      "fare_amount", "extra", "mta_tax", "tip_amount",
                      "tolls_amount", "total_amount"]
    expect("columns match Athena DDL", header == expected_cols,
           f"diff={set(expected_cols) ^ set(header)}")
    expect("CSV has 24 rows", len(rows) == 24, f"got {len(rows)}")
    expect("first row pickup zone is 'Midtown Center'",
           rows[0][5] == "Midtown Center")
    expect("first row payment_type is 'CRD'", rows[0][8] == "CRD")

    # ---------------------------------------------------------- stage 2
    section("Stage 2 -- pick workgroup + create database")
    # In production the workgroup is pre-created. Offline we just pick
    # one (a string) and assert the SQL-side schema can be created.
    # Note: DuckDB calls namespaces "schemas", not "databases" (each
    # DuckDB connection IS its own catalog). Athena's database == DuckDB
    # schema here.
    WORKGROUP = "taxi-playground-primary"
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {DATABASE}")
    schemas = [r[0] for r in con.execute(
        "SELECT schema_name FROM information_schema.schemata").fetchall()]
    expect(f"schema '{DATABASE}' created", DATABASE in schemas,
           f"schemas={schemas}")
    expect("workgroup choice is recorded", WORKGROUP.startswith("taxi-"))

    # ---------------------------------------------------------- stage 3
    section("Stage 3 -- create external table (schema on read)")
    # Athena's CREATE EXTERNAL TABLE never copies data. DuckDB's
    # equivalent is CREATE TABLE … AS SELECT * FROM read_csv_auto(...).
    # The result is the same: a table the SQL engine reads at query time.
    con.execute(f"DROP TABLE IF EXISTS {DATABASE}.{TABLE}")
    con.execute(f"""
        CREATE TABLE {DATABASE}.{TABLE} AS
        SELECT * FROM read_csv_auto('{SAMPLE_CSV}', header=true)
    """)
    cols = con.execute(f"DESCRIBE {DATABASE}.{TABLE}").fetchall()
    expect("external table has 15 columns", len(cols) == 15,
           f"got {len(cols)}")
    col_types = {name: dtype for name, dtype, *_ in cols}
    expect("pickup_datetime typed as timestamp",
           "TIMESTAMP" in col_types["pickup_datetime"].upper(),
           f"got {col_types['pickup_datetime']}")
    expect("total_amount typed as double",
           "DOUBLE" in col_types["total_amount"].upper(),
           f"got {col_types['total_amount']}")
    expect("payment_type typed as varchar",
           "VARCHAR" in col_types["payment_type"].upper(),
           f"got {col_types['payment_type']}")

    # ---------------------------------------------------------- stage 4
    section("Stage 4 -- run analytical queries")

    # Q1: row count.
    n = con.execute(f"SELECT COUNT(*) FROM {DATABASE}.{TABLE}").fetchone()[0]
    expect("SELECT COUNT(*) = 24", n == 24, f"got {n}")

    # Q2: trips + avg fare + avg tip per payment_type.
    q2 = con.execute(f"""
        SELECT payment_type, COUNT(*) AS trips,
               ROUND(AVG(fare_amount), 2) AS avg_fare,
               ROUND(AVG(tip_amount), 2)  AS avg_tip
        FROM {DATABASE}.{TABLE}
        GROUP BY payment_type
        ORDER BY trips DESC
    """).fetchall()
    expect("Q2 returns 4 payment_type buckets",
           len(q2) == 4, f"got {len(q2)}")
    payment_types_seen = {r[0] for r in q2}
    expect("Q2 payment_types include CRD/CSH/NOC/UNK",
           payment_types_seen == {"CRD", "CSH", "NOC", "UNK"},
           f"got {payment_types_seen}")
    crd_row = next(r for r in q2 if r[0] == "CRD")
    expect("CRD has nonzero avg_tip", crd_row[3] > 0,
           f"avg_tip={crd_row[3]}")
    csh_row = next(r for r in q2 if r[0] == "CSH")
    expect("CSH has zero avg_tip", csh_row[3] == 0,
           f"avg_tip={csh_row[3]}")

    # Q3: top 5 pickup zones by revenue.
    q3 = con.execute(f"""
        SELECT pickup_zone, ROUND(SUM(total_amount), 2) AS revenue
        FROM {DATABASE}.{TABLE}
        GROUP BY pickup_zone
        ORDER BY revenue DESC
        LIMIT 5
    """).fetchall()
    expect("Q3 returns 5 pickup zones", len(q3) == 5, f"got {len(q3)}")
    expect("Q3 top zone is one of Midtown/LaGuardia/JFK",
           q3[0][0] in {"Midtown Center", "LaGuardia Airport",
                          "JFK Airport"},
           f"got {q3[0][0]}")
    expect("Q3 revenue decreases monotonically",
           all(q3[i][1] >= q3[i + 1][1] for i in range(len(q3) - 1)))

    # Q4: per-day distribution.
    q4 = con.execute(f"""
        SELECT DATE(pickup_datetime) AS day, COUNT(*) AS trips
        FROM {DATABASE}.{TABLE}
        GROUP BY day
        ORDER BY day
    """).fetchall()
    expect("Q4 spans 3 distinct days", len(q4) == 3, f"got {len(q4)}")
    expect("Q4 day counts sum to 24",
           sum(r[1] for r in q4) == 24,
           f"sum={sum(r[1] for r in q4)}")
    expect("Q4 first day is 2026-08-15",
           str(q4[0][0]) == "2026-08-15", f"got {q4[0][0]}")

    # Q5: cash trips with zero tips (proves the cash/no-tip trap).
    q5 = con.execute(f"""
        SELECT COUNT(*) AS cash_zero_tip
        FROM {DATABASE}.{TABLE}
        WHERE payment_type='CSH' AND tip_amount=0
    """).fetchone()[0]
    expect("Q5 cash_zero_tip = 4", q5 == 4, f"got {q5}")

    # ---------------------------------------------------------- stage 5
    section("Stage 5 -- challenge query (top zone pairs)")
    q6 = con.execute(f"""
        SELECT pickup_zone, dropoff_zone,
               COUNT(*) AS trips,
               ROUND(AVG(trip_distance), 2) AS avg_miles
        FROM {DATABASE}.{TABLE}
        WHERE passenger_count > 0
        GROUP BY pickup_zone, dropoff_zone
        ORDER BY trips DESC
        LIMIT 5
    """).fetchall()
    expect("Q6 returns 5 zone pairs", len(q6) == 5, f"got {len(q6)}")
    pair_set = {(r[0], r[1]) for r in q6}
    # Midtown Center -> LaGuardia Airport should be among the top pairs.
    expect("Q6 includes Midtown Center -> LaGuardia Airport",
           ("Midtown Center", "LaGuardia Airport") in pair_set,
           f"pairs={pair_set}")
    expect("Q6 trips are >= 1 each",
           all(r[2] >= 1 for r in q6))

    # Bonus: NULL dropoff_zone handling (proves the schema-on-read
    # nullability).
    nulls = con.execute(f"""
        SELECT COUNT(*) FROM {DATABASE}.{TABLE}
        WHERE dropoff_zone IS NULL
    """).fetchone()[0]
    expect("1 row has NULL dropoff_zone", nulls == 1, f"got {nulls}")

    # Bonus: zero trip_distance (cancelled trip).
    cancelled = con.execute(f"""
        SELECT COUNT(*) FROM {DATABASE}.{TABLE}
        WHERE trip_distance = 0
    """).fetchone()[0]
    expect("1 row has trip_distance=0 (cancelled)", cancelled == 1,
           f"got {cancelled}")

    # Bonus: UNK payment_type is preserved (unknown enum).
    unk = con.execute(f"""
        SELECT COUNT(*) FROM {DATABASE}.{TABLE}
        WHERE payment_type='UNK'
    """).fetchone()[0]
    expect("1 row has payment_type='UNK'", unk == 1, f"got {unk}")

    # ---------------------------------------------------------- stage 6
    section("Stage 6 -- teardown (DROP SCHEMA)")
    con.execute(f"DROP SCHEMA {DATABASE} CASCADE")
    after = [r[0] for r in con.execute(
        "SELECT schema_name FROM information_schema.schemata").fetchall()]
    expect(f"schema '{DATABASE}' dropped", DATABASE not in after,
           f"remaining={after}")
    # CSV is untouched (schema-on-read guarantee).
    expect("CSV file still on disk",
           os.path.isfile(SAMPLE_CSV))
    expect("CSV still has 24 rows",
           len(open(SAMPLE_CSV, encoding="utf-8").readlines()) - 1 == 24)

    # ---------------------------------------------------------- summary
    total = len(_results)
    passed = sum(1 for ok, _ in _results if ok)
    print(f"\n=== {passed}/{total} checks passed ===")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(run())
