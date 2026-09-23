# Funnel by User Segment (New vs Returning)

## Problem
Compute the same 4-step funnel, but split by user segment (e.g., `new` vs
`returning`). Goal: see where each segment leaks differently.

## How to Think
1. Decide the segment definition first. "New" can mean first-time-ever or
   first-time-in-30d. Pin it in the dimension table.
2. Reduce events to a single row per (user, segment, max_step).
3. Pivot or case-when into columns so each segment is comparable per step.
4. A "new" user funnel is usually noisier -- segment sample sizes must be watched.
5. Always include the segment definition in the dashboard title.

## How to Remember
- **Pattern**: "join users -> funnel -> segment_by -> pivot."
- **Anti-pattern**: computing funnels separately and copy-pasting numbers.
- **Watch out**: a user belongs to one segment at a time -- don't double-count.

## SQL (Presto / Hive)
```sql
WITH step_users AS (
  SELECT u.segment,
         e.user_id,
         MAX(CASE e.event_name
             WHEN 'impression'  THEN 1
             WHEN 'click'       THEN 2
             WHEN 'add_to_cart' THEN 3
             WHEN 'purchase'    THEN 4 END) AS max_step
  FROM events e
  JOIN users  u ON u.user_id = e.user_id
  WHERE e.event_date = CURRENT_DATE
  GROUP BY u.segment, e.user_id
)
SELECT max_step,
       SUM(CASE WHEN segment = 'new'       THEN 1 ELSE 0 END) AS new_users,
       SUM(CASE WHEN segment = 'returning' THEN 1 ELSE 0 END) AS returning_users
FROM step_users
GROUP BY max_step
ORDER BY max_step;
```

## Common Mistakes
- Forgetting to join the user dimension first (segment lives in `users`, not events).
- Double-counting users who switch segments mid-day -- pick a single snapshot.
- Reporting absolute counts instead of rates -- hides the smaller segment.

## AI Use Cases
- **Acquisition vs retention models**: per-segment funnel is a label distribution input.
- **Recommendation cold-start**: new users need popularity priors; returning users get CF.
- **Bandit policies**: different exploration rates by segment based on drop-off.
- **Lookalike audience training**: seed from high-CVR segments only.
