"""
Q36: User Popularity Score   [Hard | Common Table Expressions, Aggregate Functions]
DataVidhya slug: user-popularity-score

Each row of cup_user_percentage means follower_id follows user_id. Every id in
either column is a registered user. For each user with at least one follower,
report famous_percentage = followers * 100 / total_platform_users, 2dp.

How to Think:
- Two grains, and they are the whole question:
    NUMERATOR   -> per user: COUNT(followers). Grouped.
    DENOMINATOR -> one scalar for the entire platform: distinct ids across BOTH
                   columns. Ungrouped.
  Compute them in separate CTEs and CROSS JOIN. Mixing them in one GROUP BY is
  how the denominator ends up per-group and every number comes out 100.
- Note this is the DIRECTED twin of Q31 (popularity-percentage), which is the
  undirected version. Here (1,2) and (2,1) are DIFFERENT facts -- "1 follows 2"
  is not "2 follows 1" -- so there is NO canonicalising step and no mirroring.
  Do not reuse the LEAST/GREATEST trick from Q31; it would destroy the direction.

The trap:
- total_users spans BOTH columns. Users 3, 4, 7, 8, 10 only ever appear as
  followers and never as a followed user, so `COUNT(DISTINCT user_id)` gives 8
  and every percentage is inflated. The correct denominator is 13.
- Only users that appear as a `user_id` are output -- 8 rows, not 13. Pure
  followers (3, 4, 7, 8, 10) are counted in the denominator but get no row.
  "Counted in the total but absent from the output" is the asymmetry being
  tested.
- Integer division: `followers * 100 / total_users` truncates to 0 in
  Presto/Hive. Multiply by 100.0.
- 2/13 = 15.3846... -> 15.38, and 1/13 = 7.6923... -> 7.69. Both round DOWN, so
  a truncating implementation coincidentally agrees here. Do not rely on that.

Spark note:
- The denominator CTE collapses to one row, so Spark broadcasts it and the
  CROSS JOIN costs nothing. A correlated scalar subquery evaluated per row would
  be far worse.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("36-user-popularity-score")
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
# 13 distinct ids across both columns; only 8 appear as user_id.
spark.createDataFrame(
    [(1, 2), (1, 3), (2, 4), (5, 1), (5, 3), (11, 7), (12, 8),
     (13, 5), (13, 10), (14, 12), (14, 3), (15, 14), (15, 13)],
    "user_id INT, follower_id INT",
).createOrReplaceTempView("cup_user_percentage")

from pyspark.sql import functions as F

SQL = """
WITH all_users AS (
    -- the denominator's grain: every id anywhere in the table
    SELECT user_id AS id FROM cup_user_percentage
    UNION ALL
    SELECT follower_id AS id FROM cup_user_percentage
),
platform AS (
    SELECT COUNT(DISTINCT id) AS total_users FROM all_users
),
followers AS (
    -- the numerator's grain: one row per followed user
    SELECT user_id, COUNT(DISTINCT follower_id) AS follower_count
    FROM cup_user_percentage
    GROUP BY user_id
)
SELECT f.user_id,
       ROUND(f.follower_count * 100.0 / p.total_users, 2) AS famous_percentage
FROM followers f
CROSS JOIN platform p
ORDER BY f.user_id
"""

spark.sql(SQL).show(truncate=False)

expect("Q36 famous percentage", SQL, [
    (1, 15.38),
    (2, 7.69),
    (5, 15.38),
    (11, 7.69),
    (12, 7.69),
    (13, 15.38),
    (14, 15.38),
    (15, 15.38),
])

# DataFrame API equivalent.
g = spark.table("cup_user_percentage")
platform = (g.select(F.col("user_id").alias("id"))
            .unionAll(g.select(F.col("follower_id").alias("id")))
            .agg(F.countDistinct("id").alias("total_users")))
df = (g.groupBy("user_id")
      .agg(F.countDistinct("follower_id").alias("follower_count"))
      .crossJoin(F.broadcast(platform))
      .select("user_id",
              F.round(F.col("follower_count") * F.lit(100.0) / F.col("total_users"), 2)
               .alias("famous_percentage"))
      .orderBy("user_id"))
assert [(r[0], float(r[1])) for r in df.collect()] == [
    (1, 15.38), (2, 7.69), (5, 15.38), (11, 7.69),
    (12, 7.69), (13, 15.38), (14, 15.38), (15, 15.38),
]
print("[PASS] Q36 DataFrame API matches SQL")

# ------------------------------------------------ the denominator trap
both, followed_only = spark.sql("""
SELECT (SELECT COUNT(DISTINCT id) FROM (
            SELECT user_id AS id FROM cup_user_percentage
            UNION ALL SELECT follower_id FROM cup_user_percentage)) AS both_cols,
       (SELECT COUNT(DISTINCT user_id) FROM cup_user_percentage) AS followed_only
""").collect()[0]
assert (both, followed_only) == (13, 8), (both, followed_only)
print("[PASS] Q36 denominator is 13 (both columns), not 8 (user_id only)")

# ------------------------------------------------ the output-cardinality trap
# 13 users in the denominator, but only 8 output rows.
n_rows = spark.sql(SQL).count()
assert (n_rows, both) == (8, 13), (n_rows, both)
print("[PASS] Q36 8 output rows against a denominator of 13 -- pure followers get no row")

# ------------------------------------------------ this is DIRECTED, unlike Q31
# Row (5,1) says "1 follows 5". Mirroring edges -- correct in Q31, wrong here --
# would hand user 1 a third follower and report 23.08% instead of 15.38%.
directed, mirrored = spark.sql("""
SELECT (SELECT COUNT(DISTINCT follower_id) FROM cup_user_percentage
        WHERE user_id = 1) AS directed,
       (SELECT COUNT(DISTINCT f) FROM (
            SELECT user_id AS u, follower_id AS f FROM cup_user_percentage
            UNION ALL
            SELECT follower_id AS u, user_id AS f FROM cup_user_percentage
        ) WHERE u = 1) AS mirrored
""").collect()[0]
assert (directed, mirrored) == (2, 3), (directed, mirrored)
print("[PASS] Q36 mirroring inflates user 1 from 2 followers to 3 -- follows are directed")
