# Working: The Gaps Between Clicks

> **Note on attribution:** The problem statement as quoted below is from Google's interview archive ("The Gaps Between Clicks"). It is filed here under `medium/meta/datadriven/` because the underlying modeling challenge — visit-level analysis + daily rollups + identity stitching + shared-device ownership credit — is identical to problems posed at Meta (FB/IG/WhatsApp) on data-engineering and analytics-infra interviews. SQL examples use Presto/Hive syntax (Meta-style); PySpark remains relevant for large-scale batch.

## Problem Statement (Restated)

We run a consumer web and mobile product that emits a high-volume clickstream: every page view, tap, and scroll lands as an event tied to a device, and a visitor is usually anonymous for a while before they sign in. Analysts need:
1. **Visit-level analysis** - session length, event count, drop-off points
2. **Daily engagement rolled up by page and device**
3. **A session = activity with no more than a 30-minute gap between consecutive events**
4. **Anonymous ↔ signed-in linkage** - so the same person is tracked across identity
5. **Device ownership credit** - a shared device passes between people, each owning it only for a bounded stretch → credit each visit to whoever held the device during that window

---

## How to Think About This (Step-by-Step Framework)

### Step 1: Identify the Core Entities

| Entity | Meaning | Key Fields |
|---|---|---|
| `event` | A single click/pageview/tap | `event_id, device_id, user_id, event_ts, page, event_type` |
| `visit (session)` | A bounded activity window per device | `visit_id, device_id, start_ts, end_ts, event_count, owner_user_id` |
| `device` | The physical/shared device | `device_id` |
| `user` | A person (signed-in identity) | `user_id` |
| `auth_event` | Sign-in/sign-out linking anonymous → signed-in | `device_id, user_id, auth_ts, auth_type` |

### Step 2: Identify the Business Questions

| Question Type | Granularity | Grain |
|---|---|---|
| Visit-level metrics | Per session | one row per visit |
| Daily engagement | Per day × page × device | one row per day/page/device |
| Cross-identity analysis | Per user | stitches anonymous + signed-in |
| Device ownership | Per visit-window | one row per visit with an `owner_user_id` |

### Step 3: Recognize the Challenges (The "Tricky" Parts)

1. **Anonymous → Signed-in**: a device's events have no `user_id` until sign-in, so we must back-fill identity using auth events.
2. **Shared device / ownership windows**: the same device_id may belong to User A from 8-10am and User B from 10am-12pm; visits must be credited to whoever held it **during the visit window**.
3. **Visit boundary = 30-min gap**: standard "sessionization" logic; new session when `prev_event_ts + 30min <= current_event_ts`.
4. **Late-arriving auth**: a sign-in can happen *after* events already occurred (those events were anonymous, now we know who did them).
5. **Dual output needs**: visit-level grain AND daily rollup grain — design two fact tables (or one fact + one aggregate).

### Step 4: Choose a Modeling Approach

**Dimensional + Fact Hybrid:**
- `dim_user` (SCD Type 2 not required, but track `device_history` as a fact)
- `dim_device`
- `fact_event` (grain: one row per click)
- `fact_visit` (grain: one row per session/visit — **derived from fact_event**)
- `agg_daily_page_device` (grain: one row per day × page × device — **derived from fact_visit**)
- `fact_device_ownership` (grain: one row per (device, user, window) — auth-event derived)

### Step 5: Sessionization Algorithm

```
For each device, ORDER events by timestamp:
  if first event OR (event_ts - prev_event_ts) > 30 min:
      start NEW visit
  else:
      continue CURRENT visit
Emit: visit_id, device_id, start_ts, end_ts, event_count
```

### Step 6: Identity Stitching Algorithm

For each anonymous event, find the **most recent prior auth_event** on the same device (`auth_ts <= event_ts`), and assign that `user_id`. If no prior auth, leave `user_id` as the device-level anonymous identifier.

### Step 7: Device Ownership Credit Algorithm

For each visit `[start_ts, end_ts]`, find the **overlapping device-ownership window** (i.e., `owner_auth_ts <= start_ts AND (end_auth_ts IS NULL OR end_auth_ts >= end_ts)`). If ownership changes mid-visit (rare with a 30-min gap), split the visit.

---

## Solution

### High-Level Architecture

```
                        +------------------+
RAW clickstream  --->   |  fact_event      |  (one row per click)
                        +------------------+
                                |
            +-------------------+-------------------+
            |                   |                   |
            v                   v                   v
   fact_visit (sessionize)  fact_identity_link   fact_device_ownership
            |                                       (auth-event derived)
            v
   agg_daily_page_device  <-- rolls up visits by day x page x device
```

### Data Model

