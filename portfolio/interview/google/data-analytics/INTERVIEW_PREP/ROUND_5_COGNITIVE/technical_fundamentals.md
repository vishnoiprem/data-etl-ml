# Technical Fundamentals - Rapid Reference
## Core GCP Data Services for Round 5 Rapid-Fire Q&A

---

## ☁️ BIGQUERY

### Architecture (30-sec answer)
> Serverless, storage/compute separation. **Colossus** (distributed storage), **Dremel** (query engine), **Borg** (compute slots). Data in Capacitor format (columnar, compressed). Slots = virtual CPU+RAM+network. Editions: Standard/Enterprise/Enterprise Plus.

### Partitioning vs Clustering
| Feature | Partitioning | Clustering |
|---------|-------------|------------|
| **Purpose** | Prune data (reduce bytes scanned) | Sort within partition (improve filter/join) |
| **Keys** | DATE, TIMESTAMP, DATETIME, INTEGER_RANGE, INGESTION_TIME | Up to 4 columns, high cardinality |
| **Granularity** | Daily, hourly, monthly, yearly, integer ranges | Automatic block sorting |
| **Cost Impact** | Direct: only scanned partitions billed | Indirect: better compression, faster queries |
| **Maintenance** | Auto (time-unit) or manual (integer) | Auto-reclustering (background) |

**Best Practice:** Use BOTH. Partition by date (prune 90%+), cluster by customer_id/session_id (sort within).

### Slot Management
| Concept | Detail |
|---------|--------|
| **On-demand** | Per-TB scanned, burst to 2000 slots/project |
| **Reservations** | Baseline slots (100+), 1/3/yr commitment = 17%/28%/35% off |
| **Autoscaling** | Additional slots above baseline, per-second billing |
| **Flex Slots** | On-demand reservation, 60-sec minimum, no commitment |
| **Edition Limits** | Standard: 2000 baseline. Enterprise: 10,000. Enterprise Plus: 50,000 |

**Contention Solutions:** Fair scheduling (per-project), reservation assignments (per-workload), query optimization, BI Engine for dashboards.

### Streaming & Storage Write API
| Method | Latency | Exactly-Once | Cost | Use Case |
|--------|---------|--------------|------|----------|
| **Storage Write API (default)** | <1 sec | ✅ Stream-level | $0.01/200MB ingested | Production streaming |
| **Legacy tabledata.insertAll** | <1 sec | ❌ At-least-once | Free (within limits) | Legacy only |
| **Batch Load (Load jobs)** | Minutes | ✅ Job-level | Free (within limits) | Batch/Historical |

### BQML vs Vertex AI
| Aspect | BQML | Vertex AI |
|--------|------|-----------|
| **Interface** | SQL (CREATE MODEL) | Python SDK, UI, API |
| **Algorithms** | Linear, XGBoost, ARIMA, TensorFlow, AutoML Tables | All + custom containers, distributed training |
| **Data Movement** | None (in-database) | Required (to GCS/Feature Store) |
| **Serving** | SQL PREDICT | Online endpoints (autoscaling), Batch prediction |
| **MLOps** | Basic (model versions) | Full (Pipelines, Registry, Monitoring, Feature Store) |
| **Promotion** | EXPORT MODEL → Vertex AI Model.upload() | Native |

### Cost Optimization Checklist
- [ ] Partition pruning (WHERE event_date >= ...)
- [ ] Clustering on high-cardinality filter/join keys
- [ ] Materialized Views for repeated aggregations
- [ ] BI Engine (100GB+ reservation) for dashboards
- [ ] Query result cache (24hr, free reuse)
- [ ] `MAX_BYTES_BILLED` guardrails
- [ ] Slot reservations (3yr = 35% off)
- [ ] Storage: 90d→Nearline, 365d→Coldline lifecycle

---

## 🌊 DATAFLOW (Apache Beam)

### Batch vs Streaming (Unified Model)
```python
# SAME CODE, DIFFERENT RUNNER BEHAVIOR
# Batch: Bounded PCollection, executes once
# Streaming: Unbounded PCollection, continuous execution

p = beam.Pipeline(options=PipelineOptions(
    runner='DataflowRunner',
    streaming=True  # True=Streaming, False=Batch
))
```

### Exactly-Once Semantics
| Layer | Mechanism |
|-------|-----------|
| **Source** | Idempotent keys + deduplication (Pub/Sub message IDs, Kafka offsets) |
| **Processing** | Deterministic DoFns, no side effects, stateful processing with timers |
| **Shuffle** | Dataflow Shuffle Service (managed, exactly-once) |
| **Sink** | BigQuery Storage Write API (stream-level exactly-once), Spanner, transactional DBs |

