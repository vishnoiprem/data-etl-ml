# GDPR-Compliant Delete Pipeline for Data Lakes

**Difficulty:** HARD
**Companies:** Netflix, Meta, Apple, Spotify, LinkedIn, Twitter/X
**Tags:** system-design, privacy, compliance, lakehouse, data-lineage

---

## 1. Problem Statement

> A user exercises their GDPR "right to be forgotten." Their data needs to be
> deleted from everything — the data lake, the warehouse, ML training datasets,
> analytics exports, even backups. Our data lake stores data in Parquet files
> and you can't just delete a row from a Parquet file. We need to do this
> within 30 days and prove to auditors that it's done.

### Hard Parts
- **Immutable Parquet** — you can't delete a single row; you must rewrite files
- **Data lineage** — every copy must be found: lake, warehouse, ML datasets, caches, backups
- **Derived data** — aggregates, embeddings, feature vectors may contain user data
- **Auditability** — regulators need proof; logs and receipts required
- **30-day SLA** — long enough to be safe, short enough to be operationally tight
- **Backups** — typically immutable; need retention exceptions or crypto-shredding

### Scale & Constraints

| Dimension | Value |
|---|---|
| Requests | 10K+ deletion requests/month |
| Systems | 50+ systems holding user data |
| Formats | Parquet (immutable), Iceberg, warehouse tables, Redis, S3 exports |
| Lineage | All copies and derivatives must be traced |
| Verification | Auditors require cryptographic proof |
| SLA | 30 days from request to verified deletion |

---

## 2. The 4-Step Approach

### Step 1 — Clarify Requirements
- **What counts as "deleted"?** Removal of personal data, or also derived/aggregated?
  GDPR: any data that can **re-identify** a user must go.
- **Backup handling?** Crypto-shredding (encrypt with per-user key, delete key)
- **What about ML embeddings?** Most are derived; users must opt-in OR delete must remove source data
- **Audit trail requirements?** Timestamped signed receipts for every system
- **SLA stages:** Intake → Discovery → Delete → Verify → Receipt

### Step 2 — High-Level Architecture

```
GDPR Delete Request
       │
       ▼
  Intake Service (REST + Auth + Id verification)
       │
       ▼
  Discovery Service
  ├── Lineage Graph (DataHub / Amundsen)
  ├── Data Catalog (Hive / Glue)
  └── Query user_id across all known tables
       │
       ▼
  Delete Coordinator (workflow engine: Temporal / Airflow)
       │
       ├──▶ Iceberg Delete (rewrite_data_files + delete filters)
       ├──▶ Warehouse Delete (DELETE FROM ...)
       ├──▶ Redis/KeyDB (DEL or TTL=0)
       ├──▶ S3 Object Cleanup (lifecycle + version purge)
       ├──▶ Search Index (Elasticsearch: delete_by_query)
       └──▶ ML Feature Store (mark features as deleted)
       │
       ▼
  Verification Service
  ├── Re-run discovery; assert 0 matches
  ├── Aggregate signed receipts from each system
  └── Generate Compliance Report (PDF + crypto receipt)
       │
       ▼
  Notify User + Archive for Regulator Audit
```

### Step 3 — Data Flow & Storage

**Two key techniques:**

1. **Iceberg / Delta Lake row-level deletes** — for partitioned tables, `DELETE FROM t WHERE user_id = ?` rewrites only affected files. Cheap at scale.
2. **Crypto-shredding for immutable stores** — encrypt PII columns with a per-user key; to "delete", destroy the key. Backups and ML datasets become unreadable.

**Lineage tracking:** Every pipeline write records source tables + transformations → lineage graph. Delete service queries this graph to find ALL descendants.

### Step 4 — Scale the Design

| Concern | Approach |
|---|---|
| 50+ systems | Standardized delete API; each system has a plug-in adapter |
| Immutable Parquet | Use Iceberg/Delta Lake; or rewrite affected files only |
| Backups | Crypto-shredding with per-user keys |
| ML datasets | Either regenerate from clean source OR exclude user_id rows during training |
| Aggregates | Recompute from deleted source OR add per-user suppression masks |
| Audit trail | Append-only log; signed with HSM; immutable storage |
| 30-day SLA | Orchestrate with Temporal; alerts on SLA breach |

### Step 5 — Non-Functional

- **Correctness:** Every system returns a signed receipt; aggregator verifies all receipts
- **Idempotency:** Repeated delete requests for same user_id are no-ops
- **Resumability:** Workflow can resume after failure; no partial deletes
- **Latency:** Discovery < 1 hour, delete < 24 hours per system, verify < 1 hour
- **Observability:** Delete SLA dashboard per system
- **Security:** Only authorized privacy team can trigger; requires multi-party approval

