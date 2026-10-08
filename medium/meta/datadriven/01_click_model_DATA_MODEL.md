# Data Model — The Gaps Between Clicks

> **Note on attribution:** The problem statement as quoted in `WORKING.md` is from Google's interview archive ("The Gaps Between Clicks"). It is filed under `medium/meta/datadriven/` because the modeling challenge — visit-level + daily-rollup analysis, anonymous-to-signed-in stitching, and shared-device ownership credit — is the same class of problem Meta asks on data-engineering and analytics-infra interviews for surfaces like FB/IG/WhatsApp. SQL examples below use Presto/Hive-style syntax (Meta's internal stack on top of Hive + Pinot/Presto + Spark).

A complete dimensional + fact model for clickstream visit + daily engagement, with identity stitching and shared-device ownership credit.

---

## Entity-Relationship Overview

```
                  +-----------------+
                  |     dim_user    |
                  +-----------------+
                           |
                           | user_id
                           v
  +-----------+    +-----------------+    +-----------------------+
  | dim_device|--->|    fact_event   |--->|    fact_auth_event    |
  +-----------+    | (raw clickstream)|    |  (signin / signout)   |
                   +-----------------+    +-----------------------+
                           |
            +--------------+----------------+
            |                               |
            v                               v
  +-------------------+    +--------------------------------+
  |     fact_visit   <------|      dim_device_ownership     |
  |   (sessionized)    |    |   (who held device & when)   |
  +-------------------+    +--------------------------------+
            |
            v
  +---------------------------+
  |   agg_daily_page_device   |
  |      (daily rollup)       |
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

---

## OLTP Landing Layer (Above the OLAP Fact Tables)

The OLAP tables above describe the **analyst-facing** side. Below is the **OLTP layer** that catches live clicks, performs point lookups, and feeds the OLAP layer via CDC / streaming.

### Architecture

```
[Mobile App / Web]
     │  (HTTPS INSERT, < 50 ms SLA)
     ▼
+--------------------------------------------+
|              OLTP LAYER                    |
|                                            |
|   Load Balancer                            |
|      │                                     |
|      ├──→  oltp_events         (HBase / Cassandra)
|      ├──→  oltp_auth           (MySQL)      |
|      ├──→  oltp_users          (MySQL)      |
|      ├──→  oltp_devices        (HBase)      |
|      └──→  oltp_sessions       (Redis)      |
|                                            |
+--------------------------------------------┘
     │              │              │
     │ Kafka CDC    │ binlog CDC   │  (Debezium / Maxwell)
     ▼              ▼              ▼
