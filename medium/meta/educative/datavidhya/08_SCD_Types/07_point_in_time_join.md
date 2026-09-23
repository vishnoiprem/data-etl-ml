# Point-in-Time Join

## Problem
Compute revenue per category, using the category the seller was in at sale time.

## How to Think
1. PIT join via effective_from / effective_to.
2. Aggregate after joining.
3. Be careful about end-inclusive semantics.

## How to Remember
- **Pattern**: "JOIN on (natural_key, fact_date BETWEEN effective_from AND effective_to)."
- Default end-exclusive: fact_date < effective_to.

## SQL (Presto / Hive)
```sql
SELECT d.category, SUM(s.amount) AS revenue
FROM fact_sales s
JOIN dim_seller d
  ON s.seller_id = d.seller_id
 AND s.fact_date >= d.effective_from
 AND s.fact_date <  d.effective_to
GROUP BY d.category;
```

## Common Mistakes
- Joining only on natural key — duplicates when versions overlap.
- Off-by-one on the effective_to boundary.

## AI Use Cases
- Correct historical revenue attribution.
- Cohort analysis with attribute changes.
