"""
Problem 05: Variance and Pooled Standard Error.

Meta flavor: Compute per-arm variance and the pooled SE for the difference,
typically done in SQL before plugging into z/t stats.

How to Think:
- variance = AVG(x^2) - AVG(x)^2 in SQL (Welford's algorithm in pandas).
- pooled_var (binary, equal n) = (var_t + var_c) / 2.
- pooled_se = sqrt(pooled_var/n_t + pooled_var/n_c).

How to Remember:
- "var = AVG(x*x) - AVG(x)*AVG(x). se = sqrt(var/n)."

AI Use Cases:
- Pre-computing variance in Presto/Spark for downstream stats.
- Sample size re-estimation mid-experiment.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, count, pow

spark = SparkSession.builder.getOrCreate()

# Per-user watch time per variant
data = [
    ("control",   float(i % 30 + 5)) for i in range(1, 1001)
] + [
    ("treatment", float(i % 30 + 6)) for i in range(1001, 2001)
]
df = spark.createDataFrame(data, ["variant", "watch_time"])
df.createOrReplaceTempView("ab")

result = spark.sql("""
SELECT variant,
       COUNT(watch_time)                              AS n,
       AVG(watch_time)                               AS mean,
       AVG(watch_time * watch_time) - AVG(watch_time) * AVG(watch_time) AS variance
FROM ab
GROUP BY variant
""")
result.show()

SQL = """
SELECT variant,
       COUNT(*) AS n,
       AVG(watch_time) AS mean,
       AVG(watch_time * watch_time) - AVG(watch_time) * AVG(watch_time) AS variance
FROM ab GROUP BY variant;
"""
