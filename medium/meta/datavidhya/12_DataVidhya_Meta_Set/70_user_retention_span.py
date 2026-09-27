"""
Q70: User Retention   [Medium | Date/Time Functions, Aggregate Functions]
DataVidhya slug: user-retention

Users with 2+ posts: first_post, last_post, days_between, post_count.
Sort by days_between DESC, user_id ASC.

How to Think:
- Despite the title, this is NOT a cohort-retention question (contrast Q40 and
  Q58, which are). It is a plain per-user aggregate: MIN, MAX, DATEDIFF, COUNT.
  Recognising that saves you from building cohorts you do not need.
- The 2+ filter is a condition on an AGGREGATE, so HAVING, not WHERE.
- days_between is derived from the two aggregates in the same SELECT --
  DATEDIFF(MAX(post_date), MIN(post_date)) -- not from a self-join.

The trap:
- `HAVING COUNT(*) >= 2` vs `COUNT(DISTINCT post_date) >= 2`. The spec says
  "at least two POSTS", so COUNT(*) is right -- but note a user with two posts
  on the SAME day qualifies and gets days_between 0. Worth asking about;
  asserted below so the behaviour is pinned.
- The sort is mixed-direction on two keys: days_between DESC then user_id ASC.
  Here user 1 (40 days) precedes user 2 (5 days), which coincides with user_id
  order -- so the sample cannot catch a wrong sort. Asserted on reordered data.
- DATEDIFF's argument order is (end, start) in Spark. Reversed, you get -40.
  Presto's date_diff takes a unit first -- a real portability trap.
- A user with exactly one post is excluded entirely, not shown with 0.

Spark note:
- One shuffle. All four outputs come from a single pass over each user's rows.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("70-user-retention-span")
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


MIN_POSTS = 2

# ---------------------------------------------------------- sample data
# Exactly the rows DataVidhya ships with the question.
spark.sql("""
CREATE OR REPLACE TEMP VIEW posts AS
SELECT * FROM VALUES
    (1, 1, DATE'2024-01-01', 'Hello world'),
    (2, 1, DATE'2024-01-15', 'Second post'),
    (3, 1, DATE'2024-02-10', 'Third post'),
    (4, 2, DATE'2024-01-05', 'My first post'),
    (5, 2, DATE'2024-01-10', 'Update')
AS t(post_id, user_id, post_date, content)
""")

from pyspark.sql import functions as F

# DATEDIFF(end, start) in Spark -- argument order matters.
SQL = f"""
SELECT user_id,
       MIN(post_date)                              AS first_post,
       MAX(post_date)                              AS last_post,
       DATEDIFF(MAX(post_date), MIN(post_date))    AS days_between,
       COUNT(*)                                    AS post_count
FROM posts
GROUP BY user_id
HAVING COUNT(*) >= {MIN_POSTS}
ORDER BY days_between DESC, user_id
"""

spark.sql(SQL).show(truncate=False)

import datetime as dt

EXPECTED = [
    (1, dt.date(2024, 1, 1), dt.date(2024, 2, 10), 40, 3),
    (2, dt.date(2024, 1, 5), dt.date(2024, 1, 10),  5, 2),
]
expect("Q70 post span per repeat poster", SQL, EXPECTED)

# DataFrame API equivalent.
df = (spark.table("posts").groupBy("user_id")
      .agg(F.min("post_date").alias("first_post"),
           F.max("post_date").alias("last_post"),
           F.count(F.lit(1)).alias("post_count"))
      .filter(F.col("post_count") >= MIN_POSTS)
      .withColumn("days_between", F.datediff("last_post", "first_post"))
      .select("user_id", "first_post", "last_post", "days_between", "post_count")
      .orderBy(F.col("days_between").desc(), F.col("user_id")))
assert [tuple(r) for r in df.collect()] == EXPECTED
print("[PASS] Q70 DataFrame API matches SQL")

# ------------------------------------------------ DATEDIFF argument order
fwd, rev = spark.sql("""
SELECT DATEDIFF(DATE'2024-02-10', DATE'2024-01-01') AS fwd,
       DATEDIFF(DATE'2024-01-01', DATE'2024-02-10') AS rev
""").collect()[0]
assert (fwd, rev) == (40, -40), (fwd, rev)
print("[PASS] Q70 DATEDIFF(MAX, MIN) = 40; reversed gives -40")

# ------------------------------------------------ the single-post user
spark.sql("""
CREATE OR REPLACE TEMP VIEW posts AS
SELECT * FROM VALUES
    (1, 1, DATE'2024-01-01', 'Hello world'),
    (2, 1, DATE'2024-01-15', 'Second post'),
    (9, 9, DATE'2024-01-20', 'Only post')
AS t(post_id, user_id, post_date, content)
""")
expect("Q70 a single-post user is excluded, not shown with 0", SQL, [
    (1, dt.date(2024, 1, 1), dt.date(2024, 1, 15), 14, 2),
])

# ------------------------------------------------ the sort-order trap
# User 3 posts across 100 days; user 7 across 2. days_between DESC must put
# user 3 first even though its user_id is smaller -- and a plain user_id sort
# would coincidentally agree, so give user 7 the SMALLER id instead.
spark.sql("""
CREATE OR REPLACE TEMP VIEW posts AS
SELECT * FROM VALUES
    (1, 2, DATE'2024-01-01', 'a'),
    (2, 2, DATE'2024-01-03', 'b'),
    (3, 8, DATE'2024-01-01', 'c'),
    (4, 8, DATE'2024-04-10', 'd')
AS t(post_id, user_id, post_date, content)
""")
expect("Q70 the longer span sorts first even with a larger user_id", SQL, [
    (8, dt.date(2024, 1, 1), dt.date(2024, 4, 10), 100, 2),
    (2, dt.date(2024, 1, 1), dt.date(2024, 1, 3),    2, 2),
])

by_user = [r[0] for r in spark.sql(f"""
SELECT user_id FROM ({SQL.replace('ORDER BY days_between DESC, user_id', '')})
ORDER BY user_id
""").collect()]
assert by_user == [2, 8], by_user
print("[PASS] Q70 sorting by user_id reverses the intended order (2, 8 vs 8, 2)")

# ------------------------------------------------ two posts, same day
spark.sql("""
CREATE OR REPLACE TEMP VIEW posts AS
SELECT * FROM VALUES
    (1, 5, DATE'2024-03-01', 'a'),
    (2, 5, DATE'2024-03-01', 'b')
AS t(post_id, user_id, post_date, content)
""")
expect("Q70 two posts on one day qualify with days_between 0", SQL, [
    (5, dt.date(2024, 3, 1), dt.date(2024, 3, 1), 0, 2),
])

distinct_dates = spark.sql("""
SELECT COUNT(*) FROM (
    SELECT user_id FROM posts GROUP BY user_id HAVING COUNT(DISTINCT post_date) >= 2
)
""").collect()[0][0]
assert distinct_dates == 0
print("[PASS] Q70 COUNT(DISTINCT post_date) >= 2 would exclude them -- "
      "spec says POSTS, so COUNT(*) is right")
