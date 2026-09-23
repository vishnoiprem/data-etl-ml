"""
Problem 04: PERCENT_RANK and CUME_DIST — continuous distribution analysis.

Meta flavor: For each creator, compute their percentile rank and cumulative
distribution of monthly views so the partnership team can sort top X%.

How to Think:
- PERCENT_RANK = (rank - 1) / (total_rows - 1). 0 for the smallest, 1 for the largest.
- CUME_DIST = (rows with value <= current) / total_rows. Use when you want a CDF.
- Both are continuous, not bucketed like NTILE.

How to Remember:
- "PERCENT_RANK: how many rows are STRICTLY below me."
- "CUME_DIST: how many rows are <= me (includes me)."

AI Use Cases:
- Fairness analysis across ranking buckets.
- Threshold tuning for precision/recall tradeoffs.
- Cumulative gain / lift charts in recommendation evaluation.
"""
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import percent_rank, cume_dist, col

spark = SparkSession.builder.getOrCreate()

data = [(1, 100), (2, 200), (3, 300), (4, 400), (5, 500)]
df = spark.createDataFrame(data, ["creator_id", "monthly_views"])

w = Window.orderBy(col("monthly_views").asc())
result = df.withColumn("pct_rank", percent_rank().over(w)) \
           .withColumn("cume_dist", cume_dist().over(w))
result.show()

SQL = """
SELECT creator_id, monthly_views,
       PERCENT_RANK() OVER (ORDER BY monthly_views ASC) AS pct_rank,
       CUME_DIST()    OVER (ORDER BY monthly_views ASC) AS cume_dist
FROM creator_metrics;
"""
