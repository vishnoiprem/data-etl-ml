# Data Model — The Gaps Between Clicks

A complete dimensional + fact model for clickstream visit + daily engagement, with identity stitching and shared-device ownership credit.

---

## Entity-Relationship Overview

```
                +----------------+
                |   dim_user     |
                +----------------+
                       |
                       |  user_id
                       v
+----------+   +----------------+   +-------------------+
| dim_device|-->|  fact_event    |-->| fact_auth_event   |
+----------+   | (raw clickstream)|  | (signin / signout)|
              +----------------+   +-------------------+
                       |
        +--------------+---------------+
        |                              |
        v                              v
+---------------+        +----------------------------+
|  fact_visit   |<------| dim_device_ownership        |
| (sessionized) |       | (who held device & when)    |
+---------------+        +----------------------------+
        |
        v
+---------------------------+
| agg_daily_page_device     |
| (daily rollup)            |
+---------------------------+
```

---

## 1. `dim_user` (Conformed Dimension)

**Grain:** one row per unique user (signed-in identity).

```sql
CREATE TABLE dim_user (
  user_id          BIGINT       PRIMARY KEY,
  email            STRING,
  registration_dt  DATE,
  country          STRING,
  age_band         STRING,
  -- SCD Type 2 columns (optional, easy to drop)
  valid_from       TIMESTAMP    NOT NULL,
  valid_to         TIMESTAMP,            -- NULL = current version
  is_current       BOOLEAN      NOT NULL
);
```

| Field | Type | Notes |
|---|---|---|
| `user_id` | BIGINT | Natural key from auth system |
| `registration_dt` | DATE | When the user signed up |
| `country`, `age_band` | STRING | Optional demographic attrs |
| `valid_from` / `valid_to` | TIMESTAMP | SCD2; NULL `valid_to` = current |

**Used by:** all joins where we need user attributes; `fact_visit.owner_user_id` looks up here.

---

## 2. `dim_device` (Conformed Dimension)

**Grain:** one row per physical device (e.g., phone, laptop, tablet).

```sql
CREATE TABLE dim_device (
  device_id         BIGINT       PRIMARY KEY,
  device_type       STRING,              -- mobile | tablet | desktop | other
  os                STRING,
  os_version        STRING,
  first_seen_ts     TIMESTAMP,
  is_shared_device  BOOLEAN      DEFAULT FALSE
);
```

| Field | Type | Notes |
|---|---|---|
| `device_id` | BIGINT | Hardware-derived (e.g., IDFA / cookie) |
| `device_type` | STRING | Channels for analyst filtering |
| `is_shared_device` | BOOLEAN | If TRUE → use `dim_device_ownership` |

**Used by:** visit-level and daily rollup aggregations; joined on `device_id`.

---

## 3. `fact_event` (Raw Clickstream — Immutable)

**Grain:** one row per click, pageview, tap, or scroll.

```sql
CREATE TABLE fact_event (
  event_id     BIGINT       PRIMARY KEY,
  device_id    BIGINT       NOT NULL,    -- FK -> dim_device
  user_id      BIGINT,                   -- FK -> dim_user (NULL = anonymous)
  event_ts     TIMESTAMP    NOT NULL,
  event_type   STRING,                   -- click | pageview | tap | scroll
  page         STRING,
  referrer     STRING,
  session_id   STRING                    -- backfilled during sessionization
);
PARTITION BY DATE(event_ts);
CLUSTER BY device_id, user_id;
```

| Field | Type | Notes |
|---|---|---|
| `event_id` | BIGINT | Surrogate / de-dupe key |
| `user_id` | BIGINT | **NULL allowed** for pre-auth events |
| `event_ts` | TIMESTAMP | UTC; the only time field that matters |
| `page` | STRING | URL path or screen name |
| `session_id` | STRING | Filled post-hoc by Step A in WORKING.md |

**Index hints:**
- Partition by `DATE(event_ts)` (clicks-per-day is the dominant access pattern).
- Cluster by `(device_id, user_id)` for sessionization and identity-stitching scans.

**Used by:** sessionization (Step A) and identity stitching (Step B).

---

## 4. `fact_auth_event` (Identity-Link Fact)

**Grain:** one row per signin / signout event per device.

```sql
CREATE TABLE fact_auth_event (
  auth_id      BIGINT       PRIMARY KEY,
  device_id    BIGINT       NOT NULL,    -- FK -> dim_device
  user_id      BIGINT       NOT NULL,    -- FK -> dim_user
  auth_ts      TIMESTAMP    NOT NULL,
  auth_type    STRING                    -- signin | signout
);
PARTITION BY DATE(auth_ts);
```

| Field | Type | Notes |
|---|---|---|
| `auth_type` | STRING | `signin` anchors ownership windows |
| `auth_ts` | TIMESTAMP | When signin/signout happened |

**Used by:**
- Identity stitching (most-recent prior signin → fills anonymous `user_id`)
- Building `dim_device_ownership` (signin → start window, next signin → end)

---

## 5. `dim_device_ownership` (Device-Holder History)

**Grain:** one row per (device, user, ownership window).

```sql
CREATE TABLE dim_device_ownership (
  device_id    BIGINT       NOT NULL,
  user_id      BIGINT       NOT NULL,
  valid_from   TIMESTAMP    NOT NULL,
  valid_to     TIMESTAMP,                -- NULL = still owns device
  PRIMARY KEY (device_id, valid_from)
);
```

| Field | Type | Notes |
|---|---|---|
| `valid_from` | TIMESTAMP | Signin time |
| `valid_to` | TIMESTAMP | Next signin time, or NULL |

