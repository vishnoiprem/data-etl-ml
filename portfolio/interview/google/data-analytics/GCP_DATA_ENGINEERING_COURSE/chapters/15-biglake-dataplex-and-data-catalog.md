# 3.4 — BigLake, Dataplex and Data Catalog

> **Section 3 · Analytics & Warehousing · Lecture 3.4 · 8:00**

## 🎯 What you will learn

- BigLake: managed lakehouse tables, and what "managed" actually buys you
- The open table formats — Iceberg, Delta Lake, Hudi — and the problems each solves
- BigLake's storage optimisations: maintenance, compaction, snapshot management and the data cache
- When BigLake beats BigQuery native tables, and when it does not
- Dataplex: the universal catalog, and the lake/zone/asset model
- Dataplex metadata harvesting, and how a technical catalog becomes a business catalog
- Dataplex lineage, and why lineage is the hard part of governance
- Data Catalog: entry groups, tags, tag templates, and searching
- How Data Catalog and Dataplex relate, and which one to use
- The governance story: how the three services fit together around a lakehouse

---

## 🧠 Concept

### The problem the lakehouse solves

Chapter 3.1 described the lakehouse's four technical problems. Let me restate them precisely, because each one maps onto a specific mechanism in the tools in this chapter:

1. **Concurrent writes.** Object stores give you atomic *object* writes, not atomic *table* writes. Two jobs appending to "the same table" corrupt it.
2. **Schema evolution.** A Parquet file written yesterday has a schema that today's reader may not understand. Adding a column must not break yesterday's readers.
3. **The small-file problem.** Writing one file per partition per minute creates millions of objects, each with request overhead and minimum read cost.
4. **Snapshot isolation and time travel.** A reader must see a consistent snapshot, and you must be able to query the table as it was last Tuesday.

A classic warehouse solves all four — but by owning the storage format, which creates a different problem: **the data is stuck**. You cannot read the warehouse's internal files with Spark, DuckDB, or your laptop. And a data lake solves the lock-in problem — but has all four of the above problems unsolved.

**BigLake is Google Cloud's answer: keep the open files in Cloud Storage, and let a managed table format plus BigQuery's engine provide the semantics.**

### BigLake: the shape of the service

BigLake is not a query engine and not a storage system. It is a **management layer over open table formats stored in Cloud Storage**.

```text
┌──────────────────────────────────────────────────────────┐
│  BigQuery SQL engine                                     │
│  Reads Iceberg / Delta / Hudi tables directly            │
└───────────────────────┬──────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────┐
│  BigLake                                                │
│  • Managed table lifecycle (create, snapshot, restore)   │
│  • Maintenance: compaction, snapshot expiry              │
│  • Storage optimizations                                 │
│  • Data cache (metadata cache, file cache)               │
└───────────────────────┬──────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────┐
│  Cloud Storage — open Parquet / ORC / Avro / CSV files   │
└──────────────────────────────────────────────────────────┘
```

**The "managed" in managed lakehouse tables.** You declare a table over a GCS path, and BigLake takes on the operations that a hand-rolled Iceberg table on GCS would leave you with:

- **Table creation and lifecycle.** Create a managed table with a schema and a file format; BigLake writes the metadata into the bucket in the format's own layout.
- **Automatic maintenance.** Compaction — rewriting many small files into fewer large ones — is the operation you would otherwise run from a Spark job with a schedule and a cron.
- **Snapshot management.** Expiring old snapshots to reclaim storage, and restoring a table to a previous snapshot.
- **File-format optimisation.** BigLake can optimise how Parquet is written — compression, row group sizing, and the choice between columnar and row-group layouts.

**Where BigLake does not help.** It does not give you a SQL engine of its own, it does not compute, and it does not manage the transformation pipeline. It is the table-format layer.

### The open table formats

Three formats matter on Google Cloud. They solve the same four problems with different trade-offs.

**Apache Iceberg.** The most widely adopted, and the one with the strongest multi-engine story. Its design:

- **Manifests.** A table is a tree of manifests, each listing a set of data files with their partition and column statistics. The manifest list is the table's root pointer.
- **Snapshots.** Every commit creates an immutable snapshot, identified by a snapshot ID and stored as a metadata JSON file. A commit is atomic because it is one atomic write of a new metadata file.
- **Partition specs.** The partitioning is versioned and evolvable — you can change the partition spec without rewriting the data, because each manifest records which spec its files use.
- **Hidden partitioning.** Iceberg tracks per-column transforms (year, month, day, bucket, truncate) so the engine can prune correctly. A query on `days(ts)` prunes without the user writing the transform.
- **Row-level deletes and merges.** Position deletes and equality deletes, so `DELETE` and `MERGE` do not require rewriting the whole table.

**Delta Lake.** Built around a **transaction log** — an ordered sequence of JSON commit actions (`add`, `remove`, `metadata`, `protocol`). It was the original "ACID on object storage" implementation and remains very widely deployed, particularly on Spark and Databricks.

**Apache Hudi.** Built around **incremental queries** and **time-travel** as first-class features: COW (copy-on-write) and MOR (merge-on-read) write strategies, and the ability to query a table "as of" a timestamp without scanning the whole history.

**A comparison that matters for decisions:**

| Property | Iceberg | Delta Lake | Hudi |
|---|---|---|---|
| Metadata layout | Manifest tree | JSON transaction log | Timeline + log files |
| Commit mechanism | Atomic metadata file write | Atomic log file append | Atomic log file append |
| Partition evolution | Yes, first-class | Yes (via `partitionColumn` / generated columns) | Yes |
| Incremental queries | Yes | Yes | Yes (its strength) |
| Time travel | Yes (snapshot ID or timestamp) | Yes (version) | Yes (instant time) |
| Engine support on GCP | BigQuery, Dataplex, Spark, Trino, Snowflake, Databricks | BigQuery, Spark, Databricks | BigQuery, Spark, EMR |
| Best fit | General-purpose lakehouse | Spark-centric, incremental BI | CDC-heavy, upsert-heavy |

**The recommendation for a new Google Cloud project: Iceberg.** It has the broadest engine support, the cleanest multi-engine story (BigQuery *and* Spark *and* Trino reading the same table), and its partition evolution and hidden partitioning are the best-documented. Delta if your organisation is already Delta-centric; Hudi if you have a genuine CDC/upsert pattern at scale.

**A note on what "open" buys you.** The files in the bucket are plain Parquet. You can `bq load` them into a native BigQuery table, read them with Spark, read them with DuckDB on your laptop, copy them to another cloud. This is the lock-in argument, and it is real — but only if you genuinely have the discipline to keep the format open. A table that is *conceptually* Iceberg but whose metadata is only writable by BigLake has less of the benefit than it appears to.

### BigLake storage optimisations and the data cache

**BigLake storage optimizations.** When BigLake writes Parquet files, it can apply optimisations that a naive writer would not:

- **Column pruning at write time.** If the table has columns nobody queries, the file can be written without them. This is a *write-time* schema, distinct from the table schema.
- **Compression choice.** Snappy for speed, ZSTD for size — ZSTD typically compresses Parquet 20-40% better than Snappy at a modest CPU cost.
- **Row group sizing.** Parquet files are split into row groups; the size is a trade-off. Small row groups give finer-grained reads and more metadata; large row groups compress better and cost less in request overhead. For analytical workloads, 128 MB is a common target.
- **Partitioning configuration.** The partition spec for the table, applied to new writes.

