"""
Q67: Statistical Calculations per Group   [Medium | Mathematical Functions, Aggregate Functions]
DataVidhya slug: statistical-calculations

Per subject: distinct student count, avg, min, max, SAMPLE standard deviation,
and median. Round avg and std_dev to 2dp.

How to Think:
- Six aggregates, one GROUP BY. Five are trivial; the two that carry the
  question are std_dev and median, and both are "which variant?" questions.
- SAMPLE vs POPULATION standard deviation:
      stddev_samp  divides by (n - 1)   <- the spec asks for this
      stddev_pop   divides by n
  `STDDEV()` is an alias for stddev_samp in Spark and Postgres, so the bare name
  happens to be right -- but say which one you mean rather than relying on the
  alias, because the default differs across engines.
- Median is percentile 0.5. With n even there is no middle row, so it is the
  midpoint of the two central values: here 55.6 and 59.9 -> 57.75.

The trap:
- stddev_pop instead of stddev_samp gives 9.14 rather than 9.77 on this data --
  a 6% difference that looks entirely plausible. The (n-1) denominator (Bessel's
  correction) is the whole distinction, and with n=8 it matters.
- `student_count` counts DISTINCT STUDENTS, not rows. They coincide here (8
  tests, 8 different students), so the shipped data CANNOT catch a plain
  COUNT(*). Give one student two tests and the two diverge; asserted below.
- Round ONLY avg_score and std_dev. min_score and max_score are actual data
  points and must keep their own scale (51.5, not 51.50).
- median needs `percentile()` (exact, interpolating) not `percentile_approx()`.

Spark note:
- `percentile` is exact so it buffers each subject's scores. Fine per subject;
  on a high-cardinality group-by, switch to percentile_approx and say why.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("67-statistical-calculations")
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
# 8 tests by 8 DIFFERENT students, so COUNT(*) and COUNT(DISTINCT) coincide.
spark.sql("""
CREATE OR REPLACE TEMP VIEW test_results AS
SELECT * FROM VALUES
    (1, 1040, 'Math', CAST(55.6 AS DECIMAL(10,2)), DATE'2024-02-17'),
    (2, 1017, 'Math', CAST(62.2 AS DECIMAL(10,2)), DATE'2024-01-09'),
    (3, 1047, 'Math', CAST(55.1 AS DECIMAL(10,2)), DATE'2024-02-17'),
    (4, 1034, 'Math', CAST(54.3 AS DECIMAL(10,2)), DATE'2024-01-28'),
    (5, 1002, 'Math', CAST(51.5 AS DECIMAL(10,2)), DATE'2024-01-14'),
    (6, 1014, 'Math', CAST(75.3 AS DECIMAL(10,2)), DATE'2024-01-02'),
    (7, 1035, 'Math', CAST(59.9 AS DECIMAL(10,2)), DATE'2024-02-11'),
    (8, 1044, 'Math', CAST(77.2 AS DECIMAL(10,2)), DATE'2024-01-15')
AS t(test_id, student_id, subject, score, test_date)
""")

from pyspark.sql import functions as F

# STDDEV_SAMP is explicit; median via exact, interpolating PERCENTILE.
SQL = """
SELECT subject,
       COUNT(DISTINCT student_id)                        AS student_count,
       ROUND(AVG(score), 2)                              AS avg_score,
       MIN(score)                                        AS min_score,
       MAX(score)                                        AS max_score,
       ROUND(STDDEV_SAMP(CAST(score AS DOUBLE)), 2)      AS std_dev,
       PERCENTILE(CAST(score AS DOUBLE), 0.5)            AS median_score
FROM test_results
GROUP BY subject
ORDER BY subject
"""

spark.sql(SQL).show(truncate=False)

expect("Q67 per-subject statistics", SQL, [
    ("Math", 8, 61.39, 51.5, 77.2, 9.77, 57.75),
])

# DataFrame API equivalent.
score_d = F.col("score").cast("double")
df = (spark.table("test_results").groupBy("subject")
      .agg(F.countDistinct("student_id").alias("student_count"),
           F.round(F.avg("score"), 2).alias("avg_score"),
           F.min("score").alias("min_score"),
           F.max("score").alias("max_score"),
           F.round(F.stddev_samp(score_d), 2).alias("std_dev"),
           F.expr("percentile(cast(score as double), 0.5)").alias("median_score"))
      .orderBy("subject"))
assert [(r[0], r[1], float(r[2]), float(r[3]), float(r[4]), float(r[5]), float(r[6]))
        for r in df.collect()] == [("Math", 8, 61.39, 51.5, 77.2, 9.77, 57.75)]
print("[PASS] Q67 DataFrame API matches SQL")

# ------------------------------------------------ verify avg and median by hand
scores = [55.6, 62.2, 55.1, 54.3, 51.5, 75.3, 59.9, 77.2]
assert round(sum(scores) / len(scores), 2) == 61.39
srt = sorted(scores)                                  # ..., 55.6, 59.9, ...
assert (srt[3] + srt[4]) / 2 == 57.75, srt
print(f"[PASS] Q67 hand-computed avg 61.39 and median 57.75 (midpoint of "
      f"{srt[3]} and {srt[4]})")

# ------------------------------------------------ the sample-vs-population trap
both = spark.sql("""
SELECT ROUND(STDDEV_SAMP(CAST(score AS DOUBLE)), 2) AS samp,
       ROUND(STDDEV_POP(CAST(score AS DOUBLE)), 2)  AS pop,
       ROUND(STDDEV(CAST(score AS DOUBLE)), 2)      AS bare
