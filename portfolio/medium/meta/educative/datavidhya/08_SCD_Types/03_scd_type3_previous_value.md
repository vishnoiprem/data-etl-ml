# SCD Type 3: Previous-Value Column

## Problem
Track one step of history without versioning — store previous value in a side column.

## How to Think
1. UPDATE in place.
2. Copy the old value into `category_prev`.
3. Use when only "what was it before" matters, not full history.

## How to Remember
- **Pattern**: "Type 3: current + category_prev column."
- Only one step of history.

## SQL (Presto / Hive)
```sql
UPDATE dim_seller
SET category_prev = category, category = 'Cat-B'
WHERE seller_id = 1;
```

## Common Mistakes
- Forgetting to copy old value before updating — overwrites history.
- Using Type 3 when you actually need full history.

## AI Use Cases
- Quick "what did this value used to be?" without versioning.
- Cheap audits.