```sql
-- 1) Raw events: fact_event (immutable, append-only)
CREATE TABLE fact_event (
  event_id        BIGINT,
  device_id       BIGINT,
  user_id         BIGINT,           -- may be NULL (anonymous)
  event_ts        TIMESTAMP,
  page            STRING,
  event_type      STRING,           -- click | pageview | tap | scroll
  session_id      STRING            -- backfilled during sessionization
);

-- 2) Auth events: linking anonymous to signed-in
CREATE TABLE fact_auth_event (
  auth_id         BIGINT,
  device_id       BIGINT,
  user_id         BIGINT,
  auth_ts         TIMESTAMP,
  auth_type       STRING            -- signin | signout
);

-- 3) Device ownership: who held the device and when
CREATE TABLE dim_device_ownership (
  device_id       BIGINT,
  user_id         BIGINT,
  valid_from      TIMESTAMP,
  valid_to        TIMESTAMP         -- NULL = still active
);

-- 4) Visit fact: session-level metrics
CREATE TABLE fact_visit (
  visit_id        STRING,
  device_id       BIGINT,
  owner_user_id   BIGINT,           -- whoever held device during window
  start_ts        TIMESTAMP,
  end_ts          TIMESTAMP,
  event_count     INT,
  duration_sec    INT,
  pages_visited   INT,
  is_authenticated BOOLEAN
);

-- 5) Daily rollup: pre-aggregated for analyst dashboards
CREATE TABLE agg_daily_page_device (
  dt              DATE,
  page            STRING,
  device_id       BIGINT,
  visits          INT,
  events          BIGINT,
  unique_visitors INT
);
```

### Spark / SQL Implementation

#### Step A: Sessionize Events (30-min gap)

```sql
WITH ordered AS (
  SELECT
    event_id, device_id, user_id, event_ts, page, event_type,
    LAG(event_ts) OVER (PARTITION BY device_id ORDER BY event_ts) AS prev_ts,
    LAG(event_id) OVER (PARTITION BY device_id ORDER BY event_ts)  AS prev_id
  FROM fact_event
)
SELECT
  event_id, device_id, user_id, event_ts, page, event_type,
  SUM(CASE
        WHEN prev_ts IS NULL OR (event_ts - prev_ts) > INTERVAL 30 MINUTES
        THEN 1 ELSE 0
      END) OVER (PARTITION BY device_id ORDER BY event_ts) AS visit_seq
FROM ordered;
```

#### Step B: Stitch Anonymous → Signed-In Identity

```sql
WITH auth_match AS (
  SELECT
    e.event_id, e.device_id,
    COALESCE(e.user_id,
             (SELECT a.user_id
              FROM fact_auth_event a
              WHERE a.device_id = e.device_id
                AND a.auth_type = 'signin'
                AND a.auth_ts <= e.event_ts
              ORDER BY a.auth_ts DESC LIMIT 1)
    ) AS resolved_user_id,
    e.event_ts
  FROM fact_event e
)
SELECT * FROM auth_match;
```

#### Step C: Build Device Ownership Windows

```sql
WITH auth_pairs AS (
  SELECT
    device_id, user_id, auth_ts,
    LEAD(auth_ts) OVER (PARTITION BY device_id ORDER BY auth_ts) AS next_auth_ts,
    auth_type
  FROM fact_auth_event
)
SELECT
  device_id, user_id,
  auth_ts AS valid_from,
  COALESCE(LEAD(auth_ts) OVER (PARTITION BY device_id ORDER BY auth_ts),
           TIMESTAMP '2099-12-31') AS valid_to
FROM auth_pairs
WHERE auth_type = 'signin';
```

#### Step D: Credit Each Visit to the Owner During Its Window

```sql
SELECT
  v.visit_id, v.device_id,
  o.user_id AS owner_user_id,    -- whoever held device during [start_ts, end_ts]
  v.start_ts, v.end_ts, v.event_count
FROM fact_visit v
JOIN dim_device_ownership o
  ON v.device_id = o.device_id
 AND v.start_ts >= o.valid_from
 AND v.start_ts <  COALESCE(o.valid_to, TIMESTAMP '2099-12-31');
```

> **Edge case:** if ownership changes *inside* a single visit (visit > 30-min gap from auth), split the visit at the auth boundary — apply Step A again with a **hard split** at any ownership change.

#### Step E: Daily Page × Device Rollup

```sql
INSERT INTO agg_daily_page_device
SELECT
  CAST(v.start_ts AS DATE) AS dt,
  e.page,
  v.device_id,
  COUNT(DISTINCT v.visit_id)        AS visits,
  SUM(e_per_visit.cnt)              AS events,
  COUNT(DISTINCT v.owner_user_id)   AS unique_visitors
FROM fact_visit v
JOIN (SELECT visit_id, COUNT(*) cnt FROM fact_event GROUP BY visit_id) e_per_visit
  ON v.visit_id = e_per_visit.visit_id
JOIN fact_event e ON e.visit_id = v.visit_id
GROUP BY 1, 2, 3;
```

### PySpark Equivalent (for scale)

