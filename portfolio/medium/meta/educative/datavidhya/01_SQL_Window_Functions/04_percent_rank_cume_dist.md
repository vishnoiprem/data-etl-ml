# PERCENT_RANK and CUME_DIST — Continuous Distribution

## Problem
Compute both percentile rank and cumulative distribution for each creator's monthly views.

## How to Think
1. PERCENT_RANK = (rank - 1) / (n - 1). Range [0, 1].
2. CUME_DIST = (count <= current) / n. Range (0, 1].
3. Useful when NTILE buckets are too coarse.

## How to Remember
- **Pattern**: "PERCENT_RANK for rank-based; CUME_DIST for CDF."
- PERCENT_RANK is a position in the distribution; CUME_DIST is a cumulative probability.

## SQL (Presto / Hive)
```sql
SELECT creator_id, monthly_views,
       PERCENT_RANK() OVER (ORDER BY monthly_views ASC) AS pct_rank,
       CUME_DIST()    OVER (ORDER BY monthly_views ASC) AS cume_dist
FROM creator_metrics;
```

## Common Mistakes
- Confusing PERCENT_RANK with PERCENTILE_CONT — latter is a value at the percentile.
- Expecting PERCENT_RANK to return the percentage of rows strictly below; ties all share the same value.

## AI Use Cases
- Fairness analysis across ranking buckets.
- Threshold tuning for precision/recall tradeoffs.
- Cumulative gain / lift charts in recommendation evaluation.
