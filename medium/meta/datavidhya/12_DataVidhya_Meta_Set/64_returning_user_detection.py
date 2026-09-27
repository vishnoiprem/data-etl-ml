"""
Q64: Returning User Detection   [Medium | Self Joins, Mathematical Functions]
DataVidhya slug: returning-user-detection

A returning active user has two purchases on DIFFERENT dates at most 7 days
apart. Return the distinct qualifying user_ids.

How to Think:
- "Two events within N days of each other" is a SELF-JOIN on user with a range
  predicate on the date difference. The existence of ONE such pair qualifies the
  user, so it is a semi-join in spirit: DISTINCT user_id, no counting.
- Write the predicate one-directional (`b.created_at > a.created_at`) rather
  than using ABS(). It halves the join output and encodes "different dates"
  in the same condition -- strict `>` excludes same-date pairs for free.
- The LAG alternative (compare each purchase to the user's previous one) is
  cheaper -- one window instead of a join -- and is equivalent here because if
  ANY pair is within 7 days then some ADJACENT pair is too. That argument is
  worth making out loud; it is the optimisation the interviewer is listening for.

The trap:
- "No more than seven days apart" is INCLUSIVE: exactly 7 qualifies. `< 7`
  silently drops the boundary case. The shipped data has gaps of 5 and 11 days,
  so it cannot catch this -- asserted separately below.
- "On DIFFERENT dates" excludes two purchases on the SAME day. A user who buys
  twice on 2024-01-01 has a 0-day gap, which passes `<= 7` but must NOT qualify.
  This is the second planted requirement and the reason for strict `>`.
- DISTINCT is required: a user with three qualifying purchases produces multiple
  pairs and would otherwise be listed several times.
- User 30 has only one purchase, so there is no pair at all -- the self-join
  drops them naturally.

Spark note:
- The self-join predicate is a range, so Spark cannot hash it: it becomes a
  shuffle-hash on user_id plus a nested loop inside each partition. The LAG form
  is one window -- prefer it at scale.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("64-returning-user-detection")
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


MAX_GAP_DAYS = 7

# ---------------------------------------------------------- sample data
# Exactly the rows DataVidhya ships with the question.
# User 10: 5-day gap (qualifies). User 20: 11 days. User 30: one purchase.
spark.sql("""
CREATE OR REPLACE TEMP VIEW amazon_transactions AS
SELECT * FROM VALUES
    (1, 10, 'Book', DATE'2024-01-01', 20),
    (2, 10, 'Pen',  DATE'2024-01-06',  5),
    (3, 20, 'Game', DATE'2024-02-01', 40),
    (4, 20, 'Toy',  DATE'2024-02-12', 30),
    (5, 30, 'Lamp', DATE'2024-03-01', 25)
AS t(id, user_id, item, created_at, revenue)
""")

from pyspark.sql import functions as F, Window as W

# Strict > encodes "different dates"; <= MAX_GAP_DAYS is inclusive.
SQL = f"""
SELECT DISTINCT a.user_id
FROM amazon_transactions a
JOIN amazon_transactions b
  ON b.user_id = a.user_id
 AND b.created_at > a.created_at                              -- different dates
 AND DATEDIFF(b.created_at, a.created_at) <= {MAX_GAP_DAYS}   -- inclusive
