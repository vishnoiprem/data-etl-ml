# Reels Watch-Session Model

## Problem
Reels needs a data model that answers: how long are watch sessions, how many reels
fit in a session, what makes a user keep watching, and which reels drive exits.
Sessions are the natural unit of analysis, not individual videos.

## How to Think
1. List the metrics:
   - Session duration, videos-per-session, completion %, like/share/save per session.
   - Per-reel engagement during a session.
   - Entry-source breakdown (profile vs explore vs share).
2. Identify the grains:
   - `fact_reels_session`: one row per session.
   - `fact_reel_view`: one row per (user, reel) view inside a session.
3. Pick fact-table types:
   - `fact_reels_session` -> accumulating snapshot if you track lifecycle stages,
     otherwise transactional (one row per session open event).
   - `fact_reel_view` -> transactional.
4. Dimensions and SCD:
   - `dim_reel` SCD2 (hashtags/audio/visibility change).
   - `dim_user` SCD2, `dim_sound` SCD1, `dim_device` SCD1.

## How to Remember
- **Pattern**: "Metrics -> Grains -> Fact table types -> Dims with SCD."
- **Grain mnemonic**:
  - "One session = one continuous viewing episode."
  - "One view = one reel shown once in a session."
- Session-level metrics (sums, ratios) live in the session fact;
  reel-level metrics live in the view fact. Don't mix.

## Schema (DDL)
```sql
CREATE TABLE fact_reels_session (
  session_key BIGINT, user_key BIGINT, session_date_key INT,
  device_key INT, entry_source_key INT,
  videos_watched INT, total_duration_ms BIGINT,
  likes_in_session INT, shares_in_session INT, saves_in_session INT,
  is_loop_heavy BOOLEAN, exit_reason VARCHAR(20)
);

CREATE TABLE fact_reel_view (
  view_key BIGINT, session_key BIGINT, user_key BIGINT, reel_key BIGINT,
  author_key BIGINT, position_in_session INT, view_date_key INT,
  watch_duration_ms INT, video_duration_ms INT, completion_pct DECIMAL(5,2),
  liked BOOLEAN, shared BOOLEAN, saved BOOLEAN
);

CREATE TABLE dim_reel (
  reel_key BIGINT, reel_id VARCHAR(40), author_user_key BIGINT,
  sound_key BIGINT, duration_ms INT, hashtags VARCHAR(20),
  effective_from DATE, effective_to DATE, is_current BOOLEAN
);

CREATE TABLE dim_user (
  user_key BIGINT, user_id VARCHAR(40), age_bucket VARCHAR(10),
  country VARCHAR(60), locale VARCHAR(20), tenure_days INT,
  effective_from DATE, effective_to DATE, is_current BOOLEAN
);

CREATE TABLE dim_sound ( sound_key BIGINT, sound_id VARCHAR(40), sound_name VARCHAR(120), artist VARCHAR(120), is_original BOOLEAN );
CREATE TABLE dim_device ( device_key INT, device_type VARCHAR(20), os VARCHAR(20), browser VARCHAR(20) );
CREATE TABLE dim_entry_source ( source_key INT, source_name VARCHAR(40) );
CREATE TABLE dim_date ( date_key INT PRIMARY KEY, full_date DATE, day_of_week VARCHAR(10), month INT, quarter INT, year INT );
```

## Common Mistakes
- Modeling each reel impression as a "session" -> destroys session-level metrics.
- Forgetting `position_in_session` -> cannot model drop-off curves.
- Storing `total_duration_ms` only at the view grain -> must aggregate carefully.
- Ignoring entry source; it is the strongest predictor of session length.

## AI Use Cases
- Predict session length from the first 3 reels' completion %.
- Cluster sessions into "binge", "casual", "bounce" for product analytics.
- Next-reel recommendation conditioned on session position.

## Interview Questions (natural flow)

These escalate from scope to production reality. Ask in order; each answer unlocks the next.

### 1. Scope
> "Walk me through what this session model is supposed to answer. Why is 'session' the right unit and not 'reel'?"

*Why it's natural:* tests the candidate's understanding that the *question* determines the grain, not the other way around. Reel-grain loses session metrics; user-grain loses per-content signals.

### 2. The split
> "You split session and view into two facts. Why? What happens to session-level metrics if I collapse them into one view-grain fact?"

*Why it's natural:* forces grain defense. The right answer: session-level SUMs require pre-aggregation; collapsing to view grain forces DISTINCT session_id everywhere.

### 3. Session definition
> "How do you define 'session boundary'? 30 minutes of inactivity? App backgrounding? A pull-to-refresh? Where in the schema does that decision live?"

*Why it's natural:* tests understanding that sessionization is a *policy*, not a schema column. The right answer involves a sessionizer job upstream, not a flag on the table.

### 4. Position matters
> "You have `position_in_session`. PM asks: 'At what position do users typically exit?' Walk me through the analysis and one pitfall."

*Why it's natural:* tests understanding that position is a *per-session* number, not a per-reel property. Same reel at position 3 vs position 30 has different exit probability — and that's a feature, not a bug.

### 5. SCD2 on dim_reel
> "A reel's hashtags change from #funny to #comedy. For sessions in January, which hashtag shows up in the 'top exit-reason reels' report?"

*Why it's natural:* SCD2 application. Tests if the candidate aligns dim_reel version with the session timestamp, not the reel's current state.

### 6. Metric trap
> "A junior computes 'avg completion per reel' as `AVG(completion_pct)`. Why is this biased, and what's the right metric?"

*Why it's natural:* avg-of-ratios is biased by reel duration. The right metric is `SUM(watch_duration_ms) / SUM(video_duration_ms)`.

