# 1.1 — Introduction to Cloud Computing

> **Section 1 · GCP Fundamentals · Lecture 1.1 · 8:00**

## 🎯 What you will learn
- What actually changes when you move a workload from a server you own to a cloud platform
- The five service models — IaaS, PaaS, FaaS, CaaS, SaaS — and how they differ in what you still operate
- Serverful versus serverless, and why "serverless" never means "no servers"
- Vertical versus horizontal scaling, and which one each Google Cloud service gives you
- The concrete benefits of cloud: elasticity, global reach, managed operations, and the trade-offs you accept
- Why Google Cloud is a strong fit for data engineering workloads
- How GCP, AWS and Azure map onto each other, and where the mapping breaks down
- How the Google Cloud free tier actually works, and how to activate an account without surprises

---

## 🧠 Concept

### What "cloud" means mechanically

A cloud is not a magic datacenter in the sky. It is a **capital-intensive operator running standard hardware in scale-out racks, renting slices of that capacity by the minute, and exposing it through a control plane that automates the parts you used to do by hand**.

Replace "renting slices of capacity" with the three properties that actually matter:

1. **The control plane is the product.** In a traditional datacenter, buying a server was a procurement event: order, rack, cable, patch, image, hand to ops. On Google Cloud, creating a VM is an API call that returns a running instance with a boot disk, a network interface and an identity attached. The difference is not the hardware; it is that the provisioning, decommissioning, backup, patching and monitoring are code paths owned by Google rather than by your team.
2. **Capacity is inventory, not a purchase order.** A capacity plan says "we will have 40 TB by Q3". A cloud plan says "we will have 40 TB of growth available on demand, and we will pay for it while it exists". That is the single most important economic change in the shift, and it cuts both ways: capacity planning becomes trivial, and runaway spend becomes possible.
3. **Billing follows the resource, not the contract.** Every resource you create accrues cost per second (or per hour, or per request) until it is deleted. This is why "delete the test cluster" is an engineering task, not an administrative one.

For a data engineer specifically, the third property matters more than the first two. A pipeline that runs on 20 nodes for 90 minutes every night is nearly free on Google Cloud if you use ephemeral clusters and shut them down; the same pipeline on a permanently-allocated cluster bills 730 hours a month regardless of whether it ran.

### The five service models

The models differ in one dimension that matters more than the marketing labels: **how much of the stack remains your responsibility**.

| Model | You manage | You do not manage | Google Cloud examples |
|---|---|---|---|
| IaaS — Infrastructure as a Service | OS, runtime, patches, network config, capacity | Hardware, virtualisation, physical network, data centre | Compute Engine, Persistent Disk, Cloud Load Balancing |
| PaaS — Platform as a Service | Your code and its configuration | OS, runtime, scaling, patching | App Engine, Cloud Run (with a source deploy), Cloud SQL |
| FaaS — Function as a Service | Function code and its triggers | Servers, instances, scaling entirely | Cloud Run functions, Eventarc functions |
| CaaS — Containers as a Service | Container images, manifests, cluster config (partly) | Node provisioning, control plane, some autoscaling | Google Kubernetes Engine (GKE), Cloud Run |
| SaaS — Software as a Service | Nothing but data and access | The whole application | Looker Studio, BigQuery console, Firebase |

The practical decision rule is: **every layer you manage is a layer that can break, patch late, and cost you time.** But every layer you give up is a layer where you may hit a platform limitation that forces an architectural compromise. Managed services are not free — you trade control for leverage.

### Serverful versus serverless

"Serverless" is the most abused term in cloud engineering, so let's be precise about what Google Cloud actually means by it.

**Serverful** means there is a resource that exists continuously and you are billed for its existence whether or not it does useful work. A Compute Engine instance with nothing to do still bills for its vCPUs and its disk. A Dataproc cluster with no jobs still bills for its workers. A Composer environment with no DAGs still bills for its node.

**Serverless** means:

- The platform allocates and reclaims capacity on demand — you describe the *shape* of the work, not the *size* of the fleet.
- You are billed for work performed (requests, vCPU-seconds, bytes processed, rows ingested), not for capacity reserved.
- The platform handles availability, patching and instance replacement.

The critical misconception to kill early: **serverless does not mean "there are no servers."** There is always a server; you have simply delegated its lifecycle to a control plane. Under the hood, Cloud Run is running containers on machines, and GKE Autopilot runs Kubernetes on a node pool Google manages. What you delegated is not the hardware — it is the *provisioning and reclamation*.

