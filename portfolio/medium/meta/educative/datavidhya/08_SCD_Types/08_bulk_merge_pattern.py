"""
Problem 08: Bulk Dimension Load (MERGE Pattern for SCD2).

Meta flavor: Daily batch MERGE from staging into the dim for hundreds of
seller changes.

How to Think:
- Stage 1: Compare natural key + tracked columns.
- Stage 2: For changes, close current row + insert new.
- Stage 3: For new natural keys, insert with effective_from = today.
- MERGE / INSERT patterns work, but at scale, prefer rewriting the whole dim.

How to Remember:
- "Compare natural key + tracked cols -> close old, insert new."

AI Use Cases:
- Daily dimension ETL.
- Rebuilding dim from scratch (full refresh).
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

spark = SparkSession.builder.getOrCreate()

# Conceptual MERGE flow
SQL = """
-- Step 1: identify changes
WITH changes AS (
  SELECT s.seller_id, s.category
  FROM staging_seller s
  JOIN dim_seller d
    ON s.seller_id = d.seller_id AND d.is_current = 1
  WHERE s.category <> d.category
),
-- Step 2: close current rows
closes AS (
  UPDATE dim_seller d
  SET effective_to = CURRENT_DATE, is_current = 0
  FROM changes c
  WHERE d.seller_id = c.seller_id AND d.is_current = 1
),
-- Step 3: insert new versions
inserts AS (
  INSERT INTO dim_seller (seller_key, seller_id, category, effective_from, effective_to, is_current)
  SELECT NEXT_SELLER_KEY() + ROW_NUMBER() OVER (ORDER BY seller_id) - 1,
         seller_id, category, CURRENT_DATE, '9999-12-31', 1
  FROM changes
)
SELECT 1;
"""
print(SQL)
