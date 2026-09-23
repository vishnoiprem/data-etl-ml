"""
Problem 09: Cross-device Session Stitching (via login event)
Meta flavor: "When a user logs in, their iPhone and iPad events should be joined into one logical session. Implement via a 'login anchor' lookup."

How to Think:
- An anonymous device_id is attached to most events; a `login` event carries the canonical user_id.
- Build a lookup: for each login event, pair `(device_id, login_ts)` to the canonical user.
- Propagate the canonical user_id to subsequent events on the same device for a time window (e.g., 30 days).
- Then run the standard sessionization using the canonical user_id.

How to Remember:
- Stitching = "anchor device -> user -> propagate."
- Choose a TTL — too long and stale logins bleed into new users on shared devices; too short and you miss legit re-use.

AI Use Cases
- Cross-device attribution: a Facebook ad click on mobile and a conversion on desktop count as one journey.
- Frequency capping: limit ad impressions per REAL user across devices.
- Identity resolution as a feature for downstream models.
"""
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import *

spark = SparkSession.builder.getOrCreate()

events = [
    ("device_A", "2026-09-23 09:00:00", "open", None),
    ("device_A", "2026-09-23 09:02:00", "login", "u1"),       # login anchor
    ("device_A", "2026-09-23 09:05:00", "scroll", None),
    ("device_B", "2026-09-23 09:10:00", "view_post", "u1"),  # u1 on device B
    ("device_B", "2026-09-23 10:00:00", "view_post", "u1"),
    ("device_A", "2026-09-23 10:05:00", "click_ad", None),    # still u1 due to anchor
]
schema = ["device_id", "event_ts", "event_name", "user_id"]
df = spark.createDataFrame(events, schema).withColumn("event_ts", col("event_ts").cast("timestamp"))

# Backfill canonical user_id from the most recent login within the TTL
w_login = Window.partitionBy("device_id").orderBy("event_ts").rowsBetween(Window.unboundedPreceding, Window.currentRow)
canonical = df.withColumn("canonical_user", last("user_id", ignorenulls=True).over(w_login)).fillna({"canonical_user": "anon"})

# Now sessionize on (canonical_user, device_id)
w = Window.partitionBy("canonical_user").orderBy("event_ts")
stitched = (
    canonical.withColumn("prev_ts", lag("event_ts").over(w))
              .withColumn("is_new", when(col("prev_ts").isNull() | ((col("event_ts").cast("long") - col("prev_ts").cast("long")) > 1800), 1).otherwise(0))
              .withColumn("session_id", concat_ws("_", col("canonical_user"), sum("is_new").over(w)))
)
stitched.show(truncate=False)

# SQL (Presto / Hive)
SQL = """
WITH canonical AS (
  SELECT device_id, event_ts, event_name,
         LAST_VALUE(user_id IGNORE NULLS) OVER (PARTITION BY device_id ORDER BY event_ts ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS canonical_user
  FROM events
)
SELECT device_id, event_ts, event_name,
       COALESCE(canonical_user, 'anon') AS canonical_user,
       CONCAT(COALESCE(canonical_user, 'anon'), '_',
              SUM(CASE WHEN prev_ts IS NULL OR (event_ts - prev_ts) > INTERVAL '30' MINUTE THEN 1 ELSE 0 END)
              OVER (PARTITION BY COALESCE(canonical_user, 'anon') ORDER BY event_ts)
       ) AS session_id
FROM canonical
"""
