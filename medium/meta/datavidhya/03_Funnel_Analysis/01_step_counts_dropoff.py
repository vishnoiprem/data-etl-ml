"""
Problem 01: Funnel step counts and drop-off (LOOSE definition).

Meta flavor: "Marketplace funnel is view -> message -> purchase. Where do we
leak the most users?"

How to Think:
- COUNT(DISTINCT user_id) per step. Events, not users, is the wrong grain —
  user 5 viewed twice.
- The event table has no inherent step order. Pin it with a VALUES spine so the
  window functions have something to ORDER BY.
- conv_from_prev = users / LAG(users); drop_off = 100 - that.
- LOOSE means each step is counted independently. User 3 purchased without
  messaging and still counts in `purchase` here. Ask which definition the
  interviewer wants — see 02_strict_ordered_funnel.py for the other one.

Spark note:
- One distinct-count shuffle; the 3-row window is free.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import spark, expect
from pyspark.sql import functions as F, Window

SQL = """
WITH spine AS (
    SELECT * FROM VALUES ('view',1), ('message',2), ('purchase',3) AS t(step, step_num)
),
per_step AS (
    SELECT s.step, s.step_num, COUNT(DISTINCT f.user_id) AS users
    FROM spine s
    LEFT JOIN funnel_events f ON f.step = s.step
    GROUP BY s.step, s.step_num
)
SELECT step, users,
       ROUND(100.0 * users / LAG(users) OVER (ORDER BY step_num), 2) AS conv_from_prev_pct,
       ROUND(100.0 - 100.0 * users / LAG(users) OVER (ORDER BY step_num), 2) AS drop_off_pct
FROM per_step
ORDER BY step_num
"""
expect("loose funnel step counts", SQL, [
    ("view", 5, None, None),
    ("message", 3, 60.00, 40.00),
    ("purchase", 2, 66.67, 33.33),
])

# ---- PySpark DataFrame API, same result -----------------------------------
spine = spark.createDataFrame([("view", 1), ("message", 2), ("purchase", 3)],
                              ["step", "step_num"])
per_step = (spine.join(spark.table("funnel_events"), "step", "left")
            .groupBy("step", "step_num")
            .agg(F.countDistinct("user_id").alias("users")))
w = Window.orderBy("step_num")
out = (per_step
       .withColumn("prev", F.lag("users").over(w))
       .withColumn("conv_from_prev_pct", F.round(100.0 * F.col("users") / F.col("prev"), 2))
       .withColumn("drop_off_pct", F.round(100.0 - 100.0 * F.col("users") / F.col("prev"), 2))
       .orderBy("step_num")
       .select("step", "users", "conv_from_prev_pct", "drop_off_pct"))
assert [tuple(r) for r in out.collect()] == [
    ("view", 5, None, None), ("message", 3, 60.00, 40.00), ("purchase", 2, 66.67, 33.33)]
print("[PASS] loose funnel — DataFrame API matches SQL")
