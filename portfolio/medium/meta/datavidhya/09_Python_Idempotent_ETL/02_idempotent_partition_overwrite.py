"""
Problem 02: Make a partitioned write idempotent (re-runnable without duplicates).

Meta flavor: "The 2am job failed halfway and got retried. Why is revenue now
double, and how do you make that impossible?"

How to Think:
- APPEND is not idempotent. Retry an appending job and you get duplicate rows
  with no error and no alert. This is the most common production data bug.
- Three ways to make a write idempotent, in increasing sophistication:
    1. Overwrite the WHOLE table                 - safe, wasteful, no history
    2. Overwrite only the affected PARTITIONS    - the standard answer
    3. MERGE on a primary key (Delta/Iceberg)    - needed for late-arriving
                                                   updates to old partitions
- Option 2 requires `spark.sql.sources.partitionOverwriteMode = dynamic`.
  Without it, `mode("overwrite")` on a partitioned path wipes the ENTIRE table,
  not just the partitions in your DataFrame. That default has destroyed a lot
  of real warehouses. Knowing this flag by name is the signal.

How to Remember:
- "Append breaks on retry. Dynamic partition overwrite is the fix. MERGE when
  old partitions can change."

This file PROVES the property: it writes the same day twice and asserts the row
count does not grow, then appends the same data to show the count doubling.
"""
import os
import shutil
import tempfile

from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("idempotent-partition-overwrite")
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
out = os.path.join(tempfile.mkdtemp(prefix="idem_"), "orders")

day = spark.sql("SELECT * FROM orders WHERE order_date = '2026-01-01'")
n_src = day.count()


def load(df, mode):
    df.write.mode(mode).partitionBy("order_date").parquet(out)


# First load, then an identical retry using dynamic partition overwrite.
load(day, "overwrite")
after_first = spark.read.parquet(out).count()
load(day, "overwrite")
after_retry = spark.read.parquet(out).count()

assert after_first == n_src, f"first load wrong: {after_first} != {n_src}"
assert after_retry == n_src, f"NOT idempotent: {after_retry} != {n_src}"
print(f"[PASS] overwrite is idempotent — {n_src} rows after load, "
      f"{after_retry} after retry")

# Now demonstrate the bug that append would have caused.
load(day, "append")
after_append = spark.read.parquet(out).count()
assert after_append == n_src * 2, f"expected doubling, got {after_append}"
print(f"[PASS] append duplicates on retry — {n_src} rows became {after_append}")

# Loading a DIFFERENT partition must not disturb the first one.
load(day, "overwrite")                                   # reset to clean state
other = spark.sql("SELECT * FROM orders WHERE order_date = '2026-01-03'")
load(other, "overwrite")
both = spark.read.parquet(out)
# NOTE: Spark INFERS partition-column types when reading a partitioned path, so
# the string 'order_date' we wrote comes back as a date. str() it before
# comparing — this catches people out constantly.
dates = sorted(str(r["order_date"]) for r in both.select("order_date").distinct().collect())
assert dates == ["2026-01-01", "2026-01-03"], f"partition clobbered: {dates}"
print(f"[PASS] dynamic mode preserved the untouched partition — {dates}")

# ---- MySQL way ----------------------------------------------------------
# "APPEND on a retry is the most common production data bug." MySQL has no
# Spark-style dynamic partition overwrite; equivalent patterns:
#
# CREATE TABLE + sample data:
#   CREATE TABLE orders (
#       order_id     INT PRIMARY KEY,
#       buyer_id     INT,
#       seller_id    INT,
#       order_date   DATE NOT NULL,
#       gross_amount DECIMAL(10,2),
#       status       VARCHAR(20),
#       KEY idx_orders_date (order_date)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO orders VALUES
#       (9001, 1, 501, '2026-01-01', 25.00, 'completed'),
#       (9002, 2, 502, '2026-01-01', 40.00, 'completed'),
#       (9003, 3, 501, '2026-01-02', 15.00, 'cancelled'),
#       (9004, 1, 503, '2026-01-03', 60.00, 'completed'),
#       (9005, 4, 502, '2026-01-08', 10.00, 'completed');
#
# Idempotent partition-equivalent: replace the day's rows only, in a single
# transaction. RUN THIS WRAPPED IN A TX so a mid-run failure rolls back.
#   START TRANSACTION;
#   DELETE FROM orders WHERE order_date = '2026-01-01';
#   INSERT INTO orders (order_id, buyer_id, seller_id, order_date, gross_amount, status)
#   SELECT order_id, buyer_id, seller_id, order_date, gross_amount, status
#   FROM orders_stage
#   WHERE order_date = '2026-01-01';
#   COMMIT;
# Re-runnable. Retries with identical source data leave row count unchanged.
#
# Per-day idempotent upsert for full late-arriving updates to old partitions
# (the equivalent of Delta/Iceberg MERGE, MySQL 8.0+):
#   INSERT INTO orders (order_id, buyer_id, seller_id, order_date, gross_amount, status)
#   SELECT order_id, buyer_id, seller_id, order_date, gross_amount, status
#   FROM orders_stage
#   ON DUPLICATE KEY UPDATE
#       buyer_id     = VALUES(buyer_id),
#       seller_id    = VALUES(seller_id),
#       gross_amount = VALUES(gross_amount),
#       status       = VALUES(status);
# Choose option 1 (DELETE+INSERT in a TX) for whole-day refresh; option 2
# (ON DUPLICATE KEY UPDATE) when old partitions can change row-by-row.
# Note: without a TX wrapper around DELETE+INSERT, a crash mid-load leaves
# a hole — always wrap the swap.

shutil.rmtree(os.path.dirname(out), ignore_errors=True)