ORDER BY a.user_id
"""

spark.sql(SQL).show(truncate=False)

expect("Q64 returning users", SQL, [(10,)])

# DataFrame API equivalent.
a, b = (spark.table("amazon_transactions").alias("a"),
        spark.table("amazon_transactions").alias("b"))
df = (a.join(b,
             (F.col("b.user_id") == F.col("a.user_id")) &
             (F.col("b.created_at") > F.col("a.created_at")) &
             (F.datediff(F.col("b.created_at"), F.col("a.created_at")) <= MAX_GAP_DAYS))
      .select(F.col("a.user_id").alias("user_id")).distinct()
      .orderBy("user_id"))
assert [tuple(r) for r in df.collect()] == [(10,)]
print("[PASS] Q64 DataFrame API matches SQL")

# ------------------------------------------------ the LAG formulation
SQL_LAG = f"""
SELECT DISTINCT user_id
FROM (
    SELECT user_id,
           DATEDIFF(created_at,
                    LAG(created_at) OVER (PARTITION BY user_id ORDER BY created_at)) AS gap
    FROM (SELECT DISTINCT user_id, created_at FROM amazon_transactions)
)
WHERE gap BETWEEN 1 AND {MAX_GAP_DAYS}
ORDER BY user_id
"""
expect("Q64 LAG formulation agrees (one window, no range join)", SQL_LAG, [(10,)])

# ------------------------------------------------ show the gaps
gaps = spark.sql("""
SELECT user_id, DATEDIFF(MAX(created_at), MIN(created_at)) AS span, COUNT(*) AS purchases
FROM amazon_transactions GROUP BY user_id ORDER BY user_id
""").collect()
assert [(r[0], r[1], r[2]) for r in gaps] == [(10, 5, 2), (20, 11, 2), (30, 0, 1)], gaps
print(f"[PASS] Q64 gaps: user 10 = 5 days, user 20 = 11 days, user 30 = 1 purchase")

# ------------------------------------------------ the inclusive-boundary trap
# A gap of exactly 7 days MUST qualify.
spark.sql("""
CREATE OR REPLACE TEMP VIEW amazon_transactions AS
SELECT * FROM VALUES
    (1, 40, 'A', DATE'2024-01-01', 10),
    (2, 40, 'B', DATE'2024-01-08', 10),
    (3, 50, 'C', DATE'2024-01-01', 10),
    (4, 50, 'D', DATE'2024-01-09', 10)
AS t(id, user_id, item, created_at, revenue)
""")
expect("Q64 exactly 7 days qualifies; 8 does not", SQL, [(40,)])

strict = spark.sql(f"""
SELECT DISTINCT a.user_id FROM amazon_transactions a
JOIN amazon_transactions b ON b.user_id = a.user_id AND b.created_at > a.created_at
 AND DATEDIFF(b.created_at, a.created_at) < {MAX_GAP_DAYS}
""").collect()
assert strict == [], strict
print("[PASS] Q64 using < 7 instead of <= 7 loses the exactly-7-day user")

# ------------------------------------------------ the same-date trap
# Two purchases on the SAME day are a 0-day gap and must NOT qualify.
spark.sql("""
CREATE OR REPLACE TEMP VIEW amazon_transactions AS
SELECT * FROM VALUES
    (1, 60, 'A', DATE'2024-01-01', 10),
    (2, 60, 'B', DATE'2024-01-01', 10)
AS t(id, user_id, item, created_at, revenue)
""")
expect("Q64 two purchases on the same date do NOT qualify", SQL, [])
expect("Q64 LAG formulation also rejects the same-date pair", SQL_LAG, [])

abs_version = spark.sql(f"""
SELECT DISTINCT a.user_id FROM amazon_transactions a
JOIN amazon_transactions b ON b.user_id = a.user_id AND b.id <> a.id
 AND ABS(DATEDIFF(b.created_at, a.created_at)) <= {MAX_GAP_DAYS}
""").collect()
assert [r[0] for r in abs_version] == [60], abs_version
print("[PASS] Q64 an ABS()/id-inequality version wrongly admits the same-date pair")

# ------------------------------------------------ DISTINCT matters
spark.sql("""
CREATE OR REPLACE TEMP VIEW amazon_transactions AS
SELECT * FROM VALUES
    (1, 70, 'A', DATE'2024-01-01', 10),
    (2, 70, 'B', DATE'2024-01-03', 10),
    (3, 70, 'C', DATE'2024-01-05', 10)
AS t(id, user_id, item, created_at, revenue)
""")
expect("Q64 three qualifying purchases still yield one row", SQL, [(70,)])

without_distinct = spark.sql(f"""
SELECT a.user_id FROM amazon_transactions a
JOIN amazon_transactions b ON b.user_id = a.user_id AND b.created_at > a.created_at
 AND DATEDIFF(b.created_at, a.created_at) <= {MAX_GAP_DAYS}
""").count()
assert without_distinct == 3, without_distinct
print("[PASS] Q64 without DISTINCT the user appears 3 times (one row per qualifying pair)")
