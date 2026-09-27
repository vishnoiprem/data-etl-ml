"""
Q13: Popularity Percentage by Domain   [Hard | Aggregation + Window]

Each domain's percentage share of total views.

How to Think:
- Share-of-total needs the grand total on every row. Two ways:
    1. SUM(views) OVER ()          <- window with empty OVER, one pass
    2. CROSS JOIN (SELECT SUM(views) ...) <- explicit, also fine
  Form 1 is what the "Hard" tag is really testing: knowing that OVER () with no
  PARTITION BY and no ORDER BY means "the whole result set".
- Shares must sum to 100. Say that as your own sanity check — interviewers
  notice candidates who verify their own output.

Spark note:
- SUM(...) OVER () collapses to a single partition to compute the total, then
  broadcasts it. Cheap on aggregates, dangerous on raw rows.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("13-popularity-by-domain")
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
    ("facebook.com", 500), ("instagram.com", 300),
    ("whatsapp.com", 150), ("threads.net", 50),
],
    ["domain", "views"]
).createOrReplaceTempView("domain_views")


SQL = """
SELECT domain,
       views,
       ROUND(100.0 * views / SUM(views) OVER (), 2) AS pct_of_total
FROM domain_views
ORDER BY pct_of_total DESC, domain
"""

expect("Q13 popularity % by domain", SQL, [
    ("facebook.com", 500, 50.00),
    ("instagram.com", 300, 30.00),
    ("whatsapp.com", 150, 15.00),
    ("threads.net", 50, 5.00),
])
