"""
Problem 05: SCD2 Surrogate Key vs Natural Key.

Meta flavor: A natural key (seller_id) may repeat across versions.
Use a surrogate key (seller_key) for stable joins in fact tables.

How to Think:
- Natural key = business identifier (e.g., seller_id).
- Surrogate key = synthetic primary key, unique per row version.
- Fact tables join on surrogate key to disambiguate "which version of seller did this sale attribute to?"

How to Remember:
- "Surrogate key in fact joins. Natural key only for source system identification."

AI Use Cases:
- ML feature stores benefit from stable surrogate keys.
- Slowly-changing entity-aware embeddings.
"""
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# Example: versioned dim
dim = spark.createDataFrame(
    [(101, 1, "Cat-A", 1),  # version 1
     (102, 1, "Cat-B", 1)], # version 2 (current)
    ["seller_key", "seller_id", "category", "is_current"]
)
# Fact sales referencing seller_key
fact = spark.createDataFrame(
    [(201, 101, 100.0),   # sale during version 1
     (202, 102, 150.0)],  # sale during version 2
    ["sale_id", "seller_key", "amount"]
)
# PIT join
joined = fact.join(dim, "seller_key").select("sale_id", "amount", "category")
joined.show()

SQL = """
SELECT s.sale_id, s.amount, d.category
FROM fact_sales s
JOIN dim_seller d ON s.seller_key = d.seller_key;
"""