### 7. Scale
> "500M sessions per day, 5B views. What breaks first, and what's the cheapest fix?"

*Why it's natural:* signals production reality. Position-in-session queries are the killer — `position` isn't a great partition key. The fix is bucketing or pre-aggregated drop-off curves.

### 8. Edge case
> "A user opens Reels, watches 1 reel, kills the app, reopens 2 hours later, watches 4 more. Is that 1 session or 2? What does your data say?"

*Why it's natural:* tests whether the candidate can reason about ambiguity in the session boundary policy. The data model must allow either answer to be reconstructed from raw events.

## 30-Day Sample Data (January 2026)

Volume budget for a small Reels test cohort:

| Table | Rows |
|-------|------|
| `dim_date` | 31 |
| `dim_user` | 25 (24 users, 1 SCD2 split for u-005 on Jan 10) |
| `dim_sound` | 8 |
| `dim_reel` | 30 |
| `dim_device` | 4 |
| `dim_entry_source` | 4 |
| `fact_reels_session` | ~110 (week 1-2 fully expanded; weeks 3-4 follow the same pattern) |
| `fact_reel_view` | ~1,500 (~6 views per session on average) |

### Drop-off curve (the model in action)

The defining feature of `fact_reel_view` is `position_in_session`. Within a session,
`completion_pct` typically decreases as position rises — early reels get full watch,
late reels show mid-roll exits. Session 1 (8 videos, user 1) shows this clearly:

```
position 1  -> 100.00%   (full watch)
position 2  ->  81.82%
position 3  ->  66.67%
position 4  ->  75.00%
position 5  ->  52.00%   (mid-roll drop)
position 6  ->  62.50%
position 7  ->  57.89%
position 8  ->  36.36%   (last reel, often truncated)
```

Session 2 (user 2, 14 videos, all 100% through position 8) and session 7 (user 8,
18 videos, full completion through position 16) are **outliers** — binge sessions
where the algorithm matched intent. Session 7 is also flagged `is_loop_heavy=1`
in `fact_reels_session`.

### SCD2 highlight

User u-005 (user_key=5) flips `locale` from `en_GB` to `en_US` on **2026-01-10**.
Two rows in `dim_user` with `effective_from`/`effective_to` boundary. Sessions
from Jan 1–9 report her English-UK feed-mix; sessions from Jan 10 onward report
US feed-mix.

### Sample queries that work against the 30-day load

```sql
-- Drop-off curve: avg completion_pct by position_in_session (view grain).
SELECT v.position_in_session,
       COUNT(*)                    AS views,
       ROUND(AVG(v.completion_pct), 1) AS avg_completion_pct
FROM fact_reel_view v
WHERE v.view_date_key BETWEEN 20260101 AND 20260114
GROUP BY v.position_in_session
ORDER BY v.position_in_session;

-- Session length distribution by entry source (session grain).
SELECT e.source_name,
       COUNT(*)                   AS sessions,
       ROUND(AVG(s.videos_watched), 1) AS avg_videos,
       ROUND(AVG(s.total_duration_ms) / 1000.0, 1) AS avg_duration_sec
FROM fact_reels_session s
JOIN dim_entry_source e ON e.source_key = s.entry_source_key
WHERE s.session_date_key BETWEEN 20260101 AND 20260114
GROUP BY e.source_name
ORDER BY avg_duration_sec DESC;

-- Loop-heavy sessions: how do they differ?
SELECT is_loop_heavy,
       COUNT(*)                   AS sessions,
       ROUND(AVG(videos_watched), 1) AS avg_videos,
       ROUND(AVG(likes_in_session), 1) AS avg_likes
FROM fact_reels_session
WHERE session_date_key BETWEEN 20260101 AND 20260114
GROUP BY is_loop_heavy;

-- SCD2 demo: sessions for u-005 before and after the en_GB->en_US locale flip.
-- He moved on Jan 10. Before that his locale='en_GB'; after, locale='en_US'.
SELECT u.locale,
       COUNT(*) AS sessions,
       ROUND(AVG(s.videos_watched), 1) AS avg_videos
FROM fact_reels_session s
JOIN dim_user u
  ON u.user_key = s.user_key
 AND s.session_date_key >= u.effective_from
 AND (s.session_date_key <  u.effective_to OR u.effective_to = '9999-12-31')
WHERE s.user_key = 5
GROUP BY u.locale;
```

### Expected output (sanity check)

```
drop-off by position (avg completion_pct):
  pos 1  ~ 95-100%
  pos 2  ~ 85-90%
  pos 3  ~ 75-80%
  pos 4  ~ 70-75%
  pos 5  ~ 55-65%
  pos 6  ~ 50-60%
  pos 7  ~ 45-55%
  pos 8+ ~ 35-45%

sessions by entry source:
  profile       ~ 60% of sessions, avg ~5 videos
  explore       ~ 25% of sessions, avg ~10 videos  (deepest)
  notification  ~ 10% of sessions, avg ~4 videos
  share         ~ 5%  of sessions, avg ~3 videos  (shortest)

loop-heavy sessions:
  is_loop_heavy=1 -> avg_videos ~16, avg_likes ~11
  is_loop_heavy=0 -> avg_videos ~7,  avg_likes ~3
```

Full row-by-row SQL is in `03_reels_watch_session.py` (`DIM_DATE_30D_REELS`,
`DIM_USER_30D_REELS`, `DIM_SOUND_30D`, `DIM_REEL_30D`, `DIM_DEVICE_30D_REELS`,
`DIM_ENTRY_SOURCE_30D`, `FACT_REELS_SESSION_30D`, `FACT_REEL_VIEW_30D`).