For data engineering, the split usually looks like this:

- **Streaming pipelines** are the best serverless case in the platform. Dataflow runs a job for the duration of the stream; a stream that is quiet still bills (the workers are reserved), but a batch job that runs 20 minutes bills 20 minutes of slot time.
- **Elasticity** is what serverless buys you. A query engine that can scale to hundreds of nodes for a two-hour backfill and then vanish is qualitatively different from a cluster you must size for the peak and pay for continuously.

### Vertical versus horizontal scaling

These two terms get confused constantly, so define them by the axis they move along.

**Vertical scaling** increases the capacity of *one* machine: more vCPUs, more RAM, a bigger disk, a larger machine type. The unit of scaling stays the same; the unit gets bigger.

**Horizontal scaling** increases the number of machines. Each machine does less, and together they do more. The unit of scaling is replicated.

```text
Vertical:    [ worker-1: 64 vCPU ]                    -> [ worker-1: 128 vCPU ]

Horizontal:  [ w1: 8 ] [ w2: 8 ] [ w3: 8 ]            -> [ w1: 8 ] [ w2: 8 ] [ w3: 8 ] [ w4: 8 ] [ w5: 8 ]
```

Mechanically, vertical scaling is limited by the largest machine type that exists and by the fact that a bigger machine is a **bigger failure domain** — more memory pressure, longer GC pauses, and a longer restart when it dies. It also cannot help a workload that does not parallelise, such as a single-threaded parser.

Horizontal scaling is limited by the coordination overhead: at some point the workers spend more time talking to each other than computing. It requires the workload to be decomposable, which is exactly why the MapReduce and Beam models are built around it.

Which one Google Cloud gives you depends on the service, and this distinction is a real selection criterion:

| Service | Scaling axis | Practical consequence |
|---|---|---|
| Compute Engine | Both — resize the machine type or add instances | You own the scaling logic |
| App Engine | Horizontal | Automatic, per-instance scaling, no vertical option exposed |
| GKE | Horizontal | Node pools scale; pods scale via HPA/VPA (vertical in Kubernetes terms) |
| Cloud Run | Horizontal | Scales request concurrency by adding container instances |
| Cloud Run functions | Horizontal | Scales invocations by adding instances |
| BigQuery | Horizontal and invisible | Slots scale automatically under the hood |
| Dataflow / Dataproc | Horizontal | Workers are added; you choose the shape |

Opinionated take: **for batch data processing, horizontal scaling is not optional.** A 10 TB backfill on one giant machine is a single-threaded gamble; the same backfill split across 200 workers is a bounded, restartable, parallel job. Choose platforms that expose horizontal scaling as the default.

### Benefits of cloud — with the trade-offs attached

Every cloud benefit is a trade-off wearing a hat. Here is the honest accounting, because a proposal that only lists benefits will fail in the client's first month.

| Benefit | Mechanism | The trade-off you accept |
|---|---|---|
| Elasticity | Control plane allocates/reclaims on demand | You stop planning capacity and start managing cost variance |
| Global reach | Regions and zones across 12+ regions here | Data residency, cross-region latency, and egress bills |
| Managed operations | Google patches, monitors, and replaces hardware | Less control over the OS, kernel, and runtime versions |
| Disaster recovery | Multi-zone and multi-region resources | You pay for the replica and you own the failover logic |
| Cost efficiency at low scale | No hardware capital, per-second billing | Price is *per unit*, so runaway queries are expensive |
| Access to specialist services | BigQuery, Dataflow, Vertex AI | Vendor lock-in and API surface you must learn |

The trade-off people underestimate is **cost predictability**. A physical server has a fixed monthly cost. A BigQuery query that scans a partitioned table costs cents; the same query against an unpartitioned table scans the whole table and costs dollars, every time someone runs it. The course project makes this concrete: the same 1 TB workload costs $6.25 unpartitioned and $0.0625 partitioned — a 100× difference caused entirely by table design.

### Why Google Cloud for data engineering

Five reasons, each of which maps to a specific platform capability rather than a slogan:

