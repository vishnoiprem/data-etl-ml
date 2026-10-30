"""
Problem 07: 7-Day Rolling DAU.

Meta flavor: For each day, the average DAU over the trailing 7 days — used
to smooth weekday/weekend noise.

How to Think:
- For each day D, AVG(DAU(D-6..D)).
- Self-join or window with a 7-row frame.

How to Remember:
- "AVG(dau) OVER (ORDER BY dt ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)."

AI Use Cases:
- Anomaly detection (sudden drops vs rolling baseline).
- Time-series forecasting baseline.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, countDistinct, avg
from pyspark.sql.window import Window

spark = SparkSession.builder.getOrCreate()

events = spark.createDataFrame(
    [(d, 100 + (d % 7) * 5) for d in range(1, 16)] +
    [(d, (d % 3) + 1) for d in range(1, 16) for _ in range(2)],
    ["event_date", "user_id"]
)
events.createOrReplaceTempView("events")

dau = spark.sql("""
SELECT event_date, COUNT(DISTINCT user_id) AS dau
FROM events GROUP BY event_date
""")
dau.createOrReplaceTempView("dau")

w = Window.orderBy("event_date").rowsBetween(-6, 0)
result = dau.withColumn("dau_7d_avg", avg("dau").over(w))
result.show()

SQL = """
SELECT event_date, COUNT(DISTINCT user_id) AS dau
FROM events GROUP BY event_date
"""; dau_sql = SQL  # placeholder
SQL_FINAL = """
SELECT event_date, dau,
       AVG(dau) OVER (ORDER BY event_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS dau_7d_avg
FROM dau_tmp
ORDER BY event_date;
"""
