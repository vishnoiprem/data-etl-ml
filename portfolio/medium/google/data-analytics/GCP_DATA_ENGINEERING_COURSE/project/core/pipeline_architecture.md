# Pipeline Architecture — Capstone Project Deep Dive
## GCP Data Engineering Course: Production-Grade Pipeline (Local Runner)

---

## 🎯 Pipeline Overview

This document provides the complete architecture, code walkthrough, and interview talking points for the capstone pipeline implemented in `pipeline_logic.py` and orchestrated via `local_runner.py`.

**What it demonstrates:** End-to-end data engineering on GCP — implemented in pure Python for zero-cost local execution, with 1:1 mapping to GCP services.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CAPSTONE PIPELINE ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐  │
│  │  RAW     │───▶│  INGEST &    │───▶│  NORMALIZE  │───▶│  AGGREGATE   │  │
│  │  EVENTS  │    │  VALIDATE    │    │  & ENRICH   │    │  BY REGION   │  │
│  │  (CSV)   │    │  (DLQ)       │    │  (Currency) │    │  (Partition) │  │
│  └──────────┘    └──────────────┘    └─────────────┘    └──────┬───────┘  │
│                                                                  │          │
│                          ┌─────────────────────────────────────┘          │
│                          ▼                                                │
│                   ┌──────────────┐    ┌─────────────┐    ┌────────────┐  │
│                   │   PUBLISH    │    │   WRITE     │    │  DEDUP     │  │
│                   │  TO TOPIC    │    │  PARTITION  │    │  (Idempotent)│ │
│                   │ (Pub/Sub)    │    │  (BigQuery) │    │  (Partition │  │
│                   └──────────────┘    └─────────────┘    │   + EventID)│ │
│                                                          └────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Stage-by-Stage Code Walkthrough

### Stage 1: Ingestion & Validation (`ingest_events`)

```python
def ingest_events(lines: Iterable[str]) -> tuple[list[dict], list[dict]]:
    """
    Parse CSV lines → validate each → return (accepted, rejected)
    
    Validation rules (reject reasons):
    - wrong_field_count: Not 7 fields
    - missing_event_id: Empty event_id
    - missing_user_id: Empty user_id
    - bad_timestamp: Unparseable timestamp
    - bad_amount: Unparseable amount
    - negative_amount: Amount < 0
    - unknown_event_type: Not in {purchase, refund, signup, page_view}
    - unknown_currency: Not in {EUR, USD, GBP}
    - unknown_channel: Not in {web, mobile, app, email}
    - unknown_region: Not in {AMER, EMEA, APAC, LATAM}
    """
```

**GCP Mapping:** `Pub/Sub subscription pull` → `Dataflow DoFn` validation

**Key Code Pattern:**
```python
# Deterministic validation — no external dependencies
accepted, rejected = [], []
for line in csv.reader(...):
    if len(fields) != 7:
        rejected.append({"reason": "wrong_field_count", "detail": "...", "raw": line})
        continue
    # ... field-level validation
    accepted.append(normalised_event)
```

**Interview Talking Point:** *"Validation is deterministic and side-effect free — same input always produces same accepted/rejected split. This enables exactly-once reprocessing."*

---

### Stage 2: Normalization & Enrichment (`normalise_event`)

```python
def normalise_event(raw: dict) -> dict:
    """
    Transform raw event → enriched event:
    - event_ts → event_dt (DATE partition key)
    - amount_eur = amount * FX_RATE[currency]  (FX rates: USD=0.92, GBP=1.17)
    - All fields typed, standardized
    """
```

**Currency Conversion Table (Hardcoded for Determinism):**
| Currency | Rate to EUR |
|----------|-------------|
| EUR      | 1.00        |
| USD      | 0.92        |
| GBP      | 1.17        |

**GCP Mapping:** `Dataflow Map` + `Side Input` (currency reference table from BigQuery)

**Interview Talking Point:** *"In production, FX rates come from a BigQuery reference table via side input — refreshed daily. Here it's hardcoded for deterministic test outputs."*

---