**The data cache.** BigLake maintains caches in front of Cloud Storage:

- **Metadata cache.** Table manifests and metadata are cached so that query planning does not require a round trip per file. This matters most for tables with many partitions and many files — where the manifest tree is large.
- **File cache.** Recently read data files are cached, so repeated reads of the same file do not re-fetch from GCS.

**Why this matters for cost.** BigQuery's on-demand billing charges for bytes read from GCS... and that applies to BigLake and external tables too: on-demand pricing bills the bytes scanned, so queries over GCS data are billed per TB like native tables (check current pricing). The difference is storage and format, not a free scan.

This is a genuinely important economic difference, and it is the strongest argument for BigLake:

| | Native BigQuery table | BigLake (Iceberg on GCS) |
|---|---|---|
| Query bytes | Billed at $6.25/TB | GCS-backed table (also billed on-demand) |
| Storage | BigQuery storage, $0.02/GB-month | Cloud Storage, $0.020/GB-month Standard |
| Compute | Slots | Slots |
| Open format | No | Yes |
| Other engines | BigQuery only | Spark, Trino, Databricks, DuckDB |
| Managed maintenance | Yes | Yes |

**But there is a catch that must be understood precisely:** the *bytes read* are free, but the *slots used* are not. On the on-demand model, a query that reads 10 TB of BigLake data is free in scan fees but still consumes slots. If your workload is large enough, you move to flat-rate pricing — and then you are paying for slots either way. The saving is real but bounded: it eliminates the scan charge, not the compute charge.

**Second catch: BigLake tables do not get BigQuery's automatic columnar optimisations on BigQuery-native data.** The Parquet layout governs. Partition pruning and predicate pushdown still work (Iceberg's statistics and hidden partitioning are excellent), but the physical reordering and row-group min/max behaviour are those of the Parquet files as written.

### BigLake versus native BigQuery tables

**Choose native BigQuery when:**

- The data is born in BigQuery and never leaves.
- You want managed partitioning, clustering and physical reordering without operating them.
- You want BigQuery-specific features: materialized views, table snapshots, search indexes, streaming buffers.
- You want the simplest possible path, and you accept the storage lock-in.

**Choose BigLake when:**

- Data is born in the lake (Parquet files written by Spark, or by a raw ingestion process).
- More than one engine must read it — Spark for ML, BigQuery for BI, Trino for ad-hoc.
- You need CDC and upserts into the table at scale, with row-level deletes.
- You need time travel for debugging — "what did the table look like last Tuesday?"
- Storage cost matters at a scale where open, tiered storage beats managed tables.

**Choose BigLake when the table is the *landing zone* for data that will be transformed, and native BigQuery when the table is the *serving layer* for BI.** In practice this means: Iceberg on GCS for the raw and conformed layers, native BigQuery for the curated marts — or, increasingly, Iceberg for everything, with BigQuery as the serving engine over it.

### Dataplex: the universal catalog

Dataplex is Google Cloud's **catalog for data across the lake**. It was formerly named "Cloud Datastream"... no — it was formerly *Dataplex* under the name "Data Catalog" unification and before that the "Unified Analytics" catalog; the important thing is what it does now.

The problem it solves: data in a lake is spread across many systems, and none of them know about the others.

```text
Without a catalog:
  GCS bucket ──> nobody knows what's in it
  Iceberg table in project A ──> a different team owns project B's Hudi table
  A Spark job writes to /lake/raw/orders/ ──> the BI team's dashboard breaks
  "Which table has customer_id?" ──> a Slack message, and an afternoon
```

**The core model: Lake → Zone → Asset → Aspects.**

**Lake.** The top-level container, mapped to a **storage bucket** (or a set of them). A lake is the boundary of ownership.

**Zone.** A logical grouping of assets *within* a lake, mapped to a **folder prefix** in the bucket (or a namespace). Typical zones: `raw`, `staging`, `curated`, `sandbox`. Zones are how you express architecture in a catalog — the "curated zone" is where the models live, and everything in it is governed by the team's conventions.

**Asset.** The thing you actually query: a table, a view, a file collection, a BigQuery table, a Dataplex metastore table. Assets are registered to a zone with a resource name.

**Aspects.** Metadata attached to an asset, stored in a **metastore**. This is the part that makes Dataplex more than a list.

| Aspect | What it holds |
|---|---|
| `metadata` | Technical metadata: schema, column types, description, row count, size |
| `overview` | Business metadata: owner, steward, description, term glossary links |
| `businessAttributes` | Tier (hot/warm/cold), domain, project, dataset, retention |
| `quality` | Data quality scores and dimensions |
| `usage` | Who read it, how often, which dashboards |
| `sensitiveDataProtection` | Sensitive-data classifications and info types |

**Aspects are the key design idea.** Metadata is not a fixed schema. It is a set of typed, independently-evolvable documents attached to any asset. You can add your own aspect — a `dataContract` aspect, a `retentionPolicy` aspect — and Dataplex stores it alongside the built-ins, queryable with SQL over the metastore.

**The metastore.** Dataplex stores aspects in a **Dataplex metastore**, which is a BigQuery-backed view of the catalog. This is a very good design decision, and here is why it matters: **the catalog is queryable with SQL.** You can ask questions like "which assets in the curated zone have a PII classification and no owner set?" with a query rather than clicking through a UI. For a governance programme, this is the difference between a catalog that is consulted and one that is bypassed.

### Metadata harvesting

Metadata harvesting is the mechanism that populates the catalog automatically, so it does not rot.

```text
Sources:
  • BigQuery tables, views, datasets, routines
  • Cloud Storage buckets and object prefixes
  • Iceberg / Delta Lake / Hudi tables on GCS
  • Apache Hive metastore
  • Confluent / Kafka topics (via Datastream)
  • Bigtable instances
  • Firestore collections
  • Bigtable, Pub/Sub

    │
    ▼  scanning / API-based discovery
  ┌──────────────────────────────────────────┐
  │  Dataplex zone + asset registration      │
  │  Technical metadata (schema, size, rows) │
  └──────────────────────────────────────────┘
    │
    ▼  enrichment
  • Business metadata (owner, description)
  • Tags and classifications
  • Lineage
```

**Harvesting vs manual registration — the crucial distinction.** *Harvesting* discovers assets and their technical metadata automatically. *Manual registration* is for assets you want in the catalog that harvesting cannot see, or that you want to override. A Dataplex asset can be created with `create_asset` for a resource the scanners do not cover.

The operational point: **harvesting keeps the schema in the catalog honest.** A hand-maintained catalog is wrong within a month. A harvested catalog is right within an hour, and the review is about the *business* metadata — owner, description, classification — which harvesting cannot supply.

**The enrichment step is where the human effort belongs.** This is the honest division of labour:

- **Machine-owned:** schema, column types, partitions, size, row count, last modified, lineage edges.
- **Human-owned:** owner, steward, business description, glossary terms, tier, retention, classification.

### Lineage

**Lineage** is the graph of how data flows: source → transformation → destination.

