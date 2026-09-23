# Time-to-Convert Between Steps (Avg/Median per Step)

## Problem
For users who successfully transition between step N and step N+1, compute the
average and median time-to-convert (in seconds) between each pair of adjacent steps.

## How to Think
1. Reduce events to "first occurrence per user per step" -- that's the canonical timestamp.
2. Self-join those first-step rows to align step N with step N+1 for the same user.
3. Take the time diff in seconds (or minutes depending on scale).
4. AVG captures the long-tail; MEDIAN captures the typical user -- report both.
5. Cap extreme diffs (e.g., ignore users whose gap > 30 days) -- they're noise.

## How to Remember
- **Pattern**: "first per step -> self-join on user + step+1 -> diff."
- **Anti-pattern**: averaging across all events (repeats the same user many times).
- **Watch out**: missing step -- drop the row, not zero it out.

## SQL (Presto / Hive)
```sql
WITH first_step AS (
  SELECT user_id,
         CASE event_name
           WHEN 'impression'  THEN 1
           WHEN 'click'       THEN 2
           WHEN 'add_to_cart' THEN 3
           WHEN 'purchase'    THEN 4 END AS step,
         MIN(event_ts) AS ts
  FROM events
  WHERE event_date = CURRENT_DATE
  GROUP BY user_id, event_name
),
transitions AS (
  SELECT a.user_id,
         a.step AS from_step,
         UNIX_TIMESTAMP(b.ts) - UNIX_TIMESTAMP(a.ts) AS secs
  FROM first_step a
  JOIN first_step b
    ON a.user_id = b.user_id
   AND b.step   = a.step + 1
   AND UNIX_TIMESTAMP(b.ts) > UNIX_TIMESTAMP(a.ts)
)
SELECT from_step,
       AVG(secs) AS avg_secs,
       APPROX_PERCENTILE(secs, 0.5) AS median_secs
FROM transitions
GROUP BY from_step
ORDER BY from_step;
```

## Common Mistakes
- Joining without enforcing `b.step = a.step + 1` -- can skip steps or reorder.
- Computing on raw events instead of first-occurrence per user.
- Reporting only AVG -- hides skew; median or P90 is equally important.

## AI Use Cases
- **Conversion-VPC transformers**: time gaps become positional encodings.
- **Real-time bidding**: time-to-convert proxies ad freshness for ranking.
- **Retention DL**: time gaps feed sequential user-journey embeddings.
- **SRE alerting**: SLO regression detection on time-to-cart per Geo.
