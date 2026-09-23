"""
Problem 06: Funnel with strict ordering (must follow step1 -> step2 -> step3 in order)
Meta flavor: "How many WhatsApp Business accounts followed sign-up -> verify -> first message in order?"

How to Think:
- Strict ordering means step2's timestamp must be > step1's, step3's > step2's.
- Use ROW_NUMBER per (user, event_name) to pick the FIRST occurrence of each step.
- Self-join each step to the next, comparing timestamps.
- Without ordering, a user who clicked before the impression would still count.

How to Remember:
- Pattern: "ROW_NUMBER first -> self-join step1 < step2 < step3."
- Strict ordering catches "out-of-order" data (client clock skew).
- For Meta, `event_received_ts` (server time) is safer than `event_ts` (client time).

AI Use Cases:
- Causal funnel inference: ordered transitions are valid counterfactual samples.
- Graph-SAGE over user journeys uses ordered edges for correct message passing.
- Sequential recommenders model strict ordering with causal attention masks.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.window import Window

spark = SparkSession.builder.getOrCreate()

events = [
    ("u1", "signup",  "2026-09-23 10:00:00"),
    ("u1", "verify",  "2026-09-23 10:05:00"),
    ("u1", "message", "2026-09-23 10:10:00"),
    ("u2", "signup",  "2026-09-23 10:01:00"),
    ("u2", "verify",  "2026-09-23 09:55:00"),  # out of order
    ("u2", "message", "2026-09-23 10:20:00"),
    ("u3", "signup",  "2026-09-23 10:02:00"),
    ("u3", "verify",  "2026-09-23 10:03:00"),
    ("u4", "signup",  "2026-09-23 10:04:00"),
]
df = spark.createDataFrame(events, ["user_id","event_name","event_ts"])

# First occurrence per (user, event_name) ordered by ts
w = Window.partitionBy("user_id","event_name").orderBy("event_ts")
first_ts = (df
            .withColumn("rn", row_number().over(w))
            .filter(col("rn") == 1)
            .select("user_id","event_name","event_ts"))

# Self-join with strict time order
s1 = first_ts.filter(col("event_name")=="signup").alias("s1")
s2 = first_ts.filter(col("event_name")=="verify").alias("s2")
s3 = first_ts.filter(col("event_name")=="message").alias("s3")

strict = (s1.join(s2, (col("s1.user_id")==col("s2.user_id")) &
                       (col("s2.event_ts") > col("s1.event_ts")))
             .join(s3, (col("s1.user_id")==col("s3.user_id")) &
                       (col("s3.event_ts") > col("s2.event_ts")))
             .select(col("s1.user_id").alias("user_id")))

strict_count = strict.distinct().count()
print(f"users with strict-ordered funnel: {strict_count}")

# SQL (Presto / Hive)
SQL = """
WITH first_ts AS (
  SELECT user_id, event_name,
         ROW_NUMBER() OVER (PARTITION BY user_id, event_name
                            ORDER BY event_ts) AS rn,
         event_ts
  FROM events
  WHERE event_date = CURRENT_DATE
),
s1 AS (SELECT user_id, event_ts AS t1 FROM first_ts
       WHERE rn=1 AND event_name='signup'),
s2 AS (SELECT user_id, event_ts AS t2 FROM first_ts
       WHERE rn=1 AND event_name='verify'),
s3 AS (SELECT user_id, event_ts AS t3 FROM first_ts
       WHERE rn=1 AND event_name='message')
SELECT COUNT(DISTINCT s1.user_id) AS strict_funnel_users
FROM s1
JOIN s2 ON s1.user_id = s2.user_id AND s2.t2 > s1.t1
JOIN s3 ON s1.user_id = s3.user_id AND s3.t3 > s2.t2;
"""
