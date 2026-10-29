"""
Q46: Consecutive Numbers   [Medium | Window Functions, Gap And Island]
DataVidhya slug: consecutive-numbers

Find every `num` that appears in 3+ back-to-back rows by id. A value recurring
later, separated by other values, starts a fresh run.

How to Think:
- Gap-and-island. The trick: for rows sharing the same `num`,
  `id - ROW_NUMBER() OVER (PARTITION BY num ORDER BY id)` is CONSTANT across a
  run of consecutive ids and CHANGES whenever the run breaks. That constant is
  the island key, so GROUP BY (num, key) + HAVING COUNT(*) >= 3 is the answer.
- Why it works: inside a run, id and the row number both increase by 1, so the
  difference is fixed. A gap in id advances id faster than the row number and
  the difference jumps.
- The alternative -- three chained LAGs -- is shorter to write but only handles
  "exactly 3" thresholds and does not generalise to "N in a row".

The trap:
- "Consecutive" means ADJACENT IDS, not "adjacent rows in the scan". Those
  differ the moment ids have gaps (deleted rows). `LAG(num) OVER (ORDER BY id)`
  compares the previous ROW regardless of how far away its id is, so ids
  1,2,50 all holding value 1 would wrongly qualify. The shipped data is
  contiguous (1..8) so it cannot catch this -- asserted separately below.
- It is also not "consecutive num VALUES": 1,2,3 in adjacent rows is not a run.
- DISTINCT at the end. A value with two separate qualifying runs must be
  listed once.
- Value 2 occupies ids 4 and 5 -- two in a row, short of the threshold, and it
  is the planted near-miss.

Spark note:
- PARTITION BY num means one shuffle keyed on num, then a sort. Skew is a real
  risk if one value dominates the log.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("46-consecutive-numbers")
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
# 1 runs on ids 1-3, 2 only on 4-5 (the near-miss), 3 on ids 6-8.
spark.sql("""
CREATE OR REPLACE TEMP VIEW logs AS
SELECT * FROM VALUES
    (1, 1), (2, 1), (3, 1),
    (4, 2), (5, 2),
    (6, 3), (7, 3), (8, 3)
AS t(id, num)
""")

from pyspark.sql import functions as F, Window as W

RUN_LENGTH = 3

SQL = f"""
WITH islands AS (
    -- id minus the row number is constant within a run of consecutive ids
    SELECT num,
           id - ROW_NUMBER() OVER (PARTITION BY num ORDER BY id) AS island
    FROM logs
),
runs AS (
    SELECT num, island, COUNT(*) AS run_length
    FROM islands
    GROUP BY num, island
)
SELECT DISTINCT num AS consecutive_num
FROM runs
WHERE run_length >= {RUN_LENGTH}
ORDER BY consecutive_num
"""

spark.sql(SQL).show(truncate=False)

expect("Q46 values appearing 3+ times consecutively", SQL, [(1,), (3,)])

# DataFrame API equivalent.
w = W.partitionBy("num").orderBy("id")
df = (spark.table("logs")
      .withColumn("island", F.col("id") - F.row_number().over(w))
      .groupBy("num", "island").agg(F.count(F.lit(1)).alias("run_length"))
      .filter(F.col("run_length") >= RUN_LENGTH)
      .select(F.col("num").alias("consecutive_num")).distinct()
      .orderBy("consecutive_num"))
assert [tuple(r) for r in df.collect()] == [(1,), (3,)]
print("[PASS] Q46 DataFrame API matches SQL")

# ------------------------------------------------ the chained-LAG variant agrees here
SQL_LAG = """
SELECT DISTINCT num AS consecutive_num
FROM (
    SELECT id, num,
           LAG(num, 1) OVER (ORDER BY id) AS prev1,
           LAG(num, 2) OVER (ORDER BY id) AS prev2
    FROM logs
)
WHERE num = prev1 AND num = prev2
ORDER BY consecutive_num
"""
expect("Q46 chained-LAG variant agrees on contiguous ids", SQL_LAG, [(1,), (3,)])

# ------------------------------------------------ the id-gap trap
# ids 1, 2, 50 all hold value 7. Those ids are NOT adjacent, so 7 must not
# qualify -- but LAG compares the previous ROW and wrongly accepts it.
spark.sql("""
CREATE OR REPLACE TEMP VIEW logs AS
SELECT * FROM VALUES
    (1, 7), (2, 7), (50, 7),
    (60, 9), (61, 9), (62, 9)
AS t(id, num)
""")

expect("Q46 id gaps break the run (7 excluded, 9 kept)", SQL, [(9,)])

lag_result = [r[0] for r in spark.sql(SQL_LAG).collect()]
assert lag_result == [7, 9], lag_result
print("[PASS] Q46 the LAG variant wrongly accepts 7 across the id 2 -> 50 gap")

# ------------------------------------------------ a value with two runs is listed once
spark.sql("""
CREATE OR REPLACE TEMP VIEW logs AS
SELECT * FROM VALUES
    (1, 5), (2, 5), (3, 5),
    (4, 8),
    (5, 5), (6, 5), (7, 5)
AS t(id, num)
""")
expect("Q46 two separate runs of 5 yield one row", SQL, [(5,)])

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports the same `id - ROW_NUMBER() OVER (PARTITION BY num
# ORDER BY id)` gap-and-island pattern verbatim.
#
# CREATE TABLE logs (
#     id  INT NOT NULL,
#     num INT NOT NULL,
#     PRIMARY KEY (id),
#     KEY ix_logs_num (num, id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO logs (id, num) VALUES
#     (1, 1), (2, 1), (3, 1),
#     (4, 2), (5, 2),
#     (6, 3), (7, 3), (8, 3);
#
# WITH islands AS (
#     SELECT num,
#            id - ROW_NUMBER() OVER (PARTITION BY num ORDER BY id) AS island
#     FROM logs
# ),
# runs AS (
#     SELECT num, island, COUNT(*) AS run_length
#     FROM islands GROUP BY num, island
# )
# SELECT DISTINCT num AS consecutive_num
# FROM runs
# WHERE run_length >= 3
# ORDER BY consecutive_num;
#
# -- Expected: (1,), (3,).
