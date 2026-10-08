# Working Comparison: Apache Pinot vs Apache Druid vs ClickHouse

> A working article comparing three real-time / OLAP columnar engines: their architectures, working models, costs, and when each is the right pick.

---

## TL;DR

| Question | Pinot | Druid | ClickHouse |
|---|---|---|---|
| Best for | User-facing analytical dashboards (sub-second, high concurrency) | Time-series + event analytics (sub-second, high ingestion) | General OLAP, log/event analytics, broadest use case |
| Architecture | Cluster of Helix-managed nodes (Controller / Broker / Server / Minion) | Cluster of Coordinator / Overlord / Historical / Middle Manager / Broker / Router | Single binary, sharded ReplicatedMergeTree, async replication |
| Data model | Star schema, pre-built star-tree indexes per table | Druid-native (segments, rollup at ingestion) | Wide table, no enforced schema, MergeTree families |
| Ingestion | Batch + streaming (Kafka, S3, HDFS, Kinesis) | Streaming-first (Kafka, Kinesis), micro-batches | Streaming + bulk (`INSERT`, Kafka engine, materialized views) |
| Query language | SQL (compatible with ANSI subset) | SQL (Druid SQL) | SQL (most complete ANSI / TPC-H dialect of the three) |
| Latency | <1 sec p99 typical | <1 sec p99 typical | <1 sec typical; second-best under high concurrency |
| Sweet spot | 10⁴–10⁶ events/sec with millisecond latency | 10⁵–10⁶ events/sec with rollups / aggregations | 10⁶+ events/sec, broad SQL access |

**One sentence:** **Pinot** wins dashboards, **Druid** wins time-series / rollups, **ClickHouse** wins general-purpose OLAP.

---

## 1. How Each System Architecturally Works

### 1.1 Apache Pinot — LinkedIn origin, dashboard-first

```
                       ┌──────────────────────────────────────┐
                       │              CONTROLLER             │
                       │     (cluster coordinator, Helix)     │
                       │        manages configs & segments   │
                       └───────┬──────────────────┬───────────┘
                               │                  │
                               │ 1. plan / route  │ 1. plan / route
                               ▼                  ▼
                  ┌────────────────────┐  ┌──────────────────────┐
                  │      BROKERS       │  │       SERVERS        │
                  │     (stateless)    │  │      (stateful)      │
                  │  scatter-gather    │  │  hold segments       │
                  │  query planning    │  │  + indexes           │
                  └─────────▲──────────┘  └─────────▲────────────┘
                            │                     │
                  feedback / metrics             │
                            │                     │
                  ┌─────────┴──────────┐  ┌───────┴────────────┐
                  │       MINIONS      │  │      INGESTION     │
                  │   batch tasks      │  │   Kafka, S3,       │
                  │  compaction        │  │   HDFS, GCS        │
                  └────────────────────┘  └────────────────────┘
```

| Component | Role |
|---|---|
| **Controller** | Zookeeper-less (Helix) cluster coordinator; manages table configs, segment assignment, schema evolution |
| **Broker** | Stateless query routers; scatter-gather, query planning |
| **Server** | Stateful, holds segments + indexes (forward, sorted, range, bitmap, JSON, star-tree) in memory or on disk |
| **Minion** | Background tasks: compaction, conversion, purge |
| **Ingestion** | Real-time (Kafka) and batch (HDFS / S3 / GCS) into segments |

**Key idea:** Query result planning is done in the broker, segments are queried in parallel on servers, results merged in broker. Uses **multi-dimensional indexes** (star-tree) — answers `GROUP BY country, page` with one segment lookup.

### 1.2 Apache Druid — Imply / Kafka origin, time-series first

```
        ┌──────────────────────┐                  ┌──────────────────────┐
        │     COORDINATOR      │                  │       OVERLORD       │
        │ (segments,           │                  │  (task mgmt /        │
        │  load balance,       │                  │   ingestion)         │
        │  deep-storage)       │                  │                      │
        └──────────┬───────────┘                  └──────────┬───────────┘
                   │                                       │
                   ▼ schedules segments                    ▼ assigns tasks
        ┌──────────────────────┐                  ┌──────────────────────┐
        │     HISTORICALS      │                  │   MIDDLE MANAGERS    │
        │  (cold segments,     │                  │ (real-time ingest,   │
        │   deep storage,     │                  │  in-memory + persist)│
        │   S3/HDFS)           │                  │                      │
        └─────────▲────────────┘                  └─────────▲────────────┘
                  │                                       │
                  └─────────┬─────────────────────────────┘
                            ▼ served from
                ┌──────────────────────┐
                │     BROKER          │  (stateless query)
                │     ROUTER          │  (stateless API)
                └──────────────────────┘
```

| Component | Role |
|---|---|
| **Coordinator** | Segment lifecycle, balancing, loading from deep storage |
| **Overlord** | Ingests (real-time + batch) via middle managers / peons |
| **Historical** | Loads immutable segments from deep storage (S3, HDFS, GCS) |
| **Middle Manager** | Spawns peons for real-time ingestion; writes to "hot" mem segments |
| **Broker** | Scatter-gather query router |
| **Router** | Routes external API requests to brokers |
| **Deep storage** | Single source of truth (S3/HDFS) — segments, not servers |

