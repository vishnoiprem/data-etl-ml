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
                    ┌─────────────────────────────────────┐
                    │            CONTROLLER              │
                    │  (cluster coordinator, Helix)       │
                    └─────────────────────────────────────┘
                                │            │
                manages          │            │          manages
                                ▼            ▼
                    ┌──────────────┐  ┌─────────────────┐
                    │   BROKERS    │  │   SERVERS       │
                    │  (stateless  │  │  (stateful:     │
                    │   query      │  │   hold segments │
                    │   routing)   │  │   + indices)    │
                    └──────────────┘  └─────────────────┘
                                ▲            ▲
                                │            │
                    ┌───────────┴──┐  ┌──────┴────────┐
                    │   MINIONS    │  │  INGESTION    │
                    │ (batch tasks │  │  (Kafka, S3,  │
                    │  + compactor)│  │   HDFS, etc.) │
                    └──────────────┘  └───────────────┘
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
                  ┌────────────────┐         ┌───────────────────┐
                  │  COORDINATOR   │         │   OVERLORD        │
                  │  (segments,    │         │   (task mgmt /    │
                  │   load balance)│         │    ingestion)     │
                  └────────────────┘         └───────────────────┘
                            │                          │
                            ▼                          ▼
            ┌────────────────────────┐    ┌────────────────────────┐
            │     HISTORICALS        │    │   MIDDLE MANAGERS     │
            │ (cold segments,        │    │ (real-time ingestion, │
            │  deep storage, S3/HDFS)│    │  in-memory + persist) │
            └────────────────────────┘    └────────────────────────┘
                            ▲                          ▲
                            │                          │
                            └──────────┬───────────────┘
                                       ▼
                              ┌─────────────────┐
                              │    BROKER       │  (stateless query)
                              │    ROUTER       │  (stateless API)
                              └─────────────────┘
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
