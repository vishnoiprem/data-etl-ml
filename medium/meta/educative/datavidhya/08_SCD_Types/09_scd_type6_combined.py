"""
Problem 09: SCD Type 6 (Combined 1+2+3).

Meta flavor: Most comprehensive — keeps the current value (Type 1),
versioned rows (Type 2), and the original value (Type 3) all in one row.

How to Think:
- Track: current_value (overwrite), history (versions), original_value (one-step).
- All three present -> powerful point-in-time queries without joins.

How to Remember:
- "Type 6 = Type 1 + Type 2 + Type 3."
- Rarely used in practice — storage cost high.

AI Use Cases:
- Compliance reporting that needs original values.
- Forensic audits.
"""
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# Example dim with Type 6 columns
dim = spark.createDataFrame(
    [
        # seller_key, seller_id, category, original_category, effective_from, effective_to, is_current
        (101, 1, "Cat-A", "Cat-A", "2025-01-01", "2025-12-31", 0),
        (102, 1, "Cat-B", "Cat-A", "2026-01-01", "9999-12-31", 1),
    ],
    ["seller_key", "seller_id", "category", "original_category",
     "effective_from", "effective_to", "is_current"]
)
dim.show(truncate=False)

SQL = """
SELECT seller_key, seller_id, category, original_category,
       effective_from, effective_to, is_current
FROM dim_seller
ORDER BY seller_key;
"""
