"""
Problem 05: Running total / cumulative SUM.

Meta flavor: Compute cumulative daily ad revenue and the day each campaign
hits 50% of its lifetime target.

How to Think:
- SUM(col) OVER (PARTITION BY ... ORDER BY ...) gives the running total.
- Default frame: RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW.
- Cumulative without resetting per partition = global running total.

How to Remember:
- "Cumulative SUM = SUM(col) OVER (ORDER BY date)."
- Use a frame clause to control reset behavior.

AI Use Cases:
- Cumulative ad spend / revenue tracking.
- Time-to-target detection.
- Sequential training labels.
"""
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import sum, col

spark = SparkSession.builder.getOrCreate()

data = [
    ("2026-01-01", 100),
    ("2026-01-02", 200),
    ("2026-01-03", 150),
    ("2026-01-04", 300),
]
df = spark.createDataFrame(data, ["dt", "revenue"])

w = Window.orderBy("dt").rowsBetween(Window.unboundedPreceding, Window.currentRow)
result = df.withColumn("cum_revenue", sum("revenue").over(w))
result.show()

SQL = """
SELECT dt, revenue,
       SUM(revenue) OVER (ORDER BY dt ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cum_revenue
FROM daily_revenue;
"""