1. **BigQuery is a genuinely serverless columnar warehouse.** Columnar storage plus a query planner that charges per byte scanned means the query cost is a function of your schema design, not of how many people are in the warehouse. There is no cluster to size, no node to patch, no vacuum to run.
2. **Dataflow unifies batch and streaming in one API.** The Beam model means the same pipeline definition can run on Dataflow (serverless, managed workers), on Apache Flink, or on Spark. The portability is real, not theoretical — that is why the [Dataflow chapter](22-apache-beam-and-dataflow.md) treats the runner as the real abstraction.
3. **Pub/Sub is a global, at-least-once message backbone** with push and pull subscriptions, ordering keys, and dead-letter topics. It is the default ingestion front door for event data on GCP.
4. **Dataform puts transformation logic in version control** as SQLX, with dependency graphs and tests — the piece most clouds still leave to spreadsheet discipline. See the [Dataform chapter](24-dataform-and-the-transformation-layer.md).
5. **The integrated data platform.** BigLake, Dataplex, Data Catalog, Sensitive Data Protection and BigQuery ML sit on the same identity, policy and networking model as everything else. Governance is not a separate product bolted on; it is `roles/`, labels, and org policy applied to resources you already have.

Honest caveat: GCP's on-demand BigQuery pricing makes careless queries expensive, its IAM model has more surface area than AWS's (permissions, roles, service accounts, org policy, VPC Service Controls), and the service catalogue is large enough that "which service?" is a real skill. You will use those as learning material, not as reasons to avoid the platform.

### GCP vs AWS vs Azure — a data engineer's comparison

Comparing clouds by console screenshots is useless. Compare them by the abstractions that shape your architecture.

| Concern | Google Cloud | AWS | Azure |
|---|---|---|---|
| Analytics warehouse | BigQuery — serverless, columnar, pay-per-TB-scanned | Redshift (provisioned) + Athena (serverless, S3-based) | Synapse (provisioned/serverless) + Fabric |
| Batch/streaming engine | Dataflow (Beam), Dataproc (Spark) | Glue, EMR, Kinesis Data Analytics | Synapse Spark, Stream Analytics, Fabric |
| Stream bus | Pub/Sub | SQS + SNS + MSK + Kinesis | Service Bus, Event Hubs, Kafka |
| Object storage | Cloud Storage | S3 | Blob Storage |
| Containers | GKE (managed upstream Kubernetes) | EKS | AKS |
| Serverless containers | Cloud Run | ECS Fargate, App Runner, Lambda | Container Apps, Functions |
| IaC | Terraform (provider), Google Cloud Deploy | Terraform, CloudFormation | Terraform, Bicep, ARM |
| Org governance | Org Policies + IAM + VPC SC | SCPs + IAM + Organizations | Azure Policy + RBAC + Management Groups |
| Notable strength for data | Unified batch/streaming model, integrated governance | Breadth and maturity, huge ecosystem | Hybrid/enterprise Microsoft estate |
| Notable rough edge | Fewer regions in some geographies; pricing needs care | Complexity, IAM sprawl | Naming inconsistencies, portal sprawl |

The deep, transferable points:

- **AWS splits "serverless analytics" across Athena and Redshift.** Athena is the BigQuery analogue (serverless, pay-per-scan). Redshift is a provisioned warehouse, which means capacity planning. GCP puts both capabilities behind BigQuery: on-demand for ad-hoc work, reservations/ Editions for flat-rate capacity, BigLake for open table formats.
- **All three now converge on managed Kubernetes.** GKE, EKS and AKS are all upstream Kubernetes with a managed control plane. Choosing GKE over EKS is usually about the surrounding GCP integration, not the Kubernetes.
- **All three have serverless containers.** Cloud Run, Fargate/App Runner and Container Apps are close analogues. Cloud Run's distinguishing feature is fine-grained billing per request *and* per CPU-second, which suits spiky workloads.
- **Governance differs in vocabulary, not in substance.** GCP's Organization Policies constrain *what can exist*; IAM decides *who can act*. AWS calls the first "SCPs" and the second "IAM"; Azure calls them "Azure Policy" and "RBAC". Chapter 1.4 makes the GCP distinction precise, because it is the distinction people get wrong most often.

My opinionated recommendation for a data engineer in 2026: **if your data platform is built primarily on GCP, stay on GCP.** The integration advantage — BigQuery, Dataflow, Pub/Sub, Composer and Dataform sharing one IAM model, one networking model and one billing system — compounds. Migrating a mature warehouse cross-cloud costs months and buys you portability you will probably never exercise.

