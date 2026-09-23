"""
Problem 06: Late-Arriving Fact Handling with SCD2.

Meta flavor: A sale landed 3 days late, attributed to a seller whose category
changed 2 days ago. Use the SCD2 window to pick the right version.

How to Think:
- fact_date falls in [effective_from, effective_to) of the dim row that was
  active when the transaction occurred.
- A simple lookup by natural_key + fact_date resolves to the right surrogate key.

How to Remember:
- "fact_date BETWEEN effective_from AND effective_to -> pick that dim row."

AI Use Cases:
- Backfilling delayed events (clicks landing days after impression).
- Reprocessing historical transactions.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

spark = SparkSession.builder.getOrCreate()

dim = spark.createDataFrame(
    [(101, 1, "Cat-A", "2025-01-01", "2025-12-31"),
     (102, 1, "Cat-B", "2026-01-01", "9999-12-31")],
    ["seller_key", "seller_id", "category", "effective_from", "effective_to"]
)

# Late-arriving fact: sale on 2025-06-15 (well after the event but late-arriving)
fact = spark.createDataFrame(
    [(201, 1, "2025-06-15")],
    ["sale_id", "seller_id", "fact_date"]
)

# PIT join
joined = fact.join(dim, (fact.seller_id == dim.seller_id) &
                          (fact.fact_date >= dim.effective_from) &
                          (fact.fact_date < dim.effective_to))
joined = joined.select("sale_id", "seller_id", "fact_date", "category", "seller_key")
joined.show()

SQL = """
SELECT s.sale_id, s.seller_id, s.fact_date, d.category, d.seller_key
FROM fact_sales s
JOIN dim_seller d
  ON s.seller_id = d.seller_id
 AND s.fact_date >= d.effective_from
 AND s.fact_date <  d.effective_to;
"""
