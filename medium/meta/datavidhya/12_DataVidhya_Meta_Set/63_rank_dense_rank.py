"""
Q63: Rank and Dense Rank by Group   [Medium | Window Functions, Partitioning]
DataVidhya slug: rank-dense-rank

Every sale with BOTH sale_rank (RANK: ties leave a gap) and sale_dense_rank
(DENSE_RANK: no gap), per store, amount descending.

How to Think:
- This is the definition question for the whole rank family, asked directly.
  Both columns use the SAME window spec; only the function differs -- so write
  the window once and change the function.
- The mental model:
      ROW_NUMBER  1 2 3 4   always distinct, ties broken arbitrarily
      RANK        1 1 3 4   ties share, next position SKIPS
      DENSE_RANK  1 1 2 3   ties share, no gap
  RANK answers "how many rows are ahead of me, plus one." DENSE_RANK answers
  "how many DISTINCT values are ahead of me, plus one." Say it that way and the
  gap behaviour stops needing memorisation.
- Store A's two 100s make the two columns diverge at the 80 row: RANK 3 (two
  rows precede it) versus DENSE_RANK 2 (80 is the second distinct amount).

The trap:
- Forgetting PARTITION BY store_id. Store B's lone sale of 50 must be rank 1 in
  its own store; globally ranked it would be 5/4. The partition restarts the
  numbering, and that is what "positions restart independently for each store"
  means.
- Substituting ROW_NUMBER for RANK: it gives 1, 2, 3, 4 for store A and never
  shares the tie, so BOTH output columns are wrong.
- The ORDER BY of the final result (store_id, amount DESC, sale_date) is not the
  same as the window's ORDER BY (amount DESC). The extra sale_date key is what
  makes the two tied rows appear in a stable order.
- amount is DECIMAL; 100 prints as 100.00 or 100 depending on scale.

Spark note:
- Both windows share one spec, so Spark computes them in a SINGLE window
  operator over one shuffle+sort. Two different specs would cost two exchanges.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("63-rank-dense-rank")
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
# Store A's sales 1 and 2 both total 100 -- the tie that separates the functions.
spark.sql("""
CREATE OR REPLACE TEMP VIEW store_sales AS
SELECT * FROM VALUES
    (1, 'A', DATE'2024-01-01', CAST(100 AS DECIMAL(10,2))),
    (2, 'A', DATE'2024-01-02', CAST(100 AS DECIMAL(10,2))),
    (3, 'A', DATE'2024-01-03', CAST( 80 AS DECIMAL(10,2))),
    (4, 'A', DATE'2024-01-04', CAST( 60 AS DECIMAL(10,2))),
    (5, 'B', DATE'2024-01-01', CAST( 50 AS DECIMAL(10,2)))
AS t(sale_id, store_id, sale_date, amount)
""")

from pyspark.sql import functions as F, Window as W

# One window spec, two functions.
SQL = """
SELECT store_id,
       sale_date,
       amount,
       RANK()       OVER (PARTITION BY store_id ORDER BY amount DESC) AS sale_rank,
       DENSE_RANK() OVER (PARTITION BY store_id ORDER BY amount DESC) AS sale_dense_rank
