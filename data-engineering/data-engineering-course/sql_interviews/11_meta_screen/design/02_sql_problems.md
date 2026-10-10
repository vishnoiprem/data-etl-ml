# 02 — The 5 SQL Screen Problems (Worked Solutions)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
>
> **Companion:** [medium.com/@premvishnoi](https://medium.com/@premvishnoi)

The 5 problems below are calibrated to the 2026 Meta DE CoderPad
screen. They mirror the [Aced.io 2026](https://www.aced.io/guides/meta-data-engineer-interview)
"5 SQL in 25 min" format. Each problem has a 5-minute target.

Solutions in `code/meta_screen_sql.sql`. Tests in `tests/test_meta_screen_sql.py`.
Runnable notebook in `notebooks/01_meta_screen_sql.ipynb`.

---

## TL;DR

| # | Pattern tested | What it tests | 5-min target |
|---|----------------|---------------|--------------|
| 1 | Window function + cohort + HAVING filter | Filter *after* aggregation, not before | CTE → window → HAVING |
| 2 | Time-window JOIN + self-comparison | Compare per-post to per-page peak | JOIN ON range → HAVING |
| 3 | HAVING-then-RANK (qualifying-page predicate) | Filter dim by MIN before ranking | subquery → RANK() |
| 4 | Sessionization (LAG + cumulative sum) | The signature Meta pattern | LAG → flag → SUM OVER |
| 5 | Gaps-and-islands (date trick) | Longest streak per entity | ROW_NUMBER → DATE math |

The pass bar is 3 of 5. Problem 4 is the **most-skipped** problem on the
real test — it's the one most candidates haven't seen before. Problem 5 is
the **most-failed** problem — the date trick is non-obvious.

---

## Problem 1 — 7-day rolling retention by country

> *"From the instagram_story_events table, compute the 7-day rolling
> retention: for each user who first appeared on day D, what
> percentage returned at any point in the 7 days after D? Return
> the country and the retention rate, for users with at least
> 1,000 first-time posters per country."*

### Solution

```sql
WITH first_seen AS (
    SELECT user_id,
           country,
           MIN(DATE(event_ts)) AS first_day
    FROM   instagram_story_events
    GROUP BY user_id, country
),
window_activity AS (
    SELECT f.user_id, f.country, f.first_day,
           MAX(CASE WHEN DATE(e.event_ts) BETWEEN f.first_day
                                            AND DATE(f.first_day, '+7 days')
                    THEN 1 ELSE 0 END) AS returned
    FROM   first_seen f
    JOIN   instagram_story_events e
      ON   e.user_id = f.user_id
    GROUP BY f.user_id, f.country, f.first_day
),
country_stats AS (
    SELECT country,
           COUNT(*) AS total,
           SUM(returned) AS returned_count
    FROM   window_activity
    GROUP BY country
)
SELECT country,
       CAST(returned_count AS REAL) / total AS retention_7d
FROM   country_stats
WHERE  total >= 1000
ORDER BY retention_7d DESC;
```

### What the interviewer is testing

- **Window vs. join.** The naive answer is a self-join on
  `user_id` with `DATEDIFF` filtering. The clean answer is
  a single window over `event_ts`. The window is faster on
  large event tables.
- **`MIN(DATE(...))` vs. `MIN(event_ts)`.** The first gives a
  day-grain first_seen. The second gives the timestamp. The
  question asks for *day*, so the first is correct.
- **The 1,000-user threshold.** "At least 1,000 first-time
  posters per country" — this is a *post-aggregation* filter.
  You cannot `WHERE total >= 1000` before grouping. Use a
  CTE and filter in the outer query.

---

## Problem 2 — Peak engagement in first hour

> *"From facebook_post and a separate engagement_event table,
> find posts where the engagement in the first hour after
> publication was >= 10% of the peak hour-1 engagement ever
> observed for that page. Return post_id, page_id, hour-1
> engagement, and the page's peak."*

### Solution

```sql
WITH hour1 AS (
    SELECT p.post_id, p.page_id, p.post_ts,
           COUNT(e.event_id) AS hour1_eng
    FROM   facebook_post p
    LEFT JOIN engagement_event e
      ON  e.post_id = p.post_id
     AND  e.event_ts BETWEEN p.post_ts
                        AND DATETIME(p.post_ts, '+1 hour')
    GROUP BY p.post_id, p.page_id, p.post_ts
),
peak AS (
    SELECT page_id, MAX(hour1_eng) AS peak_hour1
    FROM   hour1
    GROUP BY page_id
)
SELECT h.post_id, h.page_id, h.hour1_eng, p.peak_hour1
FROM   hour1 h
JOIN   peak p ON p.page_id = h.page_id
WHERE  h.hour1_eng >= 0.10 * p.peak_hour1
ORDER BY h.hour1_eng DESC;
```

### What the interviewer is testing

- **`BETWEEN` with `DATETIME` arithmetic.** SQLite uses the
  `DATETIME(x, '+N hours')` modifier, not `DATE_ADD`. Naming
  the dialect in narration is a 4/4 signal.
- **LEFT JOIN for "posts with 0 engagement."** `INNER JOIN`
  drops posts with no engagement events. The right answer is
  `LEFT JOIN` so the count is 0.
- **Two-step aggregation.** Hour-1 first, then peak. The
  wrong answer is one giant CTE that mixes both. Two CTEs is
  cleaner and faster.

---

## Problem 3 — Top-3 posts per page (with threshold)

> *"Return the top 3 posts per page by likes, but only for
> pages where the median post has at least 50 likes."*

### Solution

```sql
WITH page_stats AS (
    SELECT page_id, likes
    FROM   facebook_post
),
qualified_pages AS (
    SELECT page_id
    FROM   page_stats
    GROUP BY page_id
    HAVING MIN(likes) >= 50  -- proxy for median ≥ 50
),
ranked AS (
    SELECT post_id, page_id, likes,
           ROW_NUMBER() OVER (PARTITION BY page_id
                              ORDER BY likes DESC) AS rk
    FROM   facebook_post
    WHERE  page_id IN (SELECT page_id FROM qualified_pages)
)
SELECT post_id, page_id, likes
FROM   ranked
WHERE  rk <= 3
ORDER BY page_id, rk;
```

### What the interviewer is testing

- **"Filter before window, not after."** The 2026 Meta guide
  explicitly calls this out as a common mistake. The
  `WHERE page_id IN (...)` is in the *ranked* CTE, not the
  outer query.
- **`MIN` as a proxy for median.** SQLite has no `MEDIAN`
  function. Using `MIN(likes) >= 50` is a conservative
  under-approximation. Naming the proxy in narration is
  the senior move.
- **`ROW_NUMBER` vs `RANK` vs `DENSE_RANK`.** The question
  says "top 3." That's `ROW_NUMBER` (ties are *not* allowed
  to take the same rank). Naming the choice in narration
  is a 4/4 signal.

---

## Problem 4 — Sessionize events (30-min gap)

> *"From instagram_story_events, define a session as a sequence
> of events by the same user where no two consecutive events
> are more than 30 minutes apart. Return user_id, session_id,
> session_start, session_end, and event_count."*

### Solution

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

### What the interviewer is testing

- **`LAG` for the previous event.** This is the heart of
  sessionization. The window function is preferred over a
  self-join.
- **`JULIANDAY` for time math.** `event_ts - prev_ts`
  doesn't work on ISO strings. Convert to Julian day
  numbers first.
- **Cumulative sum of `new_session` for session IDs.**
  The pattern is `SUM(flag) OVER (ORDER BY ts)` — the
  flag increments only on a gap. This is the *signature*
  Meta sessionization pattern. See
  `design/05_sessionization_pattern.md` for the full
  deep-dive.

---

## Problem 5 — Gaps-and-islands (3+ consecutive days)

> *"Find users who had at least one instagram_story event on
> 3 or more consecutive calendar days. Return user_id and the
> longest streak."*

### Solution

```sql
WITH user_days AS (
    SELECT DISTINCT user_id, DATE(event_ts) AS d
    FROM   instagram_story_events
),
grp AS (
    SELECT user_id, d,
           DATE(d, '-' || (ROW_NUMBER() OVER (PARTITION BY user_id
                                              ORDER BY d)) || ' days') AS grp_key
    FROM   user_days
),
streaks AS (
    SELECT user_id, grp_key,
           COUNT(*)      AS streak_len,
           MIN(d)        AS streak_start,
           MAX(d)        AS streak_end
    FROM   grp
    GROUP BY user_id, grp_key
)
SELECT user_id, MAX(streak_len) AS longest_streak
FROM   streaks
WHERE  streak_len >= 3
GROUP BY user_id
ORDER BY longest_streak DESC;
```

### What the interviewer is testing

- **Gaps-and-islands pattern.** The trick is
  `d - ROW_NUMBER()` to make consecutive days map to the
  same offset. This is the *single most-asked* SQL
  pattern at Meta in 2026.
- **JULIANDAY arithmetic via `DATE(d, '-' || n || ' days')`.**
  This is the SQLite idiom. Production Meta uses Presto's
  `INTERVAL` syntax. Naming the dialect difference is
  the senior move.
- **Streak length via `COUNT(*)` per group.** The streak
  length is the count of rows in each `grp_key` partition.
  No recursive CTE needed.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
