# Classic 4-Step Funnel (Impression -> Click -> Add-to-Cart -> Purchase)

## Problem
Given an `events(user_id, event_name, event_ts)` table with four event types
(`impression`, `click`, `add_to_cart`, `purchase`), compute the number of distinct
users who reach each step of the funnel on a given day.

## How to Think
1. A user counts as "reached step N" only if they performed every prior step.
   Don't count a purchase unless the same user also clicked and saw an impression.
2. Avoid double counting. Each user appears once per step.
3. The simplest mental model: per user, find the highest step they achieved.
   Then bucket users by `max_step`.
4. `COUNT(DISTINCT user_id)` is correct over `COUNT(*)` because one user can
   emit the same event many times.
5. Partition by date so the funnel is a single-day slice, not lifetime.

## How to Remember
- **Pattern**: "Boolean per step -> MAX per user -> COUNT(DISTINCT)."
- **Anti-pattern**: `GROUP BY event_name` -- gives you event counts, not funnel users.
- **Watch out**: a user who purchase-skips by API (rare but real) inflates the funnel.

## SQL (Presto / Hive)
```sql
WITH step_flags AS (
  SELECT user_id,
         MAX(CASE event_name
             WHEN 'impression'  THEN 1
             WHEN 'click'       THEN 2
             WHEN 'add_to_cart' THEN 3
             WHEN 'purchase'    THEN 4 END) AS max_step
  FROM events
  WHERE event_date = CURRENT_DATE
  GROUP BY user_id
)
SELECT max_step,
       COUNT(DISTINCT user_id) AS users_at_step
FROM step_flags
GROUP BY max_step
ORDER BY max_step;
```

## Common Mistakes
- Counting event occurrences instead of users -- repeated events inflate the funnel.
- Forgetting to scope by date -- lifetime funnels mislead daily decisions.
- Including a step without its prerequisite (e.g., purchases without clicks).
- Using `COUNT(*)` after a `GROUP BY user_id` instead of `COUNT(DISTINCT user_id)`
  at the outer level.

## AI Use Cases
- **Ad ranking**: stage-wise reach rates feed the p(click | impression) feature.
- **Recommendation**: drop-off between cart and purchase surfaces items to re-rank.
- **Anomaly detection**: sudden drops at any step trigger PagerDuty to the on-call DE.
- **Lookalike modeling**: top-of-funnel reach is the population pool for embeddings.
