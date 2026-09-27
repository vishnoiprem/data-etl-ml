"""
Q38: 3 Most Recent Posts Per User   [Medium | Window Functions]
DataVidhya slug: ranking-3-most-recent-posts-per-user

Per user, return their 3 newest posts with post_rank (1 = newest).

How to Think:
- Canonical top-N-per-group: rank inside a window, then filter the rank in an
  OUTER query. You cannot filter a window function in WHERE or HAVING -- the
  window is computed after both -- so the subquery is structural, not stylistic.
- ROW_NUMBER is correct here because the spec guarantees at most one post per
  user per date, so there are no ties to resolve and rank 1..3 is unambiguous.

The trap:
- LIMIT 3 limits the WHOLE RESULT, not each user. User 20 would vanish.
- Rank descending. `ORDER BY created_at` (ascending) returns each user's OLDEST
  three, which still produces 4 rows on this data and still looks plausible.
- If the "one post per date" guarantee were dropped, ROW_NUMBER would break ties
  arbitrarily and the output would be non-deterministic -- add post_id as a
  tiebreak. Asserted below, because interviewers remove that guarantee.
- The dropped post is user 10's Jan-01 "Old" row. A user with fewer than 3 posts
  (user 20) must still appear with all they have -- this is not an inner filter.

Spark note:
- One shuffle on user_id, then a sort. Filtering rank <= 3 after the window
  cannot be pushed down, so the window sees every row; partitioning the source
  by user_id is what makes this cheap at scale.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("38-three-recent-posts")
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
# User 10 has 4 posts (the oldest is dropped); user 20 has only 1.
spark.sql("""
CREATE OR REPLACE TEMP VIEW posts AS
SELECT * FROM VALUES
    (1, 10, 'Old',       DATE'2024-01-01', 1),
    (2, 10, 'Middle',    DATE'2024-01-02', 2),
    (3, 10, 'Recent',    DATE'2024-01-03', 3),
    (4, 10, 'Newest',    DATE'2024-01-04', 4),
    (5, 20, 'Only post', DATE'2024-02-01', 5)
AS t(post_id, user_id, content, created_at, likes)
""")

from pyspark.sql import functions as F, Window as W

SQL = """
SELECT user_id, post_id, content, created_at, post_rank
FROM (
    SELECT user_id,
           post_id,
           content,
           created_at,
           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS post_rank
    FROM posts
)
WHERE post_rank <= 3
ORDER BY user_id, post_rank
"""

spark.sql(SQL).show(truncate=False)

import datetime as dt

EXPECTED = [
    (10, 4, "Newest",    dt.date(2024, 1, 4), 1),
    (10, 3, "Recent",    dt.date(2024, 1, 3), 2),
    (10, 2, "Middle",    dt.date(2024, 1, 2), 3),
    (20, 5, "Only post", dt.date(2024, 2, 1), 1),
]
expect("Q38 three most recent posts per user", SQL, EXPECTED)

# DataFrame API equivalent.
w = W.partitionBy("user_id").orderBy(F.col("created_at").desc())
df = (spark.table("posts")
      .withColumn("post_rank", F.row_number().over(w))
      .filter(F.col("post_rank") <= 3)
      .select("user_id", "post_id", "content", "created_at", "post_rank")
      .orderBy("user_id", "post_rank"))
assert [tuple(r) for r in df.collect()] == EXPECTED
print("[PASS] Q38 DataFrame API matches SQL")

# ------------------------------------------------ the LIMIT trap
# LIMIT 3 caps the whole result, so user 20 disappears entirely.
limited = spark.sql("""
SELECT user_id, post_id FROM posts ORDER BY user_id, created_at DESC LIMIT 3
""").collect()
assert {r.user_id for r in limited} == {10}, limited
print("[PASS] Q38 global LIMIT 3 drops user 20 -- per-group ranking is required")

# ------------------------------------------------ cannot filter a window in WHERE
try:
    spark.sql("""
    SELECT user_id, post_id,
           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS post_rank
    FROM posts
    WHERE ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) <= 3
    """).collect()
    raise AssertionError("expected a window function in WHERE to be rejected")
except Exception as e:
    assert type(e).__name__ != "AssertionError", e
    print("[PASS] Q38 window functions are illegal in WHERE -- the subquery is structural")

# ------------------------------------------------ the tie-determinism trap
# Drop the "one post per date" guarantee and ROW_NUMBER picks arbitrarily.
# Adding post_id to the ORDER BY makes it reproducible.
spark.sql("""
CREATE OR REPLACE TEMP VIEW posts AS
SELECT * FROM VALUES
    (1, 10, 'A', DATE'2024-01-04', 1),
    (2, 10, 'B', DATE'2024-01-04', 2),
    (3, 10, 'C', DATE'2024-01-03', 3),
    (4, 10, 'D', DATE'2024-01-02', 4)
AS t(post_id, user_id, content, created_at, likes)
""")
deterministic = spark.sql("""
SELECT post_id, post_rank FROM (
    SELECT post_id,
           ROW_NUMBER() OVER (PARTITION BY user_id
                              ORDER BY created_at DESC, post_id DESC) AS post_rank
    FROM posts
) WHERE post_rank <= 3 ORDER BY post_rank
""").collect()
assert [(r.post_id, r.post_rank) for r in deterministic] == [(2, 1), (1, 2), (3, 3)], deterministic
print("[PASS] Q38 same-date posts need post_id as a tiebreak to be reproducible")
