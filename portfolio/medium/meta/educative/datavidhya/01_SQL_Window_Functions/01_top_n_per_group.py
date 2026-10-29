"""
Problem 01: Top-N per group (e.g., top 3 posts per user by engagement).

Meta flavor: "Show the top 5 reels by watch-time per creator in the last 7 days."

How to Think:
- Rank within a partition with ROW_NUMBER() or RANK(), then filter.
- ROW_NUMBER() = exact N per group; RANK() = allow ties (may exceed N).
- Always partition by the group key; order by the metric descending.

How to Remember:
- "PARTITION BY group, ORDER BY metric DESC, then wrap and filter rn <= N."
- ROW_NUMBER breaks ties arbitrarily → use when duplicates are not meaningful.

AI Use Cases:
- Top-k recommendation candidates before reranking.
- Per-user feature extraction (top 3 clicked items -> embedding).
- Anomaly detection: top-1 baseline vs current.
"""
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number, col

spark = SparkSession.builder.getOrCreate()

# posts(user_id, post_id, engagement_score, created_at)
data = [
    (1, 101, 50, "2026-01-01"),
    (1, 102, 80, "2026-01-02"),
    (1, 103, 30, "2026-01-03"),
    (2, 201, 90, "2026-01-01"),
    (2, 202, 70, "2026-01-02"),
]
posts = spark.createDataFrame(data, ["user_id", "post_id", "engagement_score", "created_at"])

w = Window.partitionBy("user_id").orderBy(col("engagement_score").desc())
top3 = posts.withColumn("rn", row_number().over(w)).filter(col("rn") <= 3)
top3.show()

SQL = """
SELECT user_id, post_id, engagement_score
FROM (
  SELECT user_id, post_id, engagement_score,
         ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY engagement_score DESC) AS rn
  FROM posts
) t
WHERE rn <= 3;
"""
