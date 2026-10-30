"""
Problem 09: New vs Returning DAU Split.

Meta flavor: For each day, separate DAU into new users (first activity ever)
and returning users.

How to Think:
- A user is new on day D if it's their first-ever event_date.
- Returning = active on D AND first_event_date < D.

How to Remember:
- "New = first_event_date = D. Returning = active on D AND first < D."

AI Use Cases:
- Acquisition-vs-retention dashboards.
- Marketing efficiency analysis.
- Feature onboarding targeting.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, countDistinct, min as smin

spark = SparkSession.builder.getOrCreate()

events = spark.createDataFrame(
    [(1, "2026-01-01"), (1, "2026-01-02"),  # user 1: new D1, returning D2
     (2, "2026-01-01"),                       # new D1
     (3, "2026-01-02"),                       # new D2
     (4, "2026-01-03"), (1, "2026-01-03")],   # user 4 new D3, user 1 returning D3
    ["user_id", "event_date"]
)
events.createOrReplaceTempView("events")

result = spark.sql("""
WITH first_seen AS (
  SELECT user_id, MIN(event_date) AS first_event_date FROM events GROUP BY user_id
)
SELECT e.event_date,
       COUNT(DISTINCT CASE WHEN f.first_event_date = e.event_date THEN e.user_id END) AS new_dau,
       COUNT(DISTINCT CASE WHEN f.first_event_date < e.event_date THEN e.user_id END) AS returning_dau
FROM events e
JOIN first_seen f USING (user_id)
GROUP BY e.event_date
ORDER BY e.event_date
""")
result.show()

SQL = """
WITH first_seen AS (
  SELECT user_id, MIN(event_date) AS first_event_date FROM events GROUP BY user_id
)
SELECT e.event_date,
       COUNT(DISTINCT CASE WHEN f.first_event_date = e.event_date THEN e.user_id END) AS new_dau,
       COUNT(DISTINCT CASE WHEN f.first_event_date < e.event_date THEN e.user_id END) AS returning_dau
FROM events e JOIN first_seen f USING (user_id)
GROUP BY e.event_date ORDER BY e.event_date;
"""
