"""
Problem 09: Gaps and islands — find consecutive date ranges per user.

Meta flavor: For each user, find their longest active streak of consecutive days
so we can compute power-user rewards (>= 7 consecutive days).

How to Think:
- The "islands" trick: subtract an increasing sequence from the date to get a constant.
- Equivalently: ROW_NUMBER() over (user_id, ordered date); then date - rn gives the island id.
- GROUP BY (user_id, island_id) gives the start/end of each streak.

How to Remember:
- "date - row_number() = island_id. Group by island_id."

AI Use Cases:
- Streak detection (login streaks, purchase streaks).
- Activity burst detection.
- Consecutive-event windowing.
"""
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number, col, date_sub, min as smin, max as smax, count

spark = SparkSession.builder.getOrCreate()

data = [
    (1, "2026-01-01"),
    (1, "2026-01-02"),
    (1, "2026-01-03"),
    (1, "2026-01-05"),  # gap
    (1, "2026-01-06"),
    (2, "2026-01-01"),
]
df = spark.createDataFrame(data, ["user_id", "dt"]).withColumn("dt", col("dt").cast("date"))

w = Window.partitionBy("user_id").orderBy("dt")
df_island = df.withColumn("rn", row_number().over(w)) \
              .withColumn("island_id", date_sub("dt", col("rn")))

result = df_island.groupBy("user_id", "island_id") \
                  .agg(smin("dt").alias("streak_start"),
                       smax("dt").alias("streak_end"),
                       count("*").alias("days"))
result.show()

SQL = """
WITH base AS (
  SELECT user_id, dt,
         ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY dt) AS rn
  FROM user_logins
)
SELECT user_id,
       DATE_SUB(dt, rn) AS island_id,
       MIN(dt) AS streak_start,
       MAX(dt) AS streak_end,
       COUNT(*) AS days
FROM base
GROUP BY user_id, island_id;
"""
