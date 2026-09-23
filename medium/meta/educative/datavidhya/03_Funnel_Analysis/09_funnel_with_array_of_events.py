"""
Problem 09: Funnel with array of events (Presto array_agg approach)
Meta flavor: "Per-user event sequences on Instagram Stories -- which sequences lead to a swipe-up?"

How to Think:
- Build a single row per user with all events in a sorted array.
- Filter for users whose array contains the desired step sequence IN ORDER.
- Presto's `array_agg(event ORDER BY ts)` is the canonical pattern.
- Then check `array_position(arr, step)` -- the index of step N must be <
  the index of step N+1.

How to Remember:
- Pattern: "array_agg -> sequence_match UDF -> count."
- Reduces N self-joins to one row per user -- much faster on Presto.
- Watch out for events with identical timestamps -- array_agg needs a tie-breaker.

AI Use Cases:
- Sequence-DL training data is exactly this array-of-events per user.
- Transformer over user journeys consumes the array as tokens.
- Auto-ML feature stores pre-compute these arrays for fast lookup.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import *

spark = SparkSession.builder.getOrCreate()

events = [
    ("u1", "impression",  "2026-09-23 10:00:00"),
    ("u1", "click",       "2026-09-23 10:01:00"),
    ("u1", "add_to_cart", "2026-09-23 10:05:00"),
    ("u1", "purchase",    "2026-09-23 10:07:00"),
    ("u2", "impression",  "2026-09-23 10:02:00"),
    ("u2", "add_to_cart", "2026-09-23 10:04:00"),  # skipped click
    ("u3", "impression",  "2026-09-23 10:05:00"),
    ("u3", "click",       "2026-09-23 10:06:00"),
]
df = spark.createDataFrame(events, ["user_id","event_name","event_ts"])

# Per-user sorted event array
arrays = (df
          .groupBy("user_id")
          .agg(collect_list(struct("event_ts","event_name")).alias("evt"))
          .withColumn("events", sort_array("evt").getField("event_name")))

arrays.show(truncate=False)

# Step counts via array_position (Presto/Spark syntax)
funnel = (arrays
    .withColumn("i",  array_position(col("events"), "impression"))
    .withColumn("c",  array_position(col("events"), "click"))
    .withColumn("a",  array_position(col("events"), "add_to_cart"))
    .withColumn("p",  array_position(col("events"), "purchase"))
    .withColumn("reached_step",
                when(col("i").isNotNull(), 1).otherwise(0)
              + when(col("i").isNotNull() & col("c").isNotNull()
                     & (col("c") > col("i")), 1).otherwise(0)
              + when(col("i").isNotNull() & col("c").isNotNull()
                     & col("a").isNotNull()
                     & (col("c") > col("i"))
                     & (col("a") > col("c")), 1).otherwise(0)
              + when(col("i").isNotNull() & col("c").isNotNull()
                     & col("a").isNotNull() & col("p").isNotNull()
                     & (col("c") > col("i"))
                     & (col("a") > col("c"))
                     & (col("p") > col("a")), 1).otherwise(0)))
funnel.groupBy("reached_step").agg(countDistinct("user_id").alias("users")).show()

# SQL (Presto / Hive)
SQL = """
WITH user_arr AS (
  SELECT user_id,
         array_agg(event_name ORDER BY event_ts) AS events
  FROM events
  WHERE event_date = CURRENT_DATE
  GROUP BY user_id
)
SELECT COUNT(DISTINCT user_id) AS users
FROM user_arr
WHERE array_position(events,'impression')  IS NOT NULL
  AND array_position(events,'click')       > array_position(events,'impression')
  AND array_position(events,'add_to_cart') > array_position(events,'click')
  AND array_position(events,'purchase')    > array_position(events,'add_to_cart');
"""
