# Conversion Rate Between Consecutive Steps

## Problem
Compute step-to-step conversion rate: step k / step k-1.

## How to Think
1. Compute distinct user count per step.
2. LAG the previous step's count via window function.
3. Divide current by previous — wrap denominator in NULLIF to avoid div-by-zero.

## How to Remember
- **Pattern**: "step_k * 1.0 / NULLIF(LAG(step_k), 0)."
- Add ROW_NUMBER step ordering to keep window order explicit.

## SQL (Presto / Hive)
```sql
WITH step_counts AS (
  SELECT event_name, n_users,
         ROW_NUMBER() OVER (ORDER BY CASE event_name
                                       WHEN 'impression' THEN 1
                                       WHEN 'click' THEN 2
                                       WHEN 'add_to_cart' THEN 3
                                       WHEN 'purchase' THEN 4 END) AS step_id
  FROM events
)
SELECT event_name, n_users,
       LAG(n_users) OVER (ORDER BY step_id) AS prev_step_users,
       n_users * 1.0 / NULLIF(LAG(n_users) OVER (ORDER BY step_id), 0) AS step_conversion
FROM step_counts
ORDER BY step_id;
```

## Common Mistakes
- Dividing by 0 in the first step — wrap with NULLIF.
- Reusing window-order by a column that has ties — add a tie-breaker.

## AI Use Cases
- Step-by-step conversion optimization.
- Cohort quality comparison.
- Funnel feature for ML ranking.
