"""
Q50: Find Mutual Friends Between Two Users   [Medium | Self Joins]
DataVidhya slug: mutual-friends

Return the friends common to user 1 and user 2.

How to Think:
- Two friend lists, one intersection. The clearest expression is literally
  INTERSECT, which also dedupes for free -- the spec's "return each mutual
  friend once" requirement disappears into the operator.
- The self-join formulation is the same thing:
      f1 JOIN f2 ON f1.friend_id = f2.friend_id
      WHERE f1.user_id = 1 AND f2.user_id = 2
  Worth having both ready: INTERSECT reads better, the join generalises to
  "mutual friends for every PAIR of users" when the follow-up arrives.

The trap:
- Users 1 and 2 are friends WITH EACH OTHER: row (1,2) and row (2,1) exist. So
  2 appears in user 1's list and 1 appears in user 2's list. Neither is a MUTUAL
  friend, and the expected output is {3, 5} -- not {1, 2, 3, 5}. Any solution
  that unions the lists instead of intersecting them, or that forgets the two
  principals are in each other's lists, gets this wrong.
- INTERSECT is set semantics and dedupes; INTERSECT ALL does not. If the table
  can hold duplicate (user_id, friend_id) rows, the self-join version needs an
  explicit DISTINCT.
- The table here is DIRECTED as stored (each user's own list), so do NOT mirror
  or canonicalise the pairs the way Q31 does -- you would drag in friends of
  user 2 that user 1 never listed.
- Sort ascending; set operations do not preserve order.

Spark note:
- Both sides come from one scan of a tiny table. INTERSECT compiles to a
  left-semi join plus a distinct, so it is not more expensive than the manual
  self-join -- pick it for readability.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("50-mutual-friends")
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


USER_A, USER_B = 1, 2

# ---------------------------------------------------------- sample data
# Exactly the rows DataVidhya ships with the question.
# Note (1,2) and (2,1): the two principals are in each other's lists.
spark.sql("""
CREATE OR REPLACE TEMP VIEW friendships AS
SELECT * FROM VALUES
    (1, 2), (1, 3), (1, 4), (1, 5),
    (2, 1), (2, 3), (2, 5), (2, 6)
AS t(user_id, friend_id)
""")

from pyspark.sql import functions as F

SQL = f"""
SELECT friend_id AS mutual_friend_id FROM friendships WHERE user_id = {USER_A}
INTERSECT
SELECT friend_id AS mutual_friend_id FROM friendships WHERE user_id = {USER_B}
ORDER BY mutual_friend_id
"""

spark.sql(SQL).show(truncate=False)

expect("Q50 mutual friends of users 1 and 2", SQL, [(3,), (5,)])

# The self-join formulation -- generalises to all pairs.
SQL_JOIN = f"""
SELECT DISTINCT f1.friend_id AS mutual_friend_id
FROM friendships f1
JOIN friendships f2 ON f2.friend_id = f1.friend_id
WHERE f1.user_id = {USER_A}
  AND f2.user_id = {USER_B}
ORDER BY mutual_friend_id
"""
expect("Q50 self-join formulation agrees", SQL_JOIN, [(3,), (5,)])

# DataFrame API equivalent.
fr = spark.table("friendships")
a = fr.filter(F.col("user_id") == USER_A).select(F.col("friend_id").alias("mutual_friend_id"))
b = fr.filter(F.col("user_id") == USER_B).select(F.col("friend_id").alias("mutual_friend_id"))
df = a.intersect(b).orderBy("mutual_friend_id")
assert [tuple(r) for r in df.collect()] == [(3,), (5,)]
print("[PASS] Q50 DataFrame API matches SQL")

# ------------------------------------------------ the principals-are-friends trap
# 2 is in user 1's list and 1 is in user 2's list, but neither is mutual.
lists = spark.sql("""
SELECT user_id, SORT_ARRAY(COLLECT_SET(friend_id)) AS friends
FROM friendships WHERE user_id IN (1, 2) GROUP BY user_id ORDER BY user_id
""").collect()
assert [(r[0], r[1]) for r in lists] == [(1, [2, 3, 4, 5]), (2, [1, 3, 5, 6])], lists
result = {r[0] for r in spark.sql(SQL).collect()}
assert result == {3, 5} and 1 not in result and 2 not in result, result
print("[PASS] Q50 users 1 and 2 are in each other's lists but are not mutual friends")

# ------------------------------------------------ UNION is not INTERSECT
unioned = sorted({r[0] for r in spark.sql("""
SELECT friend_id FROM friendships WHERE user_id = 1
UNION
SELECT friend_id FROM friendships WHERE user_id = 2
""").collect()})
assert unioned == [1, 2, 3, 4, 5, 6], unioned
print("[PASS] Q50 UNION returns all six ids; only the intersection {3,5} is correct")

# ------------------------------------------------ duplicate rows stay deduped
spark.sql("""
CREATE OR REPLACE TEMP VIEW friendships AS
SELECT * FROM VALUES
    (1, 3), (1, 3), (1, 5),
    (2, 3), (2, 5), (2, 5)
AS t(user_id, friend_id)
""")
expect("Q50 duplicate source rows still yield one row each", SQL, [(3,), (5,)])
expect("Q50 self-join needs its explicit DISTINCT", SQL_JOIN, [(3,), (5,)])

no_distinct = spark.sql("""
SELECT f1.friend_id FROM friendships f1
JOIN friendships f2 ON f2.friend_id = f1.friend_id
WHERE f1.user_id = 1 AND f2.user_id = 2
""").count()
assert no_distinct == 4, no_distinct   # 3: 2x1 rows, 5: 1x2 rows
print("[PASS] Q50 the self-join without DISTINCT fans out to 4 rows")

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports INTERSECT (dedupes set members). The self-join
# formulation generalises to per-pair mutual friends and needs DISTINCT
# when the source has duplicates.
#
# CREATE TABLE friendships (
#     user_id    INT NOT NULL,
#     friend_id  INT NOT NULL,
#     PRIMARY KEY (user_id, friend_id),
#     KEY ix_f_user (user_id),
#     KEY ix_f_friend (friend_id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO friendships (user_id, friend_id) VALUES
#     (1, 2), (1, 3), (1, 4), (1, 5),
#     (2, 1), (2, 3), (2, 5), (2, 6);
#
# -- INTERSECT form (dedupes):
# SELECT friend_id AS mutual_friend_id FROM friendships WHERE user_id = 1
# INTERSECT
# SELECT friend_id AS mutual_friend_id FROM friendships WHERE user_id = 2
# ORDER BY mutual_friend_id;
#
# -- Self-join form (generalises; needs DISTINCT):
# SELECT DISTINCT f1.friend_id AS mutual_friend_id
# FROM friendships f1
# JOIN friendships f2 ON f2.friend_id = f1.friend_id
# WHERE f1.user_id = 1 AND f2.user_id = 2
# ORDER BY mutual_friend_id;
#
# -- Both forms return: (3,), (5,).