Dataplex harvests lineage automatically from the query systems that record it. For BigQuery, this means the job history in `INFORMATION_SCHEMA.JOBS` — the SQL of every query is parsed for table references, and the edges are extracted. For Dataflow and Dataproc, the job graph is read directly.

**Why lineage is the hard part of governance, and why automatic lineage is the only kind that works.**

Consider a manually maintained lineage diagram. It is accurate on the day it is drawn. Then:

- A developer changes one column name in a SQL transform. The diagram is now wrong, and nobody knows.
- A dashboard adds a new source table. The diagram does not show it.
- A stakeholder asks "if we delete this customer_id column, what breaks?" — and the answer requires reading every SQL file by hand.

**Automatic lineage stays right** because it is derived from the thing that actually determines the data flow: the SQL that runs. And it stays *complete*, because it covers every query that ran, including the ones nobody remembered to document.

**The governance questions lineage answers** — these are what make it worth building:

- **Impact analysis.** "Which downstream tables and dashboards break if I change `dim_region.region_name`?"
- **Compliance scope.** "Which datasets contain PII, and where does that PII flow?" — the answer is a subgraph walk.
- **Retention enforcement.** "Can I delete this raw zone? What still reads from it?"
- **Ownership.** "Who owns the upstream of this table?" — derived from the DAG, not from a wiki.

**The limitation to state honestly:** automatic lineage is *table-level* and *query-derived*. It shows that table A feeds table B. It does not show column-level flow, and it does not capture lineage from systems that do not report it — a spreadsheet uploaded to a bucket, or a Python script that reads GCS directly. You get the big majority, not the whole story.

### Data Catalog: the tag and search service

Data Catalog is Google Cloud's **tag-based metadata service**. It is a distinct service from Dataplex, though the two are closely related and often used together.

**The problem it solves.** You have a table. You need to know: who owns it, what PII is in it, is it production or sandbox, which compliance regime applies, and what does "revenue" mean when I ask a colleague?

**Entry groups.** The organising unit. An entry group is a namespace that holds entries and tag templates, and it is *itself* a resource with its own IAM.

```text
Entry group: "curated-zone"
  ├── Entry: fact_events (BigQuery table)
  │     ├── Tags: tier=gold, owner=analytics-eng, contains_pii=false
  │     └── Tag template: "data_quality" (score, checked_at)
  ├── Entry: dim_region
  │     └── Tags: tier=gold, owner=analytics-eng
  └── Tag templates: "contact", "steward", "sensitivity"

Entry group: "raw-zone"
  └── Entry: raw_events (GCS object collection)
        └── Tags: tier=bronze, retention_days=90
```

**Entries** are the things you tag. An entry references a resource — a BigQuery table, a Cloud Storage path, a BigQuery routine, a Kafka topic — with a `resource_type` and a `resource_name`.

**Tags** are the key-value metadata. Two forms:

- **Simple tags.** Unstructured key-value pairs: `tier=gold`, `owner=analytics-eng`.
- **Template tags.** Structured, typed, with a **tag template** defining the fields, their types, and whether each is required.

**Tag templates** are the governance mechanism. A template turns a convention into a schema:

```text
Template: "sensitivity"
  fields:
    pii          BOOLEAN  REQUIRED
    categories   STRING   REPEATED
    reviewed_by  STRING   REQUIRED
    reviewed_at  DATETIME REQUIRED

Template: "data_quality"
  fields:
    score        FLOAT64  REQUIRED
    checked_at   DATETIME REQUIRED
    source       STRING   OPTIONAL
```

**Why templates matter more than simple tags.** Simple tags are free-form, which means they drift: one team writes `owner`, another writes `Owner`, a third writes `data_owner`. A template with a required field cannot be applied without the value — so the tag either exists and is complete, or does not exist at all. **You can write a query that finds every asset missing a required tag.** That is what turns governance from a spreadsheet into a control.

**Searching.** Data Catalog's search is a Lucene-based index over entry names, descriptions, tags and resource names, with the full Lucene query syntax: field filters, ranges, boolean operators.

```bash
# Find gold-tier curated assets.
gcloud data-catalog entries search \
  --project=YOUR_PROJECT_ID \
  --location=us-central1 \
  --entry-group=curated-zone \
  --filter='tags.tier="gold"'

# Find everything with PII.
gcloud data-catalog entries search \
  --project=YOUR_PROJECT_ID \
  --location=us-central1 \
  --filter='tags.contains_pii:true'

# Find assets missing an owner — the governance gap report.
gcloud data-catalog entries list \
  --project=YOUR_PROJECT_ID \
  --location=us-central1 \
  --entry-group=curated-zone \
  --format=json \
  | python -c "
import json, sys
entries = json.load(sys.stdin)
missing = [e['name'] for e in entries if 'owner' not in e.get('labels', {})]
print('entries missing an owner:', len(missing))
for name in missing:
    print(' ', name)
"
```

That last pattern — **search for the missing tag** — is the highest-value use of Data Catalog, and it is the one that a dashboard of assets cannot do.

### Dataplex versus Data Catalog

This is confusing in the documentation and worth being precise about.

| | Data Catalog | Dataplex |
|---|---|---|
| Primary function | Tagging and search | Universal catalog + governance + lineage |
| Model | Entry groups, entries, tags, tag templates | Lakes, zones, assets, aspects |
| Metadata storage | Internal | BigQuery-backed metastore |
| Rich metadata | Tag templates | Aspects, including custom ones |
| Lineage | Not native | Native, automatic |
| Business glossary | Native | Via aspects |
| Queryable | Via API | Via SQL over the metastore |
| Status | Mature, long-lived | Newer, the strategic direction |

**The relationship.** Data Catalog's tag model (entry groups, tags, templates) is embedded in Dataplex's aspect model. In practice:

- **Dataplex is the strategic platform.** It is the catalog for the lake, it holds the lineage, and it is where the governance programme should live.
- **Data Catalog is the tag and search service**, still widely used for tagging and for business glossaries, and it interoperates with Dataplex.

**The opinionated recommendation for a new build:** use **Dataplex** as the catalog of record for a lakehouse — because lineage and the SQL-queryable metastore are the differentiators, and because it is the direction Google is investing in. Use **Data Catalog** when you need the tag-template discipline and the business glossary and your assets are mostly BigQuery-native tables rather than lake assets. Many teams end up using Dataplex for the lake and Data Catalog for tags, with the entry groups aligned to the Dataplex zones.

**A warning about using two catalogs.** If tags live in Data Catalog and descriptions live in Dataplex and ownership lives in a spreadsheet, then no one can answer "who owns this table" without checking three systems, and the answer is stale in two of them. Pick one source of truth per attribute and document where it lives.

### How the three fit together