**Key idea:** **Rollup at ingestion** — Druid aggressively pre-aggregates events into segments. A 1B-event stream becomes a 100k-row segment keyed by time + chosen dimensions. Trades late-binding flexibility for query speed.

### 1.3 ClickHouse — Yandex origin, single-binary columnar

```
                 ┌──────────────────────────────────────┐
                 │       clickhouse-server (C++)       │
                 │   - ZooKeeper (replicated cluster)  │
                 │   - ClickHouse Keeper (replacement) │
                 │   - local filesystem (MergeTree)    │
                 └──────────────────────────────────────┘
                              ▲    ▲    ▲
                              │    │    │
                  Shard 1     │    │    │    Shard N
                  ┌────────────┐  │  ┌────────────┐
                  │   Replica 1│◄─┼─►│  Replica N │
                  │  (Repli-   │  │  │            │
                  │  cated-    │  │  │            │
                  │  MergeTree)│  │  │            │
                  └────────────┘  │  └────────────┘
```

| Component | Role |
|---|---|
| **Server** | Single binary; handles everything (ingest + query + storage) |
| **MergeTree family** | Engine per table: `MergeTree`, `ReplacingMergeTree`, `AggregatingMergeTree`, `SummingMergeTree`, `Log`, `Kafka`, `MaterializedView` |
| **Sharding** | Distributed across shards via `Distributed` engine; replicated via `ReplicatedMergeTree` (uses ZK / ClickHouse Keeper) |
| **Coordination** | ZooKeeper or ClickHouse Keeper (ZooKeeper replacement, GA 2024) |

**Key idea:** **Vectorized query execution + columnar compression**. No master node for queries — any node can answer. Shards are independent; replication is async per-part; no "ingestion tier" / "query tier" separation.

---

## 2. The Working Model — How a Query Actually Runs

### 2.1 Same Query, Three Engines

```sql
SELECT country, COUNT(*) AS visits, AVG(duration_sec) AS avg_dur
FROM fact_visit
WHERE start_ts >= '2026-10-01' AND start_ts < '2026-10-02'
GROUP BY country
ORDER BY visits DESC
LIMIT 20;
```

| Step | Pinot | Druid | ClickHouse |
|---|---|---|---|
| 1. Receive query | API endpoint → Controller validates | Router → Broker | HTTP → any replica |
| 2. Plan | Broker → routed to servers holding segments from `2026-10-01` | Broker → identifies historicals for the time range | Distribute to all shards, run in parallel |
| 3. Filter | Star-tree index prunes segments; sorted index on `start_ts` does range scan | Rollup segment already has time-bucketed row; bitmap filter on `country` | `WHERE` pushes into `primary key` (typically `start_ts`); runs in vectorized blocks |
| 4. Aggregate | Distributed aggregation across segments, pre-built `country` rollup if star-tree | Single segment scan + Druid's bitmap aggregator | `count()` + `avg()` are vectorized state funcs over column slices |
| 5. Merge | Broker merges partial results | Broker merges partial results | Distribute engine merges shards; final `ORDER BY` + `LIMIT 20` |
| 6. Return | Sub-second | Sub-second | Sub-second, often faster on raw scans |

### 2.2 Index Strategies

| Index | Pinot | Druid | ClickHouse |
|---|---|---|---|
| Sorted range | ✓ (per column) | ✓ (time + rollup dimensions) | ✓ (primary key, like `start_ts`) |
| Bitmap | ✓ (Bloom + Roaring) | ✓ (built-in for low-cardinality columns) | ✓ (skip indexes, e.g., `minmax`, `set`) |
| Star-tree | ✓ (pre-aggregated cubes) | ✓ (rollup segments are star-tree-like) | ✗ (use materialized views for cubes) |
| JSON | ✓ (built-in) | ✗ (requires flatten) | ✓ (`Json` data type + skip indexes) |
| HNSW / vector | ✓ (since 1.0) | ✗ | Limited; largely OLAP, not ANN |
| Text / full-text search | ✓ (native) | ✓ (search spec) | Limited; external (e.g., Tantivy) integrations |

### 2.3 Ingestion Working Models

| Phase | Pinot | Druid | ClickHouse |
|---|---|---|---|
| Streaming (Kafka) | Stream → consuming segment → off-heap buffer → flush to disk segment → commit | Stream → middle manager → peon in-memory buffer → persist (deep storage) | Kafka engine → materialized view → MergeTree; or external pipeline → `INSERT` |
| Batch (files) | Spark / Hadoop / S3 jobs build segments | Hadoop / Spark / native ingestion tasks | `INSERT INTO ... SELECT` from `s3` table function; or `clickhouse-client --query` |
| Compaction | Minion-based | Auto (Coordinators rebalance) | `OPTIMIZE ... FINAL` (manual); background merges |
| Rollup (lossy aggregation at ingest) | Optional via upsert + star-tree | First-class feature (default) | Optional via `AggregatingMergeTree` |

