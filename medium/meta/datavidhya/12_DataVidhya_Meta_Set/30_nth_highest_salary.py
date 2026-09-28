"""
Q30: Nth Highest Salary   [Hard | Window Functions, Subqueries]
DataVidhya slug: nth-highest-salary

Return the 3rd highest DISTINCT salary. If fewer than 3 distinct salaries
exist, return NULL -- as a row, not as an empty result.

How to Think:
- "3rd highest distinct" has two readings and only one is right: rank the
  DISTINCT SALARY VALUES, not the employees. Two employees on 90000 occupy one
  rank, so the answer is 50000, not 70000.
- DENSE_RANK() over DISTINCT salaries already collapses duplicates, so
  DENSE_RANK and ROW_NUMBER agree here. Using DENSE_RANK directly over
  `employees` (no DISTINCT) works too and is the tighter answer. RANK() is the
  one that breaks -- it leaves gaps, so rank 3 may not exist at all.

The trap (this is the entire question):
- "Return NULL if fewer than three exist" means ONE ROW CONTAINING NULL, not
  zero rows. `SELECT salary ... WHERE rnk = 3` returns an EMPTY RESULT SET when
  there are only two distinct salaries, which is a different thing and fails.
  Wrapping it in `MAX(...)` with no GROUP BY forces a single row: an aggregate
  over an empty input is one row of NULL. That is the fix.
- LIMIT/OFFSET (`ORDER BY salary DESC LIMIT 1 OFFSET 2`) has the same defect --
  it returns no rows rather than NULL -- and additionally does not dedupe
  unless you add DISTINCT.

Spark note:
- A window over the whole table means PARTITION BY nothing, so all data lands
  in one partition. Fine at interview scale; on a real comp table you would
  pre-aggregate to distinct salaries first (which the DISTINCT here does).
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("30-nth-highest-salary")
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


N = 3  # the "N" in Nth highest -- parameterised, because interviewers change it

# ---------------------------------------------------------- sample data
# Exactly the rows DataVidhya ships with the question.
# Employees 1 and 2 share 90000 -- that value occupies ONE rank.
spark.createDataFrame(
    [
        (1, "Employee_1", 90000),
        (2, "Employee_2", 90000),
        (3, "Employee_3", 70000),
        (4, "Employee_4", 50000),
        (5, "Employee_5", 30000),
    ],
    ["emp_id", "emp_name", "salary"],
).createOrReplaceTempView("employees")

from pyspark.sql import functions as F, Window as W

# MAX() with no GROUP BY is what guarantees a single NULL row instead of
# zero rows when the Nth rank does not exist.
SQL = f"""
SELECT MAX(salary) AS nth_highest_salary
FROM (
    SELECT salary,
           DENSE_RANK() OVER (ORDER BY salary DESC) AS rnk
    FROM (SELECT DISTINCT salary FROM employees)
)
WHERE rnk = {N}
"""

spark.sql(SQL).show(truncate=False)

expect("Q30 3rd highest distinct salary", SQL, [(50000,)])

# DataFrame API equivalent.
ranked = (spark.table("employees").select("salary").distinct()
          .withColumn("rnk", F.dense_rank().over(W.orderBy(F.col("salary").desc()))))
df = ranked.filter(F.col("rnk") == N).agg(F.max("salary").alias("nth_highest_salary"))
assert [tuple(r) for r in df.collect()] == [(50000,)], df.collect()
print("[PASS] Q30 DataFrame API matches SQL")

# ------------------------------------------------- the duplicate-salary trap
# Ranking EMPLOYEES instead of DISTINCT SALARIES gives 70000, which is wrong.
by_employee = spark.sql("""
SELECT salary FROM (
    SELECT salary, ROW_NUMBER() OVER (ORDER BY salary DESC) AS rn FROM employees
) WHERE rn = 3
""").collect()[0][0]
assert by_employee == 70000, by_employee
print("[PASS] Q30 ranking employees gives 70000 (WRONG); ranking distinct salaries gives 50000")

# ------------------------------------------------- the fewer-than-N trap
# Only two distinct salaries -> must be one row of NULL, not an empty result.
spark.createDataFrame(
    [(1, "Employee_1", 90000), (2, "Employee_2", 90000), (3, "Employee_3", 70000)],
    ["emp_id", "emp_name", "salary"],
).createOrReplaceTempView("employees")

expect("Q30 fewer than 3 distinct salaries -> one NULL row", SQL, [(None,)])

# The LIMIT/OFFSET formulation returns ZERO rows here, which is the failure.
empty = spark.sql("""
SELECT salary FROM (SELECT DISTINCT salary FROM employees)
ORDER BY salary DESC LIMIT 1 OFFSET 2
""").collect()
assert empty == [], empty
print("[PASS] Q30 LIMIT/OFFSET returns 0 rows instead of NULL -- MAX() wrapper is required")

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports DENSE_RANK() identically. The key trick is the
# outer MAX() with no GROUP BY: an aggregate over an empty input returns
# ONE row of NULL, which is the contract the question requires. A bare
# `SELECT salary WHERE rnk = N` returns an empty result set instead, and
# LIMIT 1 OFFSET N-1 has the same defect. DENSE_RANK over DISTINCT salaries
# collapses duplicates, so two employees on 90000 occupy a single rank.
#
# CREATE TABLE employees (
#     emp_id   INT         NOT NULL,
#     emp_name VARCHAR(32) NOT NULL,
#     salary   INT         NOT NULL,
#     PRIMARY KEY (emp_id),
#     KEY ix_emp_salary (salary)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO employees (emp_id, emp_name, salary) VALUES
#     (1, 'Employee_1', 90000),
#     (2, 'Employee_2', 90000),
#     (3, 'Employee_3', 70000),
#     (4, 'Employee_4', 50000),
#     (5, 'Employee_5', 30000);
#
# -- N is a SQL parameter; the literal 3 below matches the Spark script.
# SELECT MAX(salary) AS nth_highest_salary
# FROM (
#     SELECT salary,
#            DENSE_RANK() OVER (ORDER BY salary DESC) AS rnk
#     FROM (SELECT DISTINCT salary FROM employees) d
# ) ranked
# WHERE rnk = 3;
#
# -- Expected: (50000,).