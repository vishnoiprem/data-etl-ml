# Measure Health of Facebook Groups

## Problem
You are the PM for Facebook Groups. The VP asks: "How would you measure if Groups
is healthy?" Walk the interviewer through your framework.

## How to Think
1. **Goal** – restate the product mission ("meaningful communities").
2. **North Star** – pick ONE metric that captures durable value.
3. **Inputs** – 3-5 supporting metrics across the AAARR funnel.
4. **Counter-metrics** – what you DON'T want to optimize.
5. **Segmentation** – posters vs lurkers vs admins.
6. **SQL** – sketch how you'd compute the NSM daily.
7. **Experiment** – describe the next test.

## How to Remember
- **Framework**: "Goal -> NSM -> Inputs -> Counter-metrics -> SQL -> Experiment."
- North Star: Weekly Meaningful Communities (groups with >= 5 weekly contributors).

## Supporting Metrics (Py dict literal in `.py`)
| Funnel      | Metric                                    |
|-------------|-------------------------------------------|
| Acquisition | New group joins / day                     |
| Activation  | % joiners posting within D7               |
| Retention   | D7/D30 contributor retention              |
| Referral    | Invites / member, invite-to-join rate     |
| Health      | % groups with >= 5 weekly contributors    |

## SQL (Presto)
```sql
WITH weekly_contrib AS (
    SELECT group_id, DATE_TRUNC('week', event_ts) AS wk,
           COUNT(DISTINCT actor_id) AS contributors
    FROM group_events
    WHERE event_type IN ('post','comment','reaction')
      AND event_ts >= CURRENT_DATE - INTERVAL '8' DAY
    GROUP BY 1, 2
)
SELECT wk,
       COUNT(DISTINCT group_id) AS n_groups,
       SUM(CASE WHEN contributors >= 5 THEN 1 ELSE 0 END) AS meaningful_groups,
       SUM(CASE WHEN contributors >= 5 THEN 1 ELSE 0 END) * 1.0
         / COUNT(DISTINCT group_id) AS pct_meaningful
FROM weekly_contrib
GROUP BY wk
ORDER BY wk DESC;
```

## Common Mistakes
- Picking a vanity metric (total groups, total members) instead of activity.
- No counter-metrics → "increase posts" can drive spam.
- Ignoring admin health (moderation load, churned admins).

## AI Use Cases
- Auto-summarise weekly NSM movements.
- Anomaly detection on group-health features.
- Driver-tree decomposition (cohort / surface / country).
