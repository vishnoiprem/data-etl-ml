# Clickstream Pipeline into a Modern Lakehouse

**Difficulty:** HARD
**Companies:** FAANG (Amazon, Google, Meta, Apple, Netflix)
**Tags:** system-design, streaming, lakehouse, iceberg, kafka, ml, big-data

---

## 1. Problem Statement

> Design an end-to-end clickstream pipeline. We collect events from web and mobile —
> page views, clicks, scrolls, form submissions, purchases. About a billion events a
> day, 20-30% of which is bot traffic. Everything goes into a modern lakehouse using
> Delta Lake or Iceberg. Multiple consumers: dashboards, A/B testing, ML training.
> Walk me through the full architecture from SDK to serving layer.

### Hard Parts
- 1B+ events/day, peaks of 100K/sec
- 50+ event types and **growing** → schema must be extensible
- Bot traffic 20-30% of raw → must be filtered without losing legit signals
- Multiple consumers with very different SLAs (minutes / daily / ad-hoc)
- Storage at petabyte scale — partition, compact, Z-order

### Scale & Constraints

| Dimension | Value |
|---|---|
| Throughput | 1B events/day, 100K events/sec peak |
| Event types | 50+ and growing |
| Bot traffic | 20–30% of raw |
| Dashboards freshness | Minutes |
| Experimentation freshness | Daily |
| ML training | Ad-hoc on demand |
| Storage | Lakehouse (Delta Lake / Iceberg) |

---

## 2. The 5-Step Approach

### Step 1 — Clarify Requirements
- **Sources:** Web JS SDK, iOS SDK, Android SDK, Server-side events
- **Consumers:**
  - **Dashboards** (Superset, Looker) — minute-fresh, wide aggregations
  - **Experimentation** (Problem 1) — daily user-metric rollups
  - **ML training** (recommendation, ranking, churn) — feature pipelines
