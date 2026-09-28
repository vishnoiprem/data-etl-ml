"""
Q61: Pandas Apply with Lambda Functions   [Medium | Date/Time, Pandas, Apply, Lambda]
DataVidhya slug: pandas-apply-lambda

Feature-engineer an employee table: first_name (first word of full_name),
years_employed (days to 2024-01-01 / 365.25, 2dp), and a salary_band.

How to Think:
- Three independent row-level derivations, no aggregation and no join. This is
  a projection, so the whole thing is one SELECT.
- The band is an ordered CASE. Write the boundaries in ascending order and let
  the first match win, so each condition only needs its upper bound:
      < 60000            -> junior
      < 100000           -> mid          (>= 60000 implied by fall-through)
      else               -> senior
- 365.25 (not 365) is what makes the expected values come out; it is the average
  Gregorian year including leap days.

The trap:
- The band boundaries are HALF-OPEN: mid is "from 60000 up to but NOT including
  100000", so 100000 exactly is senior. A `BETWEEN 60000 AND 100000` would put
  it in mid -- BETWEEN is inclusive on both ends and is the wrong operator here.
  The shipped data has no boundary row (85000, 58000, 110000), so it cannot
  catch this; asserted separately below.
- 365 instead of 365.25 shifts every value: John becomes 5.81, not 5.80.
- "Preserve the original case of first_name" -- do not lower() or initcap().
- The first word is split on a SPACE. `substring_index(full_name, ' ', 1)` is
  the direct form; a regex is fine too.
- The question is titled "Pandas Apply with Lambda" but a per-row Python lambda
  is the WRONG answer at scale: `df.apply(..., axis=1)` is a Python loop, and in
  Spark a UDF blocks Catalyst. Native column expressions vectorise. Say this --
  the framing is bait.

Spark note:
- `datediff` returns an INT of days, so the division must be by a DOUBLE
  (365.25) to avoid integer truncation.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("61-pandas-apply-lambda")
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


REFERENCE_DATE = "2024-01-01"
DAYS_PER_YEAR = 365.25

# ---------------------------------------------------------- sample data
# Exactly the rows DataVidhya ships with the question.
spark.sql("""
CREATE OR REPLACE TEMP VIEW employees AS
SELECT * FROM VALUES
    (1, 'John Smith',   'john.smith@company.com',  DATE'2018-03-15',  85000, 'Engineering'),
    (4, 'Emma Davis',   'emma.davis@company.com',  DATE'2020-06-01',  58000, 'Sales'),
    (7, 'James Wilson', 'james.w@company.com',     DATE'2016-09-20', 110000, 'Engineering')
AS t(emp_id, full_name, email, hire_date, salary, department)
""")

from pyspark.sql import functions as F

SQL = f"""
SELECT emp_id,
       SUBSTRING_INDEX(full_name, ' ', 1) AS first_name,   -- original case kept
       department,
       ROUND(DATEDIFF(DATE'{REFERENCE_DATE}', hire_date) / {DAYS_PER_YEAR}, 2) AS years_employed,
       salary,
       CASE WHEN salary <  60000 THEN 'junior'
            WHEN salary < 100000 THEN 'mid'      -- half-open: 100000 is NOT mid
            ELSE 'senior'
       END AS salary_band
FROM employees
ORDER BY emp_id
"""

spark.sql(SQL).show(truncate=False)

EXPECTED = [
    (1, "John",  "Engineering", 5.80,  85000, "mid"),
    (4, "Emma",  "Sales",       3.58,  58000, "junior"),
    (7, "James", "Engineering", 7.28, 110000, "senior"),
]
expect("Q61 employee feature table", SQL, EXPECTED)

# DataFrame API equivalent -- native expressions, no UDF.
ref = F.lit(REFERENCE_DATE).cast("date")
df = (spark.table("employees")
      .select("emp_id",
              F.substring_index("full_name", " ", 1).alias("first_name"),
              "department",
              F.round(F.datediff(ref, F.col("hire_date")) / F.lit(DAYS_PER_YEAR), 2)
               .alias("years_employed"),
              "salary",
              F.when(F.col("salary") < 60000, "junior")
               .when(F.col("salary") < 100000, "mid")
               .otherwise("senior").alias("salary_band"))
      .orderBy("emp_id"))
assert [(r[0], r[1], r[2], float(r[3]), r[4], r[5]) for r in df.collect()] == EXPECTED
print("[PASS] Q61 DataFrame API matches SQL")

# ------------------------------------------------ verify the divisor by hand
days = spark.sql(f"""
SELECT DATEDIFF(DATE'{REFERENCE_DATE}', DATE'2018-03-15') AS d
""").collect()[0][0]
assert days == 2118, days
assert round(days / DAYS_PER_YEAR, 2) == 5.80
print(f"[PASS] Q61 John: {days} days / {DAYS_PER_YEAR} = {round(days / DAYS_PER_YEAR, 2)}")

# ------------------------------------------------ the 365-vs-365.25 trap
by_365 = spark.sql(f"""
SELECT ROUND(DATEDIFF(DATE'{REFERENCE_DATE}', hire_date) / 365.0, 2) AS y
FROM employees ORDER BY emp_id
""").collect()
got_365 = [float(r[0]) for r in by_365]
assert got_365 == [5.80, 3.59, 7.28], got_365
print("[PASS] Q61 dividing by 365 shifts Emma to 3.59 (expected 3.58)")

# ------------------------------------------------ the half-open boundary trap
# Salary exactly 100000 is SENIOR, and exactly 60000 is MID.
spark.sql("""
CREATE OR REPLACE TEMP VIEW employees AS
SELECT * FROM VALUES
    (1, 'Ann Boundary', 'a@x.com', DATE'2020-01-01',  60000, 'Ops'),
    (2, 'Bob Boundary', 'b@x.com', DATE'2020-01-01',  99999, 'Ops'),
    (3, 'Cid Boundary', 'c@x.com', DATE'2020-01-01', 100000, 'Ops'),
    (4, 'Dee Boundary', 'd@x.com', DATE'2020-01-01',  59999, 'Ops')