---

## 3. Cost Comparison (Same Load)

Reference workload:
- 5 billion events / day
- 30 days hot retention
- 100 active dashboards, avg 50 concurrent users
- 95% of queries < 1 sec p99
- Cluster in AWS us-east-1 (on-demand, no reserved)

> Costs are **indicative**, derived from typical published and community numbers for ~2023-2025 deployments. Always validate with your own benchmark.

### 3.1 Hardware Footprint

| Resource | Pinot | Druid | ClickHouse |
|---|---|---|---|
| Nodes (typical) | 30-60 (broker + server + minion, mixed sizes) | 25-50 (overlord, coordinator, historical, middle-manager, router) | 10-25 (single binary, fewer nodes thanks to per-shard compression) |
| Per-node size | m6i.4xlarge (16 vCPU, 64 GiB) | m6i.4xlarge (16 vCPU, 64 GiB) | m6i.2xlarge (8 vCPU, 32 GiB) — smaller, fewer |
| Storage per node | 1-2 TB NVMe | 1-3 TB NVMe (cold offloaded to S3) | 1-4 TB NVMe + S3 backup |
| EBS / S3 | Pin to node or external S3 | Always external deep storage | Pin to node + optional S3 backup |
| Hot cache RAM | ~50% of RAM (forward indexes + segments) | ~25% of RAM (hot memtables) | ~30% of RAM (cache, mark caches) |

### 3.2 Cost Estimates (USD/month, public cloud)

| Cost line | Pinot | Druid | ClickHouse |
|---|---|---|---|
| EC2 compute (cluster) | $30,000 - $60,000 | $25,000 - $50,000 | $10,000 - $25,000 |
| Storage (EBS + S3) | $5,000 - $12,000 | $3,000 - $8,000 | $4,000 - $10,000 |
| Kafka / streaming ingest (~$0.15/GB) | $4,000 - $10,000 | $4,000 - $10,000 | $4,000 - $10,000 |
| Managed control-plane (optional) | $5,000 (StarTree) | $5,000-$15,000 (Imply / Lenses) | $0 (self-managed) or $5,000-$15,000 (Altinity, ClickHouse Inc) |
| **Total monthly** | **~$45K - $90K** | **~$40K - $80K** | **~$20K - $60K** |

**Observations:**
- ClickHouse tends to win on **TCO for raw OLAP** because of single-binary + fewer nodes.
- Pinot and Druid pay a cluster-manager / ingestion-tier tax — more nodes, more coordination.
- All three become cost-comparable when you add **managed control planes**, **multi-AZ**, **monitoring**.

### 3.3 Hidden Costs — Often Forgotten

| Hidden line | Pinot | Druid | ClickHouse |
|---|---|---|---|
| Re-balancing | Yes (Helix) — operational work | Yes (Coordinator) — operational work | Yes (manual re-shard) — operational work |
| Deep storage contract | Required (S3/HDFS) | Required (S3/HDFS) | Optional (can pin) |
| Query memory planning | Pin the segment count per server | Tune "select" thresholds | Set `max_memory_usage`, `max_concurrent_queries` |
| Schema evolution | Mid-flight (add column OK) | Mid-flight (disable + re-ingest) | Easier — `ALTER TABLE` is fully online |
| Vendor support tier | StarTree (Uber-internal users: e.g., Uber) | Imply | ClickHouse Inc + Altinity |
| License | Apache 2.0 | Apache 2.0 | Apache 2.0 + BSL business source for cloud |

---

## 4. When to Use Each — Decision Guide

### 4.1 Use Apache Pinot When:

- You need **user-facing dashboards at scale** with millisecond latency.
- Your queries have **high concurrency** — 1000s of users, not 100s.
- **Star-tree aggregation** is a natural fit: `GROUP BY a, b, c` with `WHERE` filters on the same columns.
- You're already in a **JVM / Kafka / Helix** ecosystem (LinkedIn-style stack).
- Examples: LinkedIn (Who Viewed My Profile), Uber (Rides Dashboard), Slack.

### 4.2 Use Apache Druid When:

- Your data is mostly **time-series / events** with a known cardinality of dimensions.
- You want to **roll up at ingestion** — store less at query time.
- You need **Apache Kafka integration** as the first-class source.
- You have **strong S3/HDFS integration** for deep storage.
- Examples: Imply customers (NYSE, Lyft), Alibaba metrics, Cisco telemetry.

### 4.3 Use ClickHouse When:

- You want **one engine** for ingest + ad-hoc + analytical SQL.
- You need **broad SQL features** — JOINs, CTEs, window functions, dict functions.
- You're running **logs / events / observability** and can use `Kafka` engine + materialized views.
- You want to **embed** the engine in your own product.
- Examples: Cloudflare (HTTP logs), eBay (analytics), ByteHouse / ClickHouse Cloud, Spotify backend, Yandex.

### 4.4 Don't Use Any of Them When:

