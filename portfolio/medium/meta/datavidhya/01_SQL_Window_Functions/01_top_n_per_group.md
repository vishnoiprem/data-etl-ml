# Top-N Per Group (Window Function)

## Problem
For each user, return the top 3 posts by engagement score.

## How to Think
1. The grouping key is `user_id`. The ordering key is `engagement_score DESC`.
2. `ROW_NUMBER()` gives an arbitrary tie-break and is the right choice when you want exactly N per group.
3. `RANK()` and `DENSE_RANK()` are alternatives when ties matter — but then you may exceed N.
4. Wrap the window function in a subquery and filter `rn <= N`.

## How to Remember
- **Pattern**: "`PARTITION BY group ORDER BY metric DESC` → wrap → filter `rn <= N`."
- ROW_NUMBER = "exactly N, tie-break arbitrary."
- RANK = "may exceed N, leaves gaps on ties."
- DENSE_RANK = "may exceed N, no gaps."

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
- Using `RANK()` and expecting exactly N rows.
- Forgetting the subquery — you cannot reference a window alias in WHERE.
- Ordering ASC instead of DESC.

## AI Use Cases
- Top-k retrieval candidates before reranking.
- Per-user feature extraction (top 3 clicked items → embedding).
- Anomaly detection: top-1 baseline vs current.