### The free tier, honestly

Google Cloud's free tier (the "Free Program", plus the always-free allowances attached to certain products) has two halves, and conflating them causes billing anxiety.

**The $300 trial credit.** New accounts get $300 over 90 days. It applies to everything that is normally billable. It is a credit against charges, not a separate bucket, so it can be consumed by anything — including resources you did not intend to create.

**Always-free allowances.** A set of products have a permanent monthly allowance. From the course's own cost model, the relevant ones are:

| Resource | Monthly free allowance |
|---|---|
| Cloud Storage | 5 GB-month (Standard class, us-central1, us-east1, us-west1) |
| Network egress | 1 GB to a non-Google destination |
| BigQuery | 1 TB of query processing per month |
| Compute Engine | One `e2-micro` instance in each of us-central1, us-east1, us-west1, with 30 GB-month of Standard PD |
| Cloud Run | 2,000,000 requests, 180,000 vCPU-seconds, 1 GB egress |
| Cloud Run functions | 2,000,000 invocations |
| Pub/Sub | 10 GB of message ingest |
| Cloud SQL | $0.30 of usage per month (a shared-core instance for ~7 hours) |
| BigQuery Data Transfer | 1 TB of data transferred per month |
| BigQuery Storage | 10 GB of active logical storage, and 10 GB of long-term logical storage |

Two things people get wrong:

1. **The free tier is per billing account, and the trial credit is per account.** You cannot "reset" by deleting a project. Deleting a project stops the charges but does not restore the credit.
2. **"Always free" still requires the resource to be in a supported region.** A Compute Engine `e2-micro` in `europe-west4` is not free. Storage in `asia-east1` is not free. Region choice is a cost decision before it is a latency decision.

The practical instruction to give any client: **enable a budget alert with a small threshold the day the account is created**, before creating any resources. Google Cloud does not stop a resource when the budget is exceeded; it only notifies you. That notification is the only safety net.

### What this means for the rest of the course

Chapter 1.2 takes "region" from marketing copy to a resource-placement decision with three axes — latency, residency and cost. Chapter 1.3 takes IAM from "grant a role" to "design an access model". Chapter 1.4 covers the compute family you will actually deploy. Chapter 1.5 pulls it all into a proposal framework: how to walk into a room with a client and propose a data processing strategy you can defend.

---

## 🛠️ Hands-On

### Exercise A — Meet the service catalogue

The course ships a local simulator of the platform. It requires no account, no credentials and no bill.

```bash
cd path/to/gcp-de   # the course root
python project/local_runner.py --services
python project/local_runner.py --categories
```

Expected shape of the output:

```text
Compute (6)
  Compute Engine                 Virtual machines you manage yourself.
  App Engine                     ...
```

The catalogue contains **34 services** across **8 categories**: Compute, Storage, Databases, Analytics, Streaming & Messaging, Integration, Security & Governance, AI & ML.

### Exercise B — Write your own catalogue query

The catalogue module is pure Python, so you can import it directly. This is the same code path the linter and the tests exercise.

```python
"""Explore the service catalogue like a service-selection exercise."""
import sys
from pathlib import Path

sys.path.insert(0, "project/core")

from service_catalog import (
    CATEGORIES,
    DATA_ENG_ROLE,
    REGIONS,
    SERVICES,
    services_by_category,
    services_with_deep_dive,
)


def main() -> None:
    print(f"{len(SERVICES)} services, {len(REGIONS)} regions, {len(CATEGORIES)} categories")

    # Which service plays each role in a data platform?
    for role in sorted(set(DATA_ENG_ROLE.values())):
        owners = sorted(
            svc.name for svc in SERVICES.values() if svc.data_role == role
        )
        print(f"{role:<40} {', '.join(owners)}")

    # Which categories have a sibling deep-dive course?
    print("\nservices with a sibling deep dive:")
    for svc in services_with_deep_dive():
        print(f"  {svc.id:<20} -> {svc.deep_dive}")

    # How many services live in each category?
    print("\ncategory sizes:")
    for category in CATEGORIES:
        print(f"  {category:<28} {len(services_by_category(category))}")


if __name__ == "__main__":
    main()
```

Save it as `explore_catalog.py` in the course root and run `python explore_catalog.py`.

### Exercise C — Compare execution models by cost

The cost model lets you price the same workload under different architectures. This is the exercise that makes "serverless" concrete.

