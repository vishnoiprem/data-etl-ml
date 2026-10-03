# Design Tables for Event-Driven Metrics (Consumer App Event Analytics)

## 1. Simple way to think

- A consumer app (think Instagram, TikTok, Spotify) generates billions of tiny "events" every day: app opened, button tapped, video played for 3 seconds, scroll, etc.
- Each event is a single row in a giant log: who did what, when, and any extra context. That's it.
- The naive way is to dump everything into one giant table. It works for 1 million events/day. It dies at 1 billion because the table becomes unqueryable.
- The first trick is to **separate raw events from rolled-up metrics**. Raw events are append-only, immutable, write-heavy. Metrics are aggregated, narrow, read-heavy. Two different shapes, two different tables.
- The second trick is **wide vs. long format**. Wide = one column per event attribute (good for analysts in BI tools). Long = one row per attribute (good for log search and ML feature extraction). You usually keep both.
- The third trick is **high cardinality**. A "user_id" column has billions of distinct values. A "country" column has ~250. Most databases choke on high-cardinality group-bys. Pre-aggregate the high-cardinality stuff.
- The fourth trick is **event taxonomy**. Without a strict schema ("screen_view", "button_click", "video_play"), you end up with 200 variants of "click" and nobody can analyze anything. A **tracking plan** is non-negotiable.
- A concrete example: Instagram. Events = `app_open`, `feed_view`, `like`, `comment`, `share`, `profile_visit`, `story_view`, `reel_play`. The metric "DAU" comes from `app_open` deduplicated by user per day.

## 2. Interview write-up (how to solve it)

**Requirements clarification.** "Before I start — what scale? Let me assume 50M DAU, each generating ~500 events/day = 25B events/day at peak. What's the latency target for metrics — minutes or hours? Are we optimizing for product analytics (DAU, retention), or also ML feature pipelines?"

**Event taxonomy (tracking plan).**

```
client_event_id     UUID (dedup key)
event_name          STRING   -- 'screen_view', 'button_click', 'video_play'
event_timestamp     TIMESTAMPTZ
user_id             BIGINT
session_id          UUID
device_id           STRING
platform            STRING   -- 'ios', 'android', 'web'
app_version         STRING
country_code        CHAR(2)
properties          JSON     -- event-specific, flexible
user_properties     JSON     -- set-once user attributes
```

**Layered schema.**

```
[Raw events: long format, append-only]
    │
    v
[Typed events: wide format, validated]
    │
    v
[Session-level aggregates]
    │
    v
[Daily user-level metrics]
    │
    v
[Funnel / cohort tables]
```

**Table designs.**

```sql
-- 1. Raw events (append-only, partitioned by day)
CREATE TABLE events_raw (
  event_id          UUID,
  event_name        VARCHAR(64),
  event_timestamp   TIMESTAMPTZ,
  user_id           BIGINT,
  session_id        UUID,
  device_id         VARCHAR(64),
  platform          VARCHAR(16),
  app_version       VARCHAR(16),
  country_code      CHAR(2),
  properties        JSONB,
  ingested_at       TIMESTAMPTZ DEFAULT now()
) PARTITION BY RANGE (event_timestamp);

-- 2. Typed events (wide, business-friendly)
CREATE TABLE events_typed_screen_view (
  event_id          UUID PRIMARY KEY,
  user_id           BIGINT,
  session_id        UUID,
  screen_name       VARCHAR(64),
  referrer_screen   VARCHAR(64),
  event_timestamp   TIMESTAMPTZ
) PARTITION BY RANGE (event_timestamp);

CREATE TABLE events_typed_video_play (
  event_id          UUID PRIMARY KEY,
  user_id           BIGINT,
  video_id          BIGINT,
  duration_played_s INT,
  completion_pct    DECIMAL(5,2),
  sound_on          BOOLEAN,
  event_timestamp   TIMESTAMPTZ
) PARTITION BY RANGE (event_timestamp);

-- 3. Session aggregates
CREATE TABLE sessions (
  session_id        UUID PRIMARY KEY,
  user_id           BIGINT,
  started_at        TIMESTAMPTZ,
  ended_at          TIMESTAMPTZ,
  event_count       INT,
  screens_viewed    INT,
  platform          VARCHAR(16),
  country_code      CHAR(2)
);

-- 4. Daily user metrics (the "metric mart")
CREATE TABLE user_daily_metrics (
  user_id           BIGINT,
  date_key          INT,        -- YYYYMMDD
  sessions          INT,
  total_events      INT,
  screens_viewed    INT,
  videos_played     INT,
  likes_given       INT,
  -- ...
  PRIMARY KEY (user_id, date_key)
) PARTITION BY RANGE (date_key);
```

