"""
Problem 03: D28 retention by signup cohort.

Meta flavor: "D28 retention — does the product hold users for a month?"

How to Think:
- Same skeleton again. The interesting part is what D28 means for the business:
  D1 measures onboarding, D28 measures habit.
- Only user 6 (signup 2026-01-02, active 2026-01-30) hits D28 in this seed, which
  is exactly the kind of sparse tail you see in real cohort tables.

How to Remember:
- "D1 = onboarding. D7 = interest. D28 = habit."

AI Use Cases:
- D28 is the usual 'good user' label for acquisition-quality scoring.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("03-d28-retention")
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
    (1, "2026-01-01", "organic",  "US"),
    (2, "2026-01-01", "paid",     "US"),
    (3, "2026-01-01", "organic",  "IN"),
    (4, "2026-01-02", "paid",     "US"),
    (5, "2026-01-02", "referral", "BR"),
    (6, "2026-01-02", "organic",  "IN"),
    (7, "2026-01-08", "paid",     "US"),
    (8, "2026-01-08", "organic",  "BR"),
],
    ["user_id", "signup_date", "channel", "country"]
).createOrReplaceTempView("users")

spark.createDataFrame(
    [
    (1, "2026-01-01", "open"),  (1, "2026-01-02", "open"),  (1, "2026-01-08", "open"),
    (2, "2026-01-01", "open"),
    (3, "2026-01-01", "open"),  (3, "2026-01-02", "open"),
    (4, "2026-01-02", "open"),  (4, "2026-01-03", "open"),  (4, "2026-01-09", "open"),
    (5, "2026-01-02", "open"),
    (6, "2026-01-02", "open"),  (6, "2026-01-03", "open"),  (6, "2026-01-30", "open"),
    (7, "2026-01-08", "open"),
    (8, "2026-01-08", "open"),  (8, "2026-01-09", "open"),
],
    ["user_id", "event_date", "event_name"]
).createOrReplaceTempView("events")


SQL = """
SELECT u.signup_date AS cohort,
       COUNT(DISTINCT u.user_id) AS cohort_size,
       COUNT(DISTINCT e.user_id) AS retained_d28,
       ROUND(100.0 * COUNT(DISTINCT e.user_id) / COUNT(DISTINCT u.user_id), 2) AS pct_d28
FROM users u
LEFT JOIN events e
       ON e.user_id = u.user_id
      AND e.event_date = DATE_ADD(u.signup_date, 28)
GROUP BY u.signup_date
ORDER BY u.signup_date
"""

expect("D28 retention by cohort", SQL, [
    ("2026-01-01", 3, 0, 0.00),
    ("2026-01-02", 3, 1, 33.33),
    ("2026-01-08", 2, 0, 0.00),
])