```python
from pyspark.sql import Window
import pyspark.sql.functions as F

# A: Sessionize
w = Window.partitionBy("device_id").orderBy("event_ts")
events = (events
    .withColumn("prev_ts", F.lag("event_ts").over(w))
    .withColumn("new_visit",
        F.when(F.col("prev_ts").isNull() |
               (F.col("event_ts") - F.col("prev_ts")) > F.expr("INTERVAL 30 MINUTES"), 1)
         .otherwise(0))
    .withColumn("visit_seq", F.sum("new_visit").over(w))
    .withColumn("visit_id",
        F.concat_ws("_", F.col("device_id"), F.col("visit_seq"))))

# B: Stitch identity via last-membership auth
auth_w = Window.partitionBy("device_id").orderBy("auth_ts")
auth = (auth_df
    .filter(F.col("auth_type") == "signin")
    .withColumn("valid_to",
        F.lead("auth_ts").over(auth_w)))

# Join: anonymous events inherit most recent prior auth
events = (events
    .join(auth.hint("broadcast"),
          on=(events.device_id == auth.device_id) &
             (events.event_ts >= auth.valid_from) &
             (events.event_ts <  F.coalesce(auth.valid_to, F.lit("2099-12-31"))),
          how="left")
    .withColumn("resolved_user_id",
        F.coalesce("user_id", "auth_user_id")))

# C: Build visits
visits = (events.groupBy("visit_id", "device_id")
    .agg(F.min("event_ts").alias("start_ts"),
         F.max("event_ts").alias("end_ts"),
         F.count("*").alias("event_count"))
    .withColumn("owner_user_id",
        F.first("resolved_user_id", ignorenulls=True)))   # owns the visit

# D: Daily rollup
rollup = (visits
    .join(events.select("visit_id", "page"), on="visit_id")
    .groupBy(F.col("start_ts").cast("date").alias("dt"),
             "page", "device_id")
    .agg(F.countDistinct("visit_id").alias("visits"),
         F.count("page").alias("events")))
```

### Why This Design Works for BOTH Levels

| Question | Table | Grain |
|---|---|---|
| "How long was the visit?" "Where did it drop off?" | `fact_visit` + drill back to `fact_event` via `visit_id` | per visit |
| "Daily engagement by page and device?" | `agg_daily_page_device` (pre-aggregated) | per day × page × device |
| "Did Anonymous on Device X become User Y later?" | `fact_auth_event` joined to `fact_event` | per identity event |
| "Who actually did this visit on a shared device?" | `fact_visit.owner_user_id` via `dim_device_ownership` | per visit |

---

## Points to Easy-to-Remove / Simplify

When presenting or scaling back the solution, you can drop these to keep the model lean:

| # | Component | What to drop | When to keep it |
|---|---|---|---|
| 1 | **`dim_device_ownership`** as a separate table | If only one user per device, derive `owner_user_id` directly from auth events | Multiple users share devices → must keep |
| 2 | **Visit splitting on ownership change** | If devices never change hands mid-visit (very short sessions), skip the hard split | Shared-family / kiosk scenarios → must keep |
| 3 | **`agg_daily_page_device`** as a physical table | Compute on-demand from `fact_visit` for small data | TB-scale → must pre-aggregate |
| 4 | **Identity stitching via subquery** | If `user_id` is always populated in `fact_event` (no anonymous period) | Pre-auth events exist → must keep |
| 5 | **`is_authenticated` flag on `fact_visit`** | Trivial to compute: `MAX(user_id IS NOT NULL)` per visit | Useful for analytics dashboards |
| 6 | **SCD Type 2 on `dim_user`** | If user attributes don't change (e.g., registration date only) | Historical demographics backfill → keep |
| 7 | **`auth_type = 'signout'` tracking** | If users only sign in once per device lifetime (no explicit signout) | Multi-user devices with active sessions → keep |
| 8 | **Page-level event ordering inside `fact_visit`** | Use `array_collect` only when you need "drop-off funnel" UI; otherwise `page` cardinalities explode | Funnels/path analysis required → keep |
| 9 | **Late-arriving auth re-stitching** | If auth events arrive in order with clicks (real-time pipeline) | Out-of-order ingestion (Kafka lag, mobile offline) → keep |
| 10 | **Bot / non-human filtering** | If your `fact_event` already excludes bots upstream | Bots detected post-hoc → keep a `is_bot` flag |

### Suggested "Easy-to-Remove" Shortlist (for the interview)

If the interviewer wants a leaner answer, cut these in priority order:
1. **Drop `dim_device_ownership`** — fold into `fact_visit` as a derived column
2. **Drop `agg_daily_page_device`** — say "computed on read from `fact_visit`"
3. **Drop visit-splitting-on-ownership-change** — note as an edge case
4. **Drop SCD Type 2** — single version of `dim_user`

---

## TL;DR (One-paragraph answer)

Model the world as **immutable events** (`fact_event`) plus a derived **visit fact** (`fact_visit`) sessionized by a 30-minute gap per device. Stitch anonymous → signed-in identity using `fact_auth_event` (most-recent-prior signin per device). Track **device ownership windows** via `dim_device_ownership` to credit each visit to whoever held the device during `[start_ts, end_ts)`. Pre-aggregate `agg_daily_page_device` for the daily rollup question. Two fact tables at different grains serve both analyst needs; identity stitching and ownership windows are the two non-obvious asks.
