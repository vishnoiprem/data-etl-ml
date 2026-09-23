# Drop-off Rate Per Step (% of Previous Step)

## Problem
Compute the drop-off rate between every pair of adjacent funnel steps.
A drop-off at step N means the fraction of step-(N-1) users who did NOT reach step N.

## How to Think
1. Drop-off at step N = `1 - (users_at_N / users_at_(N-1))`.
2. This is the mirror image of the step conversion rate -- same data, opposite framing.
3. Sort by drop-off descending so the "leakiest" step floats to the top.
4. Drop-off complements conversion: if conversion is 0.40, drop-off is 0.60.
5. Use `NULLIF` for safety when a prior step is empty.

## How to Remember
- **Pattern**: "1 - LAG ratio."
- **Anti-pattern**: drop-off relative to step 1 -- masks step-wise leakage.
- **Watch out**: a high drop-off is not always bad (it could be by design, e.g., checkout).

## SQL (Presto / Hive)
```sql
WITH step_users AS (
  SELECT user_id,
         MAX(CASE event_name
             WHEN 'impression'  THEN 1
             WHEN 'click'       THEN 2
             WHEN 'add_to_cart' THEN 3
             WHEN 'purchase'    THEN 4 END) AS max_step
  FROM events
  WHERE event_date = CURRENT_DATE
  GROUP BY user_id
),
buckets AS (
  SELECT max_step, COUNT(DISTINCT user_id) AS users
  FROM step_users
  GROUP BY max_step
)
SELECT max_step,
       users,
       1 - users * 1.0 / NULLIF(LAG(users) OVER (ORDER BY max_step), 0) AS drop_rate
FROM buckets
ORDER BY drop_rate DESC NULLS LAST;
```

## Common Mistakes
- Using step 1 as denominator (gives overall, not per-step, drop-off).
- Forgetting to handle empty intermediate steps.
- Reporting drop-off without conversion (the two should match: drop + conv = 1).

## AI Use Cases
- **Inverse propensity weighting**: drop-off is the propensity denominator.
- **Onboarding LLM agents**: target the highest drop-off step with proactive help.
- **Recommendation**: re-engage users at the highest drop-off step with tailored promos.
- **Fraud detection**: drop-off spikes flagged by anomaly models.
