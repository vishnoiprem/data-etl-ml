# Drop-Off Rate Per Step

## Problem
Compute the % of users lost between consecutive funnel steps.

## How to Think
1. drop_off = (prev - current) / prev.
2. Same skeleton as conversion — just use subtraction in numerator.
3. First step has NULL prev_users; show as 0 or NULL.

## How to Remember
- **Pattern**: "drop_off = (LAG(n) - n) / LAG(n)."
- Often shown alongside conversion in dashboards.

## SQL (Presto / Hive)
```sql
SELECT step_id, event_name, n_users,
       LAG(n_users) OVER (ORDER BY step_id) AS prev_users,
       (LAG(n_users) OVER (ORDER BY step_id) - n_users) * 1.0 / LAG(n_users) OVER (ORDER BY step_id) AS drop_off
FROM step_counts
ORDER BY step_id;
```

## Common Mistakes
- Reporting drop-off as % of total (vs % of previous step) — different denominator.
- Forgetting the first step has no prior — output NULL.

## AI Use Cases
- UX bottleneck identification.
- A/B test targeting highest-friction step.
- Funnel-health alerting (anomaly detection on drop-off spikes).
