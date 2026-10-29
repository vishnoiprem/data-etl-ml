# Hybrid SCD: Type 1 on Some, Type 2 on Others

## Problem
Some seller columns should overwrite in place (email); others should version (category).

## How to Think
1. Decide per column which SCD type fits the business need.
2. Email / phone / correction-style = Type 1.
3. Category / segment / tier = Type 2.
4. Apply in one MERGE with two WHEN MATCHED branches.

## How to Remember
- **Pattern**: "Type 1 for corrections, Type 2 for analytical attributes."
- A single MERGE can express both via WHEN branches.

## SQL (Presto / Hive)
```sql
MERGE INTO dim_seller t
USING staging_seller s
ON t.seller_id = s.seller_id AND t.is_current = 1
WHEN MATCHED AND (t.category <> s.category) THEN
  UPDATE SET t.effective_to = CURRENT_DATE, t.is_current = 0
WHEN MATCHED AND (t.email <> s.email) THEN
  UPDATE SET t.email = s.email
WHEN NOT MATCHED THEN
  INSERT (seller_key, seller_id, email, category, effective_from, effective_to, is_current)
  VALUES (NEXT_SELLER_KEY, s.seller_id, s.email, s.category, CURRENT_DATE, '9999-12-31', 1);
```

## Common Mistakes
- Forgetting to insert the new versioned row after closing the old one (Type 2 branch).
- Treating corrections as historical events.

## AI Use Cases
- Mixed-trust dimensions.
- Cost vs correctness tradeoff.
