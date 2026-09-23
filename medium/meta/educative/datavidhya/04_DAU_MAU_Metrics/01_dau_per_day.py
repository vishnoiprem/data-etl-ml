"""
Problem 01: Plain DAU per day.

Meta flavor: How many distinct Facebook users generated at least one event each day?

How to Think:
- DAU(Day D) = COUNT(DISTINCT user_id) over events on Day D.
- Grain: one row per day.
- Watch for users with multiple events (don't double-count).

How to Remember:
- "DAU(D) = COUNT(DISTINCT user_id WHERE event_date = D)."
- Add surface filter if needed (Reels, News Feed, etc.).

AI Use Cases:
- Anomaly detection on DAU drops.
- Forecasting models use DAU as a target.
- Capacity planning.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, countDistinct, to_date

spark = SparkSession.builder.getOrCreate()

events = spark.createDataFrame(
    [(1, "2026-01-01 10:00:00", "feed"), (1, "2026-01-01 14:00:00", "feed"),
     (2, "2026-01-01 11:00:00", "reels"),
     (3, "2026-01-02 09:00:00", "feed"),
     (4, "2026-01-02 10:00:00", "feed")],
    ["user_id", "ts", "surface"],
)
events.createOrReplaceTempView("events")

result = spark.sql("""
SELECT CAST(event_date AS DATE) AS dt,
       COUNT(DISTINCT user_id) AS dau
FROM (
  SELECT user_id, CAST(SUBSTR(ts, 1, 10) AS DATE) AS event_date FROM events
) e
GROUP BY CAST(event_date AS DATE)
ORDER BY dt
""")
result.show()

SQL = """
SELECT DATE(ts) AS dt, COUNT(DISTINCT user_id) AS dau
FROM events
GROUP BY DATE(ts)
ORDER BY dt;
"""
