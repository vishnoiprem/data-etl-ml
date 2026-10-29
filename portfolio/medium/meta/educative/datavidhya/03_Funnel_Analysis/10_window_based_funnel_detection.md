# Window-Based Funnel Detection (Within 7 Days of Step 1)

## Problem
Define a conversion window (default 7 days) starting at the first step-1 event
per user. A user is counted as "converted" only if they reach step N within
that window.

## How to Think
1. Pin the window length with the stakeholder -- Meta default is 7 days for
   click-through, 1 day for view-through.
2. Anchor on the first step-1 event per user (`MIN(event_ts)`).
3. Join all subsequent events and filter `b.ts BETWEEN a.anchor_ts AND a.anchor_ts + 7d`.
4. Be explicit about inclusive/exclusive endpoints -- use `>=` and `<=`.
5. Window-based funnels often diverge sharply from lifetime funnels -- call out
   which one you're reporting.

## How to Remember
- **Pattern**: "anchor first step -> self-join within window."
- **Anti-pattern**: using event timestamp without anchoring to step 1 -- includes pre-window noise.
- **Watch out**: time-zone shifts break the 7-day boundary -- pin to UTC.

## SQL (Presto / Hive)
```sql
WITH anchor AS (
  SELECT user_id, MIN(event_ts) AS anchor_ts
  FROM events
  WHERE event_name = 'impression'
  GROUP BY user_id
)
SELECT a.user_id,
       COUNT(DISTINCT CASE WHEN b.event_name = 'click'
                           THEN b.event_ts END)    AS clicks_in_window,
       COUNT(DISTINCT CASE WHEN b.event_name = 'purchase'
                           THEN b.event_ts END)    AS purchases_in_window
FROM anchor a
JOIN events b
  ON a.user_id = b.user_id
 AND b.event_ts >= a.anchor_ts
 AND b.event_ts <= a.anchor_ts + INTERVAL '7' DAY
GROUP BY a.user_id;
```

## Common Mistakes
- Using `event_date` instead of `event_ts` -- day boundaries are wrong near midnight.
- Not clarifying inclusive vs exclusive window endpoints.
- Comparing across campaigns with different windows -- apples to oranges.

## AI Use Cases
- **Multi-touch attribution**: window length controls credit assignment.
- **Delayed-feedback CVR models**: window length is the label horizon.
- **Uplift modeling**: separate "in-window converters" from "out-of-window converters".
- **Lookalike training**: seed positives from window-bounded converters only.
