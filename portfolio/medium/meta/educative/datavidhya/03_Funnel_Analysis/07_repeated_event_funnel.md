# Repeated-Event Funnel (Count ALL Events, Not Just First)

## Problem
Report the volume of each event type (impressions, clicks, add-to-carts,
purchases) by counting every event occurrence -- including repeats from the
same user.

## How to Think
1. Switch the grain from "user" to "event row". Each row counts once.
2. Use `COUNT(*)`, not `COUNT(DISTINCT user_id)` -- distinctness kills repeats.
3. Sanity check ordering: impressions >= clicks >= carts >= purchases.
4. This metric complements (does not replace) the user-level funnel.
5. Useful for capacity planning (server load) and billing (CPM).

## How to Remember
- **Pattern**: "GROUP BY event_name -> COUNT(*)."
- **Anti-pattern**: using this as a CVR denominator -- repeats inflate it.
- **Watch out**: a single user double-tapping on a slow network can double the CTR.

## SQL (Presto / Hive)
```sql
SELECT event_name, COUNT(*) AS event_count
FROM events
WHERE event_date = CURRENT_DATE
GROUP BY event_name
ORDER BY event_count DESC;
```

## Common Mistakes
- Mixing user-level and event-level funnels in the same chart.
- Comparing event counts across days without time-zone alignment.
- Trusting event counts as "users reached" -- they're not.

## AI Use Cases
- **Volume forecasting (Prophet, ARIMA)**: raw event counts as training input.
- **Ad-revenue pipelines**: CPM = impressions / 1000 -- only valid on event counts.
- **Streaming Spike Arrest**: per-event counts drive auto-scaling thresholds.
- **Bot detection**: ratio of repeated click events to users flags click farms.
