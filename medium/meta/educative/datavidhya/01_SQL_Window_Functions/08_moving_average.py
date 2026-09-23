"""
Problem 08: Moving averages / rolling windows.

Meta flavor: Compute the 7-day rolling DAU to smooth out weekday/weekend noise
in Meta's daily active user reporting.

How to Think:
- Use a frame clause: ROWS BETWEEN 6 PRECEDING AND CURRENT ROW.
- 7-day rolling = current row + 6 preceding rows.
- For time-based windows use RANGE BETWEEN INTERVAL '7' DAY PRECEDING ...

How to Remember:
- "N-day moving avg = AVG OVER (ORDER BY dt ROWS BETWEEN N-1 PRECEDING AND CURRENT ROW)."
- ROWS is row-count based; RANGE is value-based (for date/numeric columns).

AI Use Cases:
- Smoothing noisy time-series metrics.
- Anomaly detection (current vs rolling baseline).
- Time-series features for forecasting.
"""
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import avg, col

spark = SparkSession.builder.getOrCreate()

data = [(d, 100 + (d % 7) * 10) for d in range(1, 15)]
df = spark.createDataFrame(data, ["dt", "dau"])

w = Window.orderBy("dt").rowsBetween(-6, 0)
result = df.withColumn("dau_7d_avg", avg("dau").over(w))
result.show()

SQL = """
SELECT dt, dau,
       AVG(dau) OVER (ORDER BY dt ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS dau_7d_avg
FROM daily_active_users;
"""