- **Quality requirements:**
  - Reject malformed payloads at the edge (don't poison the lakehouse)
  - Bot filtering must be fast (don't burn ML inference budget on bots)
  - Lossless for **human** events, lossy is fine for **bot** events

### Step 2 — High-Level Architecture

```
Web/Mobile SDK ──▶ Event Collector API ──▶ Kafka ──▶ Stream Processing
                (Envoy + Lua + OTel)     (partitioned by user_id)
                                                    │
                                                    ▼
                                          Bot filter + Dedup + Enrich
                                                    │
                                                    ▼
                                        Lakehouse: Iceberg on S3
                                        ┌────────────┬────────────┬────────────┐
                                        │  BRONZE    │  SILVER    │   GOLD     │
                                        │  raw       │  cleaned   │  per-user  │
                                        │  immutable │  bot-      │  features  │
                                        │            │  filtered  │  + metrics │
                                        └────────────┴────────────┴────────────┘
                                                    │
                  ┌─────────────────────────────────┼─────────────────────────────────┐
                  ▼                                 ▼                                 ▼
          Dashboards (Trino)              Experimentation (Spark)           ML Training (Spark)
```

### Step 3 — Data Flow & Schema Design

**Why Iceberg over plain Parquet:**
- Schema evolution without table rewrites (essential — we have 50+ types and growing)
- Hidden partitioning (don't force callers to know partition keys)
- Time-travel / snapshot isolation (replay / debug)
- Cheap row-level deletes (for GDPR — see Problem 4)

**Schema philosophy:** "wide row, narrow properties" — known fields are typed columns;
unknown fields live in a `properties MAP<STRING, STRING>` for forward compatibility.

```
event_id           STRING  (client-generated UUID; dedup key)
user_id            STRING  (hashed at SDK)
session_id         STRING
event_ts           TIMESTAMP
event_name         STRING  (page_view, click, scroll, form_submit, purchase, ...)
platform           STRING  (web, ios, android, server)
app_version        STRING
country            STRING
device_class       STRING
properties         MAP<STRING, STRING>   ← extensible
user_traits        MAP<STRING, STRING>   ← first-party traits
context            MAP<STRING, STRING>   ← A/B tags, campaign, etc.
```

### Step 4 — Scale the Design

| Concern | Approach |
|---|---|
| 100K events/sec ingest | Kafka partitioned by `user_id` (16+ partitions per consumer group) |
| Bot filtering at scale | Two-stage: signature blocklist (in-memory, fast) + ML scorer (in Flink) |
| Dedup | `event_id` (client UUID) + 24h TTL in Flink state |
| Partitioning | Iceberg hidden partitioning by `event_ts` day |
| File optimization | Auto-compaction job + Z-ORDER by `(user_id, event_name)` for Silver/Gold |
| Cost control | TTL on Bronze (7 days) → Silver (180 days) → Gold (3+ years) |
| Late events | Watermark 24h; replay from Kafka offset if SLA breached |

### Step 5 — Address Non-Functional

- **Latency:** Collector → Kafka < 50ms p99; Silver visible < 5 min; Gold daily
- **Reliability:** Idempotent collectors (event_id), at-least-once → exactly-once in Flink
- **Observability:** Per-stage metrics — ingest rate, schema-reject rate, bot-filter rate, dedup rate
- **Security:** User IDs hashed at SDK; raw PII never leaves collector; ACLs on Gold tables
- **Privacy:** Honor DNT/cookie consent; suppress events from opted-out users at the SDK
- **Cost:** Bot events go to a separate cheap tier; raw Bronze has aggressive TTL

---

## 3. Critical Design Decisions

### 3.1 Stream vs Micro-batch?
| | True Streaming (Flink) | Micro-batch (Spark Streaming) |
|---|---|---|
| Latency | Sub-second | 1–10 minutes |
| Cost | Higher (always-on) | Lower (right-sized) |
| Exactly-once | Native | Trickier |
| **Decision** | Bot filtering, dedup, validation | Heavy aggregation, ML feature prep |

We use **both**: Flink for the "fast path" (validate, bot-filter, dedup) → Iceberg Silver;
Spark for hourly/daily aggregations into Gold.

### 3.2 Bot Detection Strategy
Three layers:
1. **Signature-based** (in-memory Bloom filter + UA blocklist) — catches 70% of bots in <1ms
2. **Heuristic** (events/sec > 50, no scroll events, headless browser UA, datacenter IP) — catches another 20%
3. **ML scorer** (gradient-boosted model on 50+ features) — catches sophisticated bots

Bots are tagged, not deleted — we keep them in a separate Bronze partition for analysis.

### 3.3 Schema Validation
- **Server-side schema registry** (Confluent / Apicurio) — backward-compatible changes only
- **Strict validation at collector** — reject malformed payloads (HTTP 400)
- **Soft validation in Flink** — quarantine unknown event_names to `events_quarantine`
- **Monitor** `schema_reject_rate`; alert on > 0.5%

### 3.4 Storage Optimization
- **Bronze:** Parquet + Snappy, partitioned by `dt`, retained 7 days
- **Silver:** Parquet + ZSTD, partitioned by `dt`, Z-ORDER by `(user_id, event_name)`, retained 180 days
- **Gold:** Columnar per use-case (user_daily_features, session_aggregates, …), Z-ORDER by `user_id`
- **Auto-compaction** job runs when small-file ratio > 30%

### 3.5 Serving Multiple Consumers
- **Dashboards:** Trino/Presto over Iceberg (column-pruned, predicate-pushed, cached)
- **Experimentation:** Spark batch reads from Silver; writes user_metric_daily
- **ML training:** Spark reads Gold; uses Petastorm/TFRecord exporters

---

## 4. Folder Layout

```
02b-clickstream-pipeline-lakehouse/
├── README.md                       # this file
├── docs/design-decisions.md
├── diagrams/
│   ├── architecture.mermaid        # end-to-end
│   ├── medallion-flow.mermaid      # Bronze→Silver→Gold lineage
│   └── bot-filter-pipeline.mermaid
├── sql/
│   ├── schema_iceberg.sql          # DDL for Bronze/Silver/Gold
│   ├── schema_validation.sql       # quarantine + reject queries
│   ├── bot_filter_features.sql     # bot feature rollups
│   └── sessionization.sql          # session rebuild query
├── python/
│   ├── sdk_payload.py              # canonical event schema, SDK helpers
│   ├── schema_validator.py         # JSON Schema / Avro validator
│   ├── bot_filter.py               # signature + heuristic bot detection
│   └── collector_handler.py        # reference Event Collector handler
├── pyspark/
│   ├── ingest_kafka_to_bronze.py   # Kafka → Iceberg Bronze
│   ├── bronze_to_silver.py         # dedup + bot filter + enrich
│   ├── silver_to_gold.py           # session + user-daily features
│   ├── compaction.py               # Z-order + file compaction
│   └── ml_feature_export.py        # Spark → TFRecord / Petastorm
├── config/
│   ├── iceberg_tables.yaml
│   ├── bot_signatures.yaml
│   └── metric_definitions.json
├── sample_data/
│   ├── events.jsonl
│   └── bot_signatures.txt
└── tests/
    ├── test_schema_validator.py
    ├── test_bot_filter.py
    └── test_sessionization.py
```

---

## 5. How to Run End-to-End

```bash
# 1. Generate sample events
python python/sdk_payload.py --emit sample_data/events.jsonl

# 2. Validate schema
python python/schema_validator.py --input sample_data/events.jsonl

# 3. Run bot filter
python python/bot_filter.py --input sample_data/events.jsonl

# 4. Kafka → Bronze (requires running Kafka)
python pyspark/ingest_kafka_to_bronze.py

# 5. Bronze → Silver
python pyspark/bronze_to_silver.py --dt 2026-09-26

# 6. Silver → Gold (user features)
python pyspark/silver_to_gold.py --dt 2026-09-26
```

---

## 6. Interview Talking Points

When presenting this design:

1. **Schema strategy** — wide + properties map; Iceberg for evolution
2. **Why Iceberg over plain Parquet** — hidden partitioning, time-travel, cheap deletes
3. **Two-tier processing** — Flink for fast path, Spark for heavy aggregations
4. **Bot filtering as a funnel** — signature → heuristic → ML
5. **Medallion architecture** — Bronze/Silver/Gold with clear contracts
6. **Multiple consumers** — same data, different SLAs, same storage
7. **Storage optimization** — Z-order, compaction, TTL by tier
8. **Cost story** — bot events in cheap tier; Bronze has aggressive TTL