```python
"""Price the same workload across architectures."""
import sys
from pathlib import Path

sys.path.insert(0, "project/core")

from cost_model import BIGQUERY_ONDEMAND_PER_TB, compare_architectures, format_comparison


def main() -> None:
    options = compare_architectures(scanned_tb=1.0, partition_factor=0.01)
    print(format_comparison(options))

    # The one number that matters: partitioning is a 100x multiplier.
    partitioned = BIGQUERY_ONDEMAND_PER_TB * 1.0 * 0.01
    unpartitioned = BIGQUERY_ONDEMAND_PER_TB * 1.0
    print(f"\npartitioned 1 TB scan: ${partitioned:.4f}")
    print(f"full 1 TB scan:         ${unpartitioned:.4f}")
    print(f"ratio:                  {unpartitioned / partitioned:.0f}x")


if __name__ == "__main__":
    main()
```

Expected output:

```text
| Architecture | Monthly cost |
|---|---|
| Streaming on Dataflow | $0.0000 |
| Spark on Dataproc | $0.0000 |
| Batch on BigQuery (partitioned) | $0.0625 |
| Batch on BigQuery (unpartitioned) | $6.2500
```

The two zero-cost rows are zero because `compare_architectures()` defaults to `streaming_hours=0`: the Dataflow and Dataproc lines are priced per **vCPU-hour**, and no hours were requested. The teaching point is that ephemeral batch execution is priced on the work performed, while a permanently running cluster is priced on its existence.

The table is sorted **cheapest first**, which is why the two $0.0000 rows lead. That ordering is a function of the inputs, not a fixed ranking: pass `streaming_hours=24` and the table reorders, because 24 hours of Dataflow at $0.0595 per vCPU-hour is no longer free. Never read a $0.00 streaming row as "free" — read it as "the hours were not counted".

### Exercise D — Cloud Shell from your laptop

Cloud Shell is a free Debian shell with `gcloud`, `kubectl`, `docker` and `git` preinstalled, billed against the same project as your code.

```bash
# Authenticate
gcloud auth login

# Who am I, and what account am I billing?
gcloud auth list
gcloud config list
gcloud config set project YOUR_PROJECT_ID

# What services are enabled here?
gcloud services list --enabled --format="table(config.name, config.title)"

# What am I allowed to do in this project?
gcloud projects get-iam-policy $(gcloud config get-value project) \
  --flatten="bindings[].members" \
  --format="table(bindings.role, bindings.members)" \
  --limit=50
```

If `gcloud` is not installed locally, run these in the Cloud Shell web terminal (the `>_` icon in the console) rather than installing the SDK on your machine.

### Exercise E — Understand the free tier before you spend it

```bash
# What quota do you have on the project?
gcloud compute regions list --project YOUR_PROJECT_ID

# Check the free trial status of the billing account
gcloud billing accounts list

# Create a budget with a small threshold, plus alerts at 50%, 90% and 100%
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="gcp-de-course-budget" \
  --budget-amount=20 \
  --threshold-rule=0.5,0.9,0.99
```

Note that the budget does **not** cap spend. It only fires notifications. To actually cap, use a budget with an automated spend cap action, or enforce quotas on the services you are experimenting with.

---

## 🛠️ Common Errors and Fixes

### Error 1 — `ERROR: (gcloud.beta.services.api) The operation failed: The project is not in a valid state`

**When:** You try to enable a service or create resources immediately after creating a project.

**Why:** A newly created project spends a short period propagating through Google's control plane. Resource Manager believes the project exists before every downstream service does.

**Fix:** Wait 30–60 seconds and retry. If it persists, confirm billing is linked to the project — an unlinked project often surfaces as this generic failure rather than a clear billing message.

```bash
gcloud projects describe YOUR_PROJECT_ID
gcloud beta billing projects link YOUR_PROJECT_ID --billing-account=BILLING_ACCOUNT_ID
```

### Error 2 — `ERROR: (gcloud.billing.projects.describe) The billing account does not exist`

**When:** `gcloud billing projects link` fails immediately after you created a billing account.

**Why:** The billing account is created asynchronously. The CLI does not wait for the backend to make it addressable.

**Fix:** List the accounts, confirm the id, and retry the link using the **account ID** rather than the display name. If requests succeed but the bill keeps growing, suspect this one: `gcloud config set project` changes the project but never the billing account, so a project can be linked to an account other than the one holding your trial credit. Check the link explicitly with `gcloud billing projects describe`.

