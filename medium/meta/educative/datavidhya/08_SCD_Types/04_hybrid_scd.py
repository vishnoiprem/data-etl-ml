"""
Problem 04: Hybrid SCD (Type 1 on some attrs, Type 2 on others).

Meta flavor: Seller email — overwrite (Type 1). Seller category — version (Type 2).
Combine in one MERGE.

How to Think:
- Some columns trigger a Type 1 overwrite (email corrections, low-stakes).
- Others trigger a Type 2 close+insert (category, region changes).
- Single MERGE handles both branches.

How to Remember:
- "Hybrid: split columns by business importance."
- Type 1 for corrections, Type 2 for analytical dimensions.

AI Use Cases:
- Mixed-trust dimensions (corrections vs analytical).
- Cost vs correctness tradeoff.
"""
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# Conceptual MERGE
SQL = """
MERGE INTO dim_seller t
USING staging_seller s
ON t.seller_id = s.seller_id AND t.is_current = 1
WHEN MATCHED AND (t.category <> s.category) THEN  -- Type 2 trigger
  UPDATE SET t.effective_to = CURRENT_DATE, t.is_current = 0
WHEN MATCHED AND (t.email <> s.email) THEN         -- Type 1 trigger
  UPDATE SET t.email = s.email
WHEN NOT MATCHED THEN
  INSERT (seller_key, seller_id, email, category, effective_from, effective_to, is_current)
  VALUES (NEXT_SELLER_KEY, s.seller_id, s.email, s.category, CURRENT_DATE, '9999-12-31', 1);
"""
print(SQL)