### Stage 3: Aggregation (`aggregate_events`)

```python
def aggregate_events(rows: Iterable[dict]) -> dict[str, dict]:
    """
    Group by region → sum(event_count), sum(revenue_eur)
    
    Returns: {region: {"event_count": N, "revenue_eur": X.XX}}
    """
```

**GCP Mapping:** `BigQuery SQL` with `GROUP BY region` OR `Dataflow CombinePerKey`

**Output Example:**
```csv
region,event_count,revenue_eur
AMER,1238,464848.02
APAC,1159,421049.85
EMEA,1176,432544.17
LATAM,1227,445554.36
```

---

### Stage 4: Publish to Topic (`publish_topic`)

```python
def publish_topic(rows, topic="events-normalised", attributes=None):
    """
    Build Pub/Sub message format:
    {
        "topic": "events-normalised",
        "data": <json-serialized-row>,
        "attributes": {
            "event_type": "...",
            "region": "..."
        }
    }
    """
```

**GCP Mapping:** `Pub/Sub Publish` — attributes enable subscriber filtering without decoding body

**Interview Talking Point:** *"Attributes carry routing metadata (event_type, region) so downstream subscribers can filter via subscription filter — no need to decode message body."*

---

### Stage 5: BigQuery Load (`write_partition`)

```python
def write_partition(rows, partition_date):
    """
    Filter rows for partition → deduplicate → return BigQuery-ready rows
    
    Partition key: event_dt (DATE) → partition decorator "20260115"
    Deduplication key: f"{partition}:{event_id}"  (deterministic!)
    """
```

**GCP Mapping:** `BigQuery Load Job` with `timePartitioning: {type: DAY, field: event_dt}`

**Idempotency Design:**
```python
def dedup_key(event_id: str, partition: str) -> str:
    """Deterministic identity — NEVER use load-time timestamp."""
    return f"{partition}:{event_id}"
```

**Interview Talking Point:** *"Deduplication key is derived from business data (event_id + partition), NOT processing time. This means retries produce identical keys — true exactly-once semantics."*

---

## 💰 Cost Model Deep Dive

### Running the Comparison
```bash
python local_runner.py --compare
```

**Output:**
```
| Architecture              | Monthly cost |
|---------------------------|--------------|
| Batch on BigQuery (partitioned) | $0.0625 |
| Batch on BigQuery (unpartitioned) | $6.2500 |
| Streaming on Dataflow     | $0.0000*    |
| Spark on Dataproc         | $0.0000*    |
```

### Why 100x Difference?
| Factor | Partitioned | Unpartitioned |
|--------|-------------|---------------|
| **Query Pattern** | `WHERE event_dt = '2026-01-15'` | Full table scan |
| **Bytes Scanned** | ~10 MB (1 day) | ~1 GB (all history) |
| **Cost @ $6.25/TB** | $0.06 | $6.25 |

**Interview Talking Point:** *"This is the single most impactful optimization in BigQuery. Partitioning on event_dt means daily queries scan only 1/365th of data. At 100TB scale: $625 vs $62,500 per query."*

---

## 🏃 Running the Pipeline

### Commands
```bash
# Full pipeline execution
python local_runner.py --run

# Cost estimate
python local_runner.py --cost

# Architecture comparison
python local_runner.py --compare

# List all commands
python local_runner.py --list
```

### Pipeline Output (Live Demo Ready)
```
organization: acme.example.com
└── folder: engineering
    └── project: GCP Data Engineering Course (gcp-de-course)
        ├── dataset: curated_us-central1  [BigQuery]
        ├── topic: events-us-central1  [Pub/Sub]
        ├── bucket: raw-events-us-central1  [Cloud Storage]
        └── serviceAccount: pipeline-sa@gcp-de-course.iam.gserviceaccount.com

▶ Running pipeline

  ingest: 4800 accepted, 0 rejected
  aggregate: 4 regions, 4800 events
  publish: 4800 messages to events-normalised
  load: partition 20260115, 4800 rows
  dedup: 4800 -> 4800 rows (0 duplicates removed)

Dead-letter path
----------------
  malformed rows rejected: 12
    wrong_field_count        2
    unknown_region           2
    bad_amount               1
    bad_timestamp            1
    missing_event_id         1
    missing_user_id          1
    negative_amount          1
    unknown_channel          1
    unknown_currency         1
    unknown_event_type       1
```