### Windowing Types
| Window | Trigger | Use Case |
|--------|---------|----------|
| **Fixed (Tumbling)** | Watermark + allowed lateness | Hourly/daily aggregations |
| **Sliding** | Watermark + allowed lateness | Rolling 5-min average |
| **Session** | Gap duration + allowed lateness | User activity sessions |
| **Custom** | Custom trigger | Complex business logic |

**Key Config:** `allowed_lateness` (default 0), `accumulation_mode` (DISCARDING/ACCUMULATING), `trigger` (AfterWatermark, AfterProcessingTime, AfterCount, OrFinally).

### Shuffle Optimization
| Problem | Solution |
|---------|----------|
| **Hot keys (skew)** | Salting (hash + random prefix), custom partitioner, CoGroupByKey |
| **Large shuffle** | CombinePerKey pre-aggregation, CombineGlobally, efficient coders |
| **Worker OOM** | Shuffle Service (managed), right-size workers, `--experiments=shuffle_mode=service` |
| **Slow shuffle** | SSD persistent disks, worker placement (same zone), reduce data before shuffle |

### Monitoring & Debugging
| Metric | Alert Threshold |
|--------|-----------------|
| **System Lag** | >5 min (streaming) |
| **Data Watermark Age** | >10 min |
| **Worker CPU/Memory** | >85% sustained |
| **Error Rate** | >1% |
| **Autoscaling** | Max workers reached |

---

## ⚡ DATAPROC (Managed Spark/Hive)

### When Dataproc vs Dataflow
| Choose Dataproc When | Choose Dataflow When |
|---------------------|---------------------|
| Existing Spark/Hive codebase | Greenfield Beam development |
| Complex DAGs, interactive notebooks | Unified batch/streaming |
| Hive Metastore compatibility critical | Exactly-once streaming required |
| Custom libraries, JARs, Python envs | Serverless, no cluster mgmt |
| Cost-sensitive batch (Spot VMs) | Auto-scaling streaming |

### Cost Optimization
- **Spot VMs:** 60-90% off for workers (preemptible)
- **Autoscaling Policies:** Scale up/down based on YARN queue
- **Image Versioning:** Pin to specific image (e.g., 2.1-debian11)
- **Enhanced Flexibility Mode:** Scale down to 0 workers
- **Preemptible GPUs:** For ML training workloads

### Metastore Options
1. **Dataproc Metastore** (Managed Hive Metastore, HA, multi-cluster)
2. **External MySQL/PostgreSQL** (Cloud SQL)
3. **BigQuery as Metastore** (BigQuery-Hive connector, unified catalog)

---

## 🎼 COMPOSER (Managed Airflow)

### Composer 1 vs 2
| Feature | Composer 1 | Composer 2 |
|---------|-----------|------------|
| **Airflow Version** | 1.10 / 2.0-2.5 | 2.6+ |
| **Deployment** | GKE-based | Cloud Build + Cloud Run (serverless) |
| **Startup Time** | 20-30 min | 3-5 min |
| **Min Environment** | 3 nodes | Micro (0.1 vCPU) |
| **Cost** | Higher (GKE overhead) | Lower (pay per DAG run) |
| **Private IP** | Complex | Native |

### Best Practices
- **TaskGroups** for UI organization (Airflow 2+)
- **XCom** only for small data (<48KB), use GCS for large
- **Sensors:** Use `poke_interval` (60s+), `timeout`, `mode=reschedule`
- **SLAs + Callbacks:** `sla=timedelta(hours=2)`, `on_failure_callback=alert`
- **Secrets:** Secret Manager (not Variables/Connections)
- **DAG Versioning:** Git sync, CI/CD via Cloud Build
- **Dataflow Operator:** `DataflowStartFlexTemplateOperator` (async + sensor)

---

## 🤖 VERTEX AI

### Feature Store
| Component | Purpose |
|-----------|---------|
| **Entity Type** | Business entity (Customer, Transaction, Product) |
| **Feature** | Attribute (age, avg_spend, last_login) |
| **Feature View** | Logical group for serving (online) or training (offline) |
| **Online Store** | Low-latency serving (<10ms), Bigtable backend |
| **Offline Store** | Training data, BigQuery backend |
| **Sync** | Batch (Dataflow) or Streaming (Pub/Sub→Dataflow) |

**Point-in-Time Correctness:** `feature_view.get_feature_values(entity_ids, timestamp)` returns values as of that timestamp.

### MLOps (Vertex AI Pipelines)
```
PIPELINE COMPONENTS:
├── Data Ingestion → Validation → Transform
├── Training (Custom / AutoML / BQML promotion)
├── Evaluation (metrics, thresholds, model cards)
├── Model Registry (versioning, aliases: champion/challenger)
├── Deployment (Endpoint: A/B, Canary, Shadow)
└── Monitoring (Drift: feature/target/prediction, Bias, Feature Attribution)
```

