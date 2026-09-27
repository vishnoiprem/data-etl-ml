"""
Q56: Max Salary from Each Department   [Medium | Inner Joins, Aggregate Functions]
DataVidhya slug: max-salary-per-dept

Per department: the name(s) of the top earner(s) and that salary. TIES MUST ALL
BE RETURNED.

How to Think:
- "Return the employee WHO earns the max" is not `MAX(salary)` -- that gives the
  number, not the person. You need the whole ROW at the maximum, which is a
  top-1-per-group problem, so: RANK() OVER (PARTITION BY department ORDER BY
  salary DESC), then keep rank 1.
- RANK (or DENSE_RANK) not ROW_NUMBER: at rank 1 they differ exactly when there
  is a tie, and this question requires keeping every tied employee. Sales has
  two employees at 111905 and both must appear.
- The GROUP BY + self-join formulation (`JOIN (SELECT dept, MAX(salary) ...)`)
  is equally correct and also keeps ties -- both are asserted below.

The trap:
- ROW_NUMBER silently returns ONE of the two Sales employees, chosen
  arbitrarily. The output still looks well-formed (3 rows), which is why this
  is the standard trap on "who earns the most" questions.
- `MAX(salary)` with a GROUP BY and any employee name in the SELECT is a grain
  error: Spark rejects it outright, but MySQL would happily return an arbitrary
  name.
- Department 3 (HR) is present; a department with NO employees would need a
  LEFT JOIN to appear at all -- worth asking about, since the sample cannot
  distinguish.

ORDERING NOTE:
- The spec mandates only `department_name` ascending, so the order WITHIN the
  Sales tie is unspecified. DataVidhya's sample shows Employee_7 before
  Employee_5, which is neither name-ascending nor id-ascending -- i.e. it is
  incidental. This file sorts ties by employee_name ascending so the result is
  reproducible; that is spec-compliant but the two tied rows appear in the
  opposite order from the site's sample.

Spark note:
- One shuffle for the window; `departments` is a dimension and broadcasts.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("56-max-salary-per-dept")
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
# Employee_5 and Employee_7 TIE at 111905 in Sales -- both must be returned.
spark.sql("""
CREATE OR REPLACE TEMP VIEW departments AS
SELECT * FROM VALUES
    (1, 'Engineering'), (2, 'Sales'), (3, 'HR')
AS t(department_id, department_name)
""")
spark.sql("""
CREATE OR REPLACE TEMP VIEW employees AS
SELECT * FROM VALUES
    ( 1, 'Employee_1',  125520, 1),
    ( 2, 'Employee_2',   84530, 1),
    ( 4, 'Employee_4',   90301, 2),
    ( 5, 'Employee_5',  111905, 2),
    ( 7, 'Employee_7',  111905, 2),
    ( 9, 'Employee_9',  145536, 3),
    (10, 'Employee_10',  72721, 3)
AS t(employee_id, name, salary, department_id)
""")

from pyspark.sql import functions as F, Window as W

SQL = """
SELECT department_name, employee_name, max_salary
FROM (
    SELECT d.department_name,
           e.name   AS employee_name,
           e.salary AS max_salary,
           RANK() OVER (PARTITION BY d.department_name
                        ORDER BY e.salary DESC) AS rnk   -- RANK keeps ties
    FROM employees e
    JOIN departments d ON d.department_id = e.department_id
)
WHERE rnk = 1
ORDER BY department_name, employee_name
"""

spark.sql(SQL).show(truncate=False)

EXPECTED = [
    ("Engineering", "Employee_1", 125520),
    ("HR",          "Employee_9", 145536),
    ("Sales",       "Employee_5", 111905),
    ("Sales",       "Employee_7", 111905),
]
expect("Q56 top earners per department", SQL, EXPECTED)

# DataFrame API equivalent.
w = W.partitionBy("department_name").orderBy(F.col("salary").desc())
df = (spark.table("employees").alias("e")
      .join(F.broadcast(spark.table("departments").alias("d")), "department_id")
      .withColumn("rnk", F.rank().over(w))
      .filter(F.col("rnk") == 1)
      .select("department_name",
              F.col("name").alias("employee_name"),
              F.col("salary").alias("max_salary"))
      .orderBy("department_name", "employee_name"))
assert [tuple(r) for r in df.collect()] == EXPECTED
print("[PASS] Q56 DataFrame API matches SQL")

# ------------------------------------------------ the GROUP BY + join formulation
SQL_MAXJOIN = """
WITH dept_max AS (
    SELECT department_id, MAX(salary) AS max_salary
    FROM employees GROUP BY department_id
)
SELECT d.department_name, e.name AS employee_name, e.salary AS max_salary
FROM employees e
JOIN dept_max m ON m.department_id = e.department_id AND e.salary = m.max_salary
JOIN departments d ON d.department_id = e.department_id
ORDER BY d.department_name, e.name
"""
expect("Q56 MAX + join formulation agrees and also keeps ties", SQL_MAXJOIN, EXPECTED)

# ------------------------------------------------ the ROW_NUMBER trap
row_num = spark.sql("""
SELECT department_name, COUNT(*) AS n FROM (
    SELECT d.department_name,
           ROW_NUMBER() OVER (PARTITION BY d.department_name ORDER BY e.salary DESC) AS rn
    FROM employees e JOIN departments d ON d.department_id = e.department_id
) WHERE rn = 1 GROUP BY department_name ORDER BY department_name
""").collect()
assert [(r[0], r[1]) for r in row_num] == [
    ("Engineering", 1), ("HR", 1), ("Sales", 1),
], row_num
print("[PASS] Q56 ROW_NUMBER returns 3 rows -- it drops one of the tied Sales employees")

assert spark.sql(SQL).count() == 4
print("[PASS] Q56 RANK returns 4 rows -- both Sales employees at 111905")

# ------------------------------------------------ MAX(salary) is not the person
try:
    spark.sql("""
    SELECT d.department_name, e.name, MAX(e.salary)
    FROM employees e JOIN departments d ON d.department_id = e.department_id
    GROUP BY d.department_name
    """).collect()
    raise AssertionError("expected Spark to reject the ungrouped name column")
except Exception as e:
    assert type(e).__name__ != "AssertionError", e
    print("[PASS] Q56 selecting a name alongside MAX() without grouping it is rejected")

# ------------------------------------------------ an empty department needs a LEFT JOIN
spark.sql("""
CREATE OR REPLACE TEMP VIEW departments AS
SELECT * FROM VALUES
    (1, 'Engineering'), (2, 'Sales'), (3, 'HR'), (4, 'Legal')
AS t(department_id, department_name)
""")
expect("Q56 Legal has no employees, so INNER JOIN omits it", SQL, EXPECTED)
print("[PASS] Q56 an employee-less department is absent -- ask whether it should appear")
