"""
Problem 05: Funnel by User Segment (new vs returning).

Meta flavor: Segment users as new vs returning (first activity in last 30 days),
then compute the same funnel per segment.

How to Think:
- Step 1: Derive segment attribute per user.
- Step 2: GROUP BY (segment, step).
- Step 3: Pivot or simply list per segment.

How to Remember:
- "Add segment to GROUP BY -> funnel per segment."

AI Use Cases:
- Comparing new vs power-user conversion.
- Personalization opportunity sizing.
- Segment-targeted feature rollout evaluation.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, countDistinct, max as smax, datediff, current_date

spark = SparkSession.builder.getOrCreate()

events = spark.createDataFrame(
    [(1, "2026-01-01", "impression"),
     (1, "2026-01-02", "click"),
     (2, "2025-12-01", "impression"),  # user 2 active 30 days ago -> "returning"
     (2, "2026-01-02", "click"),
     (3, "2026-01-01", "impression"),
     (3, "2026-01-02", "purchase")] +
    [(i, "2026-01-01", "impression") for i in range(4, 11)],
    ["user_id", "event_date", "event_name"],
)
events.createOrReplaceTempView("events")

result = spark.sql("""
WITH user_first AS (
  SELECT user_id, MIN(event_date) AS first_event_date
  FROM events GROUP BY user_id
),
segments AS (
  SELECT user_id, first_event_date,
         CASE WHEN DATEDIFF(CAST('2026-01-02' AS DATE), first_event_date) <= 30
              THEN 'returning'
              ELSE 'lapsed'
         END AS user_segment
  FROM user_first
)
SELECT s.user_segment,
       COUNT(DISTINCT CASE WHEN e.event_name = 'impression' THEN e.user_id END) AS impressions,
       COUNT(DISTINCT CASE WHEN e.event_name = 'click'      THEN e.user_id END) AS clicks
FROM events e
JOIN segments s USING (user_id)
GROUP BY s.user_segment
""")
result.show()

SQL = """
WITH user_first AS (
  SELECT user_id, MIN(event_date) AS first_event_date FROM events GROUP BY user_id
),
segments AS (
  SELECT user_id, first_event_date,
         CASE WHEN DATEDIFF(CAST('2026-01-02' AS DATE), first_event_date) <= 30
              THEN 'returning' ELSE 'lapsed' END AS user_segment
  FROM user_first
)
SELECT s.user_segment,
       COUNT(DISTINCT CASE WHEN e.event_name = 'impression' THEN e.user_id END) AS impressions,
       COUNT(DISTINCT CASE WHEN e.event_name = 'click'      THEN e.user_id END) AS clicks
FROM events e
JOIN segments s USING (user_id)
GROUP BY s.user_segment;
"""
