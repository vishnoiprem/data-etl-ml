# SCD Type 6: Combined 1+2+3

## Problem
Carry current, versioned, AND original values in one row.

## How to Think
1. Type 2 columns: versioned (category, region).
2. Type 1 columns: overwrite (email).
3. Type 3 columns: previous value (original_category).
4. Combine into one wide row.

## How to Remember
- **Pattern**: "Type 6 = Type 1 + Type 2 + Type 3."
- Storage-heavy; rarely used in practice.

## SQL (Presto / Hive)
```sql
SELECT seller_key, seller_id, category, original_category,
       effective_from, effective_to, is_current
FROM dim_seller
ORDER BY seller_key;
```

## Common Mistakes
- Using Type 6 by default — storage cost grows fast.
- Not updating original_category correctly on subsequent changes.

## AI Use Cases
- Compliance reporting needing original values.
- Forensic audits.
