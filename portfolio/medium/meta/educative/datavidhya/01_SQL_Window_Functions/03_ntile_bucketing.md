# NTILE — Bucketing into Equal-Sized Segments

## Problem
Bucket users into 10 engagement deciles by score (decile 1 = highest score).

## How to Think
1. NTILE(N) divides the partition into N tiles as evenly as possible.
2. Larger tiles absorb the remainder rows.
3. Often used with `ORDER BY metric DESC` to make tile 1 = top.

## How to Remember
- **Pattern**: "NTILE(N) OVER (ORDER BY metric DESC) -> decile."
- 100 rows / NTILE(4) -> 25 rows per tile.
- 102 rows / NTILE(4) -> first two tiles have 26, last two have 25.

## SQL (Presto / Hive)
```sql
SELECT user_id, score,
       NTILE(10) OVER (ORDER BY score DESC) AS decile
FROM user_scores;
```

## Common Mistakes
- Confusing NTILE with PERCENT_RANK — NTILE guarantees equal-sized tiles; PERCENT_RANK gives a continuous rank.
- Forgetting ORDER BY — assignment is arbitrary.

## AI Use Cases
- Fairness analysis across user segments.
- Stratified sampling for training/eval splits.
- Top-decile targeting in ranking and recommendations.