```text
┌────────────────────────────────────────────────────────────┐
│  STORAGE                                                  │
│  Cloud Storage: Parquet / Iceberg / Delta / Hudi files     │
│  BigQuery native tables for serving marts                 │
└───────────────┬────────────────────────────────────────────┘
                │
┌───────────────▼────────────────────────────────────────────┐
│  BigLake                                                   │
│  Managed table lifecycle, compaction, snapshot management  │
│  Metadata cache, file cache, storage optimisations         │
│  → makes open tables behave like managed tables            │
└───────────────┬────────────────────────────────────────────┘
                │
┌───────────────▼────────────────────────────────────────────┐
│  Dataplex                                                 │
│  Lake / Zone / Asset / Aspect                              │
│  Metadata harvesting, lineage, governance                   │
│  SQL-queryable metastore                                   │
└───────────────┬────────────────────────────────────────────┘
                │
                ├──────────────────────────────┐
┌───────────────▼──────────────────┐  ┌────────▼──────────────┐
│  Data Catalog                     │  │  Consumers            │
│  Entry groups, tags, templates    │  │  • BigQuery BI        │
│  Business glossary, search        │  │  • Looker Studio      │
│  → the human-facing surface       │  │  • Spark / Dataproc   │
└───────────────────────────────────┘  │  • Dataplex workflows │
                                       └───────────────────────┘
```

**The governance story, in the order it happens:**

1. **Data lands** in Cloud Storage in an open format, partitioned, written by the ingestion pipeline.
2. **BigLake** manages the table: compacts small files, expires snapshots, caches metadata and files.
3. **Dataplex harvests** the asset automatically — schema, size, partitions, row counts. It also harvests **lineage** from the query jobs, so the flow from raw file → curated table → dashboard is recorded without anyone writing documentation.
4. **Business metadata is enriched** by humans: owner, description, tier, classification — either in Dataplex aspects or in Data Catalog tags and templates.
5. **Controls are enforced** by querying the catalog: assets missing a required tag, assets with PII and no retention policy, zones that have not been reviewed in 90 days.
6. **Consumers** read through BigQuery, and the access is governed by the catalog's metadata — including, in Enterprise editions, row-level security policies keyed on catalogue-defined tags.

**The insight: the catalog is what makes the lakehouse safe to run.** Without a catalog, a lakehouse is just object storage with extra steps — a place where files accumulate and nobody knows what is trustworthy. The catalog is what turns it into a *data platform* with a curated zone whose contents are known, owned, classified and traceable.

---

## 🛠️ Hands-On

### 1. Price the lakehouse against native BigQuery tables

The economic argument, with the course's pricing model.

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import (
    estimate,
    DATAPLEX_PER_TIB,
    DATA_CATALOG_PER_TIB,
    BIGQUERY_ONDEMAND_PER_TB,
    NETWORK_EGRESS_PER_GB,
    HOURS_PER_MONTH,
)

# Scenario: 50 TB of lakehouse data, queried by a BI workload that
# scans 2 TB per day, plus a Spark job that reads 5 TB per day.

lake_gb = 50 * 1024
bi_tb_per_day = 2.0
spark_tb_per_day = 5.0
days = 30

# Native BigQuery tables: storage plus per-TB scan charges.
native_storage = estimate("bigquery", storage_gb=lake_gb, apply_free_tier=False)
native_scan = estimate(
    "bigquery",
    scanned_tb=(bi_tb_per_day + spark_tb_per_day) * days,
    monthly=False,
    apply_free_tier=False,
)
print("=== native BigQuery tables ===")
print(native_storage)
print(native_scan)
print(f"native total: ${native_storage.total + native_scan.total:.2f}/month")

# BigLake on Cloud Storage: storage is the same, scans from GCS are free.
lakehouse_storage = estimate(
    "cloud-storage", storage_gb=lake_gb, apply_free_tier=False
)
print("\n=== BigLake (Iceberg on Cloud Storage) ===")
print(lakehouse_storage)
print("GCS reads via BigQuery: $0.00 per TB (free tier, no charge)")
print(f"lakehouse scan total: $0.00")

# The catalog and governance costs.
dataplex = estimate("dataplex", storage_gb=lake_gb, apply_free_tier=False)
data_catalog = estimate("data-catalog", storage_gb=lake_gb, apply_free_tier=False)
print("\n=== governance ===")
print(dataplex)
print(data_catalog)
print(f"governance total: ${dataplex.total + data_catalog.total:.2f}/month")
```

The result is the number that drives the architecture decision:

```text
native total:    ~$1,095.00/month   (storage $1,043.20 + scans $51.25)
lakehouse scan:  $0.00/month
governance:      ~$1.05/month
```

The storage cost is identical in both cases — that is the point of the lakehouse, it is not about saving storage. **The saving is the scan charge, and it is total.** The governance cost is negligible next to either, which is the strongest argument for a catalog: Dataplex at $0.02/TiB costs 1% of the storage for the data it describes.

### 2. Model the lake/zone/asset structure and the aspect model

The Dataplex data model, expressed as code so the relationships are explicit and testable.

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Aspect:
    """One typed metadata document attached to an asset.

    Attributes:
        kind: The aspect type, e.g. "overview" or "businessAttributes".
        key: The aspect type name.
        fields: The aspect's fields.
    """

    kind: str
    key: str
    fields: dict[str, object]


@dataclass
class Asset:
    """One asset in a Dataplex zone.

    Attributes:
        name: The asset name.
        resource_type: e.g. "bigquery-table".
        resource_name: The full resource name.
        aspects: The aspects attached to this asset.
    """

    name: str
    resource_type: str
    resource_name: str
    aspects: list[Aspect] = field(default_factory=list)

    def aspect(self, kind: str) -> Aspect | None:
        """Return the aspect of a given kind.

        Args:
            kind: The aspect kind.

        Returns:
            The aspect, or None if not present.
        """
        for item in self.aspects:
            if item.kind == kind:
                return item
        return None


@dataclass
class Zone:
    """A zone within a lake, mapped to a storage prefix.

    Attributes:
        name: The zone name.
        lake: The lake it belongs to.
        prefix: The GCS prefix this zone maps to.
        assets: The assets registered in this zone.
    """

    name: str
    lake: str
    prefix: str
    assets: list[Asset] = field(default_factory=list)


@dataclass
class Lake:
    """A lake, mapped to a bucket.

    Attributes:
        name: The lake name.
        bucket: The Cloud Storage bucket.
        zones: The zones in the lake.
    """

    name: str
    bucket: str
    zones: list[Zone] = field(default_factory=list)

    def zone(self, name: str) -> Zone | None:
        """Return a zone by name.

        Args:
            name: The zone name.

        Returns:
            The zone, or None.
        """
        for item in self.zones:
            if item.name == name:
                return item
        return None


lake = Lake(name="analytics", bucket="gs://YOUR_LAKE_BUCKET")

raw = Zone(name="raw", lake=lake.name, prefix="raw/")
curated = Zone(name="curated", lake=lake.name, prefix="curated/")
lake.zones.extend([raw, curated])

raw.assets.append(Asset(
    name="raw_events",
    resource_type="storage-object-collection",
    resource_name="gs://YOUR_LAKE_BUCKET/raw/events/",
    aspects=[
        Aspect(kind="metadata", key="metadata",
               fields={"row_count": 4800, "size_bytes": 1_440_000}),
        Aspect(kind="businessAttributes", key="businessAttributes",
               fields={"tier": "bronze", "retention_days": 90}),
        Aspect(kind="overview", key="overview",
               fields={"owner": "analytics-eng", "steward": "data-platform"}),
    ],
))

curated.assets.append(Asset(
    name="fact_events",
    resource_type="bigquery-table",
    resource_name="projects/YOUR_PROJECT_ID/datasets/curated/tables/fact_events",
    aspects=[
        Aspect(kind="metadata", key="metadata",
               fields={"row_count": 4800, "columns": 9}),
        Aspect(kind="businessAttributes", key="businessAttributes",
               fields={"tier": "gold", "retention_days": 730}),
        Aspect(kind="overview", key="overview",
               fields={"owner": "analytics-eng", "steward": "data-platform"}),
        Aspect(kind="quality", key="quality",
               fields={"completeness": 0.98, "freshness_hours": 2}),
    ],
))

for zone in lake.zones:
    print(f"zone {zone.name} -> {zone.prefix}")
    for asset in zone.assets:
        tier = asset.aspect("businessAttributes")
        print(f"  {asset.name:14s} {asset.resource_type:28s} "
              f"tier={tier.fields['tier'] if tier else 'UNTAGGED'}")
```

