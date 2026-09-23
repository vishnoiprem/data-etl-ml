"""
Problem 03: Drop-off rate per step (% of previous step).

Meta flavor: Where in the funnel are we losing the most users?
Drop-off = 1 - conversion_rate. Or expressed as % of previous step that left.

How to Think:
- drop_off = (prev - current) / prev = 1 - conversion.
- Same logic as conversion, just subtract from 1.
- Often shown alongside conversion in dashboards.

How to Remember:
- "drop_off = 1 - conversion_rate. Often visualized as funnel width."

AI Use Cases:
- UX bottleneck identification.
- A/B test targeting highest-friction step.
- Funnel-health alerting.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lag
from pyspark.sql.window import Window

spark = SparkSession.builder.getOrCreate()

step_counts = [(1, "impression", 1000),
               (2, "click",       600),
               (3, "add_to_cart", 200),
               (4, "purchase",     50)]
df = spark.createDataFrame(step_counts, ["step_id", "event_name", "n_users"])

w = Window.orderBy("step_id")
result = df.withColumn("prev_users", lag("n_users").over(w)) \
           .withColumn("drop_off", (col("prev_users") - col("n_users")) / col("prev_users"))
result.show()

SQL = """
SELECT step_id, event_name, n_users,
       LAG(n_users) OVER (ORDER BY step_id) AS prev_users,
       (LAG(n_users) OVER (ORDER BY step_id) - n_users) * 1.0 / LAG(n_users) OVER (ORDER BY step_id) AS drop_off
FROM step_counts
ORDER BY step_id;
"""
