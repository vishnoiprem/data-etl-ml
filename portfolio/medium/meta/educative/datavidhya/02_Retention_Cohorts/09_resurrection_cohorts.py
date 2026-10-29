"""
Problem 09: Resurrection Cohorts.

Meta flavor: A "resurrected" user is one who churned for >= 30 days and then
came back. PM wants monthly resurrection counts.

How to Think:
- Define churn gap (e.g., 30 days).
- Find activity streaks: for each user, find max gap between consecutive events.
- Users whose max gap >= 30 AND who had activity after the gap -> resurrected.

How to Remember:
- "Resurrected = max gap >= N days AND active after the gap."

AI Use Cases:
- Win-back campaign triggers.
- Churn-revival prediction.
- LTV recovery modeling.
"""
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import col, lag, datediff, max as smax

spark = SparkSession.builder.getOrCreate()

activity = spark.createDataFrame(
    [(1, "2026-01-01"), (1, "2026-01-02"), (1, "2026-03-15"),  # 72-day gap -> resurrected
     (2, "2026-01-01"), (2, "2026-01-05"),                       # 4-day gap -> active, not resurrected
     (3, "2026-01-01"), (3, "2026-04-01")],                      # 90-day gap -> resurrected
    ["user_id", "event_date"],
)
activity.createOrReplaceTempView("activity")

w = Window.partitionBy("user_id").orderBy("event_date")
gap_df = activity.withColumn("prev_event", lag("event_date").over(w)) \
                  .withColumn("gap_days", datediff("event_date", "prev_event"))

result = gap_df.groupBy("user_id") \
               .agg(smax("gap_days").alias("max_gap")) \
               .withColumn("resurrected", col("max_gap") >= 30)
result.show()

SQL = """
WITH gaps AS (
  SELECT user_id,
         event_date,
         LAG(event_date) OVER (PARTITION BY user_id ORDER BY event_date) AS prev_event,
         DATEDIFF(event_date, LAG(event_date) OVER (PARTITION BY user_id ORDER BY event_date)) AS gap
  FROM activity
)
SELECT user_id,
       MAX(gap) AS max_gap,
       MAX(gap) >= 30 AS resurrected
FROM gaps
GROUP BY user_id;
"""