+--------------------------------------------+
|          STREAM + BATCH ETL                |
|                                            |
|   Kafka topics → Flink / Spark Streaming   |
|         │                                  |
|         ▼                                  |
|   Parquet landing on S3/HDFS               |
|         │                                  |
|         ▼                                  |
|   Tables 3-7 above (OLAP)                  |
+--------------------------------------------┘
```

### Why two stores?

| Concern | OLTP store chosen | Why |
|---|---|---|
| Billions of writes/day from clicks | **HBase / Cassandra** | Wide-column, row-key sharded by `(device_id, ts)`, append-only — survives write spikes; no contention on the row key path |
| Auth + user metadata (point lookups, ACID) | **MySQL** | ACID for `users`, `auth_events`; replication for read scaling |
| Hot session state (TTL: 30 min inactivity) | **Redis** | In-memory, automatic expiration, lookup on every click to test if visit should continue |
| Devices (write-once, read-many) | **HBase** | One row per device; mutable attributes (model, OS) are write-light |

---

### 1. `oltp_events` (Click Landing — OLTP)

**Store:** HBase / Cassandra
**Grain:** one row per click; row key = `(device_id, event_ts, event_id)` for locality + append-only writes.
**SLA:** ingest < 10 ms p99, return 200 OK to client immediately.

```sql
-- HBase schema sketch
CREATE TABLE oltp_events (
  row_key   VARBINARY,              -- hash(device_id) | reverse(event_ts) | event_id
  cf:meta   -- device_id, user_id (NULL if anonymous), page, event_type, app_version
  cf:auth   -- session_token_hash
  cf:dt     -- DATE(event_ts) for partition pruning
);
-- TTL = 30 days (then ETL'd to S3 / Parquet)
```

| Field | Source | Notes |
|---|---|---|
| `device_id` | Client SDK | Hardware-derived IDFA / cookie |
| `user_id` | Server-side | NULL until signin → resolved later |
| `event_ts` | Client | Wall-clock; reconcile via `received_ts` |
| `page` | Client | URL or screen name |
| `session_token` | Server | SHA-256 of session cookie → lookup against Redis `oltp_sessions` |

**Why HBase, not MySQL?**
- 100k+ writes/sec sustained per cluster; MySQL row-locks on hot partitions become a bottleneck.
- Append-only — no UPDATE traffic; tall-narrow columns fit HBase's storage model.
- Auto-sharding by row key (`device_id`) keeps a single device's events on the same region server (good for sessionization in the OLAP layer).

---

### 2. `oltp_auth` (Signin / Signout — OLTP)

**Store:** MySQL (ACID, transactional signin flow)
**Grain:** one row per auth event.

```sql
CREATE TABLE oltp_auth (
  auth_id        BIGINT       PRIMARY KEY AUTO_INCREMENT,
  device_id      BIGINT       NOT NULL,
  user_id        BIGINT       NOT NULL,
  auth_ts        TIMESTAMP(3) NOT NULL,
  auth_type      ENUM('signin','signout') NOT NULL,
  session_token  CHAR(64)     NOT NULL,            -- SHA-256 hex
  ip_address     VARBINARY(16),
  user_agent     STRING,
  INDEX idx_device_ts (device_id, auth_ts DESC)
);
```

**Workflow on sign-in:**
1. App calls `POST /signin` (user + password / OAuth)
2. Server creates row in `oltp_auth` (atomic with `oltp_users.last_login_ts`)
3. Server creates Redis key `oltp_sessions:<token>` with TTL = 30 min (refreshed on activity)
4. Server returns session token to app
5. CDC → Kafka topic `cdc.oltp_auth` → downstream Lambda/Flink → `fact_auth_event` (OLAP)

---

### 3. `oltp_users` (User Master)

**Store:** MySQL — normalized, ACID.

```sql
CREATE TABLE oltp_users (
  user_id          BIGINT       PRIMARY KEY,
  email            STRING       UNIQUE,
  phone            STRING,
  hashed_password  STRING,
  registration_ts  TIMESTAMP   NOT NULL,
  last_login_ts    TIMESTAMP,
  account_status   ENUM('active','suspended','deleted') DEFAULT 'active',
  updated_ts       TIMESTAMP   NOT NULL
);
```

**Avoided in OLTP:**
- Aggregations (those live in OLAP)
- Free-text profile blobs
- Anything analysts want — kept lean for fast point reads

---

### 4. `oltp_devices` (Device Registry)

**Store:** HBase — write-once / read-many.

```sql
-- HBase row per device; never updated frequently
Row key = hash(device_id)
cf:profile: device_type, os, os_version, app_version, manufacturer
cf:first:  first_seen_ts, first_user_id
```

**Use case:** "This device hit us for the first time" — creates a row; subsequent reads return cached attributes.

---

### 5. `oltp_sessions` (Hot Session State in Redis)

**Store:** Redis cluster, with TTL = 30 min (sliding).

```sql
-- Key:   session:<token>
-- Value: hash { device_id, user_id, last_event_ts, visit_id }
-- TTL:   30 min, refreshed on every click
EXPIRE session:<token> 1800
```

**Why Redis (not HBase/MySQL):**
- O(1) point lookup on every click ("is this the same visit?")
- Atomic INCR + EXPIRE for "30-min no gap" rule — no need to scan `fact_event`
- Auto-evicts dead sessions for free

**Lookup flow per click:**
```
1. App sends click + session_token
2. Backend GET session:<token> from Redis
3. If exists → reuse visit_id; INCR event_count; EXPIRE
4. If TTL expired or missing → start NEW visit_id, write to oltp_events (HBase)
5. Write-through to oltp_events ensures durability even if Redis evicts
```

---

### CDC / Streaming Bridge (OLTP → OLAP)

| Source | CDC tool | Kafka topic | Downstream consumer | Target OLAP table |
|---|---|---|---|---|
| `oltp_events` (HBase) | HBase replication or Kafka producer | `ods.clicks` | Spark Streaming / Flink | `fact_event` |
| `oltp_auth` (MySQL) | Debezium / Maxwell | `cdc.oltp_auth` | Flink | `fact_auth_event` |
| `oltp_users` (MySQL) | Debezium | `cdc.oltp_users` | Spark batch | `dim_user` |
| `oltp_devices` (HBase) | HBase replication | `ods.devices` | Spark batch | `dim_device` |

**Idempotency:** every Kafka message carries the original OLTP `event_id` / `auth_id`; the OLAP loader uses `INSERT … ON DUPLICATE KEY UPDATE` or `MERGE INTO` to avoid duplicates during re-delivery.

**Schema evolution:** use **Avro / Protobuf** for Kafka payload (Confluent Schema Registry, or Meta's internal equivalent) — adds columns without breaking downstream consumers.

---

### Latency SLA Table

| Surface | SLA | Layer |
|---|---|---|
| App → server click ingest | < 50 ms p99 | OLTP (HBase write) |
| Sign-in → session created | < 200 ms p99 | OLTP (MySQL + Redis) |
| Session continuity (same visit) | < 10 ms p99 | OLTP (Redis lookup) |
| Click visible in `fact_event` (OLAP) | < 5 min | Kafka → Spark Streaming |
| `fact_visit` materialized | < 1 hour | Spark batch |
| `agg_daily_page_device` latest | < 24 hours | Nightly rollup |
| Real-time dashboard tile ("active users now") | < 1 sec | Streaming OLAP (Pinot / Druid) |

---

### What Lives Where — Final Map

| Question | System | Table |
|---|---|---|
| "Accept this click right now" | **OLTP** | `oltp_events` (HBase) |
| "Is this the same visit?" | **OLTP** | `oltp_sessions` (Redis) |
| "User signed in on this device" | **OLTP** | `oltp_auth` (MySQL) |
| "User profile lookup" | **OLTP** | `oltp_users` (MySQL) |
| "Daily engagement by page & device" | **OLAP** | `agg_daily_page_device` |
| "Average session duration last week" | **OLAP** | `fact_visit` |
| "Drop-off funnel on page X" | **OLAP** | `fact_visit` + `fact_event` drill |
| "Who held this device at 10am?" | **OLAP** | `dim_device_ownership` |
| "Active users right now" | **Real-time OLAP** | Pinot/Druid stream from Kafka |

---

### Easy-to-Remove Pieces (OLTP additions)

| Component | Drop when… |
|---|---|
| Redis `oltp_sessions` | Sessions are computed purely in OLAP batch (acceptable for non-realtime use cases) |
| Separate `oltp_devices` table | Devices fit naturally inside `oltp_events` payload if app already has them |
| CDC layer (Kafka → Debezium) | Small scale — run a nightly `mysqldump` → Hive instead |
| HBase for `oltp_events` | Low write volume → MySQL with shard-by-`device_id` partitions works |
| Streaming OLAP / Pinot | Batch-only analytics acceptable; no real-time dashboards |

---

## "Which System Should I Design?" — Decision Tree for Click Problems

When an interviewer says *"design a system"* about clickstream, this is the framework to choose **what to actually build**. Read their question; pick the leaf.

### Quick Listening Test

Scan the prompt for these keywords → jump to that branch:

| Keywords in the prompt | Branch | Skip |
|---|---|---|
| "API", "request", "live", "< 100ms", "sub-second" | **OLTP path** | OLAP rollups, Parquet |
| "real-time dashboard", "active users now", "right now", "live tile" | **Streaming OLAP** | Nightly rollups, batch sessionization |
| "analytics", "roll-up", "daily", "weekly", "report", "analyst" | **Batch OLAP** | Redis session state, CDC |
| "schema", "fact table", "dimension", "warehouse", "how would you model" | **OLAP model** | HBase row keys, OLTP replication |
| "pipeline", "ETL", "ingestion", "Kinesis/Kafka", "how do events arrive" | **OLTP + Streaming bridge** | Fact tables themselves |
| "scale to N billion events/day" | **Architecture + numbers** | Full design, focused on bottlenecks |
| Nothing specific | **End-to-end default** (this doc) | — |

---

### Decision Tree

```
                       "Design a system"
                              │
              ┌───────────────┼───────────────┐
              │               │               │
        "real-time?"    "sub-second?"    "sub-100ms API?"
              │               │               │
              ▼               ▼               ▼
      Streaming OLAP    OLTP + Streaming    OLTP only
      (Pinot/Druid)       bridge          
              │               │
              │               ▼
              │       Full End-to-End
              │       (this doc, all sections)
              │
              └─── "daily/weekly analytics only?"
                          │
                          ▼
                    Batch OLAP only
                    (fact_event, fact_visit, rollups)
```

---

### Branch 1: OLTP Only — "How would you ingest clicks?"

**When to use:** interviewer asks only about accepting events; no analytics questions.

**Stack:**
- Load balancer → API server → **HBase** (write) + **Redis** (session state) + **MySQL** (auth/users)

**Key answers:**
- HBase row key = `(device_id, reverse(event_ts))` for write locality
- Redis holds `visit_id` with 30-min sliding TTL
- CDC from MySQL → Kafka for downstream

**Skip:** `fact_visit`, sessionization job, Presto, Parquet.

---

### Branch 2: Batch OLAP Only — "How would you model analyst queries?"

**When to use:** interviewer wants the warehouse schema only; no live traffic.

**Stack:**
- Parquet on S3/HDFS → **Spark / Hive / Presto**

**Key answers:**
- Partition `fact_event` by `DATE(event_ts)`, cluster by `device_id`
- Sessionization in Spark (Step A in WORKING.md)
- Identity stitching in Spark (Step B)
- Ownership windows derived from `fact_auth_event`
- Pre-aggregate `agg_daily_page_device` nightly

**Skip:** HBase, Redis, CDC, MySQL.

---

### Branch 3: Streaming OLAP — "Show active users right now"

**When to use:** interviewer specifies sub-second freshness for dashboards.

**Stack:**
- Kafka clicks → **Flink / Spark Streaming** → **Pinot / Druid / Scuba realtime**

**Key answers:**
- Sliding window of 30 min → emit current `visit_id` events
- Late-arriving auth → stateful re-key in Flink
- Stream aggregated K-V (visit_id → visit_metrics) into Pinot
- Dashboard queries push down to Pinot (sub-second)

**Trade-off:** harder to recompute history; **keep batch pipeline in parallel** as the source of truth.

---

### Branch 4: Full End-to-End — Default Safe Answer

**When to use:** prompt mentions both live and analytical use cases; or no specifics.

**Stack:** OLTP (HBase/MySQL/Redis) + Kafka + Spark Streaming + Spark Batch + Presto.

**Order to present:**
1. **OLTP layer** — accept clicks, point lookups, hot session state.
2. **CDC bridge** — Kafka topics for events, auth, users, devices.
3. **OLAP batch** — `fact_event`, `fact_visit`, `agg_daily_page_device`.
4. **(Optional) streaming OLAP** — only if real-time dashboards mentioned.

This is the layout of this whole document.

---

### Branch 5: Schema Only — "How would you model this?"

**When to use:** interviewer says "just give me the schema" or "what tables?"

**Answer:** jump to the [OLAP section](#) and present 7 tables in order:
1. `dim_user`
2. `dim_device`
3. `fact_event`
4. `fact_auth_event`
5. `dim_device_ownership`
6. `fact_visit`
7. `agg_daily_page_device`

Mention grain and one non-obvious trick per table (30-min gap, identity stitching, ownership window, etc.).

---

### Branch 6: Numbers / Scale Round — "How big?"

**When to use:** interviewer presses on scale numbers, cost, capacity.

**Key numbers to know:**

| Metric | Value |
|---|---|
| Clicks/day (large consumer product) | 1-50 billion |
| Peak writes/sec | 500k - 5M |
| Avg session events | 10-50 |
| Visits/day | 100M - 5B |
| Auth events/day | 100M - 10B (heavy traffic sites) |
| Storage of raw Parquet / day | ~1-50 TB compressed |
| Storage of `fact_visit` / day | ~10-100 GB |
| Storage of `agg_daily_page_device` / day | ~1-10 GB |
| Presto query latency (rollup table, day scan) | 1-10 sec |
| Spark sessionization job (1-day data) | 10-60 min on 100-1000 node cluster |
| HBase cluster size for 1M writes/sec | ~50-200 region servers |

---

### How to Start the Interview (90 seconds)

> "The click problem has **two layers**. Let me ask: is the focus on the live write path (OLTP), the analyst query path (OLAP), or end-to-end?"

Then either:
- **OLTP focus:** draw `App → LB → API → HBase/Redis/MySQL`; explain row keys + session state.
- **OLAP focus:** draw `Kafka → Parquet → fact_* → agg_*`; explain sessionization + stitching.
- **End-to-end:** draw both, in that order, OLTP first (where data lands), then OLAP (where it gets analyzed).

The decision tree above is your escape valve when the prompt is ambiguous.

---

### Anti-Patterns to Avoid in a Click-System Design

| Anti-pattern | Why it's wrong |
|---|---|
| Putting `fact_event` in MySQL | Locks + cost at billions/day |
| Running nightly aggregations in the OLTP path | Blocks writes; creates stale data |
| Sessionizing clicks in MySQL with `LAG()` over a billion rows | Single query kills the DB |
| Treating `user_id` as non-NULL on first click | Breaks anonymous → signed-in stitching |
| Ignoring ownership windows on shared devices | Misattributes visits; fails the literal problem statement |
| Designing only one layer | Missing the "visit + daily rollup" requirement |
| Confusing "session" (technical) with "visit" (business) | 30-min gap is technical; "visit credit" needs ownership join |