FROM store_sales
ORDER BY store_id, amount DESC, sale_date
"""

spark.sql(SQL).show(truncate=False)

import datetime as dt


def d(day):
    return dt.date(2024, 1, day)


EXPECTED = [
    ("A", d(1), 100.0, 1, 1),
    ("A", d(2), 100.0, 1, 1),
    ("A", d(3),  80.0, 3, 2),
    ("A", d(4),  60.0, 4, 3),
    ("B", d(1),  50.0, 1, 1),
]
expect("Q63 rank and dense_rank per store", SQL, EXPECTED)

# DataFrame API equivalent -- one spec reused.
w = W.partitionBy("store_id").orderBy(F.col("amount").desc())
df = (spark.table("store_sales")
      .select("store_id", "sale_date", "amount",
              F.rank().over(w).alias("sale_rank"),
              F.dense_rank().over(w).alias("sale_dense_rank"))
      .orderBy("store_id", F.col("amount").desc(), "sale_date"))
assert [(r[0], r[1], float(r[2]), r[3], r[4]) for r in df.collect()] == EXPECTED
print("[PASS] Q63 DataFrame API matches SQL")

# ------------------------------------------------ the gap, stated precisely
gap_row = [r for r in spark.sql(SQL).collect() if float(r[2]) == 80.0][0]
assert (gap_row[3], gap_row[4]) == (3, 2), gap_row
print("[PASS] Q63 the 80 sale: RANK 3 (two rows ahead) vs DENSE_RANK 2 "
      "(one distinct amount ahead)")

# ------------------------------------------------ all three functions side by side
trio = spark.sql("""
SELECT amount,
       ROW_NUMBER() OVER (PARTITION BY store_id ORDER BY amount DESC, sale_date) AS rn,
       RANK()       OVER (PARTITION BY store_id ORDER BY amount DESC) AS rnk,
       DENSE_RANK() OVER (PARTITION BY store_id ORDER BY amount DESC) AS dense
FROM store_sales WHERE store_id = 'A'
ORDER BY amount DESC, sale_date
""").collect()
assert [(float(r[0]), r[1], r[2], r[3]) for r in trio] == [
    (100.0, 1, 1, 1),
    (100.0, 2, 1, 1),
    ( 80.0, 3, 3, 2),
    ( 60.0, 4, 4, 3),
], trio
print("[PASS] Q63 store A: ROW_NUMBER 1,2,3,4 / RANK 1,1,3,4 / DENSE_RANK 1,1,2,3")

# ------------------------------------------------ the missing-PARTITION-BY trap
# Rank in a subquery, THEN filter -- WHERE runs before window functions, so
# filtering in the same SELECT would rank a single row and hide the bug.
unpartitioned = spark.sql("""
SELECT store_id, amount, rnk, dense FROM (
    SELECT store_id, amount,
           RANK()       OVER (ORDER BY amount DESC) AS rnk,
           DENSE_RANK() OVER (ORDER BY amount DESC) AS dense
    FROM store_sales
) WHERE store_id = 'B'
""").collect()[0]
assert (unpartitioned[2], unpartitioned[3]) == (5, 4), unpartitioned
print("[PASS] Q63 without PARTITION BY, store B's only sale ranks 5/4 instead of 1/1")

# Worth knowing on its own: WHERE is evaluated BEFORE the window, so filtering
# first silently makes the un-partitioned query look correct.
filtered_first = spark.sql("""
SELECT RANK() OVER (ORDER BY amount DESC) AS rnk
FROM store_sales WHERE store_id = 'B'
""").collect()[0][0]
assert filtered_first == 1, filtered_first
print("[PASS] Q63 filtering in the same SELECT ranks only the surviving row -> 1")

# ------------------------------------------------ a three-way tie
spark.sql("""
CREATE OR REPLACE TEMP VIEW store_sales AS
SELECT * FROM VALUES
    (1, 'C', DATE'2024-02-01', CAST(90 AS DECIMAL(10,2))),
    (2, 'C', DATE'2024-02-02', CAST(90 AS DECIMAL(10,2))),
    (3, 'C', DATE'2024-02-03', CAST(90 AS DECIMAL(10,2))),
    (4, 'C', DATE'2024-02-04', CAST(70 AS DECIMAL(10,2)))
AS t(sale_id, store_id, sale_date, amount)
""")
expect("Q63 three-way tie: RANK skips to 4, DENSE_RANK goes to 2", SQL, [
    ("C", dt.date(2024, 2, 1), 90.0, 1, 1),
    ("C", dt.date(2024, 2, 2), 90.0, 1, 1),
    ("C", dt.date(2024, 2, 3), 90.0, 1, 1),
    ("C", dt.date(2024, 2, 4), 70.0, 4, 2),
])
