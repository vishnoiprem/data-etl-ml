"""
Problem 10: Frame specification (ROWS vs RANGE BETWEEN).

Meta flavor: Compute "DAU in the last 7 days from each row's date" using a
calendrical window so missing dates don't shrink the window.

How to Think:
- ROWS BETWEEN N PRECEDING = N physical rows in the partition.
- RANGE BETWEEN INTERVAL '7' DAY PRECEDING = by time, regardless of how many rows.
- Choose ROWS when the partition is dense and well-ordered; RANGE when dates have gaps.

How to Remember:
- "ROWS = count. RANGE = value."
- For rolling-by-time on sparse data, always prefer RANGE.

AI Use Cases:
- Rolling time-windowed features.
- Sparse-event aggregations.
- Correct window behavior for irregular time series.
"""
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import sum, col

spark = SparkSession.builder.getOrCreate()

# Notice the gap: 2026-01-01 -> 2026-01-05 (missing 02, 03, 04)
data = [
    (1, "2026-01-01", 10),
    (1, "2026-01-05", 20),
    (1, "2026-01-08", 30),
]
df = spark.createDataFrame(data, ["user_id", "dt", "events"]).withColumn("dt", col("dt").cast("date"))

w_rows = Window.partitionBy("user_id").orderBy("dt").rowsBetween(-1, 0)
w_range = Window.partitionBy("user_id").orderBy("dt").rangeBetween(-7, 0)

result = df.withColumn("sum_rows", sum("events").over(w_rows)) \
           .withColumn("sum_7d_range", sum("events").over(w_range))
result.show()

SQL = """
SELECT user_id, dt, events,
       SUM(events) OVER (PARTITION BY user_id ORDER BY dt
                        ROWS  BETWEEN 1 PRECEDING AND CURRENT ROW) AS sum_rows,
       SUM(events) OVER (PARTITION BY user_id ORDER BY dt
                        RANGE BETWEEN INTERVAL '7' DAY PRECEDING AND CURRENT ROW) AS sum_7d_range
FROM user_events;
"""