- Your workload is **OLTP** — use MySQL / HBase / Postgres.
- You have **< 1 TB** of historical data — DuckDB single-node gives you 90% of value for $0.
- You have **streaming-only "freshness" requirements** — Flink alone suffices; the queries run in process.
- You have **batch-only overnight analytics** — Presto / Spark on Parquet is cheaper.

---

## 5. Real-World Worked Examples

### 5.1 Scenario: User-Facing Analytics Dashboard ("Today's engagement")

**Requirements:**
- 50M DAU, sub-second dashboard queries
- 1B events / day
- "Visits per page, last 7 days, by device type, filtered by country"

**Best fit: Pinot**

> Why: Star-tree index built at ingestion; broker-scatter-gather handles 50k concurrent users; query plan pins to specific segments. LinkedIn's Who Viewed My Profile uses this exact pattern.

```sql
-- Pinot SQL
SELECT
  page,
  SUM(event_count) AS events,
  COUNT(DISTINCT device_id) AS unique_devices
FROM agg_daily_page_device
WHERE dt BETWEEN '2026-10-01' AND '2026-10-07'
  AND device_type = 'mobile'
  AND country = 'US'
GROUP BY page
ORDER BY events DESC
LIMIT 100;
```

### 5.2 Scenario: Observability + Time-Series Metrics

**Requirements:**
- 100M metrics / sec
- 90 days hot retention
- Top-N queries: top tenants by error rate in last 5 min
- Operators want star-tree-style rollups

**Best fit: Druid**

> Why: Rollup at ingest collapses high-cardinality streams into compact segments; bitmap indexes for top-N; deep storage in S3 keeps hot tier lean.

```json
{
  "type": "index_parallel",
  "spec": {
    "ioConfig": { "type": "kafka", "topic": "metrics.raw" },
    "tuningConfig": {
      "type": "kafka",
      "maxRowsPerSegment": 5_000_000,
      "intermediaryPersistPeriod": "PT10M"
    },
    "dataSchema": {
      "dataSource": "metrics",
      "granularitySpec": {
        "type": "uniform",
        "segmentGranularity": "hour",
        "queryGranularity": "minute",
        "rollup": true
      }
    }
  }
}
```

### 5.3 Scenario: Internal Analytics Tool — Logs / Events

**Requirements:**
- 10B events / day
- Product analysts run ad-hoc SQL
- "Find every user who hit 5xx in the last 24h" — flexible queries

**Best fit: ClickHouse**

> Why: Ad-hoc SQL is the dominant workload; vectorized execution beats the others on raw scans; simple ops with one binary.

```sql
-- ClickHouse
SELECT user_id, count() AS errors
FROM events
WHERE event_ts >= now() - INTERVAL 1 DAY
  AND http_status >= 500
  AND environment = 'prod'
GROUP BY user_id
ORDER BY errors DESC
LIMIT 100;
```

---

## 6. How to Choose — Practical Matrix

### 6.1 Capability Matrix

| Capability | Pinot | Druid | ClickHouse |
|---|---|---|---|
| SQL completeness | Medium | Medium | High (closest to ANSI / TPC) |
| Sub-second p99 on dashboards | Excellent | Good | Good |
| Ingestion throughput | Very high | Very high | Highest (single binary) |
| Operational complexity | High | High | Low-Medium |
| Multi-tenancy | Native | Native | Manual (DB-level) |
| Star-schema / star-tree | First-class | First-class (rollup segments) | Manual via materialized views |
| JOINs | Limited (left-semi, anti) | Limited (lookup extract) | Full ANSI JOIN support |
| Upserts | Upsert tables; pinned hard | Append only (typical) | `ReplacingMergeTree` |
| Rollup at ingest | Optional | First-class | Optional (`AggregatingMergeTree`) |
| Cost for same workload | Medium-High | Medium-High | Low-Medium |
| License | Apache 2.0 | Apache 2.0 | Apache 2.0 (BSL cloud add-on) |

### 6.2 Choose by Workload

| Workload | Pick |
|---|---|
| User-facing dashboards with fixed query patterns | **Pinot** |
| Time-series + rollup-heavy observability | **Druid** |
| Broad ad-hoc SQL by analysts | **ClickHouse** |
| Pure logs, fast grep + aggregations | **ClickHouse** |
| Kafka-native streaming metrics with rollups | **Druid** |
| LinkedIn-style "User X viewed Profile Y" tiles | **Pinot** |
| Embedded engine in your SaaS product | **ClickHouse** |
| Multi-tenant SaaS BI platform | **Pinot or Druid** |
| Cost-sensitive, mid-scale (10 TB - 100 TB) | **ClickHouse** |

---

## 7. How To Make This Work In Production

### 7.1 Common Pitfalls

| Pitfall | How to avoid |
|---|---|
| Pinot: forgetting to size broker heap | Brokers hold `stageTrace` + scatter buffers — 32 GiB minimum |
| Druid: forgetting segment size tuning | Tune `targetPartitionSize` and `maxRowsPerSegment`; else hot tier dies |
| ClickHouse: too many small parts | Use `INSERT` blocks of 100k rows; set `parts_to_throw_insert` threshold |
| Ingestion backpressure ignoring | All three spike memory under bad partitions; use S3 spillover / `DROP PARTITION` fast |
| Query concurrency vs node RAM | Each engine has its own knob (`max_concurrent_queries`, `taskAssignment`, `pinot.broker.max.server.queries`) |

