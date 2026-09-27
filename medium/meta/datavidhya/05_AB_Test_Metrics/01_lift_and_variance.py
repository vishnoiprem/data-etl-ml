"""
Problem 01: Per-variant mean, variance, and lift.

Meta flavor: "Treatment moved the metric 40%. Ship it?"

How to Think:
- Report n, mean, variance, and stddev per variant. A mean with no n and no
  variance is not a result, it is a rumour.
- VAR_SAMP (n-1 denominator) is what you want for an experiment sample.
  VAR_POP (n denominator) understates variance and inflates significance.
  Knowing which one you called is a real signal.
- Lift has two forms, and people conflate them:
      absolute lift = mean_t - mean_c            (4.0 here)
      relative lift = (mean_t - mean_c)/mean_c   (40% here)
  Always say which one you mean.

Spark note:
- Single grouped aggregate. Nothing clever needed.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("01-lift-and-variance")
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
    (1, "control",   12.0), (2, "control",   9.0),  (3, "control",  11.0),
    (4, "control",   10.0), (5, "control",    8.0),
    (6, "treatment", 14.0), (7, "treatment", 13.0), (8, "treatment", 15.0),
    (9, "treatment", 12.0), (10, "treatment", 16.0),
],
    ["user_id", "variant", "metric"]
).createOrReplaceTempView("experiment")


SQL = """
SELECT variant,
       COUNT(*) AS n,
       ROUND(AVG(metric), 2) AS mean_metric,
       ROUND(VAR_SAMP(metric), 2) AS var_samp,
       ROUND(STDDEV_SAMP(metric), 4) AS sd_samp
FROM experiment
GROUP BY variant
ORDER BY variant
"""
expect("per-variant mean/variance", SQL, [
    ("control",   5, 10.00, 2.50, 1.5811),
    ("treatment", 5, 14.00, 2.50, 1.5811),
])

LIFT = """
WITH s AS (
    SELECT
      AVG(CASE WHEN variant = 'control'   THEN metric END) AS mc,
      AVG(CASE WHEN variant = 'treatment' THEN metric END) AS mt
    FROM experiment
)
SELECT ROUND(mt - mc, 2) AS absolute_lift,
       ROUND(100.0 * (mt - mc) / mc, 2) AS relative_lift_pct
FROM s
"""
expect("absolute vs relative lift", LIFT, [(4.00, 40.00)])
