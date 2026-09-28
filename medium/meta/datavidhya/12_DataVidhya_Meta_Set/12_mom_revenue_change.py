"""
Q12: Monthly Revenue Percentage Change   [Medium | Windows, Date Functions]

Monthly revenue and month-over-month % change.

How to Think:
- pct_change = (current - previous) / previous * 100, previous via LAG.
- The first month HAS no previous value. It must be NULL, not 0 — reporting 0%
  growth for the first month is a factual error. Do not COALESCE it away.
- Divide-by-zero: if a month can have zero revenue, guard with NULLIF(prev, 0),
  which turns the division into NULL instead of erroring.
- Order the window by a sortable month key. 'yyyy-MM' strings sort correctly;
  'MM-yyyy' does not. Worth stating.

The trap:
- Month 2026-04 is flat versus March, so the answer must be exactly 0.00 —
  distinguishable from the NULL first month. If your query returns 0 for both,
  you have conflated "no change" with "no prior data".

Spark note:
- A single global window (no PARTITION BY) funnels every row to one partition.
  Fine for 4 months of aggregates; never do it on raw events.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("12-mom-revenue-change")
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
    ("2026-01", 1000.0),
    ("2026-02", 1200.0),   # +20.00%
    ("2026-03",  900.0),   # -25.00%
    ("2026-04",  900.0),   #   0.00%
],
    ["month", "revenue"]
).createOrReplaceTempView("monthly_rev")


SQL = """
SELECT month,
       revenue,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
                   / NULLIF(LAG(revenue) OVER (ORDER BY month), 0), 2) AS mom_pct_change
FROM monthly_rev
ORDER BY month
"""

expect("Q12 MoM revenue % change", SQL, [
    ("2026-01", 1000.0, None),
    ("2026-02", 1200.0, 20.00),
    ("2026-03",  900.0, -25.00),
    ("2026-04",  900.0, 0.00),
])

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports LAG and NULLIF identically. The first month has no prior
# month, so pct_change is NULL -- distinct from 0% (flat vs prior). Multiplying
# by 100.0 forces DECIMAL arithmetic; integer 100 would truncate low-rate
# months. Order the window by month, not by month number, so 'yyyy-MM' sorts
# correctly.
#
# CREATE TABLE monthly_rev (
#     month    VARCHAR(7)     NOT NULL,
#     revenue  DECIMAL(12, 2) NOT NULL,
#     PRIMARY KEY (month)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO monthly_rev (month, revenue) VALUES
#     ('2026-01', 1000.0),
#     ('2026-02', 1200.0),
#     ('2026-03',  900.0),
#     ('2026-04',  900.0);
#
# SELECT month,
#        revenue,
#        ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
#                    / NULLIF(LAG(revenue) OVER (ORDER BY month), 0), 2) AS mom_pct_change
# FROM monthly_rev
# ORDER BY month;
#
# -- Expected:
# -- 2026-01  1000.00  NULL
# -- 2026-02  1200.00  20.00
# -- 2026-03   900.00  -25.00
# -- 2026-04   900.00  0.00