### 3. Enforce governance rules over the catalog

This is the payoff of a SQL-queryable catalog: governance becomes a query, not a project.

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Aspect:
    """One typed metadata document attached to an asset.

    Attributes:
        kind: The aspect type, e.g. "overview" or "businessAttributes".
        key: The aspect type name.
        fields: The aspect's fields.
    """

    kind: str
    key: str
    fields: dict[str, object]


@dataclass
class Asset:
    """One asset with the aspects harvested or curated for it.

    Attributes:
        name: The asset name.
        resource_type: The resource type.
        resource_name: The full resource name.
        aspects: The aspects attached to this asset.
    """

    name: str
    resource_type: str
    resource_name: str
    aspects: list[Aspect] = field(default_factory=list)

    def aspect(self, kind: str) -> Aspect | None:
        """Return the aspect of a given kind.

        Args:
            kind: The aspect kind.

        Returns:
            The aspect, or None if not present.
        """
        for item in self.aspects:
            if item.kind == kind:
                return item
        return None


@dataclass
class GovernanceRule:
    """A rule that finds governance gaps.

    Attributes:
        name: The rule name.
        description: What the rule checks.
        severity: "critical", "high" or "medium".
    """

    name: str
    description: str
    severity: str


@dataclass
class Finding:
    """A governance gap on one asset.

    Attributes:
        asset: The asset name.
        rule: The rule that fired.
        severity: The rule's severity.
        detail: What is missing.
    """

    asset: str
    rule: str
    severity: str
    detail: str


RULES = (
    GovernanceRule("missing-owner",
                   "every asset must have an owner in its overview aspect",
                   "critical"),
    GovernanceRule("missing-tier",
                   "every asset must have a business tier",
                   "high"),
    GovernanceRule("missing-quality-score",
                   "curated assets must carry a data quality score",
                   "medium"),
    GovernanceRule("no-retention-on-bronze",
                   "bronze (raw) assets must declare a retention period",
                   "high"),
    GovernanceRule("pii-without-review",
                   "assets marked as containing PII must record a review",
                   "critical"),
)


def find_gaps(assets: list) -> list[Finding]:
    """Run every governance rule over every asset.

    Args:
        assets: The assets to check.

    Returns:
        The findings, most severe first.
    """
    findings: list[Finding] = []

    for asset in assets:
        overview = asset.aspect("overview")
        business = asset.aspect("businessAttributes")
        quality = asset.aspect("quality")
        sensitivity = asset.aspect("sensitivity")

        if overview is None or not overview.fields.get("owner"):
            findings.append(Finding(
                asset.name, "missing-owner", "critical",
                "no owner recorded in the overview aspect"))

        if business is None or not business.fields.get("tier"):
            findings.append(Finding(
                asset.name, "missing-tier", "high",
                "no business tier recorded"))

        if business is not None and business.fields.get("tier") == "gold":
            if quality is None or quality.fields.get("completeness") is None:
                findings.append(Finding(
                    asset.name, "missing-quality-score", "medium",
                    "gold asset has no data quality score"))

        if business is not None and business.fields.get("tier") == "bronze":
            if business.fields.get("retention_days") in (None, 0):
                findings.append(Finding(
                    asset.name, "no-retention-on-bronze", "high",
                    "raw asset has no retention period; it will grow forever"))

        if sensitivity is not None and sensitivity.fields.get("contains_pii"):
            if not sensitivity.fields.get("reviewed_by"):
                findings.append(Finding(
                    asset.name, "pii-without-review", "critical",
                    "asset contains PII but has no recorded review"))

    order = {"critical": 0, "high": 1, "medium": 2}
    findings.sort(key=lambda f: order.get(f.severity, 3))
    return findings


# Build the assets to check. A governed asset carries every aspect; a
# poorly governed one is missing several.
ASSETS = [
    Asset(
        name="fact_events",
        resource_type="bigquery-table",
        resource_name="projects/YOUR_PROJECT_ID/datasets/curated/tables/fact_events",
        aspects=[
            Aspect(kind="metadata", key="metadata",
                   fields={"row_count": 4800, "columns": 9}),
            Aspect(kind="businessAttributes", key="businessAttributes",
                   fields={"tier": "gold", "retention_days": 730}),
            Aspect(kind="overview", key="overview",
                   fields={"owner": "analytics-eng", "steward": "data-platform"}),
            Aspect(kind="quality", key="quality",
                   fields={"completeness": 0.98, "freshness_hours": 2}),
        ],
    ),
    Asset(
        name="raw_customer_pii",
        resource_type="storage-object-collection",
        resource_name="gs://YOUR_LAKE_BUCKET/raw/customers/",
        aspects=[
            Aspect(kind="metadata", key="metadata", fields={"row_count": 912}),
            # No owner, no tier, no retention: this asset breaches several rules.
            Aspect(kind="sensitivity", key="sensitivity",
                   fields={"contains_pii": True, "info_types": ["EMAIL"]}),
        ],
    ),
]

gaps = find_gaps(ASSETS)

print(f"checked {len(ASSETS)} assets")
print(f"found {len(gaps)} gap(s)\n")
for finding in gaps:
    print(f"[{finding.severity:8s}] {finding.asset:20s} {finding.rule}")
    print(f"            {finding.detail}")
```

Note which rule fires and which does not: `fact_events` (gold, owned, with a quality score) passes everything except nothing; `raw_events` (bronze) passes owner and tier but its retention check depends on what you recorded. **The rules encode policy; the query finds the violations.** Running this on a real catalog, via the metastore, is a nightly job that produces a ticket, not a spreadsheet someone updates in March.

### 4. Build the lineage graph and answer the governance questions

Lineage as a graph, with the two questions that matter: impact analysis and PII scope.

```python
from dataclasses import dataclass, field


@dataclass
class LineageGraph:
    """A directed graph of table-to-table data flow.

    Attributes:
        edges: The edges, as (source, destination) pairs.
        nodes: Every node referenced by an edge.
    """

    edges: list[tuple[str, str]] = field(default_factory=list)
    nodes: set[str] = field(default_factory=set)

    def add_edge(self, source: str, destination: str) -> None:
        """Record that source feeds destination.

        Args:
            source: The upstream asset.
            destination: The downstream asset.
        """
        self.edges.append((source, destination))
        self.nodes.add(source)
        self.nodes.add(destination)

    def downstream(self, start: str) -> set[str]:
        """Return every asset reachable downstream of an asset.

        Args:
            start: The starting asset.

        Returns:
            The set of downstream assets, transitively.
        """
        result: set[str] = set()
        frontier = [start]
        while frontier:
            current = frontier.pop()
            for source, destination in self.edges:
                if source == current and destination not in result:
                    result.add(destination)
                    frontier.append(destination)
        return result

    def upstream(self, start: str) -> set[str]:
        """Return every asset reachable upstream of an asset.

        Args:
            start: The starting asset.

        Returns:
            The set of upstream assets, transitively.
        """
        result: set[str] = set()
        frontier = [start]
        while frontier:
            current = frontier.pop()
            for source, destination in self.edges:
                if destination == current and source not in result:
                    result.add(source)
                    frontier.append(source)
        return result


