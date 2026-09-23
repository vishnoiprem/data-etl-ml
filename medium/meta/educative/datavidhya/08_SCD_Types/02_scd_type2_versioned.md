# SCD Type 2: Versioned Rows

## Problem
Seller changes category. Preserve history with effective_from / effective_to.

## How to Think
1. Close current row: set effective_to = today, is_current = 0.
2. Insert new row: new surrogate key, effective_from = today, effective_to = '9999-12-31', is_current = 1.
3. Lookups use PIT join: `effective_from <= dt AND dt < effective_to`.

## How to Remember
- **Pattern**: "effective_from + effective_to + is_current. Surrogate key."
- Two queries per change (close old, insert new).

## SQL (Presto / Hive)
```sql
-- Step 1: close current row
UPDATE dim_seller
SET effective_to = CURRENT_DATE, is_current = 0
WHERE seller_id = 1 AND is_current = 1;

-- Step 2: insert new row
INSERT INTO dim_seller (seller_key, seller_id, email, effective_from, effective_to, is_current)
SELECT MAX(seller_key) + 1, seller_id, email, CURRENT_DATE, '9999-12-31', 1
FROM dim_seller WHERE seller_id = 1 GROUP BY seller_id;
```

## Common Mistakes
- Reusing surrogate key — breaks joins.
- Forgetting to close old row — two active rows for one key.

## AI Use Cases
- Audit-friendly historical reporting.
- PIT joins in finance & ML feature engineering.
- Time-travel debugging.
