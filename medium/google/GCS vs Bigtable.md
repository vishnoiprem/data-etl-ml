# GCS vs Bigtable for Semi-Structured Data: Stop Choosing, Start Composing

### Why the smartest data architectures use both — with working code to prove it

*By a Head of AI & Data — lessons from running petabyte-scale retail data platforms*

---

One of the most common architectural debates I hear from data teams is some version of: *"Should we put our event data in Google Cloud Storage or Bigtable?"*

It's the wrong question. These two services are not competitors — they solve fundamentally different problems, and in any serious data platform, they live in the **same pipeline**. In this article I'll break down the core differences, show you exactly when each one wins, and walk through a **working end-to-end example**: JSON events landing in GCS, transformed, and served from Bigtable at millisecond latency.

---

## The Core Concept First

| Dimension | GCS (Google Cloud Storage) | Bigtable |
|---|---|---|
| **Type** | Object / blob store | NoSQL wide-column store |
| **Data format** | Files (JSON, Parquet, Avro, CSV) | Row-key based cells |
| **Access pattern** | Batch / sequential reads | Low-latency random reads |
| **Latency** | Seconds to minutes | Single-digit milliseconds |
| **Scale** | Effectively unlimited storage | Petabyte scale |
| **Cost** | Very cheap (~$0.02/GB/month standard) | Expensive (nodes + storage) |
| **Query** | Via Dataflow / Spark / BigQuery external tables | Direct key lookup, prefix scans |
| **Updates** | Overwrite entire object | Cell-level updates |

If you remember one line from this article, make it this:

> **"GCS is where data lives. Bigtable is where data serves."**

---

## When to Use GCS

GCS is your **landing zone** for raw semi-structured data:

- **Bronze layer** in a medallion architecture — cheap, durable, format-flexible
- Raw JSON events, logs, clickstream dumps, CDC files
- Batch processing input for Dataflow, Spark, or BigQuery external tables
- Long-term archival (Nearline / Coldline / Archive tiers)
- Anywhere you want **schema flexibility without upfront modeling**

In my own environment (Azure-based retail), the equivalent is **ADLS Gen2** — every raw ingestion from POS systems, e-commerce events, and supplier feeds lands there *first*, before any Delta Lake processing. The pattern is identical on GCP: land it raw, land it cheap, never lose it.

## When to Use Bigtable

Bigtable is your **serving layer** for semi-structured data with brutal latency requirements:

- High-throughput, low-latency key lookups (single-digit milliseconds)
- **Time-series data** — IoT sensor readings, clickstream, financial ticks
- **Real-time personalization** — fetching a user profile while the page renders
- Cell-level updates without rewriting entire records
- **ML feature stores** — serving fraud scores or recommendations online

> "Bigtable is purpose-built for when you need to look up a single customer's profile or event history in under 10ms — GCS simply can't do that."

And the inverse warning:

> "Bigtable without high-throughput reads is just an expensive file cabinet."

It has no secondary indexes, no SQL, and a 3-node production minimum. If your access pattern is batch, stay in GCS.

---

## The Architecture: They're Complementary

```
Raw events ──▶ GCS (bronze, cheap, durable)
                  │
                  ▼  Dataflow / Spark transform
        ┌─────────┴──────────┐
        ▼                    ▼
   BigQuery              Bigtable
 (batch analytics)   (real-time serving, <10ms)
```

The real architectural decision isn't GCS *or* Bigtable — it's **what sits between them**.

---

## Working Example: Retail Clickstream, End to End

Let's build the real thing. Scenario: an e-commerce platform emits JSON purchase events. We'll:

1. Land raw JSON events in GCS
2. Design a Bigtable schema with a hotspot-safe row key
3. Load events into Bigtable
4. Serve a customer's purchase history in milliseconds
5. (Bonus) Sketch the production Dataflow pipeline

### Setup

```bash
pip install google-cloud-storage google-cloud-bigtable apache-beam[gcp]

# Provision a dev Bigtable instance (1 node, dev tier)
gcloud bigtable instances create retail-serving \
  --display-name="Retail Serving" \
  --cluster-config=id=retail-c1,zone=asia-southeast1-a,nodes=1

# Bucket for raw events
gsutil mb -l asia-southeast1 gs://my-retail-bronze
```

### Step 1 — Land Raw JSON Events in GCS (Bronze)

