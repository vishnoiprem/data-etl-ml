"""
Problem 02: Compare current session to previous session using LAG / LEAD.

Meta flavor: "For each user, compute the time delta between consecutive sessions."

How to Think:
- LAG(col, 1) reads the previous row's value within the same partition.
- LEAD(col, 1) reads the next row's value.
- Order by event_time per user to define "consecutive."

How to Remember:
- "LAG = look BACK, LEAD = look FORWARD."
- Always order inside the window or it's meaningless.

AI Use Cases:
- Sequential feature engineering (delta time → RNN input).
- Churn prediction: gap between sessions.
- Drop-off detection: long delays before next step.
"""
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import col, lag, unix_timestamp

spark = SparkSession.builder.getOrCreate()

data = [
    (1, "session_start", "2026-01-01 10:00:00"),
    (1, "session_start", "2026-01-01 14:30:00"),
    (1, "session_start", "2026-01-03 09:00:00"),
    (2, "session_start", "2026-01-02 11:00:00"),
]
events = spark.createDataFrame(data, ["user_id", "event", "ts"])

w = Window.partitionBy("user_id").orderBy("ts")
result = events.withColumn("prev_ts", lag("ts", 1).over(w))
result = result.withColumn(
    "delta_hours",
    (unix_timestamp("ts") - unix_timestamp("prev_ts")) / 3600
)
result.show(truncate=False)

SQL = """
SELECT user_id, event, ts,
       LAG(ts, 1) OVER (PARTITION BY user_id ORDER BY ts) AS prev_ts,
       UNIX_TIMESTAMP(ts) - UNIX_TIMESTAMP(LAG(ts, 1) OVER (PARTITION BY user_id ORDER BY ts)) AS delta_sec
FROM events;
"""
