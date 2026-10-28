# 1.2 — Compute Services in GCP

> **Section 1 · Introduction to Google Cloud Platform · Lecture 1.2 · 5:35**

## 🎯 What you will learn

- The compute spectrum: VMs → containers → functions → serverless
- Where each service sits and when to reach for it
- Why BigQuery eliminated the need for most compute in analytics work

---

## 🧠 Concept

GCP's compute portfolio is best understood as a **ladder of abstraction**. Each rung trades control
for convenience, and you should climb only as high as your problem requires.

```
More control                                                    More convenience
◄──────────────────────────────────────────────────────────────────────────►
Compute Engine → GKE → Cloud Run → Cloud Functions → App Engine → BigQuery
  VMs              Containers     Containers      Events          Apps        SQL
```

### The services

| Service | Unit of deployment | Billing | Scales to | Cold start | Use for |
|---------|-------------------|---------|-----------|-----------|---------|
| **Compute Engine** | VM instance | vCPU + RAM + disk | Vertical + horizontal | None | Full OS control, legacy workloads |
| **Google Kubernetes Engine (GKE)** | Pod / node | Node pool | Horizontal | ~seconds | Container orchestration at scale |
| **Cloud Run** | Container | Request + CPU + memory | To zero | ~1s | Stateless containers, API services |
| **Cloud Functions** | Function | Invocations + memory + time | To zero | ~1s | Event-driven glue code |
| **App Engine** | Application | Instance class + traffic | Automatic | ~seconds | Full apps, extreme scale, zero ops |
| **Batch** | Job | vCPU-hour | Managed | N/A | Compute Engine for embarrassingly parallel work |

### Where BigQuery fits

The important observation for a data engineer: **most of the compute ladder disappears once you
use BigQuery**. In a traditional stack you need:

- A cluster manager (HDFS namenode, YARN resource manager)
- A query engine cluster sized for peak load
- A separate ETL compute cluster
- A separate BI-serving cluster

BigQuery replaces all of it. Your "compute" is the query engine that spins up for the duration of
the query. There is no cluster to size, no node to patch, no namenode to lose.

What remains in the stack:
- **Cloud Run / Cloud Functions** — for orchestration around BigQuery (API triggers, webhooks)
- **Cloud Storage** — the lake, staging zone, and external table source
- **Dataflow** — for pipelines BigQuery SQL alone can't express (complex streaming, unstructured data)
- **Composer** — for scheduling

---

## 🛠️ Hands-On

### 1. Launch a Compute Engine VM

```bash
# Create an instance with the gcloud CLI
gcloud compute instances create bq-lab-vm \
    --zone=us-central1-a \
    --machine-type=e2-standard-2 \
    --boot-disk-size=20GB \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud

# SSH in
gcloud compute ssh bq-lab-vm --zone=us-central1-a

# List running instances
gcloud compute instances list

# Delete when done — VMs are billed while running
gcloud compute instances delete bq-lab-vm --zone=us-central1-a
```

### 2. Deploy a container to Cloud Run

```bash
# Build and push a container
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/hello-bq

# Deploy serverlessly
gcloud run deploy hello-bq \
    --image gcr.io/YOUR_PROJECT_ID/hello-bq \
    --region us-central1 \
    --set-env-vars PROJECT_ID=YOUR_PROJECT_ID

# Get the URL
gcloud run services describe hello-bq --region us-central1 --format='value(status.url)'
```

### 3. Trigger a Cloud Function on a Pub/Sub event

```bash
gcloud functions deploy bq-on-event \
    --runtime=python311 \
    --region=us-central1 \
    --trigger-topic=my-events \
    --source=. \
    --entry-point=process_event \
    --set-env-vars PROJECT_ID=YOUR_PROJECT_ID,BIGQUERY_DATASET=analytics
```

The function body is a direct BigQuery client call:

```python
from google.cloud import bigquery

def process_event(event, context):
    """Insert a Pub/Sub message into BigQuery via the streaming insert API."""
    client = bigquery.Client()
    dataset = client.dataset("analytics")
    table = dataset.table("raw_events")

    rows_to_insert = [
        {
            "event_id": event.attributes.get("event_id"),
            "event_type": event.data.decode("utf-8"),
            "ingested_at": event.publish_time.isoformat(),
        }
    ]

    errors = client.insert_rows_json(table, rows_to_insert)
    if errors:
        raise RuntimeError(f"Streaming insert failed: {errors}")
```

### 4. Use BigQuery's own compute instead

Everything above can often be replaced by a single BigQuery job:

```sql
-- No cluster, no VM, no container. This IS the compute.
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.analytics.daily_orders`
PARTITION BY DATE(order_date)
CLUSTER BY customer_id
AS
SELECT
    DATE(order_ts)              AS order_date,
    customer_id,
    COUNT(*)                    AS order_count,
    SUM(total_amount)           AS revenue,
    ARRAY_AGG(STRUCT(product_id, qty)) AS line_items
FROM `YOUR_PROJECT_ID.raw.orders`
WHERE DATE(order_ts) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
GROUP BY order_date, customer_id;
```

---

## 💡 Production Notes

- **Cloud Run scales to zero** — an idle service costs nothing. This makes it dramatically cheaper
  than a min-1 GKE node pool for spiky APIs.
- **Cloud Run cold starts** are sub-second for small containers, but first-request latency can be
  higher after long idle periods. Set `--min-instances=1` if you need warm latency (and accept the
  cost).
- **Never leave VMs running.** A forgotten `e2-standard-8` burns ~$500/month. Use `--no-address` and
  stop instances when idle.
- **Use Spot VMs for batch work** — up to 91% cheaper, for preemptible, restartable jobs.

---

## 🔑 Key Takeaways

- Compute on GCP spans VMs → containers → functions → serverless; each step trades control for convenience.
- BigQuery is the most abstracted tier — **you never manage the compute**, only the query.
- Cloud Run is the default choice for stateless containers; Cloud Functions for event glue.
- Serverless-to-zero is the biggest cost lever for intermittent workloads.
- Analytics compute should be BigQuery first, Dataflow second, everything else third.

---

## 📚 Practice Exercises

1. **Right-size.** A team runs a Kubernetes cluster with 10 always-on nodes to serve a service with
   2 requests/hour. Redesign on GCP. What do you save per month?

2. **Trigger design.** Write a Cloud Function that reads from BigQuery and pushes a report to
   Pub/Sub. What permissions does its service account need? (Name the exact IAM roles.)

3. **Cost comparison.** Run the same workload on Cloud Run and Compute Engine for a month. At what
   request rate does a static VM become cheaper?

4. **BigQuery substitution.** For each scenario below, decide: BigQuery, Dataflow, Cloud Run, or a VM?
   - (a) Nightly aggregation of 5 TB
   - (b) A public-facing REST API with 50 req/s
   - (c) Parsing 200 GB of PDFs per day
   - (d) A scheduled report emailed to 300 people

---

## 📖 Further Reading

- Cloud Run docs — https://cloud.google.com/run/docs
- Cloud Functions docs — https://cloud.google.com/functions/docs
- Compute Engine pricing — https://cloud.google.com/compute/pricing
