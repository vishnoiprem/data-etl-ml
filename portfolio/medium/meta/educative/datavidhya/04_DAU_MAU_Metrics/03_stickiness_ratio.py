"""
Problem 03: DAU/MAU Stickiness Ratio.

Meta flavor: For each month, ratio of average DAU to that month's MAU.
Stickiness in [0, 1]; higher = users come back more often.

How to Think:
- Compute avg(DAU) over the days in the month, and MAU separately.
- Or per-day stickiness using a 28-day rolling window.
- Stickiness is commonly capped at 1.

How to Remember:
- "Stickiness = DAU / MAU. Cap at 1."

AI Use Cases:
- Engagement-quality metric (per-user stickiness is a powerful ML feature).
- Cohort health scoring.
- A/B test primary metric.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, countDistinct, date_trunc, avg, max as smax

spark = SparkSession.builder.getOrCreate()

events = spark.createDataFrame(
    [(1, "2026-01-01"), (1, "2026-01-15"),  # user 1 in Jan
     (2, "2026-01-01"),                      # user 2 only on day 1
     (3, "2026-01-02"),                      # user 3 only on day 2
     (4, "2026-02-01"), (4, "2026-02-15")],   # user 4 in Feb
    ["user_id", "event_date"],
)
events.createOrReplaceTempView("events")

result = spark.sql("""
WITH dau AS (
  SELECT DATE_TRUNC('month', event_date) AS month,
         event_date                      AS dt,
         COUNT(DISTINCT user_id)         AS dau
  FROM events GROUP BY 1, 2
),
mau AS (
  SELECT DATE_TRUNC('month', event_date) AS month,
         COUNT(DISTINCT user_id)         AS mau
  FROM events GROUP BY 1
)
SELECT d.month,
       AVG(d.dau)                              AS avg_dau,
       MAX(m.mau)                              AS mau,
       AVG(d.dau) * 1.0 / MAX(m.mau)          AS stickiness
FROM dau d JOIN mau m USING (month)
GROUP BY d.month
ORDER BY d.month
""")
result.show()

SQL = """
WITH dau AS (
  SELECT DATE_TRUNC('month', event_date) AS month,
         event_date                      AS dt,
         COUNT(DISTINCT user_id)         AS dau
  FROM events GROUP BY 1, 2
),
mau AS (
  SELECT DATE_TRUNC('month', event_date) AS month,
         COUNT(DISTINCT user_id)         AS mau
  FROM events GROUP BY 1
)
SELECT d.month, AVG(d.dau) AS avg_dau, MAX(m.mau) AS mau,
       AVG(d.dau) * 1.0 / MAX(m.mau) AS stickiness
FROM dau d JOIN mau m USING (month)
GROUP BY d.month ORDER BY 1;
"""
