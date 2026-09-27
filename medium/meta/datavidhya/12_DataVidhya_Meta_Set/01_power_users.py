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
from _seeds import spark, expect
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