---

## 🎯 Interview Talking Points by Round

### Round 2: Technical Architecture
| Question | Your Answer Anchor |
|----------|-------------------|
| "Design batch pipeline GCS → Dataflow → BQ" | Walk through 5 stages above, draw architecture |
| "How handle late data / duplicates?" | `allowed_lateness`, watermarks, deterministic `dedup_key` |
| "BigQuery optimization?" | Partition pruning (100x), clustering (colocate), materialized views |
| "Exactly-once semantics?" | `dedup_key = partition:event_id` — derived from data, not time |

### Round 3: Case Study
| Scenario | Your Response |
|----------|---------------|
| "Client has 100TB, 500 pipelines, needs migration" | This pipeline IS the migration factory pattern — Terraform-deployable, parameterized |
| "DLQ handling?" | Categorized rejection reasons, alert on `reject_counts`, replay from raw |
| "Cost control?" | `local_runner.py --compare` shows partitioned vs unpartitioned impact |

### Round 4: Presentation
| Artifact | What to Show |
|----------|--------------|
| Architecture diagram | 5-stage pipeline with GCP service mapping |
| Code snippet | `dedup_key` function — exactly-once in 3 lines |
| Cost comparison | Partitioned vs unpartitioned table |

### Round 5: Cognitive
| Question | Your Angle |
|----------|------------|
| "Skeptical CIO: GCP costs 3x on-prem" | Show `--compare` output: partitioning = 100x savings, CUDs = 40% more |
| "Sales promised 3 months, team says 6" | Pilot in 4 weeks proves scope → fixed-fee milestones |

---

## 🔧 Production Hardening (What You'd Add for Real Deployment)

| Concern | Current (Demo) | Production |
|---------|----------------|------------|
| **FX Rates** | Hardcoded dict | BigQuery reference table + side input refresh |
| **Schema Evolution** | Fixed fields | Avro/Protobuf + Schema Registry |
| **Monitoring** | Print statements | Cloud Monitoring: freshness, row counts, DLQ rate |
| **Alerting** | None | `reject_counts` by reason → PagerDuty |
| **Backfill** | Manual | Partition-level replay with `MERGE` not `APPEND` |
| **Secrets** | None | Secret Manager for API keys, CMEK for data |
| **CI/CD** | None | Cloud Build → Dataflow Flex Templates → Composer DAGs |

---

## 📋 One-Page Interview Cheat Sheet

```
PIPELINE: GCS (CSV) → Dataflow (Validate→Normalize→Aggregate) → Pub/Sub → BigQuery (Partitioned)
KEY INNOVATIONS:
  ✅ Deterministic validation (reproducible DLQ)
  ✅ Partition key = event_dt (DATE) — 100x query savings
  ✅ Dedup key = partition:event_id — exactly-once, retry-safe
  ✅ Currency enrichment via side input pattern
  ✅ DLQ categorized by reason — alertable, replayable
  ✅ Cost model: partitioned vs unpartitioned = 100x difference

GCP SERVICE MAP:
  ingest_events        → Pub/Sub pull / Dataflow DoFn
  validate_event       → Dataflow DoFn / Dataproc map
  normalise_event      → Dataflow Map + Side Input (FX table)
  aggregate_events     → BigQuery SQL / Dataflow CombinePerKey
  publish_topic        → Pub/Sub Publish (with attributes)
  write_partition      → BigQuery Load Job (timePartitioning: DAY)
  deduplicate          → MERGE on dedup_key (production)

RUN IT LIVE: python local_runner.py --run --compare --cost
```

---

*This pipeline is your **live demo** for Round 2, 3, 4. Run it in any interview — no GCP account, no credentials, zero cost. It proves you can build production-grade data engineering that maps 1:1 to GCP.*