```python
# ingest_to_gcs.py
import json
import uuid
from datetime import datetime, timezone
from google.cloud import storage

BUCKET = "my-retail-bronze"

def land_raw_events(events: list[dict]) -> str:
    """Write a batch of raw JSON events to GCS, partitioned by date.
    Newline-delimited JSON — BigQuery and Dataflow read it natively."""
    client = storage.Client()
    bucket = client.bucket(BUCKET)

    now = datetime.now(timezone.utc)
    # Hive-style partitioning: dt=YYYY-MM-DD/hour=HH
    blob_path = (
        f"clickstream/dt={now:%Y-%m-%d}/hour={now:%H}/"
        f"events-{uuid.uuid4().hex}.json"
    )

    payload = "\n".join(json.dumps(e) for e in events)
    bucket.blob(blob_path).upload_from_string(
        payload, content_type="application/json"
    )
    return f"gs://{BUCKET}/{blob_path}"


if __name__ == "__main__":
    sample_events = [
        {
            "event_id": "e-1001",
            "customer_id": "C12345",
            "event_type": "purchase",
            "sku": "SKU-998",
            "amount": 49.90,
            "ts": "2026-06-12T09:15:22Z",
            # semi-structured: nested, optional fields — GCS doesn't care
            "device": {"os": "iOS", "app_version": "5.2.1"},
        },
        {
            "event_id": "e-1002",
            "customer_id": "C67890",
            "event_type": "purchase",
            "sku": "SKU-101",
            "amount": 12.50,
            "ts": "2026-06-12T09:15:24Z",
        },
    ]
    print("Landed at:", land_raw_events(sample_events))
```

Notice what we *didn't* do: define a schema, normalize the nested `device` object, or worry about future fields. That flexibility is exactly why bronze lives in object storage.

### Step 2 — Design the Bigtable Row Key (This Is Everything)

> "The row key design in Bigtable is everything — get it wrong and you get hotspots that kill performance."

Bigtable stores rows sorted lexicographically by key and splits them across nodes by key range. Two classic mistakes:

- **Timestamp-first keys** (`2026-06-12T09:15#C12345`) → all writes hit one node. Hotspot. Dead cluster.
- **Plain sequential IDs** → same problem.

The correct pattern for "fetch a customer's recent events":

```
row key = customer_id # reversed_timestamp
e.g.      C12345#7740352477  (Long.MAX - epoch_seconds)
```

- Writes distribute across the keyspace (customer IDs are naturally spread)
- A **prefix scan on `C12345#`** returns that customer's events **newest-first** — exactly what a "recent purchases" API needs

### Step 3 — Load Events into Bigtable

```python
# load_to_bigtable.py
import datetime
import json
from google.cloud import bigtable
from google.cloud.bigtable import column_family, row_filters

PROJECT = "my-project"
INSTANCE = "retail-serving"
TABLE = "customer_events"
CF = "ev"  # short column family names save bytes at scale

MAX_TS = 9_999_999_999  # for reversed-timestamp keys


def get_table():
    client = bigtable.Client(project=PROJECT, admin=True)
    table = client.instance(INSTANCE).table(TABLE)
    if not table.exists():
        # Garbage-collect: keep only the latest cell version
        table.create(column_families={
            CF: column_family.MaxVersionsGCRule(1)
        })
    return table


def make_row_key(customer_id: str, ts_epoch: int) -> bytes:
    reversed_ts = MAX_TS - ts_epoch
    return f"{customer_id}#{reversed_ts:010d}".encode()


def write_events(events: list[dict]):
    table = get_table()
    rows = []
    for e in events:
        ts = int(datetime.datetime.fromisoformat(
            e["ts"].replace("Z", "+00:00")).timestamp())
        row = table.direct_row(make_row_key(e["customer_id"], ts))
        row.set_cell(CF, b"event_type", e["event_type"])
        row.set_cell(CF, b"sku", e.get("sku", ""))
        row.set_cell(CF, b"amount", str(e.get("amount", "")))
        # Keep the full raw payload too — schema evolution insurance
        row.set_cell(CF, b"raw", json.dumps(e))
        rows.append(row)
    results = table.mutate_rows(rows)
    failures = [r for r in results if r.code != 0]
    print(f"Wrote {len(rows) - len(failures)}/{len(rows)} rows")
```

Note the **cell-level update** model: tomorrow we can add a `fraud_score` column to existing rows without rewriting anything — impossible in GCS, where an update means rewriting the whole object.

### Step 4 — Serve Purchase History in Milliseconds

