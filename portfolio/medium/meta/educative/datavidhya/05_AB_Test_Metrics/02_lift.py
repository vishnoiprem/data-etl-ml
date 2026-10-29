"""
Problem 02: Compute Lift (treatment - control) / control.

Meta flavor: News Feed ranking experiment. Compute % lift in click-through
rate vs control.

How to Think:
- p_t = treatment conversion rate; p_c = control conversion rate.
- Absolute lift = p_t - p_c. Relative lift = (p_t - p_c) / p_c.

How to Remember:
- "Relative lift = (p_t - p_c) / p_c."
- Always pair with CI / p-value, never report lift alone.

AI Use Cases:
- A/B test reporting.
- AutoML model comparison.
- Bid strategy evaluation.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, count, when

spark = SparkSession.builder.getOrCreate()

# ab_events(user_id, variant, converted)
data = [
    (i, "control",   i % 10 == 0) for i in range(1, 1001)        # 100/1000 = 10%
] + [
    (i, "treatment", i % 8 == 0)  for i in range(1001, 2001)       # 125/1000 = 12.5%
]
df = spark.createDataFrame(data, ["user_id", "variant", "converted"])
df.createOrReplaceTempView("ab")

result = spark.sql("""
SELECT variant,
       COUNT(*)                                AS n,
       AVG(CASE WHEN converted THEN 1.0 ELSE 0.0 END) AS p
FROM ab
GROUP BY variant
""")
result.show()

# Compute lift
p_c = 0.10
p_t = 0.125
absolute_lift = p_t - p_c
relative_lift = (p_t - p_c) / p_c
print(f"Absolute lift = {absolute_lift:.4f}, Relative lift = {relative_lift:.4f}")

SQL = """
SELECT variant,
       COUNT(*) AS n,
       AVG(CASE WHEN converted THEN 1.0 ELSE 0.0 END) AS conversion_rate
FROM ab
GROUP BY variant;
"""
