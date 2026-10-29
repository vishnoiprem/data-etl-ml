"""
Problem 02: Conversion rate between consecutive steps.

Meta flavor: % of users who clicked, given they saw the impression. % who
purchased, given they added to cart. Etc.

How to Think:
- For each pair of consecutive steps: rate = users_at_step_k / users_at_step_k_minus_1.
- Use window functions to divide by the previous step.
- Or compute pairs explicitly.

How to Remember:
- "rate = step_k / step_(k-1). Wrap step counts in LAG for chain."

AI Use Cases:
- Step-by-step conversion optimization.
- Cohort quality comparison.
- Funnel feature for ML ranking.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, countDistinct, lag
from pyspark.sql.window import Window

spark = SparkSession.builder.getOrCreate()

events = spark.createDataFrame(
    [("impression", 1000), ("click", 600), ("add_to_cart", 200), ("purchase", 50)],
    ["event_name", "n_users"],
)

w = Window.orderBy("n_users")  # only safe if events ordered; use a sort key instead
# Use a numeric step order instead
events = events.createOrReplaceTempView("events")
# safer: add a step_id
spark.sql("""
WITH step_counts AS (
  SELECT event_name, n_users,
         ROW_NUMBER() OVER (ORDER BY CASE event_name
                                       WHEN 'impression' THEN 1
                                       WHEN 'click' THEN 2
                                       WHEN 'add_to_cart' THEN 3
                                       WHEN 'purchase' THEN 4 END) AS step_id
  FROM events
)
SELECT event_name, n_users,
       LAG(n_users) OVER (ORDER BY step_id) AS prev_step_users,
       n_users * 1.0 / NULLIF(LAG(n_users) OVER (ORDER BY step_id), 0) AS step_conversion
FROM step_counts
ORDER BY step_id
""").show()

SQL = """
WITH step_counts AS (
  SELECT event_name, n_users,
         ROW_NUMBER() OVER (ORDER BY CASE event_name
                                       WHEN 'impression' THEN 1
                                       WHEN 'click' THEN 2
                                       WHEN 'add_to_cart' THEN 3
                                       WHEN 'purchase' THEN 4 END) AS step_id
  FROM events
)
SELECT event_name, n_users,
       LAG(n_users) OVER (ORDER BY step_id) AS prev_step_users,
       n_users * 1.0 / NULLIF(LAG(n_users) OVER (ORDER BY step_id), 0) AS step_conversion
FROM step_counts
ORDER BY step_id;
"""
