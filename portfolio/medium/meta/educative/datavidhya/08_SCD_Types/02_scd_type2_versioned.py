"""
Problem 02: SCD Type 2 (Versioned Rows).

Meta flavor: Seller changes their category — Meta needs history ("this seller
was in Category A last year and moved to B this year") for reporting.

How to Think:
- New row per change, with effective_from / effective_to / is_current.
- Look up by JOIN on (natural_key) WHERE effective_from <= dt AND effective_to > dt.
- Use surrogate key (seller_key) — natural key can repeat.

How to Remember:
- "Type 2: effective_from + effective_to + is_current. Surrogate key."

AI Use Cases:
- Audit-friendly historical reporting.
- PIT (point-in-time) joins in finance & ML feature engineering.
- Time-travel debugging.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit

spark = SparkSession.builder.getOrCreate()

# Existing dim with versions
dim = spark.createDataFrame(
    [(101, 1, "alice@example.com", "2020-01-01", "2025-12-31", 0),
     (102, 1, "alice@example.com", "2026-01-01", "9999-12-31", 1)],
    ["seller_key", "seller_id", "email", "effective_from", "effective_to", "is_current"]
)

# Staging: Alice's category changed from Cat-A to Cat-B
staging = spark.createDataFrame(
    [(1, "alice@example.com", "Cat-B")],
    ["seller_id", "email", "new_category"]
)

# To apply Type 2 manually:
# 1) Update previous row's effective_to to today and is_current = 0
# 2) Insert new row with effective_from = today, effective_to = 9999, is_current = 1
# (Catalog attribute category lives in a separate dim; here we update email dim for demo.)

SQL = """
-- Step 1: close current row
UPDATE dim_seller
SET effective_to = CURRENT_DATE, is_current = 0
WHERE seller_id = 1 AND is_current = 1;

-- Step 2: insert new row with new surrogate key
INSERT INTO dim_seller (seller_key, seller_id, email, effective_from, effective_to, is_current)
SELECT MAX(seller_key) + 1, seller_id, email, CURRENT_DATE, '9999-12-31', 1
FROM dim_seller WHERE seller_id = 1 GROUP BY seller_id;
"""