**Indexing strategy.** On `events_raw`: `(user_id, event_timestamp DESC)` and `(event_name, event_timestamp DESC)`. Most analytics queries filter on one or both.

**Handling high cardinality.** Never `GROUP BY user_id` at the event level — that's a billion-row scan. Pre-aggregate to `user_daily_metrics` first. For drill-down to specific users, use a separate user-scoped table.

**Failure modes.** Schema drift: events with new properties break pipelines. Mitigation: schema registry, versioned tracking plan, PII tokenization. Late-arriving events: 7-day re-openable partitions. Duplicate events: dedup on `event_id` during ingest. Bot traffic: filter by `user_agent` and behavioral signals before metrics.

## 3. Best optimized solution

**Refined architecture.**

```
[Mobile/Web SDK] ──> Kafka (events.v1) ──> Flink
                                          ├── Dedup on event_id
                                          ├── Bot filtering
                                          ├── PII tokenization
                                          └── Schema validation
                                              │
                                              v
                                         S3 / Iceberg (raw, partitioned daily)
                                              │
                                       Spark/Airflow
                                              │
                                  ┌───────────┼─────────────┐
                                  v           v             v
                          Typed events    Sessions    user_daily_metrics
                                  │           │             │
                                  └───────────┴──────┬──────┘
                                                   v
                                            Snowflake / BigQuery
                                                   │
                                       ┌───────────┼───────────┐
                                       v           v           v
                                  Dashboards   ML features  Reverse ETL
```

**Storage format.** Parquet + ZSTD on Iceberg for raw. Parquet + Snappy on Snowflake for typed. JSONB only inside properties — never as the primary schema.

**Partitioning/clustering.**
- `events_raw`: partition by `event_timestamp` (daily), Z-order on `(user_id, event_name)` for common analytics queries.
- `user_daily_metrics`: partition by `date_key` (monthly), cluster on `user_id`.
- `sessions`: cluster on `(user_id, started_at)`.

**High-cardinality strategy.** Build a **derived fact table** for every common metric pattern. Don't `SELECT COUNT(DISTINCT user_id)` from raw — ever. Pre-compute DAU, WAU, MAU into materialized tables refreshed hourly. For per-user analysis, page through user_daily_metrics, not raw.

**Tracking plan governance.** Every event goes through a review process. The plan is a versioned JSON file in a repo. Schema changes trigger a CI check. New event names auto-create typed tables via a code generator.

**Cost considerations.** Raw events are 80% of storage cost. Apply **lifecycle policies**: hot in standard S3 for 30 days, IA tier for 90 days, Glacier after that. Compress aggressively. Drop `properties` columns after 30 days into a separate cold table.

**Monitoring & SLOs.**
- **Completeness**: events received vs. SDK-emitted within 0.5% (spot-check via control events).
- **Freshness**: p99 lag from event_timestamp to warehouse < 10 min.
- **Schema quality**: 0 unexpected event names, < 1% null in required fields.
- **Bot rate**: < 5% of events flagged as bot.

**Why it's optimal.**
- Layered tables (raw → typed → metrics) let you answer "what happened in detail" *and* "what's the headline number" without one path killing the other.
- Pre-aggregation makes high-cardinality analytics tractable — a DAU query is now a single COUNT on a small table.
- Schema-on-read for properties + schema-on-write for the event envelope = flexibility without chaos.
- The tracking plan as code makes the system testable, reviewable, and self-documenting.

**What the interviewer is really testing:** They want to see you understand that event analytics is fundamentally different from transactional OLTP — it's a *log* with downstream derivations. They're testing: high-cardinality awareness, the raw vs. metrics split, tracking plan discipline, and that you pre-aggregate instead of letting analysts `SELECT DISTINCT` against a billion-row table. Meta hires people who can build this at scale without blowing the budget.
