# Surrogate Key vs Natural Key (SCD2)

## Problem
Natural key repeats across versions; need a stable join key for fact tables.

## How to Think
1. Natural key = business identifier (seller_id).
2. Surrogate key = synthetic, unique per row version.
3. Fact tables reference surrogate key to disambiguate.

## How to Remember
- **Pattern**: "Surrogate key in fact joins. Natural key only for source identification."
- Surrogate key NEVER changes for the same row version.

## SQL (Presto / Hive)
```sql
SELECT s.sale_id, s.amount, d.category
FROM fact_sales s
JOIN dim_seller d ON s.seller_key = d.seller_key;
```

## Common Mistakes
- Joining facts on natural key — duplicates when multiple versions exist.
- Reusing a surrogate key — breaks history.

## AI Use Cases
- ML feature stores benefit from stable surrogate keys.
- Entity-aware embeddings (which version was active when the label was assigned?).
