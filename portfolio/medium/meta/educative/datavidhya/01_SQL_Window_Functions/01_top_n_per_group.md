# Top-N Per Group (Window Function)

## Problem
For each user, return the top 3 posts by engagement score.

## How to Think
1. Group key = `user_id`. Order key = `engagement_score DESC`.
2. ROW_NUMBER() = exactly N per group, arbitrary tie-break.
3. RANK() / DENSE_RANK() = may exceed N when ties exist.
4. Wrap in subquery, filter `rn <= N`.

## How to Remember
- **Pattern**: "PARTITION BY group, ORDER BY metric DESC, wrap, filter rn <= N."
- ROW_NUMBER = exactly N, ties broken arbitrarily.
- RANK = may exceed N, leaves gaps on ties.
- DENSE_RANK = may exceed N, no gaps.

## SQL (Presto / Hive)
```sql
SELECT user_id, post_id, engagement_score
FROM (
  SELECT user_id, post_id, engagement_score,
         ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY engagement_score DESC) AS rn
  FROM posts
) t
WHERE rn <= 3;
```

## Common Mistakes
- Using RANK() expecting exactly N rows.
- Forgetting the subquery — window alias isn't visible in WHERE.
- Ordering ASC by accident.

## AI Use Cases
- Top-k retrieval candidates before reranking.
- Per-user feature extraction (top-3 clicked items -> embedding).
- Anomaly detection: top-1 baseline vs current value.
