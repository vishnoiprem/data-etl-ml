"""
Q42: Approximate Quantiles and Percentiles   [Medium | Mathematical Functions, Aggregate Functions]
DataVidhya slug: approximate-quantiles-percentiles

Per department: p25, p50, p75 of salary with LINEAR INTERPOLATION between the
two nearest ranked values, plus iqr = p75 - p25. Round to 2dp.

How to Think:
- Read the constraints, not the title. The title says "Approximate" but the
  constraint says "use EXACT linear interpolation." Those select different
  functions, and the title is the distractor.
- Interpolated percentile: rank position = p * (n - 1), zero-indexed, then
  blend the two neighbours. Sales has n=4, so p25 sits at 0.75 -- three quarters
  of the way from 45000 to 48000 = 47250. Being able to derive the position by
  hand is what lets you sanity-check the function's output.
- iqr is p75 - p25, so compute it from the same interpolated values. Do not
  recompute the percentiles a second way.

The trap:
- `percentile_approx()` does NOT interpolate -- it returns an actual data point
  from a sketch. On Sales it returns 48000 for p25, not 47250. `percentile()`
  is the exact, interpolating one. Choosing the function whose name matches the
  question title is the intended failure.
- p50 is not `median` by naive definition either: with an even n there is no
  middle row, so the median is the midpoint of the two central values
  (48000, 52000) -> 50000. Both departments here have even n.
- Round to 2dp: 47250.00, not 47250.
- ORDER BY department puts Engineering before Sales -- the output is not in
  emp_id or insertion order.

Spark note:
- `percentile()` is exact, so it buffers every value in the group on one
  executor. Fine per department; on a high-cardinality group-by use
  percentile_approx (and accept non-interpolated values) or approx_percentile
  with a tightened accuracy parameter.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("42-quantiles-percentiles")
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
# Exactly the rows DataVidhya ships with the question.
# Sales: 45000, 48000, 52000, 55000   Engineering: 75000, 78000, 82000, 85000
spark.sql("""
CREATE OR REPLACE TEMP VIEW employee_salaries AS
SELECT * FROM VALUES
    (101, 'Sales',       45000),
    (102, 'Sales',       48000),
    (103, 'Sales',       52000),
    (104, 'Sales',       55000),
    (201, 'Engineering', 75000),
    (202, 'Engineering', 78000),
    (203, 'Engineering', 82000),
    (204, 'Engineering', 85000)
AS t(emp_id, department, salary)
""")

from pyspark.sql import functions as F

# percentile() interpolates exactly; percentile_approx() does not.
SQL = """
SELECT department,
       ROUND(PERCENTILE(salary, 0.25), 2) AS p25,
       ROUND(PERCENTILE(salary, 0.50), 2) AS p50,
       ROUND(PERCENTILE(salary, 0.75), 2) AS p75,
       ROUND(PERCENTILE(salary, 0.75) - PERCENTILE(salary, 0.25), 2) AS iqr
FROM employee_salaries
GROUP BY department
ORDER BY department
"""

spark.sql(SQL).show(truncate=False)

expect("Q42 interpolated quartiles per department", SQL, [
    ("Engineering", 77250.00, 80000.00, 82750.00, 5500.00),
    ("Sales",       47250.00, 50000.00, 52750.00, 5500.00),
])

# DataFrame API equivalent.
p = [F.expr(f"percentile(salary, {q})").alias(n)
     for q, n in [(0.25, "p25_raw"), (0.50, "p50_raw"), (0.75, "p75_raw")]]
df = (spark.table("employee_salaries")
      .groupBy("department").agg(*p)
      .select("department",
              F.round("p25_raw", 2).alias("p25"),
              F.round("p50_raw", 2).alias("p50"),
              F.round("p75_raw", 2).alias("p75"),
              F.round(F.col("p75_raw") - F.col("p25_raw"), 2).alias("iqr"))
      .orderBy("department"))
assert [(r[0], float(r[1]), float(r[2]), float(r[3]), float(r[4])) for r in df.collect()] == [
    ("Engineering", 77250.0, 80000.0, 82750.0, 5500.0),
    ("Sales",       47250.0, 50000.0, 52750.0, 5500.0),
]
print("[PASS] Q42 DataFrame API matches SQL")

# ------------------------------------------------ the percentile_approx trap
approx = spark.sql("""
SELECT department, PERCENTILE_APPROX(salary, 0.25) AS p25_approx
FROM employee_salaries GROUP BY department ORDER BY department
""").collect()
assert [(r[0], float(r[1])) for r in approx] == [
    ("Engineering", 75000.0), ("Sales", 45000.0),
], approx
print("[PASS] Q42 percentile_approx returns a real data point (45000) not the interpolated 47250")

# ------------------------------------------------ verify the interpolation by hand
# Sales n=4: position = 0.25 * (4-1) = 0.75 -> 45000 + 0.75 * (48000-45000)
manual = 45000 + 0.75 * (48000 - 45000)
engine = spark.sql("""
SELECT PERCENTILE(salary, 0.25) FROM employee_salaries WHERE department = 'Sales'
""").collect()[0][0]
assert manual == float(engine) == 47250.0, (manual, engine)
print(f"[PASS] Q42 hand-computed p25 = {manual} matches PERCENTILE()")
