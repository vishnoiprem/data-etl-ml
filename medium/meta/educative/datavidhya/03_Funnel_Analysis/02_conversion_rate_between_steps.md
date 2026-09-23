# Conversion Rate Between Consecutive Steps

## Problem
Given a multi-step funnel, compute the conversion rate between every pair of
adjacent steps (e.g., `click -> add_to_cart`, `add_to_cart -> purchase`).

## How to Think
1. Conversion between step `N` and step `N+1` uses step `N` users as the denominator.
   Do **not** divide by step 1 every time -- that gives overall conversion, not
   step-wise conversion.
2. `LAG()` over an ordered step list is the cleanest way to get adjacent pairs.
3. Round to a stable precision (4 decimals) so dashboards render cleanly.
4. Watch out for division by zero when a prior step has zero users.

## How to Remember
- **Pattern**: "step_users / LAG(step_users)."
- **Anti-pattern**: comparing step 4 to step 1 -- hides where the funnel actually leaks.
- **Watch out**: a step with 0 users makes the rate undefined; `NULLIF` it.

## SQL (Presto / Hive)
```sql
WITH step_users AS (
  SELECT MAX(CASE event_name
             WHEN 'impression'  THEN 1
             WHEN 'click'       THEN 2
             WHEN 'add_to_cart' THEN 3
             WHEN 'purchase'    THEN 4 END) AS max_step,
         user_id
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
       users * 1.0 / NULLIF(LAG(users) OVER (ORDER BY max_step), 0) AS conv_rate
FROM buckets
ORDER BY max_step;
```

## Common Mistakes
- Dividing every step by step 1's count (overall CVR, not step CVR).
- Forgetting `NULLIF` -- blows up the query when a step is empty.
- Comparing across days without re-aligning by date -- apples to oranges.

## AI Use Cases
- **CTR / CVR prediction**: per-step conversion rates are direct inputs to ranking models.
- **Reinforcement learning**: per-step rewards in Markov Decision Processes over user journeys.
- **Creative auto-selection**: bandit algorithm picks the ad with highest step-N -> step-N+1 lift.
- **Fraud detection**: abrupt step-CVR spikes flag click farms.