```python
# serve_from_bigtable.py
import time
from google.cloud.bigtable.row_set import RowSet
from load_to_bigtable import get_table, CF


def get_recent_events(customer_id: str, limit: int = 10) -> list[dict]:
    """Prefix scan: newest-first thanks to reversed timestamps."""
    table = get_table()
    row_set = RowSet()
    prefix = f"{customer_id}#".encode()
    row_set.add_row_range_with_prefix(prefix)

    results = []
    for row in table.read_rows(row_set=row_set, limit=limit):
        cells = row.cells[CF]
        results.append({
            "event_type": cells[b"event_type"][0].value.decode(),
            "sku": cells[b"sku"][0].value.decode(),
            "amount": cells[b"amount"][0].value.decode(),
        })
    return results


if __name__ == "__main__":
    t0 = time.perf_counter()
    history = get_recent_events("C12345")
    ms = (time.perf_counter() - t0) * 1000
    print(f"Fetched {len(history)} events in {ms:.1f} ms")
    # Typical warm-path result: 3–8 ms.
    # The same lookup against raw JSON in GCS: list objects,
    # download files, parse, filter — seconds, not milliseconds.
```

That latency difference — milliseconds vs seconds — is the entire reason Bigtable exists.

### Step 5 (Bonus) — The Production Bridge: Dataflow GCS → Bigtable

In production you don't run loader scripts; you run a pipeline. Here's the minimal Apache Beam job that reads the bronze layer and populates the serving layer:

```python
# pipeline_gcs_to_bigtable.py
import datetime, json
import apache_beam as beam
from apache_beam.io.gcp.bigtableio import WriteToBigTable
from google.cloud.bigtable import row as bt_row

MAX_TS = 9_999_999_999

def to_bigtable_row(line: str):
    e = json.loads(line)
    ts = int(datetime.datetime.fromisoformat(
        e["ts"].replace("Z", "+00:00")).timestamp())
    key = f"{e['customer_id']}#{MAX_TS - ts:010d}".encode()
    r = bt_row.DirectRow(row_key=key)
    r.set_cell("ev", b"event_type", e["event_type"].encode())
    r.set_cell("ev", b"raw", json.dumps(e).encode())
    return r

with beam.Pipeline() as p:
    (p
     | "ReadBronze" >> beam.io.ReadFromText(
           "gs://my-retail-bronze/clickstream/dt=2026-06-12/**/*.json")
     | "ToRows" >> beam.Map(to_bigtable_row)
     | "WriteServing" >> WriteToBigTable(
           project_id="my-project",
           instance_id="retail-serving",
           table_id="customer_events"))
```

Swap `ReadFromText` for `ReadFromPubSub` and this becomes a streaming pipeline — same serving layer, real-time freshness.

---

## The Mistakes I See Senior Teams Make

**1. Treating Bigtable as a general-purpose database.** No SQL, no secondary indexes, no joins. If you find yourself wanting `WHERE amount > 100`, you wanted BigQuery.

**2. Skipping GCS and writing straight to Bigtable.** Then the day you need to backfill, reprocess, or train an ML model on history, your only copy of the data is locked in a serving store that's expensive to scan. Bronze-first is non-negotiable.

**3. Timestamp-leading row keys.** Sequential writes hammer a single tablet. Always lead with a high-cardinality, well-distributed value (customer ID, hashed device ID, salted prefix).

**4. Ignoring the cost model.** GCS bills pennies per GB stored. Bigtable bills for *nodes running 24/7* plus storage. If your reads-per-second don't justify the nodes, you've built an expensive file cabinet.

---

## Azure Translation (For the Multi-Cloud Crowd)

| GCP | Azure Equivalent |
|---|---|
| GCS | ADLS Gen2 |
| Bigtable | Cosmos DB (or HBase on HDInsight) |
| BigQuery | Synapse Analytics / Fabric |
| Dataflow | Azure Data Factory / Databricks Spark |

The architecture pattern is cloud-agnostic: **cheap object store for landing, columnar warehouse for analytics, key-value store for serving.**

---

## The Decision Rule, In One Sentence

> **If your access pattern is batch, stay in GCS. If it's millisecond lookups by key, you need Bigtable. And in a real platform, raw data lands in the first and gets served from the second.**

---

*If this was useful, follow for more deep dives on data platform architecture, real-time serving patterns, and lessons from running enterprise-scale retail data systems.*
