"""
Problem 02: SCD Type 2 — full history with effective_from / effective_to / is_current.

Meta flavor: "I need to attribute January sales to the tier the seller had AT
THE TIME, not their tier today."

How to Think - the whole pattern is one LEAD:
      effective_from = changed_on
      effective_to   = LEAD(changed_on) OVER (PARTITION BY key ORDER BY changed_on)
      is_current     = effective_to IS NULL
- Interval convention: [effective_from, effective_to) — inclusive start,
  EXCLUSIVE end. This matters enormously. With an inclusive end, a point-in-time
  join on the boundary date matches TWO versions and silently doubles your
  revenue. State the convention out loud; it is the detail that separates people
  who have built an SCD2 from people who have read about one.
- The open end should be NULL or a sentinel like '9999-12-31'. NULL is cleaner
  semantically; the sentinel makes BETWEEN joins simpler. Either is defensible
  if you say which and why.
- Point-in-time join then reads:
      ON f.event_date >= d.effective_from
     AND (f.event_date < d.effective_to OR d.effective_to IS NULL)

How to Remember:
- "effective_from + effective_to + is_current. LEAD gives you the end."

Spark note:
- One window per natural key. To MERGE new CDC rows into an existing SCD2 table
  you would use Delta MERGE: close the open row (set effective_to) and insert
  the new version in one transaction.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("02-scd-type2-history")
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

spark.createDataFrame(
    [
    (501, "casual",   "Bangkok", "2026-01-01"),
    (501, "power",    "Bangkok", "2026-01-05"),
    (501, "power",    "Chiang Mai", "2026-01-20"),
    (502, "business", "Singapore", "2026-01-01"),
    (503, "casual",   "Hanoi",  "2026-01-03"),
],
    ["seller_id", "tier", "city", "changed_on"]
).createOrReplaceTempView("seller_changes")


SQL = """
SELECT seller_id, tier, city,
       changed_on AS effective_from,
       LEAD(changed_on) OVER (PARTITION BY seller_id ORDER BY changed_on) AS effective_to,
       LEAD(changed_on) OVER (PARTITION BY seller_id ORDER BY changed_on) IS NULL AS is_current
FROM seller_changes
ORDER BY seller_id, effective_from
"""
expect("SCD2 versioned history", SQL, [
    (501, "casual", "Bangkok",    "2026-01-01", "2026-01-05", False),
    (501, "power",  "Bangkok",    "2026-01-05", "2026-01-20", False),
    (501, "power",  "Chiang Mai", "2026-01-20", None,         True),
    (502, "business", "Singapore", "2026-01-01", None,        True),
    (503, "casual",   "Hanoi",     "2026-01-03", None,        True),
])

# Point-in-time join: attribute each completed order to the tier in effect on
# the order date. Order 9004 (2026-01-03, seller 503) -> 'casual'.
# Orders for seller 501 on 01-01 and 01-02 -> 'casual' (pre 01-05 change).
expect("point-in-time tier attribution", """
WITH scd AS (
    SELECT seller_id, tier,
           changed_on AS eff_from,
           LEAD(changed_on) OVER (PARTITION BY seller_id ORDER BY changed_on) AS eff_to
    FROM seller_changes
)
SELECT o.order_id, o.seller_id, o.order_date, s.tier
FROM orders o
JOIN scd s
  ON s.seller_id = o.seller_id
 AND o.order_date >= s.eff_from
 AND (o.order_date < s.eff_to OR s.eff_to IS NULL)
ORDER BY o.order_id
""", [
    (9001, 501, "2026-01-01", "casual"),
    (9002, 502, "2026-01-01", "business"),
    (9003, 501, "2026-01-02", "casual"),
    (9004, 503, "2026-01-03", "casual"),
    (9005, 502, "2026-01-08", "business"),
])
