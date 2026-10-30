# Aggregate Netflix Metrics in SQL

## 1. Simple way to think
- You have a `watch_sessions(user_id, content_id, watch_date, minutes_watched)` table (or similar).
- "Today's metric + all prior days" is the textbook definition of a running / cumulative total.
- Two ways: a self-join (slow, O(n²)), or a window function (fast, O(n log n) with sort).
- Always think about the time grain: per day, per user-day, per content-day.

## 2. Interview write-up (how to solve it)
First aggregate to daily totals, then layer a window function for the cumulative column.

```sql
-- Step 1: daily total watch time
WITH daily AS (
    SELECT watch_date,
           SUM(minutes_watched) AS daily_minutes
    FROM watch_sessions
    GROUP BY watch_date
)
-- Step 2: cumulative running total
SELECT watch_date,
       daily_minutes,
       SUM(daily_minutes) OVER (
           ORDER BY watch_date
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
       ) AS cumulative_minutes
FROM daily
ORDER BY watch_date;
```

If you want a 7-day rolling average instead of a true cumulative:
```sql
AVG(daily_minutes) OVER (ORDER BY watch_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
```

## 3. Best optimized solution
```sql
WITH daily AS (
    SELECT watch_date,
           SUM(minutes_watched) AS daily_minutes
    FROM watch_sessions
    WHERE watch_date >= CURRENT_DATE - INTERVAL '365 days'
    GROUP BY watch_date
)
SELECT watch_date,
       daily_minutes,
       SUM(daily_minutes) OVER (ORDER BY watch_date) AS cum_minutes
FROM daily
ORDER BY watch_date;
```

### Why it's optimal
- One aggregation in the CTE, one window in the outer query — no self-join.
- The window function is single-pass, O(n) after the sort.
- Index hint: a covering index on `(watch_date)` is enough since we only need it for grouping; `(watch_date, minutes_watched)` is better.
- Partitioning by month in a real warehouse (BigQuery / Snowflake) lets date pruning kick in.

### Common mistakes & interviewer tips
- Using `SUM(...) OVER (ORDER BY watch_date)` without an explicit frame — this defaults to `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`, which can include ties. Be explicit.
- Forgetting to handle gaps in dates (a missing day will be missing from the cumulative, not zero-filled).
- Tip: ask whether the cumulative should be dense (zero-filled gaps) or sparse (only present days). It changes the answer.