---

## 3. Critical Design Decisions

### 3.1 Two Deletion Strategies

**Direct delete** (preferred):
- Iceberg: `DELETE FROM silver.events WHERE user_id = 'X'` — file-level rewrite
- Warehouse: standard `DELETE FROM ...`
- Redis: `DEL user:X`
- Search: `delete_by_query`

**Crypto-shredding** (fallback for immutable stores):
- Encrypt PII columns with per-user KMS key
- "Delete" = `kms:schedule-key-deletion(key_id=user_X_key)`
- Backups become unreadable
- ML embeddings: regenerate without user or exclude from training

### 3.2 Lineage Graph
- **Source-of-truth catalog** (Hive Metastore / Glue / Unity Catalog)
- **Data lineage tool** (DataHub / OpenLineage / Amundsen) records transformations
- Discovery service queries lineage → "where did this column flow?"
- Catches downstream ML models, dashboards, exports, materialized views

### 3.3 Audit Trail
- Each delete event written to **append-only ledger** (e.g., AWS QLDB, S3 object lock)
- Each system adapter returns a signed receipt (timestamp, row count, system)
- Aggregator creates a **compliance receipt** (signed hash of all receipts)
- Stored for 7+ years for regulator audits

### 3.4 Aggregates & Derivatives
- Simple aggregates (count, sum): mark as "data from N-1 users" but safe to keep
- Re-identifiable aggregates: regenerate from deleted source
- ML models: don't retrain for one user; but ensure user is out of next training set
- Search suggestions / autocomplete: remove user_id references

### 3.5 Backup Strategy
- **Option A — per-user encryption keys** for sensitive columns → delete key
- **Option B — re-encrypt backups** after retention window expires
- **Option C — data exclusion lists** in restore scripts (hacky)
- Most companies use Option A combined with backup rotation

---

## 4. Folder Layout

```
04-gdpr-delete-pipeline/
├── README.md
├── docs/design-decisions.md
├── diagrams/
│   ├── architecture.mermaid
│   ├── deletion-flow.mermaid
│   └── lineage.mermaid
├── sql/
│   ├── schema.sql                    # deletion_requests, receipts, lineage
│   ├── lineage_query.sql             # find all tables containing user
│   └── iceberg_delete.sql            # row-level delete patterns
├── python/
│   ├── intake.py                     # request intake + identity verification
│   ├── discovery.py                  # lineage-based discovery
│   ├── delete_coordinator.py         # workflow orchestrator
│   ├── adapters/
│   │   ├── iceberg.py
│   │   ├── warehouse.py
│   │   ├── redis.py
│   │   ├── elasticsearch.py
│   │   └── ml_feature_store.py
│   ├── crypto_shred.py               # per-user encryption + key destruction
│   └── verification.py               # re-discover + signed receipts
├── pyspark/
│   ├── iceberg_delete.py             # bulk Iceberg deletes
│   ├── downstream_propagation.py     # find derived tables
│   └── audit_report.py               # compliance PDF + receipt
├── config/
│   ├── systems_registry.yaml
│   └── kms_keys.yaml
├── sample_data/
│   ├── user_data_locations.json
│   └── deletion_requests.jsonl
└── tests/
    ├── test_intake.py
    ├── test_discovery.py
    ├── test_crypto_shred.py
    └── test_verification.py
```

---

## 5. How to Run End-to-End

```bash
# 1. Intake a deletion request
python python/intake.py --user-id user_42

# 2. Discover all locations
python python/discovery.py --user-id user_42

# 3. Execute deletion across all systems
python python/delete_coordinator.py --user-id user_42

# 4. Verify deletion
python python/verification.py --user-id user_42

# 5. Generate compliance report
python pyspark/audit_report.py --user-id user_42 --output report.pdf
```

---

## 6. Interview Talking Points

1. **Iceberg/Delta Lake** — row-level deletes via file rewrites; not magic, just file-level
2. **Lineage is non-negotiable** — without it, you can't find every copy
3. **Crypto-shredding** — elegant for backups + ML datasets
4. **Per-system adapters** — every store is different; standardize the interface
5. **Signed receipts** — auditors need cryptographic proof, not "trust me"
6. **Aggregates** — derived data may still re-identify; regenerate or suppress
7. **30-day SLA** — workflow orchestration with Temporal/Airflow; SLA monitoring
8. **ML implications** — embeddings must be regenerated; models don't need retraining
