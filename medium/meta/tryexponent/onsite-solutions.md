# Onsite Loop — SQL & Python Solutions

The three sample questions from the Exponent guide, with worked solutions, clarifications, and scale/streaming notes.

These prompts are open-ended and tied to a product case, so the work is: **clarify → pick the right primitive (window function vs streaming aggregator vs query builder) → write it → discuss scale**.

---

## Q1 — 15-minute tumbling window over a ride-request stream

**Prompt:** Given a stream of ride requests for a service like Uber, compute the number of ride requests in each 15-minute tumbling window.

**Clarify first:**
- What's the event shape? Assume `(request_id, rider_id, driver_id?, requested_at, pickup_lat, pickup_lng)`.
- Tumbling vs sliding — the prompt says tumbling, so windows are non-overlapping: `[00:00, 00:15)`, `[00:15, 00:30)`, ...
- Late-arriving events — drop, count in original window, or count in arrival window?
- Output: per-window count, or also per-city / per-product variant?

### Approach 1 — SQL over a stored event table (batch)

```sql
SELECT
  date_trunc('hour', requested_at)
    + INTERVAL '15 min' * (EXTRACT(MINUTE FROM requested_at)::INT / 15) AS window_start,
  COUNT(*) AS request_count
FROM ride_requests
WHERE requested_at >= CURRENT_DATE - INTERVAL '7 days'   -- clarify window
GROUP BY 1
ORDER BY 1;
```

This bucket expression is the standard trick: truncate to the hour, then add back the 15-min bucket. It avoids window functions and indexes cleanly on `requested_at`.

### Approach 2 — Streaming (Python, tumbling, late events dropped)

```python
from collections import defaultdict
from datetime import datetime, timedelta

WINDOW = timedelta(minutes=15)

def window_key(ts: datetime) -> datetime:
    epoch = ts.replace(minute=0, second=0, microsecond=0)
    bucket = (ts - epoch) // WINDOW
    return epoch + bucket * WINDOW

def count_requests(events, drop_late=True, watermark=None):
    counts = defaultdict(int)
    for evt in events:
        ts = evt["requested_at"]
        if drop_late and watermark and ts < watermark - WINDOW:
            continue                    # late, dropped
        counts[window_key(ts)] += 1
    return dict(counts)
```

### Approach 3 — PyFlink / Spark Streaming (production)

```python
# Pseudocode for a streaming job
events
  .with_watermark("requested_at", "15 minutes")
  .group_by(window(col("requested_at"), "15 minutes"))
  .agg(count("*").alias("request_count"))
```

**Streaming intuition to mention out loud:**
- **Tumbling** windows don't overlap → count is straightforward.
- **Sliding** windows overlap → you'd use `window(col(ts), "15 minutes", "5 minutes")` or maintain state per slide.
- **Late events:** watermarking (`max_seen_ts - allowed_lateness`) decides whether to drop or emit to a side output.
- **State growth:** counts are bounded by `num_windows` × `num_grouping_keys`, so periodic state cleanup is required in long-running jobs.

**At scale:** partition `ride_requests` by `requested_at` (daily or hourly); the `WHERE requested_at >= ...` becomes partition pruning.

---

## Q2 — % of Messenger users active yesterday who made a video call

**Prompt:** Calculate what percentage of Messenger users who were active yesterday made a video call.

**Clarify first:**
- "Active yesterday" — sent a message, opened the app, or any session event? Most common: any `message_sent` event.
- "Made a video call" — initiated, completed, or both? Most common: initiated (events are more reliable than completions).
- Universe: daily-active Messenger users, or all registered users who logged in yesterday?

### Schema (assumed)

```sql
users (user_id, signup_date, region, ...)
message_events (event_id, user_id, event_type, event_ts)  -- event_type ∈ {'sent','received'}
video_calls   (call_id, initiator_id, callee_id, started_at, ended_at)
```

### Solution

