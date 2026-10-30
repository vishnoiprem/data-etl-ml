"""
Problem 10: DAU by Surface (News Feed, Reels, Stories, Marketplace).

Meta flavor: For each day, count distinct users per surface so PMs see where
engagement is concentrated.

How to Think:
- Each event has a surface attribute (News Feed, Reels, etc.).
- COUNT(DISTINCT user_id) GROUP BY (event_date, surface).

How to Remember:
- "GROUP BY (dt, surface), COUNT(DISTINCT user_id)."

AI Use Cases:
- Product-area engagement comparison.
- Surface-level growth attribution.
- Re-allocation of dev effort.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, countDistinct

spark = SparkSession.builder.getOrCreate()

events = spark.createDataFrame(
    [(1, "2026-01-01", "feed"), (1, "2026-01-01", "reels"),
     (2, "2026-01-01", "feed"),
     (3, "2026-01-01", "reels"),
     (3, "2026-01-02", "stories"),
     (4, "2026-01-02", "marketplace")],
    ["user_id", "event_date", "surface"]
)
events.createOrReplaceTempView("events")

result = spark.sql("""
SELECT event_date, surface,
       COUNT(DISTINCT user_id) AS dau
FROM events
GROUP BY event_date, surface
ORDER BY event_date, surface
""")
result.show()

SQL = """
SELECT event_date, surface, COUNT(DISTINCT user_id) AS dau
FROM events
GROUP BY event_date, surface
ORDER BY event_date, surface;
"""
