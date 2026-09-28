"""
Q31: Popularity Percentage   [Hard | Subqueries, Aggregate Functions]
DataVidhya slug: popularity-percentage

friendships holds UNDIRECTED pairs and the same pair may appear in either
direction. Per user, report 100 * friend_count / total_users, rounded to 2dp,
where total_users is the distinct users appearing anywhere in the table.

How to Think:
- Three separate problems stacked; solve them in this order and it stays clean:
    1. CANONICALISE the pairs. LEAST/GREATEST + DISTINCT turns (2,1) and (1,2)
       into one row. Do this FIRST -- dedupe before you mirror, never after.
    2. MIRROR the canonical pairs (UNION ALL both directions) so every user can
       be grouped as a left-hand side.
    3. The DENOMINATOR is a different grain entirely: one scalar for the whole
       table. It is not the number of rows and not the number of friends.
- Say the grain out loud: "one output row = one user who appears anywhere."

The trap:
- Mirroring BEFORE deduping double-counts. Row (1,2) and row (2,1) both mirror,
  so user 1 ends up with friend 2 twice. COUNT(DISTINCT friend) papers over it
  here, but the canonical-pair step is what actually makes it correct -- and the
  moment the metric becomes COUNT(*) or SUM, the ordering bug surfaces.
- total_users = 5 counts users from BOTH columns. Users 4 and 5 never appear in
  user1_id, so `COUNT(DISTINCT user1_id)` gives 2 and every percentage is wrong.
- Integer division: `100 * friend_count / total_users` with integer operands
  truncates to 0 in Presto/Hive. Use `100.0`.
- Self-pairs (a user linked to themselves) would survive LEAST=GREATEST and
  inflate friend_count; guard with `user1_id <> user2_id` on a real graph.

Spark note:
- The denominator is a single scalar, so CROSS JOIN against a 1-row CTE. Spark
  broadcasts it -- no shuffle. A correlated subquery per row would be far worse.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("31-popularity-percentage")
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
# Row (2,1) is the SAME undirected pair as (1,2) -- it must not count twice.
spark.createDataFrame(
    [(1, 2), (1, 3), (2, 1), (2, 4), (3, 5)],
    ["user1_id", "user2_id"],
).createOrReplaceTempView("friendships")

from pyspark.sql import functions as F

SQL = """
WITH canonical AS (
    -- dedupe FIRST: (2,1) collapses onto (1,2)
    SELECT DISTINCT LEAST(user1_id, user2_id)    AS lo,
                    GREATEST(user1_id, user2_id) AS hi
    FROM friendships
),
edges AS (
    -- then mirror, so every user appears as a left-hand side
    SELECT lo AS user_id, hi AS friend_id FROM canonical
    UNION ALL
    SELECT hi AS user_id, lo AS friend_id FROM canonical
),
totals AS (
    -- different grain: one scalar over BOTH columns
    SELECT COUNT(DISTINCT user_id) AS total_users
    FROM (
        SELECT user1_id AS user_id FROM friendships
        UNION ALL
        SELECT user2_id AS user_id FROM friendships
    )
)
SELECT e.user_id,
       ROUND(100.0 * COUNT(DISTINCT e.friend_id) / t.total_users, 2) AS popularity_percentage