### 7.2 Reference Architectures

```
┌─── Pinot reference architecture ───────────────────────┐
│  Kafka → { Controller, Minion, Server, Broker }        │
│  Deep storage: PinotFS over S3                        │
│  Query: StarTree index built per table                │
└────────────────────────────────────────────────────────┘

┌─── Druid reference architecture ───────────────────────┐
│  Kafka → Middle Manager (peon) → Deep storage (S3)    │
│                    ↓                                  │
│  Coordinator schedules Historical to load segments    │
│  Brokers + Router serve queries                       │
└────────────────────────────────────────────────────────┘

┌─── ClickHouse reference architecture ─────────────────┐
│  Kafka engine → Materialized view → MergeTree        │
│  ClickHouse Keeper (or ZK) for replication            │
│  Single binary, scale horizontally (shards)           │
│  Optional: external monitoring via Prometheus        │
└────────────────────────────────────────────────────────┘
```

### 7.3 Cost Optimization Tips

| Tip | Pinot | Druid | ClickHouse |
|---|---|---|---|
| Storage tiering | Push cold segments to S3 + Brokers replay | Native deep storage | S3-backed `StoragePolicy` |
| Reduce data via rollup | Star-tree fine-tuning | Set rollup at ingestion | `AggregatingMergeTree` materialized view |
| Prune partitions | Time-partition + star-tree | Time-bucketed segments | Partition by month/week |
| Use cheaper nodes + more brokers | Keep servers beefy, brokers small | Same | Small x86 OK; use local NVMe |
| Spot / Reserved instances | 30-50% savings | Same | Same |

---

## 8. Interview Talking-Points Cheat Sheet

When asked "Why X over Y":

| Argument | Use it for |
|---|---|
| Pin ownership of your data — file in / file out | **ClickHouse** (single binary) |
| User-facing latencies at Uber/LinkedIn scale | **Pinot** |
| Time-series workload with rollups + S3 deep storage | **Druid** |
| Budget-constrained, ad-hoc SQL | **ClickHouse** |
| Kafka-native pipelines, rollup-heavy metrics | **Druid** |
| Slack/Uber-style "you have N new things" tile | **Pinot** |

---

## 9. Final Recommendations — Three Use-Case Picks

| If you said | Pick |
|---|---|
| "We're building a SaaS BI product like Looker" | **Pinot** |
| "We're replacing our ELK observability cluster" | **ClickHouse** |
| "We're a shop with mostly Kafka metrics and S3" | **Druid** |
| "We're cost-conscious and want one engine" | **ClickHouse** |
| "We're already deep in the JVM + Hadoop + Kafka stack" | **Pinot or Druid** |
| "We have a small team, want low ops overhead" | **ClickHouse** |

---

## 10. References and Further Reading

