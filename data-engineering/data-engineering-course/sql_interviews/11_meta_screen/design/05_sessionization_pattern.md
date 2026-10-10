# 05 — The Sessionization Pattern (Deep Dive)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
>
> **Companion:** [medium.com/@premvishnoi](https://medium.com/@premvishnoi)

Sessionization is the **single most-asked SQL pattern at Meta
in 2026**. It appears in:

- The 5+5 screen (`02_sql_problems.md` Problem 4)
- The onsite SQL round (`04_onsite_flavoured_sql.md` Problem 1)
- The "investigate this metric drop" product-sense round
  (`behavioral_interviews/05_practice/design/12_product_sense_investigation.md`)
- The take-home (Meta's "Data Engineer Take-Home" format is
  *always* sessionization + funnel)

The deep-dive is here because the question is *exactly* the
kind of question that separates L4 from L5. The L4 answer
is a self-join on `event_ts` with `DATEDIFF`. The L5 answer
is a window function with a cumulative-sum flag. The L6
answer is the window function + a *named* gap heuristic
("30 min is right for *this* product because the median
inter-event gap is X").

## The pattern in 3 steps

**Step 1 — Find the previous event per user.**

```sql
LAG(event_ts) OVER (PARTITION BY user_id ORDER BY event_ts) AS prev_ts
```

The `LAG` is the heart. Without it, you're doing a
self-join, which is O(n²) on a large event table.

**Step 2 — Flag the rows that start a new session.**

A new session starts when:
- The previous event is `NULL` (the user's first event), or
- The gap from the previous event is > 30 minutes.

```sql
CASE WHEN prev_ts IS NULL
      OR (JULIANDAY(event_ts) - JULIANDAY(prev_ts)) * 24 * 60 > 30
     THEN 1 ELSE 0
END AS new_session
```

**Step 3 — Cumulative-sum the flag for a session_id.**

```sql
SUM(new_session) OVER (PARTITION BY user_id ORDER BY event_ts) AS session_id
```

The cumulative sum gives every row a *session index* per
user. Group by `(user_id, session_id)` to get the session
boundaries.

## The full query (canonical)

```sql
WITH events AS (
    SELECT user_id, event_ts,
           LAG(event_ts) OVER (PARTITION BY user_id
                               ORDER BY event_ts) AS prev_ts
    FROM   instagram_story_events
),
gaps AS (
    SELECT user_id, event_ts, prev_ts,
           CASE WHEN prev_ts IS NULL
                 OR (JULIANDAY(event_ts) - JULIANDAY(prev_ts)) * 24 * 60 > 30
                THEN 1 ELSE 0
           END AS new_session
    FROM   events
),
session_ids AS (
    SELECT user_id, event_ts,
           SUM(new_session) OVER (PARTITION BY user_id
                                  ORDER BY event_ts) AS session_id
    FROM   gaps
)
SELECT user_id,
       session_id,
       MIN(event_ts) AS session_start,
       MAX(event_ts) AS session_end,
       COUNT(*)      AS event_count
FROM   session_ids
GROUP BY user_id, session_id
ORDER BY user_id, session_id;
```

## The 5 common failure modes

1. **Self-join instead of `LAG`.** O(n²) instead of O(n).
2. **`event_ts - prev_ts` on strings.** ISO strings don't
   subtract. Use `JULIANDAY` first.
3. **Off-by-one on the gap.** "30 min" means the gap is
   *strictly greater than* 30 min, not `>=`. The right
   answer is `> 30` and the right answer is *named*.
4. **First-event handling.** The first event for a user
   has `prev_ts = NULL`. The flag must be 1.
5. **Late-arriving events.** If an event arrives 1 day late,
   the session_id may be wrong. The senior answer is to
   re-run the sessionization on a *replay* of the day's
   events.

## Variations Meta asks in 2026

- **"What if the gap is 5 min instead of 30?"** Same
  query, different constant. The senior answer names
  the constant and the *reason* (median inter-event gap).
- **"What if a session can span midnight?"** Yes, the
  session_id is per-user, not per-day. No code change.
- **"What if you want sessions with at least 2 events?"**
  `WHERE event_count >= 2` in the outer query.
- **"How do you handle late events?"** Re-run on a
  re-slice of the day's events. The senior answer
  names *replay* and *idempotency*.

## The 30-min gap is a *product* decision

The "30 min" gap is not from a textbook. It's a *product*
decision: "what counts as a session for the purposes of
*this* metric?" The right answer at L5+ is to *justify
the number*, not assume it.

A common L5 answer: "I'd look at the distribution of
inter-event gaps for a representative user cohort, and
pick a number where the gap is in the 90-95th
percentile." That's the senior move.

The notebook in `notebooks/04_sessionization.ipynb`
implements the full pattern, runs it on a 1,000-event
sample, and explores the gap-distribution question.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
