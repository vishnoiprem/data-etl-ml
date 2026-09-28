"""
Q01: Facebook Power Users (High Engagement)   [Hard | Aggregate Functions]

Find users who post at least 2 times AND average 150+ reactions
(likes + comments) per post.

How to Think:
- Two filters, both on AGGREGATES -> both belong in HAVING, not WHERE.
- "Reactions" is likes + comments, so the average is AVG(likes + comments),
  NOT AVG(likes) + AVG(comments)... which happens to be equal here, but only
  because every row has both columns non-null. With NULLs they diverge.
- ">= 150" is inclusive. User 1 averages exactly 150.0 and MUST be included.

The trap:
- User 3 has a single post with 500 reactions. High average, but only 1 post,
  so the post-count filter excludes them. Interviewers plant exactly this row.

Spark note:
- This is a plain shuffle aggregate. On a real events table you would filter
  the date partition FIRST so the shuffle carries less data.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("01-power-users")
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
spark.createDataFrame(
    [
    (1, 1, 150, 50), (2, 1, 80, 20),
    (3, 2, 250, 50), (4, 2, 150, 50), (5, 2, 70, 30),
    (6, 3, 400, 100),
    (7, 4, 60, 40), (8, 4, 70, 30),
],
    ["post_id", "user_id", "likes", "comments"]
).createOrReplaceTempView("posts")

from pyspark.sql import functions as F

SQL = """
SELECT user_id,
       COUNT(*) AS post_count,
       ROUND(AVG(likes + comments), 2) AS avg_reactions
FROM posts
GROUP BY user_id
HAVING COUNT(*) >= 2
   AND AVG(likes + comments) >= 150
ORDER BY avg_reactions DESC, user_id
"""

expect("Q01 power users", SQL, [(2, 3, 200.0), (1, 2, 150.0)])

# DataFrame API equivalent — same plan, same shuffle.
df = (spark.table("posts")
      .groupBy("user_id")
      .agg(F.count("*").alias("post_count"),
           F.round(F.avg(F.col("likes") + F.col("comments")), 2).alias("avg_reactions"))
      .filter((F.col("post_count") >= 2) & (F.col("avg_reactions") >= 150))
      .orderBy(F.col("avg_reactions").desc(), "user_id"))
assert [tuple(r) for r in df.collect()] == [(2, 3, 200.0), (1, 2, 150.0)]
print("[PASS] Q01 DataFrame API matches SQL")

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports the same GROUP BY + HAVING pattern. The two filters are
# on aggregates (post count and average reactions per post), so they must live
# in HAVING. The AVG is over (likes + comments) per row -- the equivalent of
# Spark's AVG(likes + comments). MySQL's COUNT(*) returns BIGINT but the value
# here fits in INT.
#
# CREATE TABLE posts (
#     post_id  INT NOT NULL,
#     user_id  INT NOT NULL,
#     likes    INT NOT NULL,
#     comments INT NOT NULL,
#     PRIMARY KEY (post_id),
#     KEY ix_posts_user (user_id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO posts (post_id, user_id, likes, comments) VALUES
#     (1, 1, 150, 50), (2, 1,  80, 20),
#     (3, 2, 250, 50), (4, 2, 150, 50), (5, 2,  70, 30),
#     (6, 3, 400, 100),
#     (7, 4,  60, 40), (8, 4,  70, 30);
#
# SELECT user_id,
#        COUNT(*) AS post_count,
#        ROUND(AVG(likes + comments), 2) AS avg_reactions
# FROM posts
# GROUP BY user_id
# HAVING COUNT(*) >= 2
#    AND AVG(likes + comments) >= 150
# ORDER BY avg_reactions DESC, user_id;
#
# -- Expected:
# -- 2  3  200.00
# -- 1  2  150.00
