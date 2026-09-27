"""
Q43: Avg Salary by Dept vs Company   [Medium | Window Functions]
DataVidhya slug: window-functions-dept-avg-vs-company-avg

One row per department: dept_avg, company_avg, and diff = dept_avg -
company_avg. Sort by diff descending.

How to Think:
- Two aggregates at two different grains in the same row. That is precisely
  what a window function is for:
      AVG(salary) OVER (PARTITION BY department)  -> dept grain
      AVG(salary) OVER ()                         -> whole-table grain
  An EMPTY OVER() clause means "the frame is every row" -- that is the company
  average, and knowing that idiom is the point of the question.
- The window runs per ROW, so you get N rows; DISTINCT collapses them to one per
  department. (GROUP BY + a CROSS JOIN to a 1-row CTE is the equivalent answer;
  both are asserted below.)
- You cannot write `AVG(salary)` and `AVG(salary) OVER ()` together -- mixing an
  aggregate and a window over the raw column in one SELECT is a grain error.

The trap:
- company_avg is the mean over EMPLOYEES, not the mean of the department means.
  Here: 410000/5 = 82000, whereas averaging the three dept averages gives
  (92500 + 77500 + 70000)/3 = 80000. Unequal department sizes make these differ,
  and 80000 looks entirely reasonable. This is the failure the question wants.
- diff is signed and the sort is on diff DESC, so the below-average departments
  come last in ascending order of shortfall: Engineering (+10500), Sales
  (-4500), HR (-12000). Sorting by dept_avg happens to give the same order here;
  sorting by ABS(diff) does not.
- salary is DECIMAL, so ROUND returns DECIMAL -- compare as floats, and do not
  assume 92500.00 will print as 92500.

Spark note:
- `OVER ()` with no PARTITION BY collects every row into ONE partition. On a
  real table that is a single-executor bottleneck; compute the global average
  separately and broadcast it instead.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("43-dept-avg-vs-company-avg")
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
# Department sizes are 2, 2, 1 -- unequal, which is what separates the
# employee-weighted average from the average-of-averages.
spark.sql("""
CREATE OR REPLACE TEMP VIEW employees AS
SELECT * FROM VALUES
    (1, 'Alice',   CAST(80000 AS DECIMAL(12,2)), 'Sales'),
    (2, 'Bob',     CAST(75000 AS DECIMAL(12,2)), 'Sales'),
    (3, 'Charlie', CAST(90000 AS DECIMAL(12,2)), 'Engineering'),
    (4, 'David',   CAST(95000 AS DECIMAL(12,2)), 'Engineering'),
    (5, 'Eve',     CAST(70000 AS DECIMAL(12,2)), 'HR')
AS t(employee_id, name, salary, department)
""")

from pyspark.sql import functions as F, Window as W

# OVER () with no PARTITION BY == the whole table == company average.
SQL = """
SELECT DISTINCT
       department,
       ROUND(AVG(salary) OVER (PARTITION BY department), 2) AS dept_avg,
       ROUND(AVG(salary) OVER (), 2)                        AS company_avg,
       ROUND(AVG(salary) OVER (PARTITION BY department)
             - AVG(salary) OVER (), 2)                      AS diff
FROM employees
ORDER BY diff DESC
"""

spark.sql(SQL).show(truncate=False)

EXPECTED = [
    ("Engineering", 92500.00, 82000.00,  10500.00),
    ("Sales",       77500.00, 82000.00,  -4500.00),
    ("HR",          70000.00, 82000.00, -12000.00),
]
expect("Q43 dept vs company average", SQL, EXPECTED)

# DataFrame API equivalent.
w_dept, w_all = W.partitionBy("department"), W.partitionBy()
df = (spark.table("employees")
      .select("department",
              F.avg("salary").over(w_dept).alias("dept_avg_raw"),
              F.avg("salary").over(w_all).alias("company_avg_raw"))
      .select("department",
              F.round("dept_avg_raw", 2).alias("dept_avg"),
              F.round("company_avg_raw", 2).alias("company_avg"),
              F.round(F.col("dept_avg_raw") - F.col("company_avg_raw"), 2).alias("diff"))
      .distinct()
      .orderBy(F.col("diff").desc()))
assert [(r[0], float(r[1]), float(r[2]), float(r[3])) for r in df.collect()] == [
    ("Engineering", 92500.0, 82000.0, 10500.0),
    ("Sales",       77500.0, 82000.0, -4500.0),
    ("HR",          70000.0, 82000.0, -12000.0),
]
print("[PASS] Q43 DataFrame API matches SQL")

# ------------------------------------------------ the GROUP BY + CROSS JOIN equivalent
SQL_GROUPED = """
WITH dept AS (
    SELECT department, AVG(salary) AS dept_avg FROM employees GROUP BY department
),
company AS (
    SELECT AVG(salary) AS company_avg FROM employees
)
SELECT d.department,
       ROUND(d.dept_avg, 2)                   AS dept_avg,
       ROUND(c.company_avg, 2)                AS company_avg,
       ROUND(d.dept_avg - c.company_avg, 2)   AS diff
FROM dept d CROSS JOIN company c
ORDER BY diff DESC
"""
expect("Q43 GROUP BY + CROSS JOIN agrees with the window version", SQL_GROUPED, EXPECTED)

# ------------------------------------------------ the average-of-averages trap
employee_weighted, avg_of_avgs = spark.sql("""
SELECT (SELECT ROUND(AVG(salary), 2) FROM employees) AS employee_weighted,
       (SELECT ROUND(AVG(dept_avg), 2) FROM (
            SELECT AVG(salary) AS dept_avg FROM employees GROUP BY department
        )) AS avg_of_avgs
""").collect()[0]
assert (float(employee_weighted), float(avg_of_avgs)) == (82000.0, 80000.0)
print("[PASS] Q43 company_avg is 82000 (per employee), not 80000 (average of dept averages)")

# ------------------------------------------------ the sort-key trap
by_abs = [r[0] for r in spark.sql(f"""
SELECT department FROM ({SQL_GROUPED.replace('ORDER BY diff DESC', '')})
ORDER BY ABS(diff) DESC
""").collect()]
assert by_abs == ["HR", "Engineering", "Sales"], by_abs
print("[PASS] Q43 ordering by ABS(diff) gives HR/Engineering/Sales -- diff is signed")
