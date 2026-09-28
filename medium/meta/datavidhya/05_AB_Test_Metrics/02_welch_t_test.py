"""
Problem 02: Welch's t-test for an A/B result.

Meta flavor: "Is that 40% lift real, or noise?"

How to Think:
- Standard error of a difference of means, UNEQUAL variances (Welch):
      se = sqrt(var_t/n_t + var_c/n_c)
      t  = (mean_t - mean_c) / se
- Use Welch, not Student's pooled t-test. Pooled assumes equal variances; in
  product experiments they are routinely unequal, and the pooled test is then
  anti-conservative (it over-declares significance). Naming Welch specifically
  is the signal here.
- |t| > ~1.96 is significant at 95% for large n. With n=5 per arm the critical
  value is much larger (~2.3 on ~8 df), so a small-sample result needs a bigger
  t. Say this rather than blindly comparing to 1.96.
- Sanity check first: se = sqrt(2.5/5 + 2.5/5) = sqrt(1.0) = 1.0, so t = 4/1 = 4.

Spark note:
- All scalar arithmetic on aggregates — one pass, no shuffle beyond the group-by.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("02-welch-t-test")
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
WITH stats AS (
    SELECT variant, COUNT(*) AS n, AVG(metric) AS mean_m, VAR_SAMP(metric) AS var_m
    FROM experiment GROUP BY variant
),
p AS (
    SELECT
      MAX(CASE WHEN variant = 'control'   THEN n      END) AS nc,
      MAX(CASE WHEN variant = 'control'   THEN mean_m END) AS mc,
      MAX(CASE WHEN variant = 'control'   THEN var_m  END) AS vc,
      MAX(CASE WHEN variant = 'treatment' THEN n      END) AS nt,
      MAX(CASE WHEN variant = 'treatment' THEN mean_m END) AS mt,
      MAX(CASE WHEN variant = 'treatment' THEN var_m  END) AS vt
    FROM stats
)
SELECT ROUND(mt - mc, 4) AS abs_lift,
       ROUND(SQRT(vt / nt + vc / nc), 4) AS std_error,
       ROUND((mt - mc) / SQRT(vt / nt + vc / nc), 4) AS t_stat
FROM p
"""
expect("Welch t-test", SQL, [(4.0, 1.0, 4.0)])

# ---- MySQL way ----------------------------------------------------------
# CREATE TABLE + sample data:
#   CREATE TABLE experiment (
#       user_id INT PRIMARY KEY,
#       variant VARCHAR(16) NOT NULL,
#       metric  DECIMAL(6,2) NOT NULL
#   );
#   INSERT INTO experiment (user_id, variant, metric) VALUES
#       (1,  'control',   12.00), (2,  'control',    9.00), (3,  'control',   11.00),
#       (4,  'control',   10.00), (5,  'control',    8.00),
#       (6,  'treatment', 14.00), (7,  'treatment', 13.00), (8,  'treatment', 15.00),
#       (9,  'treatment', 12.00), (10, 'treatment', 16.00);
#
# Welch t-test (UNEQUAL variances, not Student's pooled):
#   WITH stats AS (
#       SELECT variant, COUNT(*) AS n,
#              AVG(metric) AS mean_m, VAR_SAMP(metric) AS var_m
#       FROM experiment GROUP BY variant
#   ),
#   p AS (
#       SELECT
#         MAX(CASE WHEN variant = 'control'   THEN n      END) AS nc,
#         MAX(CASE WHEN variant = 'control'   THEN mean_m END) AS mc,
#         MAX(CASE WHEN variant = 'control'   THEN var_m  END) AS vc,
#         MAX(CASE WHEN variant = 'treatment' THEN n      END) AS nt,
#         MAX(CASE WHEN variant = 'treatment' THEN mean_m END) AS mt,
#         MAX(CASE WHEN variant = 'treatment' THEN var_m  END) AS vt
#       FROM stats
#   )
#   SELECT ROUND(mt - mc, 4)                                    AS abs_lift,
#          ROUND(SQRT(vt / nt + vc / nc), 4)                   AS std_error,
#          ROUND((mt - mc) / SQRT(vt / nt + vc / nc), 4)       AS t_stat
#   FROM p;
# Notes:
# - Welch (unequal variances) is correct for product experiments. The pooled
#   Student's t-test assumes equal variances and is anti-conservative here.
# - |t| > 1.96 ~ 95% only holds for large n. With n=5/arm use t_crit ~ 2.3
#   (df ~ 8). Don't blindly compare to 1.96 on small samples.
