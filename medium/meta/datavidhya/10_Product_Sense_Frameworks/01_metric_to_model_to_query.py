"""
Problem 01: The metric -> behaviour -> grain -> query chain (Marketplace).

Meta flavor: "How would you measure the health of Facebook Marketplace?"

THIS IS THE ROUND. Meta's combined technical round chains exactly this:
define the metric, model the tables, write the query, then investigate a move.
The reported signature failure is a model that cannot serve the metric you
named two questions earlier — so derive them in that order, not backwards.

The fixed spine to say out loud (30 seconds, every time):
  1. USER VALUE  - "Marketplace works when people find things worth buying
                    from sellers they trust."
  2. BEHAVIOUR   - the behaviour that PROVES it is completed transactions with
                    repeat buyers, not listing counts or page views.
  3. METRIC      - ONE primary + ONE guardrail:
                     primary   = weekly completed-order GMV per active buyer
                     guardrail = cancellation rate
                    Do NOT recite ten metrics. Pick, then defend.
  4. GRAIN       - "one row per order" for the fact; buyer/seller/date as dims.
  5. QUERY       - write it against the grain you just declared.

Why a guardrail: GMV alone is gameable and can rise while the product rots —
a spike in orders that all cancel is a worse product and a better GMV number.
Naming the guardrail unprompted is the strongest single product signal here.

Spark note:
- Filter to completed BEFORE aggregating; cancellations must never enter GMV.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("01-metric-to-model-to-query")
         .master("local[2]")
         .config("spark.sql.shuffle.partitions", "2")
         .config("spark.ui.showConsoleProgress", "false")
         .getOrCreate())
spark.sparkContext.setLogLevel("ERROR")


def expect(title, sql, expected_rows):
    """Run a query and assert its exact rows, in order. Decimal/float safe."""
    import decimal

    def norm(v):
        if isinstance(v, decimal.Decimal):
            return float(v)
        if isinstance(v, float):
            return round(v, 6)
        return v

    got = [tuple(norm(c) for c in r) for r in spark.sql(sql).collect()]
    exp = [tuple(norm(c) for c in r) for r in expected_rows]
    if got != exp:
        print(f"[FAIL] {title}")
        print(f"   expected: {exp}")
        print(f"   got:      {got}")
        raise AssertionError(title)
    print(f"[PASS] {title}")
    return got


# ---------------------------------------------------------- sample data
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

from pyspark.sql import functions as F

# PRIMARY metric at the declared grain (one row per order).
expect("primary: daily completed GMV", """
SELECT order_date,
       COUNT(*) AS completed_orders,
       ROUND(SUM(gross_amount), 2) AS gmv
FROM orders
WHERE status = 'completed'
GROUP BY order_date
ORDER BY order_date
""", [
    ("2026-01-01", 2, 65.00),
    ("2026-01-03", 1, 60.00),
    ("2026-01-08", 1, 10.00),
])

# GUARDRAIL: cancellation rate over ALL orders, not just completed ones.
# Denominator choice is the whole point — completed-only would always give 0%.
expect("guardrail: cancellation rate", """
SELECT COUNT(*) AS all_orders,
       SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled,
       ROUND(100.0 * AVG(CASE WHEN status = 'cancelled' THEN 1.0 ELSE 0.0 END), 2)
           AS cancel_rate_pct
FROM orders
""", [(5, 1, 20.00)])

# The composite the primary metric actually names: GMV per active buyer.
expect("primary: GMV per active buyer", """
SELECT COUNT(DISTINCT buyer_id) AS active_buyers,
       ROUND(SUM(gross_amount), 2) AS gmv,
       ROUND(SUM(gross_amount) / COUNT(DISTINCT buyer_id), 2) AS gmv_per_buyer
FROM orders WHERE status = 'completed'
""", [(3, 135.00, 45.00)])


# ===========================================================================
# PySpark DataFrame API — same three questions, expressed with DataFrame ops.
# Each block finishes with assert so a drift between SQL and DataFrame results
# fails the file loudly. We do this so the canonical query above and the
# DataFrame rewrite cannot silently disagree.
# ===========================================================================
orders_df = spark.table("orders")

# PRIMARY 1: daily completed GMV.
# Note .filter() BEFORE .groupBy() — same rule as the WHERE in SQL: never let
# cancellations reach the GMV aggregator.
daily_gmv_df = (orders_df
                .filter(F.col("status") == "completed")
                .groupBy("order_date")
                .agg(F.count(F.lit(1)).alias("completed_orders"),
                     F.round(F.sum("gross_amount"), 2).alias("gmv"))
                .orderBy("order_date"))
assert [tuple(r) for r in daily_gmv_df.collect()] == [
    ("2026-01-01", 2, 65.00),
    ("2026-01-03", 1, 60.00),
    ("2026-01-08", 1, 10.00),
]
print("[PASS] primary: daily completed GMV — DataFrame API matches SQL")

# GUARDRAIL: cancellation rate. Denominator is ALL orders, not completed-only.
# AVG(CASE WHEN ... 1.0 ELSE 0.0 END) collapses to a single pass over the table
# and avoids the divide-then-multiply dance.
cancel_df = (orders_df
             .agg(F.count(F.lit(1)).alias("all_orders"),
                  F.sum(F.when(F.col("status") == "cancelled", 1).otherwise(0))
                      .alias("cancelled"),
                  F.round(
                      100.0 * F.avg(F.when(F.col("status") == "cancelled",
                                           F.lit(1.0)).otherwise(0.0)),
                      2
                  ).alias("cancel_rate_pct")))
assert [tuple(r) for r in cancel_df.collect()] == [(5, 1, 20.00)]
print("[PASS] guardrail: cancellation rate — DataFrame API matches SQL")

# PRIMARY 2: GMV per active buyer. Filter FIRST, then aggregate, so the
# denominator is "buyers with at least one completed order".
gmv_per_buyer_df = (orders_df
                    .filter(F.col("status") == "completed")
                    .agg(F.countDistinct("buyer_id").alias("active_buyers"),
                         F.round(F.sum("gross_amount"), 2).alias("gmv"),
                         F.round(
                             F.sum("gross_amount") / F.countDistinct("buyer_id"),
                             2
                         ).alias("gmv_per_buyer")))
assert [tuple(r) for r in gmv_per_buyer_df.collect()] == [(3, 135.00, 45.00)]
print("[PASS] primary: GMV per active buyer — DataFrame API matches SQL")
