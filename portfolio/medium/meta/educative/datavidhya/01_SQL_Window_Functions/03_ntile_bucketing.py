"""
Problem 03: NTILE bucketing — percentile segmentation.

Meta flavor: Split daily-active users into 10 engagement deciles by watch-time,
so PMs can target the top decile for premium features.

How to Think:
- NTILE(N) divides the partition into N buckets as evenly as possible.
- Rows within the same bucket get the same bucket number (1..N).
- Useful for "top X%" / "bottom X%" segments without complex ranking.

How to Remember:
- "NTILE(N) = assign each row to one of N equal-sized buckets."
- Large partitions get the extra rows (if N does not divide evenly).

AI Use Cases:
- Percentile bucketing for fairness analysis.
- Stratified sampling.
- Top-decile targeting in ranking models.
"""
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import ntile, col

spark = SparkSession.builder.getOrCreate()

data = [(i, i * 10) for i in range(1, 21)]  # 20 users, scores 10..200
df = spark.createDataFrame(data, ["user_id", "score"])

w = Window.orderBy(col("score").desc())
result = df.withColumn("decile", ntile(10).over(w))
result.show()

SQL = """
SELECT user_id, score,
       NTILE(10) OVER (ORDER BY score DESC) AS decile
FROM user_scores;
"""