AS t(emp_id, full_name, email, hire_date, salary, department)
""")
bands = [(r[0], r[5]) for r in spark.sql(SQL).collect()]
assert bands == [(1, "mid"), (2, "mid"), (3, "senior"), (4, "junior")], bands
print("[PASS] Q61 60000 -> mid, 99999 -> mid, 100000 -> senior, 59999 -> junior")

between = spark.sql("""
SELECT emp_id, CASE WHEN salary BETWEEN 60000 AND 100000 THEN 'mid' ELSE 'other' END AS b
FROM employees WHERE salary = 100000
""").collect()[0][1]
assert between == "mid"
print("[PASS] Q61 BETWEEN 60000 AND 100000 wrongly bands 100000 as mid -- it is inclusive")

# ------------------------------------------------ case is preserved
cased = spark.sql("""
SELECT SUBSTRING_INDEX('McDonald O''Brien', ' ', 1) AS first_name
""").collect()[0][0]
assert cased == "McDonald", cased
print("[PASS] Q61 'McDonald' keeps its internal capital -- no lower()/initcap()")

# ---- MySQL way ----------------------------------------------------------
# The Spark DataFrame API example here uses NATIVE column expressions
# (substring_index, datediff, when/otherwise). All three translate to MySQL
# verbatim:
#   substring_index(str, ' ', 1) -> SUBSTRING_INDEX(str, ' ', 1)
#   datediff(end, start)         -> DATEDIFF(end, start)
#   case when salary < X ...     -> CASE WHEN salary < X ...
#
# The pandas_udf / pandas-apply-with-lambda framing in the question title is
# Spark-specific -- there is no equivalent on the MySQL side. A MySQL-native
# implementation is just the SQL CASE chain.
#
# CREATE TABLE employees (
#     emp_id      INT          NOT NULL,
#     full_name   VARCHAR(128) NOT NULL,
#     email       VARCHAR(255) NOT NULL,
#     hire_date   DATE         NOT NULL,
#     salary      INT          NOT NULL,
#     department  VARCHAR(64)  NOT NULL,
#     PRIMARY KEY (emp_id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO employees (emp_id, full_name, email, hire_date, salary, department) VALUES
#     (1, 'John Smith',   'john.smith@company.com',  '2018-03-15',  85000, 'Engineering'),
#     (4, 'Emma Davis',   'emma.davis@company.com',  '2020-06-01',  58000, 'Sales'),
#     (7, 'James Wilson', 'james.w@company.com',     '2016-09-20', 110000, 'Engineering');
#
# SELECT emp_id,
#        SUBSTRING_INDEX(full_name, ' ', 1)                                AS first_name,
#        department,
#        ROUND(DATEDIFF('2024-01-01', hire_date) / 365.25, 2)               AS years_employed,
#        salary,
#        CASE WHEN salary <  60000 THEN 'junior'
#             WHEN salary < 100000 THEN 'mid'
#             ELSE 'senior'
#        END                                                               AS salary_band
# FROM employees
# ORDER BY emp_id;
#
# -- Expected:
# -- (1, 'John',  'Engineering', 5.80,  85000, 'mid')
# -- (4, 'Emma',  'Sales',       3.58,  58000, 'junior')
# -- (7, 'James', 'Engineering', 7.28, 110000, 'senior')