```bash
gcloud billing accounts list
gcloud billing projects link YOUR_PROJECT_ID --billing-account=0A1B2C3D-4E5F6-7890-A1B2-C3D4E5F67890
```

### Error 3 — `ERROR: (gcloud.compute.instances.create) Could not fetch access token: invalid_grant: Bad Request`

**When:** Any authenticated call fails after switching accounts or revoking a session.

**Why:** The cached credential in `~/.config/gcloud/` is stale. Revoking a session or switching a Workspace account invalidates it.

**Fix:** Re-authenticate and, if you have been switching identities, drop the cached account so the wrong account is not silently reused.

```bash
gcloud auth revoke --all
gcloud auth login
gcloud auth list
```

### Error 4 — `ERROR: (gcloud.projects.create) Requested entity already exists`

**When:** `gcloud projects create` with an id that has been used before.

**Why:** Project IDs are **globally unique across all of Google Cloud** and cannot be reused after the project is deleted. The ids `my-project`, `test-project` and `demo` are effectively taken by everyone.

**Fix:** Use a unique suffix — your initials plus a random string, for example `gcp-de-anp7k3`.

```bash
gcloud projects create gcp-de-anp7k3 --name="GCP DE Course"
```

### Error 5 — `ERROR: (gcloud.run.deploy) PERMISSION_DENIED: Permission 'iam.serviceaccounts.actAs' denied on service account 'projects/PROJECT_ID/serviceAccounts/NAME@PROJECT_ID.iam.gserviceaccount.com'`

**When:** You deploy to Cloud Run, GKE or Cloud Functions and the deploy tool tries to attach a service account.

**Why:** Deploying a service with a runtime service account requires the caller to be able to *act as* that service account. This is the `iam.serviceAccounts.actAs` permission, and it is deliberately separate from the service account's own permissions.

**Fix:** Grant `roles/iam.serviceAccountUser` on that specific service account (not `roles/iam.serviceAccountAdmin` at project level).

```bash
gcloud iam service-accounts add-iam-policy-binding \
  NAME@PROJECT_ID.iam.gserviceaccount.com \
  --member="user:you@example.com" \
  --role="roles/iam.serviceAccountUser"
```

### Error 6 — `PERMISSION_DENIED: Cloud Storage bucket has no object access: ... does not have storage.objects.get access to the Google Cloud Storage object.`

**When:** `gsutil cp` from Cloud Shell to a bucket you "have access to".

**Why:** You have `storage.buckets.get` but not `storage.objects.get`. The free-tier role `roles/storage.objectViewer` grants object reads; `roles/storage.admin` grants everything about buckets and objects. If your project grant was `roles/storage.objectCreator` — create but not read — the upload works and the download does not. This exact asymmetry is modelled in the course project.

**Fix:** Grant the role that matches the operation.

```bash
gcloud storage buckets add-iam-policy-binding gs://BUCKET \
  --member="user:you@example.com" \
  --role="roles/storage.objectViewer"
```

---

## 💡 Production Notes

- **Never let a project be the unit of isolation for one workload.** Create one project per environment (`prod`, `staging`, `dev`) and, in a shared organisation, one project per team or per data domain. Project-level IAM is inherited by every resource beneath it, so a single project is a single blast radius — see Chapter 1.3.
- **Enable only the services you need, and audit `gcloud services list --enabled` monthly.** Every enabled service is an API surface someone can call. It also determines which quotas and which free-tier allowances apply.
- **Set budgets, but do not trust them as a control.** A budget alert is a notification with a delay. For a hard-ish control, combine budgets with organization policies that forbid expensive resource types in non-production projects, and with per-service quotas.
- **Cost observability is a day-one requirement, not a month-three one.** Route billing exports to BigQuery and alert on the dimensions that actually blow up: bytes scanned per query, slot-hours per job, egress by destination, and storage growth by class. The course's `cost_model` gives you the shape of these line items before you ever open the console.
- **Design for regional failure from the start.** A multi-region bucket or a BigQuery dataset in a second region costs little and removes a class of outage. A Compute Engine instance with a regional persistent disk is a single-zone resource unless you explicitly attach a regional disk and replicate yourself.
- **Beware the "two-digit retry" trap.** Every API client you write needs exponential backoff with jitter, because a retry storm against a throttled backend is how a small outage becomes a large one. The course's ingestion path handles retries by deduplicating on a deterministic key — the same idea applied to API calls.
- **Treat the region as part of the resource name.** `raw-events-us-central1` and `raw-events-europe-west4` are different buckets with different data and different residency. Naming conventions that encode location make accidental cross-region copying visible in code review.
- **Do not put production and learning in the same billing account.** The free trial credit will be consumed by whichever project is most active, and "most active" is rarely the one you are watching.

