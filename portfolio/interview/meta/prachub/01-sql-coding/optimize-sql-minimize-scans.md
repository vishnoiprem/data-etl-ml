# Optimize SQL to Minimize Scans

## 1. Simple way to think
- A "scan" is each time the engine reads a table (or a partition of one).
- Multiple CTEs that all read the same big table = multiple scans of that table.
- Often you can inline a CTE (or use a subquery) so the engine reads the table once and applies multiple predicates/aggregations.
- Other wins: predicate pushdown, join reordering (small driver table first), avoiding `SELECT *`.

## 2. Interview write-up (how to solve it)
A common refactor: three CTEs all hitting the same `events` table can be folded into one CTE that scans `events` once and emits multiple aggregates.

Before (three scans of `events`):
```sql
WITH s1 AS (SELECT user_id, COUNT(*) FROM events WHERE event_type = 'click' GROUP BY 1),
     s2 AS (SELECT user_id, COUNT(*) FROM events WHERE event_type = 'view'  GROUP BY 1),
     s3 AS (SELECT user_id, MIN(ts)   FROM events GROUP BY 1)
SELECT u.user_id, s1.count, s2.count, s3.min_ts
FROM users u
LEFT JOIN s1 USING (user_id)
LEFT JOIN s2 USING (user_id)
LEFT JOIN s3 USING (user_id);
```

After (one scan of `events`):
```sql
WITH agg AS (
    SELECT user_id,
           COUNT(*) FILTER (WHERE event_type = 'click') AS clicks,
           COUNT(*) FILTER (WHERE event_type = 'view')  AS views,
           MIN(ts)                                     AS first_event_ts
    FROM events
    GROUP BY user_id
)
SELECT u.user_id, COALESCE(a.clicks, 0), COALESCE(a.views, 0), a.first_event_ts
FROM users u
LEFT JOIN agg a USING (user_id);
```

## 3. Best optimized solution
Combine with a covering index and a date filter so the scan is a partition/index-range scan.

```sql
CREATE INDEX idx_events_user_type_ts
  ON events (user_id, event_type, ts);

WITH agg AS (
    SELECT user_id,
           COUNT(*) FILTER (WHERE event_type = 'click') AS clicks,
           COUNT(*) FILTER (WHERE event_type = 'view')  AS views,
           MIN(ts)                                     AS first_event_ts
    FROM events
    WHERE ts >= CURRENT_DATE - INTERVAL '30 days'   -- partition pruning
    GROUP BY user_id
)
SELECT u.user_id,
       COALESCE(a.clicks, 0)      AS clicks,
       COALESCE(a.views,  0)      AS views,
       a.first_event_ts
FROM users u
LEFT JOIN agg a USING (user_id);
```

### Why it's optimal
- One pass over `events` instead of three.
- `FILTER` is a planner-friendly way to do conditional aggregation (vs. `CASE WHEN`).
- Date filter enables partition pruning; covering index serves the GROUP BY.
- `LEFT JOIN` against a small dimension (`users`) keeps the hash table small.

### Common mistakes & interviewer tips
- Forgetting that some warehouses (BigQuery) charge per bytes scanned — fewer scans = lower cost.
- Using `OR` instead of `FILTER`/`UNION ALL` — `OR` often defeats indexes.
- Tip: when explaining the refactor, quantify the win: "3× reduction in I/O on the largest table." Numbers convince interviewers.