| Source | Topic |
|---|---|
| [pinot.apache.org](https://pinot.apache.org) | Pinot docs |
| [druid.apache.org](https://druid.apache.org) | Druid docs |
| [clickhouse.com/docs](https://clickhouse.com/docs) | ClickHouse docs |
| LinkedIn Engineering Blog | Pinot design origins |
| Imply.io blog | Druid rollup patterns |
| ClickHouse blog (Yandex history) | Vectorized execution |
| Uber Engineering Blog | Real-time Pinot deployments |
| Confluent blog | Three-engine comparison (kafka source patterns) |
| Meta Engineering (Folley / Scuba) | Why Scuba wasn't open-sourced |

> All comparisons are working-level approximations. Always validate with **your own load** using [Benchmarks](https://clickhouse.com/benchmark).

---

## 11. Docker Quickstart for Each Engine

All three engines are runnable locally with Docker. The patterns below are the **canonical** layouts from their official `docker-compose.yml`s.

### 11.1 Apache Pinot — Single docker-compose for the Reference Cluster

#### Prerequisites
- Docker 24+, Docker Compose v2
- 8 GB RAM available (default cluster is light)

#### Minimal `docker-compose.yml`

```yaml
# docker-compose-pinot.yml
# Source: apache/pinot > docker-compose.yml (official)
# https://github.com/apache/pinot/tree/master/docker

version: '3.8'

services:
  zookeeper:
    image: zookeeper:3.9
    container_name: pinot-zookeeper
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

  pinot-controller:
    image: apachepinot/pinot:1.2.0
    container_name: pinot-controller
    command: "bin/pinot-admin.sh start Controller"
    volumes:
      - ./pinot/config:/config
    ports:
      - "9000:9000"   # controller API
    depends_on:
      - zookeeper
    environment:
      JAVA_OPTS: "-Xms512M -Xmx1G"

  pinot-broker:
    image: apachepinot/pinot:1.2.0
    container_name: pinot-broker
    command: "bin/pinot-admin.sh start Broker"
    volumes:
      - ./pinot/config:/config
    ports:
      - "8099:8099"   # broker API
    depends_on:
      - pinot-controller
    environment:
      JAVA_OPTS: "-Xms512M -Xmx1G"

  pinot-server:
    image: apachepinot/pinot:1.2.0
    container_name: pinot-server
    command: "bin/pinot-admin.sh start Server"
    volumes:
      - ./pinot/config:/config
      - ./pinot/data:/data
    ports:
      - "8098:8098"   # server admin
    depends_on:
      - pinot-controller
    environment:
      JAVA_OPTS: "-Xms1G -Xmx2G"

  kafka:
    image: confluentinc/cp-kafka:7.6.1
    container_name: pinot-kafka
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
```

#### Start it

```bash
mkdir -p pinot/config pinot/data
docker compose -f docker-compose-pinot.yml up -d

# Tail logs
docker compose -f docker-compose-pinot.yml logs -f pinot-controller
```

#### Ingest a CSV of click events

Place `clicks.csv` next to your config dir, then:

```bash
docker exec -it pinot-controller bash -lc "
  bin/pinot-admin.sh IngestJob \
    -jobSpecFile /config/ingestion-job-spec.yml
"
```

Where `ingestion-job-spec.yml` is:

```yaml
executionFrameworkSpec:
  name: standalone
  segmentGenerationJobRunnerClassName: org.apache.pinot.tools.standalone.StandaloneSegmentGenerationJobRunner
jobType: SegmentCreation
inputDirURI: /data/clicks
includeFileNamePattern: '*.csv'
outputDirURI: /data/clicks/segments
overwriteOutput: true
recordReaderSpec:
  dataFormat: csv
  csvHeader: event_id,device_id,user_id,event_ts,page,event_type
  delimiter: ','
tableSpec:
  tableName: events
  schemaURI: /config/events_schema.json
  tableConfigURI: /config/events_table.json
```

#### Query it

```bash
# Via broker REST
curl -s "http://localhost:8099/query/sql" \
  -H 'Content-Type: application/json' \
  -d '{
        "sql": "SELECT page, COUNT(*) FROM events GROUP BY page ORDER BY COUNT(*) DESC LIMIT 10"
      }' | jq

# Browser UI (Controller): http://localhost:9000/
```

#### Common commands

| Task | Command |
|---|---|
| Stop | `docker compose -f docker-compose-pinot.yml down` |
| Reset data | `docker compose -f docker-compose-pinot.yml down -v` |
| Open controller UI | `http://localhost:9000/` |
| Broker endpoint | `http://localhost:8099/` |

---

### 11.2 Apache Druid — Single-Broker Cluster via `docker-compose.yml`

#### Prerequisites
- Docker 24+, Compose v2
- 8 GB RAM (more than Pinot because JVMs add up)

#### Minimal `docker-compose.yml`

```yaml
# docker-compose-druid.yml
# Source: apache/druid > distribution/docker/docker-compose.yml
# https://github.com/apache/druid/tree/master/distribution/docker

version: "3.8"

volumes:
  druid_shared: {}

services:
  postgres:
    image: postgres:15
    container_name: druid-postgres
    environment:
      POSTGRES_USER: druid
      POSTGRES_PASSWORD: druid
    volumes:
      - druid_shared:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  zookeeper:
    image: zookeeper:3.9
    container_name: druid-zookeeper
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

  coordinator:
    image: apache/druid:28.0.1
    container_name: druid-coordinator
    volumes:
      - druid_shared:/opt/druid/var
    ports:
      - "8081:8081"
    depends_on: [zookeeper, postgres]
    env_file: [druid.env]
    command: ["coordinator"]

  broker:
    image: apache/druid:28.0.1
    container_name: druid-broker
    volumes:
      - druid_shared:/opt/druid/var
    ports:
      - "8082:8082"
    depends_on: [zookeeper, postgres, coordinator]
    env_file: [druid.env]
    command: ["broker", "./conf/supervisord/druid.conf"]

  historical:
    image: apache/druid:28.0.1
    container_name: druid-historical
    volumes:
      - druid_shared:/opt/druid/var
    depends_on: [zookeeper, postgres, coordinator]
    env_file: [druid.env]
    command: ["historical", "./conf/supervisord/druid.conf"]

  overlord:
    image: apache/druid:28.0.1
    container_name: druid-overlord
    volumes:
      - druid_shared:/opt/druid/var
    ports:
      - "8090:8090"
    depends_on: [zookeeper, postgres, coordinator]
    env_file: [druid.env]
    command: ["overlord"]

  middlemanager:
    image: apache/druid:28.0.1
    container_name: druid-middlemanager
    volumes:
      - druid_shared:/opt/druid/var
    depends_on: [zookeeper, postgres, overlord]
    env_file: [druid.env]
    command: ["middleManager"]

  router:
    image: apache/druid:28.0.1
    container_name: druid-router
    volumes:
      - druid_shared:/opt/druid/var
    ports:
      - "8888:8888"   # unified API
      - "9090:9090"
    depends_on: [broker]
    env_file: [druid.env]
    command: ["router"]
```

#### `druid.env` (required by every Druid service)

```bash
# druid.env
DRUID_VERSION=28.0.1
DRUID_JAVA_VERSION=17
JAVA_TOOL_OPTIONS=-XX:+UseContainerSupport
DRUID_COMMON_CONF_DIR=/opt/druid/conf/druid/_common
druid_discovery_type=zk
druid_zk_service_host=zookeeper
druid_zk_service_port=2181

druid_metadata_storage_type=postgresql
druid_metadata_storage_connector_connectURI=jdbc:postgresql://postgres:5432/druid
druid_metadata_storage_connector_user=druid
druid_metadata_storage_connector_password=druid

druid_storage_type=local
druid_storage_storage_path=/opt/druid/var/data
```

#### Start it

```bash
mkdir druid && cd druid
wget https://raw.githubusercontent.com/apache/druid/master/distribution/docker/docker-compose.yml
wget https://raw.githubusercontent.com/apache/druid/master/distribution/docker/druid.env -O druid.env

# Start; takes ~1-2 min for first JVM warmup
docker compose up -d

# Wait for health
docker compose logs -f router
```

#### Ingest sample data

Use the native ingestion API (drop a JSON spec):

```bash
curl -XPOST -H'Content-Type: application/json' \
  http://localhost:8081/druid/indexer/v1/task \
  -d @sample-ingest.json
```

Where `sample-ingest.json` is a Druid streaming spec (mirrors §2.3 of this article):

```json
{
  "type": "index_parallel",
  "spec": {
    "ioConfig": {
      "type": "index",
      "inputSource": {
        "type": "local",
        "baseDir": "/opt/druid/var/",
        "filter": "wikiticker-2015-09-12-sampled.json.gz"
      },
      "inputFormat": { "type": "json" }
    },
    "dataSchema": {
      "dataSource": "wikiticker",
      "timestampSpec": { "column": "time", "format": "auto" },
      "dimensionsSpec": { "dimensions": ["channel","user","comment"] }
    }
  }
}
```

#### Query it

```bash
# Druid SQL via router API
curl -XPOST -H'Content-Type: application/json' \
  http://localhost:8888/druid/v2/sql \
  -d '{
        "query": "SELECT channel, COUNT(*) AS cnt FROM wikiticker GROUP BY channel ORDER BY cnt DESC LIMIT 5"
      }' | jq

# UI: http://localhost:8888/unified-console.html
```

#### Common commands

| Task | Command |
|---|---|
| Stop | `docker compose down` |
| Wipe (incl. volumes) | `docker compose down -v` |
| Unified Console | `http://localhost:8888/unified-console.html` |
| Coordinator UI | `http://localhost:8081/` |

---

### 11.3 ClickHouse — Single-node via Docker Compose

#### Prerequisites
- Docker 24+, Compose v2
- 4 GB RAM (single binary is light)

#### Minimal `docker-compose.yml`

```yaml
# docker-compose-clickhouse.yml
# Source: clickhouse/clickhouse-server > docker-compose.yml
# https://github.com/clickhouse/clickhouse

version: "3.8"

services:
  clickhouse-server:
    image: clickhouse/clickhouse-server:24.3
    container_name: clickhouse-server
    ulimits:
      nofile:
        soft: 262144
        hard: 262144
    ports:
      - "8123:8123"   # HTTP
      - "9000:9000"   # native TCP
      - "9009:9009"   # inter-server replication
    volumes:
      - ./clickhouse/data:/var/lib/clickhouse
      - ./clickhouse/logs:/var/log/clickhouse-server
      - ./clickhouse/conf:/etc/clickhouse-server
      - ./clickhouse/init:/docker-entrypoint-initdb.d
    environment:
      CLICKHOUSE_DB: default
      CLICKHOUSE_USER: default
      CLICKHOUSE_PASSWORD: ch_password
      CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT: 1

  clickhouse-client:
    image: clickhouse/clickhouse-client:24.3
    container_name: clickhouse-client
    depends_on:
      - clickhouse-server
    entrypoint:
      - clickhouse-client
      - --host=clickhouse-server
      - --user=default
      - --password=ch_password
      - --multiquery
    stdin_open: true
    tty: true
```

#### Custom config (optional)

```xml
<!-- clickhouse/conf/config.d/storage.xml -->
<clickhouse>
  <storage_configuration>
    <disks>
      <default><path>/var/lib/clickhouse/</path></default>
      <s3><type>s3</type><endpoint>https://s3.amazonaws.com</endpoint></disk>
    </disks>
  </storage_configuration>
</clickhouse>
```

#### Seed schema at first boot

```sql
-- clickhouse/init/01-events.sql
CREATE TABLE events_local (
  event_id   UInt64,
  device_id  UInt64,
  user_id    Nullable(UInt64),
  event_ts   DateTime,
  page       String,
  event_type LowCardinality(String)
) ENGINE = MergeTree
PARTITION BY toYYYYMM(event_ts)
ORDER BY (device_id, event_ts);

CREATE TABLE events AS events_local
ENGINE = Distributed('cluster', default, events_local);
```

#### Start it

```bash
mkdir -p clickhouse/{data,logs,conf/config.d,init}
docker compose -f docker-compose-clickhouse.yml up -d

# Tail server log
docker logs -f clickhouse-server
```

#### Query it

```bash
# HTTP API
curl -s 'http://localhost:8123/?query=SELECT+version()' \
  --user default:ch_password

# clickhouse-client (interactive)
docker exec -it clickhouse-client clickhouse-client -q "
  SELECT page, COUNT(*) AS cnt
  FROM events_local
  WHERE event_ts >= now() - INTERVAL 1 DAY
  GROUP BY page
  ORDER BY cnt DESC
  LIMIT 10
"

# Web UI: launch separately if needed
docker run -d --name ch-ui --network host \
  -p 8124:80 \
  ghcr.io/caioricciuti/ch-ui
# http://localhost:8124 — connect to localhost:8123
```

#### Common commands

| Task | Command |
|---|---|
| Stop | `docker compose -f docker-compose-clickhouse.yml down` |
| Reset data | `docker compose -f docker-compose-clickhouse.yml down -v` |
| Server logs | `docker logs -f clickhouse-server` |
| HTTP UI | `http://localhost:8123/play` (if Play enabled) |

---

### 11.4 Comparing the Three Setups Side-by-Side

| Aspect | Pinot | Druid | ClickHouse |
|---|---|---|---|
| Containers | 5 (zookeeper + controller + broker + server + kafka) | 8 (postgres + zookeeper + coordinator + broker + historical + overlord + middlemanager + router) | 2 (server + client) |
| Min memory | 8 GB | 8-12 GB | 4 GB |
| First-boot time | ~30 sec | ~90-120 sec (JVM warm) | ~10-30 sec |
| Ports exposed | 9000, 8099, 8098, 9092 | 8888, 8081, 8090, 2181, 5432 | 8123, 9000, 9009 |
| Default UI | `http://localhost:9000/` | `http://localhost:8888/unified-console.html` | None (HTTP only) |
| Reset command | `docker compose … down -v` | `docker compose … down -v` | `docker compose … down -v` |

> **Tip:** all three can share a single machine for local testing; just run each `docker-compose` against different ports if you spin up more than one at once.

---

### 11.5 Troubleshooting

| Symptom | Engine | Fix |
|---|---|---|
| `pinot-controller` stays unhealthy | Pinot | Check `zookeeper` logs; bump `JAVA_OPTS` from 512M → 1G |
| `druid-coordinator` loops on "still waiting" | Druid | Postgres not healthy; check `postgres` service first |
| `clickhouse-server` exits with code 137 | ClickHouse | Out of memory; raise Docker Desktop RAM to 4 GB+ |
| Cannot connect from client to server | ClickHouse | Verify `CLICKHOUSE_USER` and `CLICKHOUSE_PASSWORD` are set |
| "No broker available" on query | Druid | `broker` is up but `historical` is still loading segments; wait 60 sec |
| Uploads fail in Pinot controller UI | Pinot | Controller data dir permissions; `./pinot/data` not writable |
| Kafka topic not found | All | Create topic explicitly: `docker exec -it pinot-kafka kafka-topics --create --topic clicks --bootstrap-server localhost:9092 --partitions 3` |

---

### 11.6 A Single One-Liner to Test All Three in Turn

```bash
# 1. Pinot
docker compose -f docker-compose-pinot.yml up -d
sleep 30 && curl -sS 'http://localhost:8099/health' && echo "Pinot OK"

# 2. Druid
docker compose -f docker-compose-druid.yml down
docker compose -f docker-compose-druid.yml up -d
sleep 90 && curl -sS 'http://localhost:8888/status' && echo "Druid OK"

# 3. ClickHouse
docker compose -f docker-compose-clickhouse.yml down
docker compose -f docker-compose-clickhouse.yml up -d
sleep 20 && curl -sS 'http://localhost:8123/?query=SELECT+version()' --user default:ch_password && echo "ClickHouse OK"
```

---

## 12. Final Format Cheat Sheet — Pick a Section When You Need It

| If you are… | Read this section first |
|---|---|
| Doing an interview | TL;DR → §4 (when to use) → §6 (capability matrix) → §8 (interview cheat sheet) |
| Writing a design doc | §1 (architecture) → §2 (working model) → §3 (cost) → §9 (final picks) |
| Picking a tool for your team | §6 (capability matrix) → §4 (when to use) → §3 (cost) → §11 (Docker quickstart) |
| Setting up a local sandbox | §11 entirely (Pinot / Druid / ClickHouse docker-compose) |
| Debugging a production cluster | §7 (production playbook) → §11.5 (troubleshooting) |

---

## 13. Format Conventions Used in This Document

| Convention | Meaning |
|---|---|
| `code` | Inline code: filenames, commands, ports |
| **bold** | Section emphasis, the key term on a line |
| > blockquote | Note / warning / asides |
| ```yaml / sql / json ``` | Copy-pastable configuration / query |
| ✔ / ✗ | Yes / No capability |
| §section | Cross-reference inside the doc |
| →  arrow | Data flow in diagrams |
