"""
Shared Spark session + seed tables for every problem in this folder.

Why this exists: 110 problem files should not each repeat 30 lines of
createDataFrame boilerplate. Each problem file does:

    from _common import spark, show
    show("D1 retention", "SELECT ...")

and gets a live session with every seed view already registered.

Run any problem file from ITS OWN folder — the sys.path shim below finds this
module two levels up:

    cd 02_Retention_Cohorts && ../../.env/bin/python 01_d1_retention.py

Seed data is deliberately tiny and hand-checkable so you can verify a query by
eye. Every table is Presto/Hive-compatible in shape (dates as strings, ints as
ints) because that is what Meta's warehouse looks like.
"""
import decimal
import os
import sys

# Let problem files in subfolders import this module.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_REPO_PY = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))),
    ".env", "bin", "python",
)
if os.path.exists(_REPO_PY):
    os.environ.setdefault("PYSPARK_PYTHON", _REPO_PY)

from pyspark.sql import SparkSession  # noqa: E402

spark = (
    SparkSession.builder
    .appName("meta-de-prep")
    .master("local[2]")
    .config("spark.sql.shuffle.partitions", "2")
    .config("spark.ui.enabled", "false")
    .config("spark.ui.showConsoleProgress", "false")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")


def _view(name, rows, cols):
    spark.createDataFrame(rows, cols).createOrReplaceTempView(name)


# ---------------------------------------------------------------------------
# dim_users — signup cohort per user. 8 users across 3 signup days.
# ---------------------------------------------------------------------------
_view("users", [
    (1, "2026-01-01", "organic",  "US"),
    (2, "2026-01-01", "paid",     "US"),
    (3, "2026-01-01", "organic",  "IN"),
    (4, "2026-01-02", "paid",     "US"),
    (5, "2026-01-02", "referral", "BR"),
    (6, "2026-01-02", "organic",  "IN"),
    (7, "2026-01-08", "paid",     "US"),
    (8, "2026-01-08", "organic",  "BR"),
], ["user_id", "signup_date", "channel", "country"])

# ---------------------------------------------------------------------------
# events — one row per user activity event. Drives retention/DAU/funnel.
# User 1: active D0,D1,D7  | User 2: D0 only | User 3: D0,D1
# User 4: D0,D1,D7        | User 5: D0      | User 6: D0,D1,D28
# User 7: D0              | User 8: D0,D1
# ---------------------------------------------------------------------------
_view("events", [
    (1, "2026-01-01", "open"),  (1, "2026-01-02", "open"),  (1, "2026-01-08", "open"),
    (2, "2026-01-01", "open"),
    (3, "2026-01-01", "open"),  (3, "2026-01-02", "open"),
    (4, "2026-01-02", "open"),  (4, "2026-01-03", "open"),  (4, "2026-01-09", "open"),
    (5, "2026-01-02", "open"),
    (6, "2026-01-02", "open"),  (6, "2026-01-03", "open"),  (6, "2026-01-30", "open"),
    (7, "2026-01-08", "open"),
    (8, "2026-01-08", "open"),  (8, "2026-01-09", "open"),
], ["user_id", "event_date", "event_name"])

# ---------------------------------------------------------------------------
# funnel_events — multi-step product funnel. Note user 3 skips a step and
# user 5 repeats one: both are deliberate traps.
# ---------------------------------------------------------------------------
_view("funnel_events", [
    (1, "view",     "2026-01-01 10:00:00"),
    (1, "message",  "2026-01-01 10:05:00"),
    (1, "purchase", "2026-01-01 10:20:00"),
    (2, "view",     "2026-01-01 11:00:00"),
    (2, "message",  "2026-01-01 11:30:00"),
    (3, "view",     "2026-01-01 12:00:00"),
    (3, "purchase", "2026-01-01 12:10:00"),   # skipped 'message'
    (4, "view",     "2026-01-02 09:00:00"),
    (5, "view",     "2026-01-02 09:30:00"),
    (5, "view",     "2026-01-02 09:40:00"),   # duplicate step
    (5, "message",  "2026-01-02 09:50:00"),
], ["user_id", "step", "event_ts"])

# ---------------------------------------------------------------------------
# ad_events — for CTR / rate questions. The integer-division trap lives here.
# ---------------------------------------------------------------------------
_view("ad_events", [
    (1, "fb",  "impression"), (1, "fb",  "impression"), (1, "fb",  "click"),
    (2, "ig",  "impression"), (2, "ig",  "click"),
    (3, "fb",  "impression"), (3, "fb",  "impression"), (3, "fb",  "impression"),
    (4, "ig",  "impression"), (4, "ig",  "impression"), (4, "ig",  "click"),
    (5, "wa",  "impression"),
], ["user_id", "app", "event_type"])

# ---------------------------------------------------------------------------
# raw_hits — timestamped hits for sessionization (30-min gap rule).
# User 1 has 2 sessions, user 2 has 1, user 3 has 3.
# ---------------------------------------------------------------------------
_view("raw_hits", [
    (1, "2026-01-01 10:00:00"), (1, "2026-01-01 10:10:00"), (1, "2026-01-01 10:25:00"),
    (1, "2026-01-01 12:00:00"), (1, "2026-01-01 12:05:00"),
    (2, "2026-01-01 08:00:00"), (2, "2026-01-01 08:20:00"),
    (3, "2026-01-01 09:00:00"),
    (3, "2026-01-01 11:00:00"),
    (3, "2026-01-01 15:00:00"), (3, "2026-01-01 15:29:00"),
], ["user_id", "hit_ts"])

# ---------------------------------------------------------------------------
# experiment — A/B assignment + per-user metric, for lift / t-stat questions.
# ---------------------------------------------------------------------------
_view("experiment", [
    (1, "control",   12.0), (2, "control",   9.0),  (3, "control",  11.0),
    (4, "control",   10.0), (5, "control",    8.0),
    (6, "treatment", 14.0), (7, "treatment", 13.0), (8, "treatment", 15.0),
    (9, "treatment", 12.0), (10, "treatment", 16.0),
], ["user_id", "variant", "metric"])

# ---------------------------------------------------------------------------
# posts / engagement — top-N, ranking, author rollups.
# ---------------------------------------------------------------------------
_view("posts", [
    (101, 1, 50, "2026-01-01"), (102, 1, 80, "2026-01-02"), (103, 1, 30, "2026-01-03"),
    (201, 2, 90, "2026-01-01"), (202, 2, 70, "2026-01-02"), (203, 2, 70, "2026-01-04"),
    (301, 3, 20, "2026-01-05"),
], ["post_id", "author_id", "engagement_score", "created_at"])

# ---------------------------------------------------------------------------
# orders — marketplace transactions, for GMV / conversion / SCD joins.
# ---------------------------------------------------------------------------
_view("orders", [
    (9001, 1, 501, "2026-01-01", 25.00, "completed"),
    (9002, 2, 502, "2026-01-01", 40.00, "completed"),
    (9003, 3, 501, "2026-01-02", 15.00, "cancelled"),
    (9004, 1, 503, "2026-01-03", 60.00, "completed"),
    (9005, 4, 502, "2026-01-08", 10.00, "completed"),
], ["order_id", "buyer_id", "seller_id", "order_date", "gross_amount", "status"])

# ---------------------------------------------------------------------------
# seller_changes — raw CDC feed for SCD Type 1/2/3 exercises.
# ---------------------------------------------------------------------------
_view("seller_changes", [
    (501, "casual",   "Bangkok", "2026-01-01"),
    (501, "power",    "Bangkok", "2026-01-05"),
    (501, "power",    "Chiang Mai", "2026-01-20"),
    (502, "business", "Singapore", "2026-01-01"),
    (503, "casual",   "Hanoi",  "2026-01-03"),
], ["seller_id", "tier", "city", "changed_on"])

ALL_VIEWS = [
    "users", "events", "funnel_events", "ad_events", "raw_hits",
    "experiment", "posts", "orders", "seller_changes",
]


def show(title, sql, n=30):
    """Run a query and print it under a labelled header."""
    print(f"\n=== {title} ===")
    spark.sql(sql).show(n, truncate=False)


def _norm(v):
    """
    Normalise a cell for comparison. Spark returns Decimal for ROUND() over a
    decimal expression and float for ROUND() over a double, so comparing against
    a plain Python number must not depend on which one came back.
    """
    if isinstance(v, decimal.Decimal):
        return float(v)
    if isinstance(v, float):
        return round(v, 6)
    return v


def expect(title, sql, expected_rows):
    """
    Run a query and assert its rows. Used so a 'solution' cannot silently rot:
    if the query stops producing the documented answer, the file fails loudly.
    `expected_rows` is a list of tuples compared in returned order.
    """
    got = [tuple(_norm(c) for c in r) for r in spark.sql(sql).collect()]
    exp = [tuple(_norm(c) for c in r) for r in expected_rows]
    status = "PASS" if got == exp else "FAIL"
    print(f"[{status}] {title}")
    if got != exp:
        print(f"   expected: {exp}")
        print(f"   got:      {got}")
        raise AssertionError(f"{title}: expected {exp}, got {got}")
    return got
