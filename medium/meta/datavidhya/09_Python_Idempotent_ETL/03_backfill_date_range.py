"""
Problem 03: Backfill a date range safely.

Meta flavor: "Product wants two years of this metric restated. Go."

How to Think - say these four things before writing any code:
  1. PARTITION-AT-A-TIME, not one giant job. A single job over 2 years either
     OOMs or, worse, fails at 80% and leaves the table half-written.
  2. Each partition write must be IDEMPOTENT (problem 02), so a retried or
     overlapping backfill cannot duplicate.
  3. BOUND THE CONCURRENCY. Twenty parallel backfill tasks will saturate the
     cluster and starve the production pipeline running on the same queue.
     Backfills should run at lower priority than the daily job.
  4. Make it RESUMABLE. Track which partitions are done so a failure at
     partition 300 of 700 resumes at 300, not at 1.
- Also worth raising: backfilling a metric DEFINITION change means the restated
  history will not match previously published numbers. That is a stakeholder
  conversation, not just a pipeline run — mentioning it is the product signal.

How to Remember:
- "Per partition, idempotent, bounded, resumable."

This file backfills each date independently, deliberately fails one partition to
prove resumability, then re-runs and asserts the final state is complete and
un-duplicated.
"""
import os
import shutil
import tempfile

from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("backfill-date-range")
         .master("local[2]")
         .config("spark.sql.shuffle.partitions", "2")
         .config("spark.ui.showConsoleProgress", "false")
         .getOrCreate())
spark.sparkContext.setLogLevel("ERROR")

# ---------------------------------------------------------- sample data
# orders(order_id, buyer_id, seller_id, order_date, gross_amount, status)
spark.createDataFrame(
    [
        (9001, 1, 501, "2026-01-01", 25.00, "completed"),
        (9002, 2, 502, "2026-01-01", 40.00, "completed"),
        (9003, 3, 501, "2026-01-02", 15.00, "cancelled"),
        (9004, 1, 503, "2026-01-03", 60.00, "completed"),
        (9005, 4, 502, "2026-01-08", 10.00, "completed"),
    ],
    ["order_id", "buyer_id", "seller_id", "order_date", "gross_amount", "status"]
).createOrReplaceTempView("orders")

spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
out = os.path.join(tempfile.mkdtemp(prefix="backfill_"), "orders")

DATES = ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-08"]
completed = set()          # stands in for a real run-ledger table


def backfill(date, fail_on=None):
    if date == fail_on:
        raise RuntimeError(f"simulated failure on {date}")
    (spark.sql(f"SELECT * FROM orders WHERE order_date = '{date}'")
        .write.mode("overwrite").partitionBy("order_date").parquet(out))
    completed.add(date)


# --- Attempt 1: fails partway through -------------------------------------
try:
    for d in DATES:
        backfill(d, fail_on="2026-01-03")
except RuntimeError as e:
    print(f"[expected] {e}")

assert completed == {"2026-01-01", "2026-01-02"}, completed
print(f"[PASS] failed mid-run; ledger records {len(completed)}/{len(DATES)} done")

# --- Attempt 2: resume only what is missing -------------------------------
for d in DATES:
    if d not in completed:
        backfill(d)

assert completed == set(DATES), completed
print(f"[PASS] resumed and completed all {len(DATES)} partitions")

# --- Verify: complete, and NOT duplicated despite the overlap -------------
got = spark.read.parquet(out)
expected = spark.sql(
    f"SELECT * FROM orders WHERE order_date IN ({','.join(repr(d) for d in DATES)})")
assert got.count() == expected.count(), f"{got.count()} != {expected.count()}"

# Spark infers partition-column types on read, so order_date returns as a date
# object rather than the string we wrote. Normalise before comparing.
dates = sorted(str(r["order_date"]) for r in got.select("order_date").distinct().collect())
assert dates == DATES, dates
print(f"[PASS] {got.count()} rows across {len(dates)} partitions, no duplicates")

# Re-running the whole backfill over already-done partitions must be a no-op.
for d in DATES:
    backfill(d)
assert spark.read.parquet(out).count() == expected.count()
print("[PASS] full re-run is a no-op — backfill is idempotent end to end")

shutil.rmtree(os.path.dirname(out), ignore_errors=True)
