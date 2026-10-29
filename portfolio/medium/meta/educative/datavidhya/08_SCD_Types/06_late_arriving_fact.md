# Late-Arriving Fact Handling (SCD2)

## Problem
A fact row arrives after the dim has been updated. Pick the dim version that was active at fact_date.

## How to Think
1. fact_date BETWEEN dim.effective_from AND dim.effective_to.
2. PIT join produces the correct version.

## How to Remember
- **Pattern**: "fact_date >= effective_from AND fact_date < effective_to."
- For end-inclusive: change < to <=.

## SQL (Presto / Hive)
```sql
SELECT s.sale_id, s.seller_id, s.fact_date, d.category, d.seller_key
FROM fact_sales s
JOIN dim_seller d
  ON s.seller_id = d.seller_id
 AND s.fact_date >= d.effective_from
 AND s.fact_date <  d.effective_to;
```

## Common Mistakes
- Joining only on natural key — if multiple versions match, you get duplicates.
- Using fact arrival date instead of fact_date — picks the wrong version.

## AI Use Cases
- Backfilling delayed events (clicks landing days after impression).
- Reprocessing historical transactions.