**Derived from:** `fact_auth_event` using a `LEAD(auth_ts)` window.

**Used by:** attributing each `fact_visit` to the holder during `[start_ts, end_ts)`.

---

## 6. `fact_visit` (Session-Level Fact — The Primary Output)

**Grain:** one row per session (visit) — events grouped by device with ≤30-min gaps.

```sql
CREATE TABLE fact_visit (
  visit_id          STRING        PRIMARY KEY,
  device_id         BIGINT        NOT NULL,    -- FK -> dim_device
  owner_user_id     BIGINT        NOT NULL,    -- FK -> dim_user (device holder)
  start_ts          TIMESTAMP     NOT NULL,
  end_ts            TIMESTAMP     NOT NULL,
  duration_sec      INT,
  event_count       INT,
  pages_visited     INT,
  distinct_pages    INT,
  is_authenticated  BOOLEAN,
  drop_off_page     STRING                     -- last page before session end
);
PARTITION BY DATE(start_ts);
CLUSTER BY device_id, owner_user_id;
```

| Field | Type | Notes |
|---|---|---|
| `visit_id` | STRING | Stable hash of `(device_id, visit_seq)` |
| `owner_user_id` | BIGINT | **Whoever held device during `[start_ts, end_ts)`** |
| `duration_sec` | INT | `end_ts - start_ts` (seconds) |
| `event_count` | INT | `COUNT(*) FROM fact_event WHERE visit_id = v.visit_id` |
| `is_authenticated` | BOOLEAN | Any event in visit had non-NULL `user_id` |
| `drop_off_page` | STRING | Last `page` value (for funnel analysis) |

**Supports questions:**
- "How long was the visit?" → `duration_sec`
- "How many events?" → `event_count`
- "Where did it drop off?" → `drop_off_page`
- "Who actually did this visit on a shared device?" → `owner_user_id`

---

## 7. `agg_daily_page_device` (Pre-Aggregated Rollup)

**Grain:** one row per `day × page × device` — built from `fact_visit` + `fact_event`.

```sql
CREATE TABLE agg_daily_page_device (
  dt                DATE          NOT NULL,
  page              STRING        NOT NULL,
  device_id         BIGINT        NOT NULL,
  visits            INT,
  events            BIGINT,
  unique_visitors   INT,                         -- COUNT DISTINCT owner_user_id
  avg_duration_sec  DECIMAL(10,2),
  PRIMARY KEY (dt, page, device_id)
);
PARTITION BY dt;
```

| Field | Type | Notes |
|---|---|---|
| `dt` | DATE | `CAST(visit.start_ts AS DATE)` |
| `visits` | INT | `COUNT(DISTINCT visit_id)` |
| `events` | BIGINT | Sum of `fact_event` counts |
| `unique_visitors` | INT | `COUNT(DISTINCT owner_user_id)` (handles shared device correctly) |
| `avg_duration_sec` | DECIMAL | `AVG(duration_sec)` |

**Supports questions:**
- "Daily engagement by page and device?" → direct read; no on-the-fly aggregation.
- "How many unique people visited page X on device Y today?" → `unique_visitors`.

---

## Grain Summary Table

| Table | Grain | Cardinality Hint |
|---|---|---|
| `dim_user` | 1 row / user | millions |
| `dim_device` | 1 row / device | hundreds of millions |
| `fact_event` | 1 row / click | **billions/day** |
| `fact_auth_event` | 1 row / signin-signout | millions/day |
| `dim_device_ownership` | 1 row / (device, holder-window) | tens of millions |
| `fact_visit` | 1 row / session (~10-50 events each) | tens of millions/day |
| `agg_daily_page_device` | 1 row / day × page × device | millions/day |

---

## Join Paths (Cheat Sheet)

| Question | Join |
|---|---|
| "Show me everything User 42 did today" | `dim_user` → `fact_visit.owner_user_id` → `fact_event.visit_id` |
| "Today's visits by page" | `agg_daily_page_device` (no join needed) |
| "Anonymous on Device 7 — who is it?" | `fact_event[user_id IS NULL]` ↔ `fact_auth_event` on `device_id` (most-recent prior signin) |
| "Who actually did the visit on Device 7?" | `fact_visit` ↔ `dim_device_ownership` on `(device_id, start_ts ∈ [valid_from, valid_to))` |
| "Drop-off funnel on Page X" | `fact_event` filtered on `page = X`, ordered by `event_ts` within `visit_id` |

---

## Storage / Scaling Notes

| Concern | Mitigation |
|---|---|
| Clickstream volume (billions/day) | Partition `fact_event` by `DATE(event_ts)`; cluster by `device_id` |
| Sessionization latency | Incremental sessionization — only process new events, carry forward `visit_seq` per device |
| Late-arriving auth | Re-stitch `fact_event.user_id` on a replay job; mark `is_restitched = TRUE` |
| Shared-device disputes | If two ownership windows overlap a visit, split the visit at the auth boundary (see WORKING.md Step 7) |
| Daily rollup latency | Build `agg_daily_page_device` in an hourly incremental job, not from scratch |
| Storage cost | Tier `fact_event` older than 90 days to cold storage (e.g., Parquet on S3); keep `fact_visit` + rollups hot |

---

## Easy-to-Remove Pieces (Recap)

| Component | Drop when… |
|---|---|
| `dim_device_ownership` | Single-user devices only |
| `agg_daily_page_device` | Small data; compute on read |
| `is_authenticated` flag | Trivial to derive; keep only if dashboards filter on it |
| SCD2 on `dim_user` | User attributes are immutable |
| `dim_device.os_version` etc. | Only need device_type for analyst reporting |
