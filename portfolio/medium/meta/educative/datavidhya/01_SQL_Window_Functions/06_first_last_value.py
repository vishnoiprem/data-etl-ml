"""
Problem 06: FIRST_VALUE and LAST_VALUE.

Meta flavor: For each user session, find the FIRST and LAST page they visited
to compute a session's entry/exit pages.

How to Think:
- FIRST_VALUE(col) reads the first row's col in the window frame.
- LAST_VALUE(col) reads the last row's col in the window frame — but the default
  frame ends at CURRENT ROW, so it returns the current value, not the partition's
  true last. Use an explicit frame to get the partition's last value.

How to Remember:
- "FIRST_VALUE = top of window. LAST_VALUE = bottom — but default frame is wrong."

AI Use Cases:
- Session entry/exit analysis.
- First-touch vs last-touch attribution.
- Sequence start/end detection for ML.
"""
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import first_value, last_value, col

spark = SparkSession.builder.getOrCreate()

data = [
    (1, 1, "home"),
    (1, 2, "feed"),
    (1, 3, "profile"),
    (2, 1, "home"),
]
df = spark.createDataFrame(data, ["user_id", "step", "page"])

w = Window.partitionBy("user_id").orderBy("step")
w_with_end = w.rowsBetween(Window.unboundedPreceding, Window.unboundedFollowing)

result = df.withColumn("first_page", first_value("page").over(w)) \
           .withColumn("last_page",  last_value("page").over(w_with_end))
result.show(truncate=False)

SQL = """
SELECT user_id, step, page,
       FIRST_VALUE(page) OVER (PARTITION BY user_id ORDER BY step) AS first_page,
       LAST_VALUE(page)  OVER (PARTITION BY user_id ORDER BY step
                               ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS last_page
FROM session_events;
"""
