"""
Q45: Comments Histogram by Users   [Medium | Subqueries, Aggregate Functions]
DataVidhya slug: comments-histogram-by-users

January 2020 only. Count comments per user, then count how many users hit each
distinct comment total.

How to Think:
- This is AGGREGATE OF AN AGGREGATE, and naming the two grains is the whole job:
    inner -> one row per USER          (comment_count = COUNT(*) per user)
    outer -> one row per COMMENT_COUNT (user_count = COUNT(*) per bucket)
  "A histogram" always means this shape. You cannot do it in one GROUP BY.
- `users` is a decoy: it contributes no output column, and the "must have at
  least one January comment" rule is satisfied by grouping `comments` alone.
  Joining it in can only hurt.

The trap:
- The outer COUNT(*) counts USERS, because the inner result has one row per
  user. Writing SUM(comment_count) in the outer query returns comments, not
  users -- and both are plausible small integers.
- User 4's only comment is 2020-02-03. Forget the month filter and a third
  bucket appears. Note the filter must run in the INNER query; filtering after
  the per-user counts are computed is too late.
- A user with zero January comments must not land in a `comment_count = 0`
  bucket. Grouping `comments` gives that for free; a LEFT JOIN from `users`
  would manufacture it.
- The buckets are the OBSERVED totals only. Do not densify to 1,2,3,...

Spark note:
- Two shuffles, one per aggregation level. The first collapses to one row per
  user, so the second shuffle is tiny -- the cost is all in the first.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("45-comments-histogram")
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
# Comment 6 (user 4) is dated 2020-02-03 -- outside January, so user 4 drops out.
spark.sql("""
CREATE OR REPLACE TEMP VIEW comments AS
SELECT * FROM VALUES
    (1, 1, DATE'2020-01-05', 'Comment text', 16),
    (2, 1, DATE'2020-01-22', 'Comment text',  2),
    (3, 2, DATE'2020-01-09', 'Comment text', 15),
    (4, 2, DATE'2020-01-16', 'Comment text', 44),
    (5, 3, DATE'2020-01-31', 'Comment text',  8),
    (6, 4, DATE'2020-02-03', 'Comment text', 30),
    (7, 5, DATE'2020-01-11', 'Comment text',  7)
AS t(comment_id, user_id, comment_date, comment_text, likes)
""")
spark.sql("""
CREATE OR REPLACE TEMP VIEW users AS
SELECT * FROM VALUES
    (1, 'User_1', DATE'2019-12-01'),
    (2, 'User_2', DATE'2019-12-01'),
    (3, 'User_3', DATE'2019-12-01'),
    (4, 'User_4', DATE'2019-12-01'),
    (5, 'User_5', DATE'2019-12-01')
AS t(user_id, name, join_date)
""")

from pyspark.sql import functions as F

SQL = """
WITH per_user AS (
    -- inner grain: one row per user
    SELECT user_id, COUNT(*) AS comment_count
    FROM comments
    WHERE comment_date >= DATE'2020-01-01'
      AND comment_date <  DATE'2020-02-01'
    GROUP BY user_id
)
SELECT comment_count,
       COUNT(*) AS user_count      -- counts USERS, because per_user is per-user
FROM per_user
GROUP BY comment_count
ORDER BY comment_count
"""

spark.sql(SQL).show(truncate=False)

expect("Q45 comments histogram", SQL, [(1, 2), (2, 2)])

# DataFrame API equivalent.
per_user = (spark.table("comments")
            .filter((F.col("comment_date") >= F.lit("2020-01-01").cast("date")) &
                    (F.col("comment_date") < F.lit("2020-02-01").cast("date")))
            .groupBy("user_id").agg(F.count(F.lit(1)).alias("comment_count")))
df = (per_user.groupBy("comment_count")
      .agg(F.count(F.lit(1)).alias("user_count"))
      .orderBy("comment_count"))
assert [tuple(r) for r in df.collect()] == [(1, 2), (2, 2)]
print("[PASS] Q45 DataFrame API matches SQL")

# ------------------------------------------------ COUNT vs SUM in the outer query
sums = spark.sql("""
WITH per_user AS (
    SELECT user_id, COUNT(*) AS comment_count FROM comments
    WHERE comment_date >= DATE'2020-01-01' AND comment_date < DATE'2020-02-01'
    GROUP BY user_id
)
SELECT comment_count, SUM(comment_count) AS wrong_counts_comments
FROM per_user GROUP BY comment_count ORDER BY comment_count
""").collect()
assert [(r[0], r[1]) for r in sums] == [(1, 2), (2, 4)], sums
print("[PASS] Q45 SUM(comment_count) gives (1,2),(2,4) -- counts comments, not users")

# ------------------------------------------------ the month-filter trap
unfiltered = spark.sql("""
WITH per_user AS (SELECT user_id, COUNT(*) AS comment_count FROM comments GROUP BY user_id)
SELECT comment_count, COUNT(*) AS user_count
FROM per_user GROUP BY comment_count ORDER BY comment_count
""").collect()
assert [(r[0], r[1]) for r in unfiltered] == [(1, 3), (2, 2)], unfiltered
print("[PASS] Q45 dropping the month filter pulls user 4 in (bucket 1 becomes 3, not 2)")

# ------------------------------------------------ the zero-bucket trap
zero_bucket = spark.sql("""
WITH per_user AS (
    SELECT u.user_id,
           COUNT(CASE WHEN c.comment_date >= DATE'2020-01-01'
                       AND c.comment_date <  DATE'2020-02-01' THEN 1 END) AS comment_count
    FROM users u LEFT JOIN comments c ON c.user_id = u.user_id
    GROUP BY u.user_id
)
SELECT comment_count, COUNT(*) AS user_count
FROM per_user GROUP BY comment_count ORDER BY comment_count
""").collect()
assert [(r[0], r[1]) for r in zero_bucket] == [(0, 1), (1, 2), (2, 2)], zero_bucket
print("[PASS] Q45 starting from `users` invents a comment_count = 0 bucket")
