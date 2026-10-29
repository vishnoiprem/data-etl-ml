"""
Problem 07: Point-in-Time Join (fact_date vs effective window).

Meta flavor: Compute seller revenue per category over time, using the
category they were in when the sale happened.

How to Think:
- Same as Problem 06 — fact_date matches a single dim row by effective window.
- Aggregate after the join.

How to Remember:
- "PIT = join with effective_from <= fact_date < effective_to."

AI Use Cases:
- Correct historical revenue attribution.
- Cohort analysis with attribute changes.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum

spark = SparkSession.builder.getOrCreate()

dim = spark.createDataFrame(
    [(101, 1, "Cat-A", "2025-01-01", "2025-12-31"),
     (102, 1, "Cat-B", "2026-01-01", "9999-12-31")],
    ["seller_key", "seller_id", "category", "effective_from", "effective_to"]
)

sales = spark.createDataFrame(
    [(201, 1, "2025-06-15", 100.0),
     (202, 1, "2025-11-20", 200.0),  # still Cat-A
     (203, 1, "2026-02-10", 300.0)], # now Cat-B
    ["sale_id", "seller_id", "fact_date", "amount"]
)

joined = sales.join(dim, (sales.seller_id == dim.seller_id) &
                            (sales.fact_date >= dim.effective_from) &
                            (sales.fact_date <  dim.effective_to)) \
              .select("fact_date", "category", "amount")
result = joined.groupBy("category").agg(sum("amount").alias("revenue"))
result.show()

SQL = """
SELECT d.category, SUM(s.amount) AS revenue
FROM fact_sales s
JOIN dim_seller d
  ON s.seller_id = d.seller_id
 AND s.fact_date >= d.effective_from
 AND s.fact_date <  d.effective_to
GROUP BY d.category;
"""
