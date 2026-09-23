# Bulk MERGE Pattern for SCD2

## Problem
Load hundreds of daily dimension changes efficiently.

## How to Think
1. Identify changes (compare natural key + tracked columns).
2. Close current rows.
3. Insert new versions with effective_from = today.
4. New natural keys -> insert fresh row.

## How to Remember
- **Pattern**: "Identify changes -> close old -> insert new."
- Use MERGE when supported; otherwise staged CTEs.

## SQL (Presto / Hive)
```sql
WITH changes AS (
  SELECT s.seller_id, s.category
  FROM staging_seller s
  JOIN dim_seller d ON s.seller_id = d.seller_id AND d.is_current = 1
  WHERE s.category <> d.category
)
-- Step 2: close current rows
UPDATE dim_seller d
SET effective_to = CURRENT_DATE, is_current = 0
FROM changes c
WHERE d.seller_id = c.seller_id AND d.is_current = 1;

-- Step 3: insert new versions
INSERT INTO dim_seller (...)
SELECT NEXT_KEY + ROW_NUMBER() OVER (ORDER BY seller_id) - 1,
       seller_id, category, CURRENT_DATE, '9999-12-31', 1
FROM changes;
```

## Common Mistakes
- Forgetting to insert after closing — leaves gaps.
- Reusing surrogate keys.

## AI Use Cases
- Daily dimension ETL.
- Rebuilding dim from scratch (full refresh).