```sql
WITH active_yesterday AS (
  SELECT DISTINCT user_id
  FROM message_events
  WHERE event_type = 'sent'
    AND event_ts >= CURRENT_DATE - INTERVAL '1 day'
    AND event_ts <  CURRENT_DATE
),
callers_yesterday AS (
  SELECT DISTINCT initiator_id AS user_id
  FROM video_calls
  WHERE started_at >= CURRENT_DATE - INTERVAL '1 day'
    AND started_at <  CURRENT_DATE
)
SELECT
  100.0 * COUNT(DISTINCT c.user_id)
        / NULLIF(COUNT(DISTINCT a.user_id), 0) AS video_call_pct
FROM active_yesterday a
LEFT JOIN callers_yesterday c ON c.user_id = a.user_id;
```

**Why `NULLIF`?** Avoid divide-by-zero on quiet days.

**At scale:** both CTEs hit `event_ts` / `started_at` heavily — partition both tables by day. `DISTINCT` on `user_id` can be replaced by `COUNT(*) FILTER (WHERE ...)` if you don't need dedup across joins.

### Follow-up metric shapes the interviewer may push on

| Question | What it tests |
|----------|---------------|
| "What if we want users who **received** a call too?" | Add a second CTE on `callee_id` and `UNION` the caller set. |
| "What if activity = opened the app?" | Switch the source table to `app_sessions`. |
| "What if we want this per region?" | Add `users.region` to the joins and group by it. |
| "What if the dataset is at Meta scale (billions of events/day)?" | Approximate count distinct (HLL); pre-aggregate daily into a summary table. |

---

## Q3 — Dynamic SQL query formatter

**Prompt:** Write a function that dynamically formats a SQL query based on input parameters.

**Clarify first:**
- What kind of dynamism? Most common: parameterize a base query with WHERE filters, optional GROUP BY columns, and an optional LIMIT.
- Safety — always use **parameterized queries**; never f-string user input into SQL.

### Solution — composable WHERE filters

```python
def build_user_query(filters: dict, group_by: list[str] | None = None,
                     order_by: str | None = None, limit: int | None = None) -> tuple[str, list]:
    """
    Build a parameterized query against `users`.
    filters keys: allowed_columns -> value (equality) or (op, value)
    Returns (sql, params) — caller passes both to the driver.
    """
    where_clauses, params = [], []
    for col, val in filters.items():
        if isinstance(val, tuple) and len(val) == 2:
            op, v = val
            where_clauses.append(f"{col} {op} %s")
            params.append(v)
        else:
            where_clauses.append(f"{col} = %s")
            params.append(val)

    sql = "SELECT * FROM users"
    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)
    if group_by:
        sql += " GROUP BY " + ", ".join(group_by)
    if order_by:
        sql += " ORDER BY " + order_by
    if limit is not None:
        sql += " LIMIT %s"
        params.append(limit)
    return sql, params

# Example
sql, params = build_user_query(
    filters={"country": "US", "age": (">=", 18)},
    group_by=["country"],
    order_by="country",
    limit=100,
)
# sql: SELECT * FROM users WHERE country = %s AND age >= %s
#      GROUP BY country ORDER BY country LIMIT %s
# params: ["US", 18, 100]
```

### Key points to say out loud

- **Allowlist column names** before interpolating them into SQL; never trust raw strings for identifiers.
- **Parameterize values** (`%s` / `?` / `:name`) — the driver handles escaping.
- **Return `(sql, params)`** so the caller executes against a real DB; don't execute inside the function.
- **Compose, don't concatenate.** Building the query as a list of clauses keeps it readable and testable.

### At scale / production

- Pre-validate the filter keys against an allowlist.
- Use a query builder library (SQLAlchemy Core, pypika) rather than raw string composition once dynamism grows.
- Cache the query plan for repeated parameter shapes; PostgreSQL's prepared statements help automatically.

---

## Meta-tips for the onsite SQL/Python rounds

- **Tie every query back to the product case.** Don't drop into generic SQL mode; the metric must serve the round's narrative.
- **Narrate streaming choices.** Tumbling vs sliding, watermarks, late-event handling — say the words the interviewer is listening for.
- **First correct, then scale.** Get a working query, then add 1-2 sentences on indexing/partitioning.
- **For Python:** readable beats clever. Type hints and small functions > one big block.
- **Recover gracefully.** If a test fails, walk through it out loud before changing the code.