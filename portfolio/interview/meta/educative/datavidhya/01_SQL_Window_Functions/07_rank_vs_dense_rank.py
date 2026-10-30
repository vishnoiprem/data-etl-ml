"""
Problem 07: RANK vs DENSE_RANK vs ROW_NUMBER tie handling.

Meta flavor: Show the leaderboard of creators by weekly views. Ties matter
when sorting top-100 for weekly partner payouts.

How to Think:
- ROW_NUMBER(): arbitrary tie-break — each row gets a unique number.
- RANK(): same rank for ties, leaves gaps afterwards (1,1,3,4).
- DENSE_RANK(): same rank for ties, no gaps (1,1,2,3).
- Pick based on how strict the cut is.

How to Remember:
- ROW_NUMBER = "exactly N, no ties."
- RANK = "Olympic medal style — two golds, next is bronze."
- DENSE_RANK = "always packed, no gaps."

AI Use Cases:
- Top-N leaderboards with strict cutoffs.
- Multi-criteria ranking (combine via tie-breaker columns).
"""
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number, rank, dense_rank, col

spark = SparkSession.builder.getOrCreate()

data = [(1, 100), (2, 100), (3, 90), (4, 80)]
df = spark.createDataFrame(data, ["creator_id", "views"])

w = Window.orderBy(col("views").desc())
result = df.withColumn("rn", row_number().over(w)) \
           .withColumn("rk", rank().over(w)) \
           .withColumn("drk", dense_rank().over(w))
result.show()

SQL = """
SELECT creator_id, views,
       ROW_NUMBER() OVER (ORDER BY views DESC) AS rn,
       RANK()       OVER (ORDER BY views DESC) AS rk,
       DENSE_RANK() OVER (ORDER BY views DESC) AS drk
FROM creator_weekly;
"""