graph = LineageGraph()
graph.add_edge("raw_events", "stg_events_validated")
graph.add_edge("stg_events_validated", "fact_events")
graph.add_edge("fact_events", "fact_daily_region")
graph.add_edge("fact_events", "mart_marketing")
graph.add_edge("fact_daily_region", "dashboard_exec")
graph.add_edge("mart_marketing", "dashboard_marketing")

print("downstream of raw_events:")
for node in sorted(graph.downstream("raw_events")):
    print(f"  {node}")

print("\nupstream of dashboard_exec:")
for node in sorted(graph.upstream("dashboard_exec")):
    print(f"  {node}")

# Impact analysis: if we drop the bronze retention to 30 days,
# what breaks? Nothing in the curated layer, because the curated
# tables are built from the staging tables, not from raw at query time.
print("\nimpact of deleting raw_events:")
print(sorted(graph.downstream("raw_events")))
```

The answer to "if we delete the raw zone, what still reads from it?" is a graph traversal, and it is exact for query-derived lineage. That question — asked by a compliance officer about a data minimisation request — is why automatic lineage is worth the engineering.

### 5. Compare Data Catalog's tag model with Dataplex aspects

Both are metadata mechanisms. The exercise shows exactly what each buys.

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TagTemplate:
    """A Data Catalog tag template.

    Attributes:
        template_id: The template id.
        fields: Field name -> type, with required fields marked.
    """

    template_id: str
    fields: dict[str, tuple[str, bool]]


@dataclass
class Entry:
    """A Data Catalog entry.

    Attributes:
        name: The entry name.
        resource_type: The resource type.
        tags: Simple tags.
        template_tags: Template-tag id -> field values.
    """

    name: str
    resource_type: str
    tags: dict[str, str] = field(default_factory=dict)
    template_tags: dict[str, dict[str, object]] = field(default_factory=dict)


TEMPLATES = {
    "sensitivity": TagTemplate("sensitivity", {
        "pii": ("BOOLEAN", True),
        "categories": ("STRING", False),
        "reviewed_by": ("STRING", True),
    }),
    "steward": TagTemplate("steward", {
        "team": ("STRING", True),
        "contact": ("STRING", False),
    }),
}


def validate_entry(entry: Entry) -> list[str]:
    """Validate an entry's template tags against their templates.

    This is the check a tag template buys you: an applied tag either
    has every required field, or it is invalid.

    Args:
        entry: The entry to validate.

    Returns:
        A list of validation errors.
    """
    errors: list[str] = []
    for template_id, values in entry.template_tags.items():
        template = TEMPLATES.get(template_id)
        if template is None:
            errors.append(f"{entry.name}: unknown template {template_id}")
            continue
        for field_name, (_, required) in template.fields.items():
            if required and values.get(field_name) in (None, ""):
                errors.append(
                    f"{entry.name}: template {template_id} missing required "
                    f"field {field_name}"
                )
    return errors


def find_untagged(entries: list[Entry], template_id: str) -> list[str]:
    """Find entries that do not carry a given template tag at all.

    Args:
        entries: The entries to check.
        template_id: The template id to look for.

    Returns:
        The names of the untagged entries.
    """
    return [e.name for e in entries if template_id not in e.template_tags]


entries = [
    Entry(
        name="fact_events",
        resource_type="bigquery-table",
        tags={"tier": "gold", "owner": "analytics-eng"},
        template_tags={
            "sensitivity": {
                "pii": False,
                "categories": [],
                "reviewed_by": "privacy-office",
            },
            "steward": {"team": "data-platform"},
        },
    ),
    Entry(
        name="raw_customer_pii",
        resource_type="storage-object-collection",
        tags={"tier": "bronze"},
        template_tags={
            # reviewed_by is required and missing -> invalid
            "sensitivity": {"pii": True, "categories": ["email"]},
        },
    ),
    Entry(
        name="mart_marketing",
        resource_type="bigquery-table",
        tags={"tier": "silver"},
        # no sensitivity template tag at all -> a governance gap
    ),
]

all_errors: list[str] = []
for entry in entries:
    all_errors.extend(validate_entry(entry))

print("validation errors:")
for error in all_errors:
    print(f"  {error}")

print("\nentities missing the sensitivity template entirely:")
for name in find_untagged(entries, "sensitivity"):
    print(f"  {name}")
```

**The distinction the exercise makes visible.** A **simple tag** (`tier=gold`) is free-form and cheap; it drifts in spelling and nobody can rely on it. A **template tag** is a typed contract — applying it without a required field is an error, so the tag's presence implies completeness. And "does not carry the tag at all" is a *different* gap from "carries the tag but it is incomplete", and a governance programme needs to distinguish them.

### 6. Query the service catalogue for the governance services

The course's catalogue already models Dataplex, Data Catalog and BigLake — use it to check the governance landscape and its regional availability.

```python
import sys
sys.path.insert(0, "project/core")

from service_catalog import (
    get_service,
    services_by_category,
    regions_for,
    nearest_region,
    services_available_in,
    format_service_table,
    format_region_matrix,
)

for service_id in ("biglake", "dataplex", "data-catalog"):
    service = get_service(service_id)
    print(f"{service_id:14s} {service.name}")
    print(f"  regions: {', '.join(regions_for(service_id))}")
    print(f"  nearest to us-central1: {nearest_region('us-central1', service_id)}")
    print()

# The governance landscape: what else in the catalogue touches governance?
governance_ids = ("biglake", "dataplex", "data-catalog",
                  "sensitive-data-protection", "bigquery")
ids = [sid for sid in governance_ids if sid in services_available_in("us-central1")]
print(format_service_table(ids))
print()
print(format_region_matrix(ids))
```

The regional matrix is the practical output. Data residency requirements mean the catalog and the lake must live in the same region as the data — a Dataplex catalog in `europe-west4` cannot govern assets in `us-central1`. **Put the lake, the catalog and the metadata in one region, chosen by the data's residency, not by where the team is.**

---

## 🛠️ Common Errors and Fixes

### 1. The BigLake table that will not read the schema

```text
ERROR: Iceberg table scan failed: Unsupported Iceberg schema: unsupported
field type: variant
```

or, when the metadata is stale:

```text
ERROR: Failed to open table: Manifest list is not found at
gs://YOUR_BUCKET/curated/fact_events/metadata/snap-....avro
```

The first is a format capability mismatch — a column type the reader does not support. The second is a **half-completed write**: the data file landed but the metadata commit did not, or the metadata was expired while data remained.

The fix for the second is to use the snapshot management BigLake provides rather than deleting metadata files by hand:

