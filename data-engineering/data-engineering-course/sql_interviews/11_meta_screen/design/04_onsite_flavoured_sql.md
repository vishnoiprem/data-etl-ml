# 04 — Onsite-Flavored SQL Problems (Deeper, 6 problems)

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
>
> **Companion:** [medium.com/@premvishnoi](https://medium.com/@premvishnoi)

The 6 problems below are the patterns that show up in the 60-min
onsite SQL round at Meta in 2026. The screen asks 5 problems
in 25 min; the onsite asks 1-2 problems in 60 min, with more
business context and more follow-up questions.

The full onsite SQL question per [Aced 2026](https://www.aced.io/guides/meta-data-engineer-interview):

> *"Calculate what percentage of Messenger users who were
> active yesterday made a video call."*

Solutions in `code/meta_onsite_sql.sql`. Tests in
`tests/test_meta_onsite_sql.py`. Notebook in
`notebooks/03_meta_onsite_sql.ipynb`.

---

## Problem 1 — Messenger yesterday-active → video-call %

```sql
WITH yesterday_active AS (
    SELECT DISTINCT user_id
    FROM   messenger_event
    WHERE  DATE(event_ts) = DATE('now', '-1 day')
),
video_callers AS (
    SELECT DISTINCT caller_id AS user_id
    FROM   messenger_call
    WHERE  is_video = 1
      AND  DATE(started_ts) = DATE('now', '-1 day')
    UNION
    SELECT DISTINCT callee_id AS user_id
    FROM   messenger_call
    WHERE  is_video = 1
      AND  DATE(started_ts) = DATE('now', '-1 day')
)
SELECT CAST(COUNT(DISTINCT v.user_id) AS REAL) /
       COUNT(DISTINCT y.user_id) AS video_pct
FROM   yesterday_active y
LEFT JOIN video_callers v ON v.user_id = y.user_id;
```

The follow-up question is always: "How would you handle
users who logged in but didn't have any events?" The senior
answer names the `messenger_login` table as the canonical
truth for "active" — events can be noisy.

---

## Problem 2 — Instagram Stories: 7-day rolling retention by country

Already covered in `02_sql_problems.md` Problem 1. The onsite
version adds the *first_country* constraint: a user who
changed country in the last 30 days is attributed to the
first country. The implementation is a `FIRST_VALUE` window
over `country` ordered by `event_ts`.

---

## Problem 3 — WhatsApp: first-message Q1 cohort, power-user rate

> *"For users whose first message was in Q1 2024, compute
> the monthly message volume through Q3, and the % of each
> cohort that became a power user (>= 100 messages per
> month) by month 6."*

```sql
WITH first_msg AS (
    SELECT sender_id, MIN(DATE(sent_ts)) AS first_day
    FROM   whatsapp_message
    GROUP BY sender_id
),
q1_cohort AS (
    SELECT sender_id, first_day
    FROM   first_msg
    WHERE  first_day BETWEEN '2024-01-01' AND '2024-03-31'
),
monthly AS (
    SELECT q.sender_id,
           STRFTIME('%Y-%m', m.sent_ts) AS month,
           COUNT(*) AS n_msg
    FROM   q1_cohort q
    JOIN   whatsapp_message m ON m.sender_id = q.sender_id
    WHERE  STRFTIME('%Y-%m', m.sent_ts) <= '2024-09'
    GROUP BY q.sender_id, month
),
power_user_by_6 AS (
    SELECT sender_id, MAX(n_msg) AS peak
    FROM   monthly
    WHERE  month <= STRFTIME('%Y-%m', DATE(q1_first_day, '+6 months'))
    GROUP BY sender_id
)
SELECT
    (SELECT COUNT(*) FROM q1_cohort) AS cohort_size,
    SUM(CASE WHEN peak >= 100 THEN 1 ELSE 0 END) AS power_users,
    CAST(SUM(CASE WHEN peak >= 100 THEN 1 ELSE 0 END) AS REAL) /
        (SELECT COUNT(*) FROM q1_cohort) AS power_user_rate;
```

The follow-up: "How would you handle churned users?" The
senior answer names *right-censoring* — power-user rate
should be computed only over the users still active by
month 6.

---

## Problem 4 — Top-N advertisers by ad-set performance

> *"For each advertiser, return the top 3 ad-sets by
> 7-day return on ad spend (ROAS = revenue / spend). Only
> include advertisers with at least 5 ad-sets."*

```sql
WITH ad_set_perf AS (
    SELECT advertiser_id, ad_set_id,
           SUM(revenue) AS rev,
           SUM(spend)   AS sp,
           SUM(revenue) * 1.0 / NULLIF(SUM(spend), 0) AS roas
    FROM   ad_event
    WHERE  event_ts >= DATE('now', '-7 days')
    GROUP BY advertiser_id, ad_set_id
),
qualified AS (
    SELECT advertiser_id
    FROM   ad_set_perf
    GROUP BY advertiser_id
    HAVING COUNT(*) >= 5
),
ranked AS (
    SELECT a.*,
           ROW_NUMBER() OVER (PARTITION BY advertiser_id
                              ORDER BY roas DESC) AS rk
    FROM   ad_set_perf a
    WHERE  a.advertiser_id IN (SELECT advertiser_id FROM qualified)
)
SELECT advertiser_id, ad_set_id, roas
FROM   ranked
WHERE  rk <= 3
ORDER BY advertiser_id, rk;
```

The senior follow-up: "What if an ad-set has $0 spend?"
The right answer is `NULLIF(SUM(spend), 0)` to avoid
division-by-zero, and then `NULL` ROAS is filtered out
by `ORDER BY roas DESC` (NULLs sort last in SQLite).

---

## Problem 5 — Engagement-attribution by hour-of-day

> *"Compute the average engagement per post, broken out by
> the hour-of-day the post was published, for the last 30
> days. Return the 24-row series sorted by hour."*

```sql
WITH recent AS (
    SELECT post_id, post_ts, page_id
    FROM   facebook_post
    WHERE  post_ts >= DATE('now', '-30 days')
),
eng AS (
    SELECT post_id, COUNT(*) AS n_eng
    FROM   engagement_event
    WHERE  event_ts >= DATE('now', '-30 days')
    GROUP BY post_id
)
SELECT CAST(STRFTIME('%H', r.post_ts) AS INTEGER) AS hour,
       COUNT(DISTINCT r.post_id) AS n_posts,
       SUM(COALESCE(e.n_eng, 0)) AS total_eng,
       CAST(SUM(COALESCE(e.n_eng, 0)) AS REAL) /
           NULLIF(COUNT(DISTINCT r.post_id), 0) AS avg_eng
FROM   recent r
LEFT JOIN eng e ON e.post_id = r.post_id
GROUP BY hour
ORDER BY hour;
```

---

## Problem 6 — Ads auction time-travel

> *"Given the ad_auction_event table (auction_ts, ad_id,
> bid_amount, won_flag), support a time-travel query: 'what
> was the winning bid for ad X at time T?' Implement the
> schema and a query."*

```sql
CREATE TABLE ad_auction_event (
    auction_ts TEXT NOT NULL,
    ad_id      INTEGER NOT NULL,
    bid_amount REAL NOT NULL,
    won_flag   INTEGER NOT NULL  -- 0 or 1
);

CREATE INDEX idx_auction_ad_ts ON ad_auction_event(ad_id, auction_ts);

-- Time-travel query.
SELECT bid_amount
FROM   ad_auction_event
WHERE  ad_id = ?    -- ad X
  AND  won_flag = 1
  AND  auction_ts <= ?   -- time T
ORDER BY auction_ts DESC
LIMIT 1;
```

The senior follow-up: "What if there are multiple winning
bids in the same second?" The answer is to use a microsecond
timestamp or to add a sequence number.

---

*Author: Prem Vishnoi &lt;pvishnoi@avilx.com&gt;*
