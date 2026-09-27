"""
Problem 01: DAU series, MAU, and stickiness.

Meta flavor: "What is DAU/MAU for this surface, and is it improving?"

How to Think:
- DAU = COUNT(DISTINCT user_id) per day. MAU = COUNT(DISTINCT user_id) per
  month. MAU is NOT the sum of DAUs — that double counts returning users, and
  it is the single most common error on this question.
- Stickiness = avg(DAU) / MAU. Say which denominator you use for avg(DAU):
  days WITH activity, or all calendar days in the month? They differ whenever
  the product has dead days. This file uses days-with-activity and says so.
- Vocabulary matters at Meta: "stickiness" means DAU/MAU. Do not call it
  "sticky ratio" or improvise a definition.

How to Remember:
- "DAU/MAU, capped at 1. Sum of DAUs is not MAU."

Spark note:
- Two distinct-count aggregations, two shuffles. On a partitioned events table
  both prune to the month.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import spark, expect
from pyspark.sql import functions as F

DAU = """
SELECT event_date, COUNT(DISTINCT user_id) AS dau
FROM events
GROUP BY event_date
ORDER BY event_date
"""
expect("DAU series", DAU, [
    ("2026-01-01", 3), ("2026-01-02", 5), ("2026-01-03", 2),
    ("2026-01-08", 3), ("2026-01-09", 2), ("2026-01-30", 1),
])

STICKY = """
WITH dau AS (
    SELECT event_date, COUNT(DISTINCT user_id) AS dau
    FROM events GROUP BY event_date
),
mau AS (
    SELECT DATE_FORMAT(event_date, 'yyyy-MM') AS ym,
           COUNT(DISTINCT user_id) AS mau
    FROM events GROUP BY DATE_FORMAT(event_date, 'yyyy-MM')
)
SELECT m.ym, m.mau,
       ROUND(AVG(d.dau), 2) AS avg_dau,
       ROUND(100.0 * AVG(d.dau) / m.mau, 2) AS stickiness_pct
FROM mau m
JOIN dau d ON DATE_FORMAT(d.event_date, 'yyyy-MM') = m.ym
GROUP BY m.ym, m.mau
ORDER BY m.ym
"""
expect("MAU + stickiness (avg over active days)", STICKY, [("2026-01", 8, 2.67, 33.33)])

# ---- PySpark DataFrame API ------------------------------------------------
dau_df = (spark.table("events").groupBy("event_date")
          .agg(F.countDistinct("user_id").alias("dau")).orderBy("event_date"))
assert [tuple(r) for r in dau_df.collect()] == [
    ("2026-01-01", 3), ("2026-01-02", 5), ("2026-01-03", 2),
    ("2026-01-08", 3), ("2026-01-09", 2), ("2026-01-30", 1)]
print("[PASS] DAU — DataFrame API matches SQL")
