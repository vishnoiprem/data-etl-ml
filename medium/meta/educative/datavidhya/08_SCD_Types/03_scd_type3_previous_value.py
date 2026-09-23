"""
Problem 03: SCD Type 3 (Previous-Value Column).

Meta flavor: Store the previous value in a side column for quick comparison
without joining versions.

How to Think:
- UPDATE in place but also write the old value to prev_value column.
- Limited to one-step history.
- Compact; fastest lookups.

How to Remember:
- "Type 3: current + previous_value column."

AI Use Cases:
- Quick "what did this value used to be?" without versioning.
- Cheap audits.
"""
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# Existing row
dim = spark.createDataFrame(
    [(1, "Cat-A", None)],   # prev_value is NULL for first version
    ["seller_id", "category", "category_prev"]
)

# Update: change to Cat-B, store previous
SQL = """
UPDATE dim_seller
SET category_prev = category, category = 'Cat-B'
WHERE seller_id = 1;
"""

# After update, the row looks like:
# | seller_id=1 | category=Cat-B | category_prev=Cat-A |
"""
Quick read: SELECT category, category_prev FROM dim_seller WHERE seller_id = 1;
No joins required.
"""
