"""
Problem 04: Time-to-convert between steps (avg/median per step)
Meta flavor: "How long does it take from ad click to add-to-cart on a Facebook Shop carousel?"

How to Think:
- Need ordered per-user timestamps: first impression, first click, first cart, etc.
- Use a self-join: row N -> next-step row, gated by step ordering.
- AVG for expected time-to-convert, MEDIAN (or PERCENTILE) for typical case.
- Cap with a max (e.g., 24h) -- long-tail users skew the mean.

How to Remember:
- Pattern: "first event per step -> self-join on user + ts order -> diff."
- Watch out for negative diffs (clock skew or out-of-order events).
- Drop rows where next step is missing -- they didn't convert.

AI Use Cases:
- Real-time bidding models use time-to-convert as a freshness feature.
- Conversion-prediction transformers see time gaps as positional encodings.
- SLA dashboards trigger when avg time-to-cart regresses beyond SLO.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.window import Window

spark = SparkSession.builder.getOrCreate()

events = [
    ("u1", "impression",  "2026-09-23 10:00:00"),
    ("u1", "click",       "2026-09-23 10:01:00"),
    ("u1", "add_to_cart", "2026-09-23 10:05:00"),
    ("u1", "purchase",    "2026-09-23 10:07:00"),
    ("u2", "impression",  "2026-09-23 10:02:00"),
    ("u2", "click",       "2026-09-23 10:03:00"),
    ("u2", "add_to_cart", "2026-09-23 10:04:00"),
    ("u3", "impression",  "2026-09-23 10:09:00"),
]
df = spark.createDataFrame(events, ["user_id", "event_name", "event_ts"])

# First event per (user, step)
first_per_step = (df
    .withColumn("step", when(col("event_name")=="impression", 1)
                          .when(col("event_name")=="click",      2)
                          .when(col("event_name")=="add_to_cart",3)
                          .when(col("event_name")=="purchase",   4))
    .filter(col("step").isNotNull())
    .groupBy("user_id", "step")
    .agg(min("event_ts").alias("ts")))

# Self-join: step N+1 must come after step N
w = Window.partitionBy("user_id").orderBy("step")
joined = (first_per_step.alias("a")
          .join(first_per_step.alias("b"),
                (col("a.user_id") == col("b.user_id")) &
                (col("b.step")   == col("a.step") + 1))
          .select(col("a.user_id"),
                  col("a.step").alias("from_step"),
                  col("b.step").alias("to_step"),
                  (unix_timestamp("b.ts") - unix_timestamp("a.ts")).alias("secs")))

summary = (joined
           .groupBy("from_step", "to_step")
           .agg(avg("secs").alias("avg_secs"),
                expr("percentile_approx(secs, 0.5)").alias("median_secs")))
summary.show()

# SQL (Presto / Hive)
SQL = """
WITH first_step AS (
  SELECT user_id,
         step,
         MIN(event_ts) AS ts
  FROM (
    SELECT user_id, event_ts,
           CASE event_name
             WHEN 'impression'  THEN 1
             WHEN 'click'       THEN 2
             WHEN 'add_to_cart' THEN 3
             WHEN 'purchase'    THEN 4 END AS step
    FROM events
    WHERE event_date = CURRENT_DATE
  ) t
  WHERE step IS NOT NULL
  GROUP BY user_id, step
)
SELECT a.step AS from_step,
       b.step AS to_step,
       AVG(  UNIX_TIMESTAMP(b.ts) - UNIX_TIMESTAMP(a.ts)) AS avg_secs,
       APPROX_PERCENTILE(UNIX_TIMESTAMP(b.ts) - UNIX_TIMESTAMP(a.ts), 0.5) AS median_secs
FROM first_step a
JOIN first_step b
  ON a.user_id = b.user_id
 AND b.step   = a.step + 1
GROUP BY a.step, b.step
ORDER BY from_step, to_step;
"""