FROM test_results
""").collect()[0]
assert (float(both[0]), float(both[1]), float(both[2])) == (9.77, 9.13, 9.77), both
print("[PASS] Q67 stddev_samp 9.77 vs stddev_pop 9.13 -- STDDEV() aliases the sample form")

# ------------------------------------------------ the DISTINCT-students trap
# Give student 1040 a second test: COUNT(*) becomes 9, distinct stays 8.
spark.sql("""
CREATE OR REPLACE TEMP VIEW test_results AS
SELECT * FROM VALUES
    (1, 1040, 'Math', CAST(55.6 AS DECIMAL(10,2)), DATE'2024-02-17'),
    (2, 1017, 'Math', CAST(62.2 AS DECIMAL(10,2)), DATE'2024-01-09'),
    (3, 1047, 'Math', CAST(55.1 AS DECIMAL(10,2)), DATE'2024-02-17'),
    (4, 1034, 'Math', CAST(54.3 AS DECIMAL(10,2)), DATE'2024-01-28'),
    (5, 1002, 'Math', CAST(51.5 AS DECIMAL(10,2)), DATE'2024-01-14'),
    (6, 1014, 'Math', CAST(75.3 AS DECIMAL(10,2)), DATE'2024-01-02'),
    (7, 1035, 'Math', CAST(59.9 AS DECIMAL(10,2)), DATE'2024-02-11'),
    (8, 1044, 'Math', CAST(77.2 AS DECIMAL(10,2)), DATE'2024-01-15'),
    (9, 1040, 'Math', CAST(60.0 AS DECIMAL(10,2)), DATE'2024-03-01')
AS t(test_id, student_id, subject, score, test_date)
""")
counts = spark.sql("""
SELECT COUNT(*) AS rows, COUNT(DISTINCT student_id) AS students FROM test_results
""").collect()[0]
assert (counts[0], counts[1]) == (9, 8), counts
got = spark.sql(SQL).collect()[0]
assert got[1] == 8, got
print("[PASS] Q67 with a repeat test-taker: 9 rows but student_count stays 8")

# ------------------------------------------------ min/max keep their own scale
assert float(got[3]) == 51.5 and float(got[4]) == 77.2
print("[PASS] Q67 min/max are unrounded data points (51.5 / 77.2)")

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 has STDDEV_SAMP, STDDEV_POP, MIN, MAX, AVG, COUNT(DISTINCT).
# It does NOT have an exact interpolating PERCENTILE aggregate (the
# built-in PERCENTILE_CONT was added in MySQL 8.0.2 as a window function
# only, not as a GROUP BY aggregate). The portable workaround for an
# exact median per group is a self-join with row positions, or a stored
# function. The window-function form PERCENT_RANK + a sort is shown here
# for completeness; on small per-group data the self-join is simpler.
#
# CREATE TABLE test_results (
#     test_id    INT          NOT NULL,
#     student_id INT          NOT NULL,
#     subject    VARCHAR(16)  NOT NULL,
#     score      DECIMAL(10,2) NOT NULL,
#     test_date  DATE         NOT NULL,
#     PRIMARY KEY (test_id),
#     KEY ix_tr_subject (subject, score)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO test_results (test_id, student_id, subject, score, test_date) VALUES
#     (1, 1040, 'Math', 55.6, '2024-02-17'),
#     (2, 1017, 'Math', 62.2, '2024-01-09'),
#     (3, 1047, 'Math', 55.1, '2024-02-17'),
#     (4, 1034, 'Math', 54.3, '2024-01-28'),
#     (5, 1002, 'Math', 51.5, '2024-01-14'),
#     (6, 1014, 'Math', 75.3, '2024-01-02'),
#     (7, 1035, 'Math', 59.9, '2024-02-11'),
#     (8, 1044, 'Math', 77.2, '2024-01-15');
#
# SELECT subject,
#        COUNT(DISTINCT student_id)             AS student_count,
#        ROUND(AVG(score), 2)                   AS avg_score,
#        MIN(score)                             AS min_score,
#        MAX(score)                             AS max_score,
#        ROUND(STDDEV_SAMP(score), 2)           AS std_dev
# FROM test_results
# GROUP BY subject
# ORDER BY subject;
#
# -- Per-group median via self-join on row positions (exact, interpolating).
# -- For n=8, the median is AVG of the 4th and 5th sorted values:
# SELECT t.subject,
#        ( (SELECT s.score
#            FROM test_results s
#            WHERE s.subject = t.subject
#            ORDER BY s.score
#            LIMIT 1 OFFSET 3)            -- 4th value (0-indexed offset 3)
#        + (SELECT s.score
#            FROM test_results s
#            WHERE s.subject = t.subject
#            ORDER BY s.score
#            LIMIT 1 OFFSET 4) ) / 2      -- 5th value
#        AS median_score
# FROM (SELECT DISTINCT subject FROM test_results) t;
