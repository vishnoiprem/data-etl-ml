"""
Q20: Conversion Rate from View to Lead by Location   [Medium | Joins, Aggregation]

For a housing marketplace, view-to-lead conversion rate by location.

How to Think:
- Two independent fact tables at different grains. Aggregate EACH to the common
  grain (location) FIRST, then join. Joining the raw facts multiplies rows:
  4 Bangkok views x 2 Bangkok leads = 8 rows, and every count is then wrong.
  This fan-out is the most common way this question is failed.
- LEFT JOIN from views to leads so a location with views and zero leads still
  reports 0.00% instead of vanishing.
- COALESCE the lead count to 0 before dividing, or the rate comes back NULL.

The trap:
- Manila has 1 view and 0 leads. An INNER JOIN drops it entirely and the
  dashboard silently loses a market.

Spark note:
- Pre-aggregating both sides shrinks them to one row per location, so the join
  becomes a broadcast instead of a shuffle-hash join. This "aggregate then
  join" instinct is exactly what a Meta pipeline-design follow-up probes.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("20-view-to-lead-conversion")
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
    (1, "Bangkok"), (2, "Bangkok"), (3, "Bangkok"), (4, "Bangkok"),
    (5, "Hanoi"), (6, "Hanoi"),
    (7, "Manila"),
],
    ["view_id", "location"]
).createOrReplaceTempView("listing_views")

spark.createDataFrame(
    [
    (1, "Bangkok"), (2, "Bangkok"),   # 2/4 = 50.00
    (5, "Hanoi"),                     # 1/2 = 50.00
                                      # Manila 0/1 = 0.00
],
    ["lead_id", "location"]
).createOrReplaceTempView("listing_leads")


SQL = """
WITH v AS (
    SELECT location, COUNT(*) AS views FROM listing_views GROUP BY location
),
l AS (
    SELECT location, COUNT(*) AS leads FROM listing_leads GROUP BY location
)
SELECT v.location,
       v.views,
       COALESCE(l.leads, 0) AS leads,
       ROUND(100.0 * COALESCE(l.leads, 0) / v.views, 2) AS conversion_pct
FROM v
LEFT JOIN l ON l.location = v.location
ORDER BY v.location
"""

expect("Q20 view-to-lead conversion by location", SQL, [
    ("Bangkok", 4, 2, 50.00),
    ("Hanoi", 2, 1, 50.00),
    ("Manila", 1, 0, 0.00),
])