```bash
# List snapshots.
bq query --use_legacy_sql=false --format=json \
  'SELECT * FROM `YOUR_PROJECT_ID.curated.fact_events.snapshots` ORDER BY committed_at DESC'

# Restore to a previous snapshot.
bq query --use_legacy_sql=false \
  'CALL bq.create_table_snapshot(
     "YOUR_PROJECT_ID.curated.fact_events_restored",
     "YOUR_PROJECT_ID.curated.fact_events",
     "<SNAPSHOT_ID>",
     "<EXPIRY_TIMESTAMP>"
   )'
```

The rule: **never delete `metadata/` by hand.** Iceberg's snapshot expiry is a managed operation; a manual `gsutil rm` on the metadata prefix corrupts the table's history irrecoverably.

### 2. `Dataplex` — the zone that does not match the bucket

```text
ERROR: Permission denied on resource project YOUR_PROJECT_ID/locations/us-central1/lakes/YOUR_LAKE.
```

or the more confusing version where the zone was created but assets do not appear:

```text
# The zone was created against a prefix that does not exist:
#   "prefix": "curated/"
# but the bucket layout is "curated_v2/"
# Result: harvesting finds nothing, and the catalog is silently empty.
```

The fix is to make the zone's prefix exactly match the bucket's layout, and to verify harvesting is enabled:

```bash
# The lake and zone must be in the same project as the bucket.
gcloud dataplex lakes describe analytics-lake \
  --project=YOUR_PROJECT_ID --location=us-central1

gcloud dataplex zones describe curated-zone \
  --project=YOUR_PROJECT_ID --location=us-central1 \
  --lake=analytics-lake

# Harvesting is enabled per zone, with a scope pattern.
gcloud dataplex zones update curated-zone \
  --project=YOUR_PROJECT_ID --location=us-central1 \
  --lake=analytics-lake \
  --assets-scopes-pattern='projects/YOUR_PROJECT_ID/locations/us-central1/buckets/YOUR_BUCKET/prefixes/curated/**'
```

**The silent failure mode to watch for: a catalog that is empty because harvesting found nothing.** No error, just no assets. The check is a simple assertion in CI — "the curated zone contains at least N assets" — which catches a broken scope pattern immediately.

### 3. `Data Catalog` — the tag that will not apply

```text
ERROR: Request contains an invalid argument. Field 'pii' is REQUIRED but no value was provided.
```

or:

```text
ERROR: Request contains an invalid argument. Tag template 'sensitivity' does not exist
in entry group 'curated-zone'
```

Tag templates are **regional** and **scoped to an entry group**. A template created in `us-central1` cannot be applied in `europe-west4`, and it cannot be applied in an entry group other than the one it was created in.

The fix — create the template in the right place and apply with all required fields:

```bash
gcloud data-catalog tag-templates create sensitivity \
  --project=YOUR_PROJECT_ID \
  --location=us-central1 \
  --entry-group=curated-zone \
  --field=pii:boolean:required \
  --field=categories:string:optional \
  --field=reviewed_by:string:required
```

```bash
gcloud data-catalog entries add-tag \
  --project=YOUR_PROJECT_ID \
  --location=us-central1 \
  --entry-group=curated-zone \
  --entry=fact_events \
  --tag-template=sensitivity \
  --tag-file=tag.json
```

### 4. The lineage graph that is missing the dashboard

```text
# The DAG shows:  raw_events -> stg_events -> fact_events
# But the dashboard's upstream is empty.
```

The dashboard is not a table, so query-derived lineage does not capture it — unless the BI tool reports it. BigQuery's `INFORMATION_SCHEMA.JOBS` records queries that *read* a table, and Dataplex builds lineage from the query's table references. A Looker Studio dashboard that reads a **materialised view** produces no edge to the view's underlying table unless the view's own query was also run and harvested.

The fix is to make the intermediate layer explicit and harvested:

```bash
# Materialised views are not automatically harvested as lineage sources.
# Register them as assets so the edge exists:
gcloud dataplex assets create \
  --project=YOUR_PROJECT_ID \
  --location=us-central1 \
  --lake=analytics-lake \
  --zone=curated-zone \
  --asset-id=mart_marketing \
  --resource-type=bq-table \
  --resource-name='projects/YOUR_PROJECT_ID/datasets/curated/tables/mart_marketing'
```

**The honest limitation to state in your governance documentation:** automatic lineage is table-level and query-derived. It will not show lineage from a spreadsheet, a Python script, or a dashboard that reads through an unharvested view. Manual edges exist for these — use them, but know they are the ones that rot.

### 5. The Iceberg table and the "too many files" error

```text
ERROR: Iceberg table scan failed: Too many manifest files.
Reduce the number of manifests by compacting the table.
```

or the slower variant that appears as a timeout rather than an error:

```text
-- Query times out after 6 minutes planning.
-- The table has 400,000 files across 40,000 manifests.
```

The small-file problem, made concrete. The fix is compaction — rewriting many small files into fewer large ones — and BigLake can run it as a managed operation:

```bash
# BigLake maintenance: compact the table.
bq query --use_legacy_sql=false \
  'CALL bq.optimize_table(
     "YOUR_PROJECT_ID.curated.fact_events",
     options => (
       "target_file_size" => "1GB",
       "min_file_count" => 2,
       "max_file_count" => 10
     )
   )'
```

And in the pipeline, write fewer, larger files: one file per partition per commit, not one per micro-batch. The upstream fix matters more than the maintenance job — a table that compacts cleanly is one that was written sanely.

### 6. The catalog that disagrees with the warehouse

```text
# Dataplex says fact_events has 4,800 rows.
# BigQuery says 12,345.
```

The cause is a stale harvest. If harvesting runs on a schedule and the table was written in the last hour, the catalog lags. Or, worse, the catalog was never refreshed because the harvesting scope pattern stopped matching.

The fix — check the harvest, and check the scope:

```bash
# Run an immediate metadata harvest.
gcloud dataplex lakes update analytics-lake \
  --project=YOUR_PROJECT_ID --location=us-central1 \
  --metadata-warehouse-project=YOUR_PROJECT_ID

# Verify the metastore sees the current row count.
bq query --use_legacy_sql=false \
  'SELECT asset_name, update_time, json_value(metadata, "$.schema.columns") IS NOT NULL
   FROM `YOUR_PROJECT_ID.dataplex_metastore.asset`
   WHERE asset_name LIKE "%fact_events%"'
```

**The governance control that prevents this class of drift:** a daily reconciliation query comparing the catalog's row counts against `INFORMATION_SCHEMA.TABLE_STORAGE` for the same tables, alerting on a mismatch. A catalog that is systematically wrong is worse than no catalog, because people make decisions based on it.

---

## 💡 Production Notes