### BQML → Vertex AI Promotion
```sql
-- 1. Train in BigQuery
CREATE MODEL `project.dataset.churn_model`
OPTIONS (model_type='BOOSTED_TREE_CLASSIFIER') AS
SELECT * FROM `project.dataset.training_data`;

-- 2. Export to GCS
EXPORT MODEL `project.dataset.churn_model`
OPTIONS (uri='gs://bucket/models/churn/');

-- 3. Upload to Vertex AI (Python)
from google.cloud import aiplatform
model = aiplatform.Model.upload(
    display_name="churn_model",
    artifact_uri="gs://bucket/models/churn/",
    serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/xgboost-cpu.1-6:latest"
)

-- 4. Deploy to Endpoint
endpoint = model.deploy(machine_type="n1-standard-4", min_replica_count=2)
```

---

## 🔐 SECURITY & GOVERNANCE

### VPC Service Controls
| Concept | Implementation |
|---------|----------------|
| **Perimeter** | Boundary around projects (data projects + service projects) |
| **Bridge** | Allowed egress to specific external services |
| **Ingress/Egress Rules** | CIDR-based, identity-based, service-based |
| **Dry Run** | Test before enforce (log violations only) |
| **Private Service Connect** | Access BQ, Dataflow, Vertex AI without public IPs |

### CMEK + Cloud HSM
| Layer | Option | Use Case |
|-------|--------|----------|
| **Google-managed (default)** | Google owns keys, rotates | Baseline |
| **CMEK (Customer-Managed)** | Customer owns KMS keys, auto-rotate | Compliance, key sovereignty |
| **CMEK + Cloud HSM** | Keys in FIPS 140-2 L3 HSM | MAS-TRM, PCI-DSS, highest assurance |
| **CSEK (Customer-Supplied)** | Customer provides key per request | Maximum control, customer manages rotation |

**Key Hierarchy:** Key Ring → Key → Key Version. Rotation: 90 days auto, manual anytime. Destruction: scheduled (24hr minimum).

### Dataplex Governance
| Component | Purpose |
|-----------|---------|
| **Lake** | Logical container (region, metastore, security) |
| **Zone** | Raw (unstructured, immutable) / Curated (structured, governed) |
| **Asset** | GCS bucket, BigQuery dataset, Pub/Sub topic |
| **Policy Tags** | Column-level taxonomy (PII, Financial, Restricted) |
| **Data Quality** | Great Expectations scans, scheduled, threshold-based |
| **DLP Integration** | Auto-classify → apply policy tags |
| **Lineage** | Column-level: Source → BQ → Looker → Vertex AI |

---

## 📊 QUICK REFERENCE: Service Limits (Singapore Region)

| Service | Default Quota | Request Increase |
|---------|--------------|------------------|
| **BigQuery Slots** | 2,000 on-demand | Up to 50,000 (Enterprise Plus) |
| **BigQuery Concurrent Queries** | 100 | 200+ |
| **Dataflow Workers** | 1,000 | 5,000+ |
| **Dataproc Clusters** | 50 | 200+ |
| **Composer Environments** | 20 | 50+ |
| **Vertex AI Endpoints** | 100 | 500+ |
| **VPC-SC Perimeters** | 5 | 20+ |
| **KMS Keys** | 100 | 1,000+ |

---

## 🎯 Rapid-Fire Practice Questions

**BigQuery:**
1. "Explain BigQuery architecture in 30 seconds."
2. "Partition vs Cluster - when to use each?"
3. "How do you handle slot contention?"
4. "Streaming inserts: Storage Write API vs legacy?"
5. "BQML vs Vertex AI - when to use which?"
6. "How do you control query costs?"
7. "Multi-cloud query - how does Omni work?"

**Dataflow:**
1. "Batch vs Streaming in Beam - same code?"
2. "How do you achieve exactly-once?"
3. "Windowing types - Fixed vs Session vs Sliding?"
4. "Shuffle skew - how to fix?"
5. "Late data handling - allowed lateness?"
6. "Monitoring - what metrics matter?"

**Dataproc:**
1. "When Dataproc over Dataflow?"
2. "Cost optimization strategies?"
3. "Metastore options?"

**Composer:**
1. "Composer 1 vs 2 differences?"
2. "Best practices for production DAGs?"

**Vertex AI:**
1. "Feature Store - online vs offline?"
2. "MLOps pipeline components?"
3. "BQML to Vertex promotion?"

**Security:**
1. "VPC-SC - how does it prevent exfiltration?"
2. "CMEK vs CMEK+HSM vs CSEK?"
3. "Policy Tags - how do they enforce masking?"

---

*Memorize the 30-second versions. The details are in your head—interviewers want the structured summary.*