---

## 🔑 Key Takeaways

- Cloud's real product is the **control plane**: provisioning, patching and reclamation become API calls rather than procurement projects.
- The five service models differ by **how much of the stack you still own**. Every layer you delegate is a layer that cannot break you at 3 a.m.; every layer you keep is a layer you can break.
- **Serverless means delegated lifecycle, not absent servers.** You are billed for work performed, not capacity reserved.
- **Vertical scaling makes one unit bigger; horizontal scaling makes units more numerous.** Batch data processing needs horizontal scaling to be practical.
- Every cloud benefit has a matching cost exposure — most importantly **unbounded variable spend**, which makes cost engineering a first-class skill.
- For data work, GCP's edge is **integration**: BigQuery, Dataflow, Pub/Sub, Composer, Dataform and the governance products share one identity, networking and billing model.
- Comparing clouds by service names is misleading; compare them by **the abstractions that shape your architecture** — serverless analytics, unified batch/streaming, managed Kubernetes, and how governance is expressed.
- The free tier has two parts: a **$300/90-day trial credit** and **per-product always-free allowances**. Neither is a cap on spend, and the trial credit is consumed by any billable resource.
- Budget alerts are notifications, not limits. Region choice changes whether a resource is free at all.

---

## 📚 Practice Exercises

1. Run `python project/local_runner.py --services` and `--categories`. Write down the eight categories and list every service you could not name from memory before looking. Target: 30 of the 34 services.
2. Run `python project/local_runner.py --compare` and then reproduce the same comparison by hand using `BIGQUERY_ONDEMAND_PER_TB = 6.25` and a partition factor of `0.01`. Explain in two sentences why partitioning by event date changes the price by 100× rather than by a small percentage.
3. Write a script that imports `service_catalog` and prints, for each of the 12 regions, the count of services generally available there. Use `services_available_in(region)`. Then identify the region with the widest service coverage and justify deploying a new production data platform there using latency, residency and cost.
4. Without looking anything up, sketch the five service models (IaaS, PaaS, FaaS, CaaS, SaaS) as nested boxes with the word "you manage" at each boundary. Then check which layer App Engine, Cloud Run and Cloud Run functions each stop at, and which they do not.
5. Create a GCP account (or use an existing one), enable Billing, create a project named `gcp-de-<your-initials><random>` and set a $20 budget with alerts at 50%, 90% and 99%. Then create a Cloud Storage bucket in `us-central1` and confirm it falls under the 5 GB-month free allowance. Repeat the bucket creation in `europe-west4` and check the billing export to see what the non-free region cost.
6. Read the free tier table in the [Google Cloud Free Program documentation](https://cloud.google.com/free/docs/free-cloud-features) and find two products on it that this course does not cover. For each, write one paragraph on what a data engineer would use it for and what the bill would look like when it is misused.
7. In `project/core/cost_model.py`, read the `FREE_TIER` dictionary and write a script that prints the free-tier allowances in a table with the unit of each allowance. Then state which of those allowances would run out first for a team of five students running the course pipeline continuously for a week.
8. Choose one workload you currently run on servers you own. Write two paragraphs: what it would cost per month on Google Cloud using the most expensive plausible architecture, and what it would cost using the cheapest plausible architecture. Then name the one measurement you would need to make first, and explain why guessing is dangerous.

---

## 📖 Further Reading
- [Google Cloud Free Program](https://cloud.google.com/free/docs/free-cloud-features)
- [Cloud Locations and Regions](https://cloud.google.com/about/locations)
- [Google Cloud Pricing](https://cloud.google.com/pricing)
- [Cloud Architecture Center: Choosing a Compute Option](https://cloud.google.com/architecture/choose-compute-option)
- [Compute Engine Documentation](https://cloud.google.com/compute/docs)
- [Google Cloud Training and Certification](https://cloud.google.com/learn/training)