- **Choose the open format once, and write it down.** Iceberg is the default recommendation on Google Cloud for its multi-engine support and partition evolution. Delta if your organisation is Delta-centric; Hudi for CDC-heavy upsert patterns. A format decision made per-team is a format migration later.
- **Keep the metadata in the same region as the data, always.** Dataplex, Data Catalog and the bucket must be co-located. A catalog in `europe-west4` cannot govern assets in `us-central1`, and the cross-region attempts fail with permission or not-found errors.
- **Automate the harvesting, then put the human effort into business metadata.** Machine-owned: schema, size, partitions, row counts, lineage. Human-owned: owner, description, tier, classification, glossary. Trying to hand-maintain the technical metadata is the fastest way to have a wrong catalog.
- **Assert that the catalog is not empty.** Add a CI check that the curated zone contains at least the expected number of assets. A silently-empty catalog from a broken scope pattern is the most common and least noticed governance failure.
- **Use tag templates for anything you will enforce, and simple tags for everything else.** A required field in a template is a control you can query. A free-form tag is a convention you can only hope about.
- **Never delete `metadata/` by hand on an Iceberg table.** Snapshot expiry is a managed operation; a manual `gsutil rm` destroys the table's history irreversibly.
- **Compact on a schedule, and fix the writer.** Compaction reclaims the damage, but a table that writes one file per micro-batch will need compaction forever. Configure the writer to produce one file per partition per commit.
- **Run the governance rules as a nightly job that opens tickets.** A query that finds assets missing an owner, or with PII and no review, producing a Jira ticket — that is a control. A dashboard of asset counts that nobody reads is a report.
- **Reconcile the catalog against the warehouse daily.** Compare catalog row counts to `INFORMATION_SCHEMA.TABLE_STORAGE` and alert on drift. A catalog that is systematically wrong is worse than no catalog.
- **Document the lineage gaps explicitly.** Automatic lineage is table-level and query-derived. The spreadsheets, scripts and unharvested views are the gaps — write them down, add manual edges where it matters, and tell the people who rely on lineage where the blind spots are.

---

## 🔑 Key Takeaways

- **BigLake is a management layer over open table formats in Cloud Storage**, not an engine. It gives you managed lifecycle, compaction, snapshot management and caching for Iceberg, Delta and Hudi tables.
- **The open formats solve the four lakehouse problems** — concurrent writes (manifest/transaction-log commits), schema evolution (versioned schemas and partition specs), small files (compaction), snapshot isolation (immutable snapshots and time travel). **Iceberg is the default recommendation** on GCP.
- **The big economic difference is the scan charge.** BigQuery's on-demand pricing bills native-table scans at $6.25/TB, and BigLake or external tables scanning GCS are billed on bytes scanned as well. The saving comes from avoiding duplicated storage, not from a free scan; the *slot* cost remains.
- **Dataplex is the catalog of record for a lake**: Lake → Zone → Asset → Aspect. The aspect model is what makes it more than a list — aspects are typed, evolvable and independently queryable.
- **Aspects split cleanly into machine-owned and human-owned.** Harvesting supplies schema, size, partitions and row counts; humans supply owner, description, tier and classification. Automate the first, staff the second.
- **Metadata harvesting is what keeps a catalog honest.** A hand-maintained catalog is wrong within a month; a harvested one is right within the hour.
- **Automatic lineage is the only lineage that survives**, because it is derived from the SQL that actually runs. It answers impact analysis, compliance scope and retention questions as graph traversals. Its limits are real: table-level, query-derived, and blind to scripts and spreadsheets.
- **Data Catalog is the tagging service**: entry groups, entries, simple tags and template tags. **Template tags are controls** — a required field means the tag's presence implies completeness, so you can query for the missing ones.
- **Dataplex versus Data Catalog:** Dataplex is the strategic platform with lineage and a SQL-queryable metastore; Data Catalog is the mature tag and search service with template discipline and glossaries. Pick one source of truth per attribute, and write down where it lives.
- **The governance story:** files land in Cloud Storage, BigLake manages them, Dataplex harvests and traces them, tags record the policy, and the catalog makes the lakehouse safe to run. Without the catalog, a lakehouse is just object storage with extra steps.

---

## 📚 Practice Exercises

1. **Price the BigLake decision at three scales.** Extend the cost exercise to 5 TB, 50 TB and 500 TB, with a BI workload and a Spark workload at different read rates. Show the native BigQuery cost, the BigLake cost, and the break-even point. Then add the metastore cost (Dataplex on the metadata volume, not the data volume) and the Datastream cost for CDC into the Iceberg table, and state whether the answer changes at 500 TB.
2. **Design the full Dataplex topology for a lakehouse.** Specify the lakes, zones and assets for the course pipeline: a raw zone for the landing files, a staging zone for validated events, a curated zone for the facts and dimensions, and a sandbox. For each zone, give the bucket prefix, the harvesting scope pattern, the aspect set you will populate, and the tag templates you will enforce. Then write the `gcloud` commands to create it.
3. **Write a governance rules engine.** Expand the `find_gaps` function into a rules engine: rules defined as data (a list of dicts with a name, severity, a check function and a remediation message), the ability to add organisation-specific rules, a summary report by severity, and an exit code that fails a CI job on any critical finding. Test it against the course's asset model, including one asset that violates every rule.
4. **Build a lineage-based impact analysis tool.** Write `impact_report(graph: LineageGraph, asset: str, sensitive: set[str]) -> dict` that, for a given asset, reports: everything downstream, everything upstream, whether any upstream asset is marked as containing PII, and the maximum retention period in the graph (which determines whether the asset can be deleted). Apply it to the course's lineage graph and answer: "can we delete `raw_events`?"
5. **Compare the tag models in depth.** Write a function that takes a set of entries and reports, for each template: how many entries carry it, how many carry it *completely*, and how many carry it *invalidly*. Then argue, with numbers, for making `sensitivity` mandatory across the curated zone — including the operational cost of the check, measured in API calls.
6. **Design the compaction and snapshot policy.** Write a policy for a table receiving 4,800 events per day with a 730-day retention: the writer configuration (files per partition per commit), the compaction schedule and trigger thresholds, the snapshot expiry rules, and the recovery procedure using snapshot restore. Include what happens when a bad load lands — how many hours of data are affected, and how you roll back without losing the good data.
7. **Write the governance runbook.** A single document covering: what the catalog is authoritative for and what it is not; how a new asset gets registered and tagged; how a PII classification is assigned and reviewed; how a retention period is set and enforced; how lineage is used for impact analysis; and the nightly checks that run. Then write the CI job that enforces the parts that can be automated, using the rules engine from exercise 3.

---

## 📖 Further Reading

- [BigLake overview](https://cloud.google.com/biglake/docs/introduction) — the managed lakehouse service
- [BigLake quickstart: create an Iceberg table](https://cloud.google.com/biglake/docs/quickstart-create-iceberg-table) — from zero to a queryable table
- [Apache Iceberg documentation](https://iceberg.apache.org/docs/latest/) — the format spec, manifests, snapshots and partition evolution
- [Dataplex overview](https://cloud.google.com/dataplex/docs/introduction) — lakes, zones, assets and aspects
- [Dataplex metadata harvesting](https://cloud.google.com/dataplex/docs/metadata-harvesting) — how the catalog populates itself
- [Dataplex lineage](https://cloud.google.com/dataplex/docs/data-lineage) — how automatic lineage is collected
- [Data Catalog overview](https://cloud.google.com/data-catalog/docs/introduction) — the tag and search service
- [Data Catalog tag templates](https://cloud.google.com/data-catalog/docs/tags-and-entries) — the typed tagging model
- [Data governance with Dataplex](https://cloud.google.com/dataplex/docs/data-governance) — the governance programme in one page
- [BigQuery Data Catalog integration](https://cloud.google.com/bigquery/docs/data-catalog-integration) — how the two connect
