# Lesson 4 — Concrete Solutions to the 5 Most-Asked Schema Questions

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
>
> **Source:** [Aced 2026](https://www.aced.io/guides/meta-data-engineer-interview), [Interview101 2026](https://www.interview101.com/interviews/meta/data-engineer)

The 5 most-asked data-modeling questions from the 2026 guides, with
worked ER diagrams in plain text and the SQLite DDL that backs them.

---

## Q1 — Design a star schema to track Instagram Reels performance metrics across different recommendation algorithms.

### Grain
One row per (reel_id, viewer_id, hour_bucket, algorithm_version_id).

### Dimensions
- `dim_user` (SCD Type 1 on PII, Type 2 on `user_segment`)
- `dim_reel` (SCD Type 2 on `algorithm_version_id`, `audio_id`, `hashtag_set_id`)
- `dim_time` (hour-bucket dimension: 24 × 365 rows)
- `dim_algorithm_version` (SCD Type 2 — the *killer* dim, changes weekly)

### Facts
- `fct_reel_view` — 1 row per (reel, viewer, hour, algo)
  - `n_views`, `n_likes`, `n_shares`, `n_saves`, `n_completes`, `view_duration_ms`
- `fct_reel_skip` — 1 row per (reel, viewer, hour, algo) where viewer skipped < 3s

### Bridges
- `reel_hashtag_bridge(reel_id, hashtag_id)` — many-to-many
- `reel_audio_bridge(reel_id, audio_id)` — many-to-many
- `user_audience_bridge(user_id, audience_id)` — many-to-many

### Scale story
- 1B Reels/day × 5KB/row = 5TB/day raw
- Parquet + ZSTD → 0.5TB/day
- Partition key: `event_date` (1 partition per day)
- Sort key: `(algorithm_version_id, user_id, event_ts)`
- Pre-aggregate to 1-hour buckets in the mart

```sql
-- The fact table. One row per (reel, viewer, hour, algorithm version).
CREATE TABLE fct_reel_view (
    event_date              TEXT    NOT NULL,    -- YYYY-MM-DD
    hour_bucket             INTEGER NOT NULL,    -- 0..23
    reel_id                 INTEGER NOT NULL,
    viewer_id               INTEGER NOT NULL,
    algorithm_version_id    INTEGER NOT NULL,
    n_views                 INTEGER NOT NULL DEFAULT 0,
    n_likes                 INTEGER NOT NULL DEFAULT 0,
    n_shares                INTEGER NOT NULL DEFAULT 0,
    n_saves                 INTEGER NOT NULL DEFAULT 0,
    n_completes             INTEGER NOT NULL DEFAULT 0,
    view_duration_ms        INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (event_date, hour_bucket, reel_id, viewer_id, algorithm_version_id)
) WITHOUT ROWID;

-- The SCD2 dimension that the interviewer wants to hear about.
CREATE TABLE dim_algorithm_version (
    algorithm_version_id  INTEGER PRIMARY KEY,
    algorithm_name        TEXT    NOT NULL,
    parameters_json       TEXT    NOT NULL,         -- blob of weights, thresholds, etc.
    valid_from            TEXT    NOT NULL,         -- YYYY-MM-DD
    valid_to              TEXT    NOT NULL DEFAULT '9999-12-31',
    is_current            INTEGER NOT NULL DEFAULT 1
);
```

---

## Q2 — Meta wants to build a unified data model for cross-platform user behavior analysis (FB, IG, WA).

### Grain
One row per (unified_user_id, event_id, event_ts).

### Dimensions
- `dim_user` (SCD Type 1, with `unified_user_id` as the resolved identity)
- `dim_platform` (FB, IG, WA — SCD Type 1)
- `dim_content` (any post, message, story — SCD Type 2 on `lifecycle_state`)
- `dim_time`

### The killer: identity resolution
- `user_identity_bridge(unified_user_id, platform, platform_user_id, valid_from, valid_to)`
- 1 unified_user_id maps to N platform_user_ids
- This is the de-dupe problem: same person, 2 devices, 2 platforms

### Facts
- `fct_user_event` — 1 row per (user, event, time, platform)
- `fct_cross_platform_session` — 1 row per (unified_user, session, platform_chain)
  - `platform_chain` = e.g., "IG→WA→FB" — the "user used all 3 today" metric

### Scale story
- 3B users × 100 events/user/day = 300B events/day
- 300B events × 200 bytes/event = 60TB/day raw
- Parquet + ZSTD → ~6TB/day
- Hot partition: `(event_date, platform)` — keeps hot days small
- Pre-aggregate to 1-day buckets in the mart

```sql
CREATE TABLE user_identity_bridge (
    unified_user_id    INTEGER NOT NULL,
    platform           TEXT    NOT NULL,            -- 'FB' | 'IG' | 'WA'
    platform_user_id   INTEGER NOT NULL,
    valid_from         TEXT    NOT NULL,
    valid_to           TEXT    NOT NULL DEFAULT '9999-12-31',
    PRIMARY KEY (platform, platform_user_id, valid_from)
) WITHOUT ROWID;

CREATE TABLE fct_user_event (
    event_date         TEXT    NOT NULL,
    event_ts           TEXT    NOT NULL,
    unified_user_id    INTEGER NOT NULL,
    platform           TEXT    NOT NULL,
    event_type         TEXT    NOT NULL,
    content_id         INTEGER,
    session_id         INTEGER,
    PRIMARY KEY (event_date, event_ts, unified_user_id, event_type)
) WITHOUT ROWID;
```

---

## Q3 — Design an event-driven data model for Meta's advertising auction system (real-time bid + historical).

### Grain
Two grain choices (this is the trap):
- **Auction events**: 1 row per auction event
- **Impressions**: 1 row per impression (the result of a winning auction)

### Dimensions
- `dim_advertiser` (SCD Type 1 on name, Type 2 on `industry`)
- `dim_ad_set` (SCD Type 2 — the killer dim, the *campaign* state changes)
- `dim_ad` (SCD Type 2 on creative, copy, format)
- `dim_user` (for targeting)

### Facts
- `fct_auction_event` — immutable, append-only
  - 1 row per auction (whether won or lost)
  - `bid_amount`, `won_flag`, `auction_ts`
  - **The history-of-bids question:** time-travel queries on this fact
- `fct_impression` — 1 row per impression
  - joined to `fct_auction_event` via `auction_id`
  - `revenue`, `spend`, `user_action`

### The killer: time-travel vs current-state
- `fct_auction_event` is immutable → time-travel is just "WHERE auction_ts <= T"
- `dim_ad_set` is SCD2 → point-in-time state is "JOIN fact to dim valid at auction_ts"
- The interviewer wants you to know which question each pattern answers

### Scale story
- 1B auctions/day, 1KB/row = 1TB/day raw
- Parquet + ZSTD → 100GB/day
- Real-time path: Kafka → Flink → 5-min aggregates
- Historical path: S3 → daily Spark batch → 1-hour aggregates

```sql
CREATE TABLE fct_auction_event (
    auction_ts    TEXT    NOT NULL,
    auction_id    INTEGER NOT NULL,
    ad_id         INTEGER NOT NULL,
    advertiser_id INTEGER NOT NULL,
    user_id       INTEGER,
    bid_amount    REAL    NOT NULL,
    won_flag      INTEGER NOT NULL,
    PRIMARY KEY (auction_ts, auction_id)
) WITHOUT ROWID;

CREATE TABLE dim_ad_set (
    ad_set_id        INTEGER PRIMARY KEY,
    advertiser_id    INTEGER NOT NULL,
    name             TEXT    NOT NULL,
    campaign_state   TEXT    NOT NULL,    -- 'active' | 'paused' | 'archived'
    budget_cents     INTEGER NOT NULL,
    valid_from       TEXT    NOT NULL,
    valid_to         TEXT    NOT NULL DEFAULT '9999-12-31',
    is_current       INTEGER NOT NULL DEFAULT 1
);
```

---

## Q4 — Design a data model for a ride-sharing app like Uber. Walk through partitioning at scale.

### Grain
Two facts:
- `fct_trip` — 1 row per trip (the trip is the unit of work)
- `fct_trip_event` — 1 row per trip event (request, match, pickup, dropoff, cancel)

### Dimensions
- `dim_rider` (SCD Type 1)
- `dim_driver` (SCD Type 2 on `vehicle_id`, `city_id`)
- `dim_city` (SCD Type 1)
- `dim_time`

### Partitioning
- Hot path: `fct_trip_event` partitioned by `event_date` (1 day per partition)
- Cold path: `fct_trip` partitioned by `trip_date` (1 month per partition)
- Sub-partition: by `city_id` within each date (so a single city's hot day doesn't blow the partition)

### Scale story
- 1B trips/day × 200 events/trip × 500B = 200B events/day
- Hot path: last 7 days on SSD, 5TB
- Cold path: S3 + Parquet, 200GB/day, $5/mo
- Pre-aggregate to 15-min buckets for the city-dashboard

```sql
CREATE TABLE fct_trip (
    trip_id        INTEGER PRIMARY KEY,
    rider_id       INTEGER NOT NULL,
    driver_id      INTEGER NOT NULL,
    city_id        INTEGER NOT NULL,
    request_ts     TEXT    NOT NULL,
    pickup_ts      TEXT,
    dropoff_ts     TEXT,
    status         TEXT    NOT NULL,        -- 'completed' | 'cancelled' | 'no_show'
    fare_cents     INTEGER NOT NULL
);

CREATE TABLE fct_trip_event (
    event_date   TEXT    NOT NULL,
    event_ts     TEXT    NOT NULL,
    trip_id      INTEGER NOT NULL,
    event_type   TEXT    NOT NULL,           -- 'requested' | 'matched' | 'pickup' | 'dropoff' | 'cancelled'
    city_id      INTEGER NOT NULL,
    lat          REAL,
    lon          REAL,
    PRIMARY KEY (event_date, event_ts, trip_id)
) WITHOUT ROWID;
```

---

## Q5 — An Instagram metric is dropping. Walk through your root-cause analysis, the data model, and the follow-up.

This is the *investigation* question, not a pure schema design. The interviewer is testing your structured-thinking under ambiguity.

### The 4-step framework

1. **Confirm the drop is real.** Is the metric definition changed? Is the population the same? (Compare last-7-day vs prior-7-day, segmented by `country` and `device_type` to localize the regression.)
2. **Decompose.** The metric is `n_likes / n_views`. Decompose numerator and denominator separately. Is the *engagement rate* dropping, or just the *view count*?
3. **Localize the segment.** Once you know numerator vs denominator, segment by the 5 dims: country, device, age cohort, content type, time-of-day. The drop is in 1-2 segments, not all.
4. **Hypothesize the cause.** Algorithm change? Bug? Seasonal? Test the hypothesis with a counterfactual: "would we have expected the drop if the algo didn't change?"

### The data model that supports the investigation

You need a *per-metric, per-time-bucket, per-segment* fact table:
- `fct_metric_value(metric_id, time_bucket, segment_id, value, sample_size)`

And the segment dim is a JSON blob (because the segments change every investigation):
- `dim_segment(segment_id, definition_json)`

This is the right answer because the *same* fact table supports any future metric drop. You don't build a new schema every time a metric drops.

```sql
CREATE TABLE fct_metric_value (
    metric_id      INTEGER NOT NULL,
    time_bucket    TEXT    NOT NULL,    -- YYYY-MM-DDTHH:00:00
    segment_id     INTEGER NOT NULL,
    value          REAL    NOT NULL,
    sample_size    INTEGER NOT NULL,
    PRIMARY KEY (metric_id, time_bucket, segment_id)
) WITHOUT ROWID;

CREATE TABLE dim_metric (
    metric_id   INTEGER PRIMARY KEY,
    name        TEXT    NOT NULL,
    definition  TEXT    NOT NULL,    -- the formula
    owner_team  TEXT    NOT NULL
);
```

---

## What's in the SQLite file

All 5 schemas (Reels, cross-platform, Ads Auction, ride-share, metric-investigation) are in
`code/meta_onsite_schemas.sql` and executable against SQLite. The
3 Jupyter notebooks load them and run a sample query each.
