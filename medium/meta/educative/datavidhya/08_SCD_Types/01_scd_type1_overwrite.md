# SCD Type 1: Overwrite

## Problem
Seller updates email — overwrite the row, don't keep history.

## How to Think
1. MERGE dim INTO target using natural key.
2. WHEN MATCHED -> UPDATE.
3. WHEN NOT MATCHED -> INSERT.

## How to Remember
- **Pattern**: "Type 1: UPDATE / INSERT, no effective dates."
- History lost; smallest storage.

## SQL (Presto / Hive)
```sql
MERGE INTO dim_seller t
USING staging_seller s
ON t.seller_id = s.seller_id
WHEN MATCHED THEN UPDATE SET email = s.email
WHEN NOT MATCHED THEN INSERT VALUES (s.seller_id, s.email, s.name);
```

## Common Mistakes
- Using Type 1 when regulatory or business needs historical analysis.
- Skipping MERGE — naive UPDATE+INSERT can leave duplicates.

## AI Use Cases
- Trivial dimensional updates (low-stakes corrections).
- Where history isn't needed (typo fixes).
