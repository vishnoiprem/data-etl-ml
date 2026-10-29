"""
Problem 01: SCD Type 1 (Overwrite).

Meta flavor: Seller updates their email. New row overwrites the old.
History is lost — Type 1 doesn't keep versions.

How to Think:
- One dim row per natural key.
- MERGE / UPDATE in place.
- Fastest, smallest storage, but no history.

How to Remember:
- "Type 1: UPDATE dim SET col = new WHERE key = X."
- No effective_from / is_current.

AI Use Cases:
- Trivial dimensional updates (low-stakes corrections).
- Where history isn't needed (e.g., typo fixes).
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

spark = SparkSession.builder.getOrCreate()

# Current dim
dim = spark.createDataFrame(
    [(1, "alice@example.com", "Alice"),
     (2, "bob@example.com",   "Bob")],
    ["seller_id", "email", "name"]
)

# Incoming update: Alice's email changed
staging = spark.createDataFrame(
    [(1, "alice.new@example.com", "Alice")],
    ["seller_id", "email", "name"]
)

# Simple overwrite (Type 1)
result = dim.union(staging).dropDuplicates(["seller_id"])
result.show()

# Equivalent MERGE (Presto / Hive syntax varies; Hive MERGE shown):
SQL_MERGE = """
MERGE INTO dim_seller t
USING staging_seller s
ON t.seller_id = s.seller_id
WHEN MATCHED THEN UPDATE SET email = s.email
WHEN NOT MATCHED THEN INSERT VALUES (s.seller_id, s.email, s.name);
"""
