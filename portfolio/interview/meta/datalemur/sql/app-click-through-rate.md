## Problem
**App Click-through Rate (CTR) [Easy]** — Compute the click-through rate (CTR) for each app in 2022. CTR = clicks / impressions.

**Schema:**
- `events(app_id, event_type, timestamp)` where `event_type` is one of `'impression'`, `'click'`.

Return one row per `app_id` with its CTR rounded to 2 decimal places.

---

## 1. Simple way to think
- For every app, count how many times it was clicked and how many times it was shown.
- Divide clicks by impressions. That's CTR.
- If an app has zero impressions, the CTR is `0.00` (or NULL — be explicit).
- The trick: both counts come from the same `events` table, so we can count them in one pass using `CASE` inside `SUM`, or by pivoting with conditional aggregation.
- It's like a survey: of everyone who saw the ad, how many clicked?

## 2. Interview write-up (how to solve it)
I'll filter to 2022 first to shrink the data, then use conditional aggregation to count clicks and impressions in one scan.

```sql
SELECT
  app_id,
  ROUND(
    100.0 * SUM(CASE WHEN event_type = 'click' THEN 1 ELSE 0 END) /
    NULLIF(SUM(CASE WHEN event_type = 'impression' THEN 1 ELSE 0 END), 0),
    2
  ) AS ctr
FROM events
WHERE timestamp >= '2022-01-01' AND timestamp < '2023-01-01'
GROUP BY app_id;
```

Explanation:
- The `WHERE` prunes everything outside 2022 up front.
- `SUM(CASE WHEN ...)` counts only the rows we care about per type.
- `NULLIF(..., 0)` avoids division-by-zero for apps with no impressions.
- Multiply by 100.0 to get a percentage and `ROUND(..., 2)` for two decimals.

## 3. Best optimized solution
```sql
SELECT
  app_id,
  ROUND(
    100.0 * SUM(event_type = 'click') / NULLIF(SUM(event_type = 'impression'), 0),
    2
  ) AS ctr
FROM events
WHERE timestamp >= '2022-01-01' AND timestamp < '2023-01-01'
GROUP BY app_id;
```

(MySQL/PostgreSQL both treat `boolean_expr` as 0/1 in arithmetic.) For PostgreSQL strictly, wrap with `::int`:
```sql
ROUND(
  100.0 * SUM((event_type = 'click')::int) /
  NULLIF(SUM((event_type = 'impression')::int), 0),
  2
) AS ctr
```

### Why it's optimal
- Single scan over a date-filtered partition — predicate pushdown uses an index on `timestamp`.
- No self-join; both numerator and denominator come from one aggregate pass.
- `NULLIF` keeps the query safe and exact — no NaN or runtime error.

### Common mistakes & interviewer tips
Common mistakes: dividing without `NULLIF` and crashing on zero-impression apps, forgetting the date filter and mixing years, or returning 0/1 decimals instead of a percentage. Tip: in interviews, clarify whether the answer is a fraction (0.05) or a percentage (5.00). Mention that an index on `(timestamp)` or partitioning by date is the production move at Facebook scale.