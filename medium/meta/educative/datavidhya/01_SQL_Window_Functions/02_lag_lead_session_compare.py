"""
Problem 02: Compare current to previous/next session using LAG / LEAD.

Meta flavor: For each daily active user, find the gap (in hours) between
consecutive active days on Facebook.

How to Think:
- LAG(col, 1) reads the previous row's value within the partition.
- LEAD(col, 1) reads the next row's value.
- Always ORDER BY inside the window — otherwise the result is meaningless.

How to Remember:
- "LAG = look BACK, LEAD = look FORWARD."
- Default offset is 1; default fill is NULL.

AI Use Cases:
- Sequential feature engineering (delta -> RNN input).
- Churn prediction (gap between sessions).
- Drop-off detection (long delays before next step).
"""
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import col, lag, unix_timestamp

spark = SparkSession.builder.getOrCreate()

data = [
    (1, "2026-01-01 10:00:00"),
    (1, "2026-01-01 14:30:00"),
    (1, "2026-01-03 09:00:00"),
    (2, "2026-01-02 11:00:00"),
]
events = spark.createDataFrame(data, ["user_id", "ts"])

w = Window.partitionBy("user_id").orderBy("ts")
result = events.withColumn("prev_ts", lag("ts", 1).over(w))
result = result.withColumn(
    "delta_sec",
    unix_timestamp("ts") - unix_timestamp("prev_ts")
)
result.show(truncate=False)

SQL = """
SELECT user_id, ts,
       LAG(ts, 1) OVER (PARTITION BY user_id ORDER BY ts) AS prev_ts,
       UNIX_TIMESTAMP(ts) - UNIX_TIMESTAMP(LAG(ts, 1) OVER (PARTITION BY user_id ORDER BY ts)) AS delta_sec
FROM events;
"""