FROM edges e
CROSS JOIN totals t
GROUP BY e.user_id, t.total_users
ORDER BY e.user_id
"""

spark.sql(SQL).show(truncate=False)

expect("Q31 popularity percentage", SQL, [
    (1, 40.00),
    (2, 40.00),
    (3, 40.00),
    (4, 20.00),
    (5, 20.00),
])

# DataFrame API equivalent -- same dedupe-then-mirror order.
fr = spark.table("friendships")
canonical = (fr.select(
                F.least("user1_id", "user2_id").alias("lo"),
                F.greatest("user1_id", "user2_id").alias("hi"))
             .distinct())
edges = (canonical.select(F.col("lo").alias("user_id"), F.col("hi").alias("friend_id"))
         .unionAll(canonical.select(F.col("hi").alias("user_id"),
                                    F.col("lo").alias("friend_id"))))
total_users = (fr.select(F.col("user1_id").alias("u"))
               .unionAll(fr.select(F.col("user2_id").alias("u")))
               .agg(F.countDistinct("u").alias("total_users")))
df = (edges.crossJoin(F.broadcast(total_users))
      .groupBy("user_id", "total_users")
      .agg(F.countDistinct("friend_id").alias("friend_count"))
      .select("user_id",
              F.round(F.lit(100.0) * F.col("friend_count") / F.col("total_users"), 2)
               .alias("popularity_percentage"))
      .orderBy("user_id"))
assert [(r[0], float(r[1])) for r in df.collect()] == [
    (1, 40.0), (2, 40.0), (3, 40.0), (4, 20.0), (5, 20.0),
]
print("[PASS] Q31 DataFrame API matches SQL")

# ------------------------------------------------- the denominator trap
# total_users must span BOTH columns. Users 4 and 5 never appear in user1_id.
both, left_only = spark.sql("""
SELECT (SELECT COUNT(DISTINCT user_id) FROM (
            SELECT user1_id AS user_id FROM friendships
            UNION ALL SELECT user2_id AS user_id FROM friendships)) AS both_cols,
       (SELECT COUNT(DISTINCT user1_id) FROM friendships) AS left_only
""").collect()[0]
assert (both, left_only) == (5, 3), (both, left_only)
print("[PASS] Q31 denominator is 5 (both columns), not 3 (user1_id only)")

# ------------------------------------------------- the mirror-before-dedupe trap
# Mirroring raw rows gives user 1 the friend 2 twice.
raw_dupes = spark.sql("""
SELECT COUNT(*) FROM (
    SELECT user1_id AS u, user2_id AS f FROM friendships
    UNION ALL SELECT user2_id, user1_id FROM friendships
) WHERE u = 1 AND f = 2
""").collect()[0][0]
canon_dupes = spark.sql("""
WITH canonical AS (
    SELECT DISTINCT LEAST(user1_id, user2_id) AS lo, GREATEST(user1_id, user2_id) AS hi
    FROM friendships
)
SELECT COUNT(*) FROM (
    SELECT lo AS u, hi AS f FROM canonical UNION ALL SELECT hi, lo FROM canonical
) WHERE u = 1 AND f = 2
""").collect()[0][0]
assert (raw_dupes, canon_dupes) == (2, 1), (raw_dupes, canon_dupes)
print("[PASS] Q31 mirroring raw rows duplicates the (1,2) edge; canonicalising first does not")

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports LEAST, GREATEST, CTEs, and UNION ALL identically. The
# dedupe-then-mirror order is what keeps an undirected pair from inflating a
# friend's count. The denominator must count distinct ids across BOTH
# columns, not just user1_id. Multiplying by 100.0 forces DECIMAL so integer
# division cannot truncate to 0.
#
# CREATE TABLE friendships (
#     user1_id INT NOT NULL,
#     user2_id INT NOT NULL,
#     PRIMARY KEY (user1_id, user2_id),
#     KEY ix_friends_user2 (user2_id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO friendships (user1_id, user2_id) VALUES
#     (1, 2), (1, 3), (2, 1), (2, 4), (3, 5);
#
# WITH canonical AS (
#     SELECT DISTINCT LEAST(user1_id, user2_id)    AS lo,
#                     GREATEST(user1_id, user2_id) AS hi
#     FROM friendships
# ),
# edges AS (
#     SELECT lo AS user_id, hi AS friend_id FROM canonical
#     UNION ALL
#     SELECT hi AS user_id, lo AS friend_id FROM canonical
# ),
# totals AS (
#     SELECT COUNT(DISTINCT user_id) AS total_users
#     FROM (
#         SELECT user1_id AS user_id FROM friendships
#         UNION ALL
#         SELECT user2_id AS user_id FROM friendships
#     ) both
# )
# SELECT e.user_id,
#        ROUND(100.0 * COUNT(DISTINCT e.friend_id) / t.total_users, 2) AS popularity_percentage
# FROM edges e
# CROSS JOIN totals t
# GROUP BY e.user_id, t.total_users
# ORDER BY e.user_id;
#
# -- Expected:
# -- 1  40.00
# -- 2  40.00
# -- 3  40.00
# -- 4  20.00
# -- 5  20.00