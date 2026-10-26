# AWS for Data Engineering — CTO / Principal Study Plan

**Source course:** Data Vidhya — *AWS for Data Engineering* by Darshil Parmar.
**Course URL:** https://datavidhya.com/learn/aws-data-engineering/
**Coverage:** 5 modules • 36 lessons
**Audience:** Data engineers targeting **Staff → Principal → Director → VP/CTO**
track in cloud data platforms.

> **How to use this file.** Each lesson is broken into four lenses:
>
> 1. **Theory** — what the lesson teaches and the mental model behind it.
> 2. **Practical Example** — a concrete scenario (numbers, code, costs) that
>    makes the theory stick.
> 3. **AI Use Case** — where GenAI / ML fits in or on top of this lesson
>    (the angle that makes a Principal's resume stand out).
> 4. **CTO / Principal Motivation** — the *career reason* to invest in this
>    topic; what decisions you will be trusted with when you are senior.
>
> The lesson bodies themselves live in `aws_de_full_detail.md`. This file is
> the **decision-grade companion**: it answers *why* each topic matters and
> *how* it shows up in production architecture and in promotion conversations.

---

# Module 1 · Cloud Fundamentals (7 lessons)

## Lesson 1 — AWS vs GCP vs Azure

### Theory

The three hyperscalers are functionally similar but strategically different.
AWS leads market share (~32%) and breadth of services. Azure is strong where
Microsoft is (Active Directory, Office, enterprises with Windows estates).
GCP leads in data/AI primitives (BigQuery, Vertex AI, TPUs) and developer
ergonomics. The real decision is rarely "which cloud is best" — it is
"which cloud already has our identity, contracts, compliance footprint, and
talent pipeline."

| Dimension         | AWS                        | GCP                       | Azure                       |
|-------------------|----------------------------|---------------------------|-----------------------------|
| Market share      | ~32%                       | ~10%                      | ~24%                        |
| Identity          | IAM (mature, complex)      | Cloud IAM                 | Entra ID (best AD integ.)   |
| Object storage    | S3                         | GCS                       | ADLS Gen2                   |
| Data warehouse    | Redshift                   | BigQuery                  | Synapse                     |
| Streaming         | Kinesis / MSK              | Pub/Sub / Dataflow        | Event Hubs                  |
| Orchestration     | Step Functions / MWAA      | Cloud Composer (Airflow)  | Data Factory                |
| AI/ML             | Bedrock + SageMaker        | Vertex AI                 | Azure ML + OpenAI           |
| Pricing model     | Per-second, complex        | Per-second, automatic SUS | EA + per-second             |

**Architectural primitives are similar**; the lock-in is in identity, networking
peering, and data gravity (where the bytes already live).

### Practical Example

A fintech with 200 TB on S3 and 100+ IAM roles cannot lift-and-shift to GCP in
a quarter. The migration cost includes data egress ($0.02/GB out of S3 →
$20k+), DNS cutover, and re-onboarding hundreds of SaaS integrations. By
contrast, a greenfield ML startup with no data should benchmark BigQuery vs
Redshift Serverless on TPC-DS before defaulting to AWS — the cheaper warehouse
often saves $300k/year.

### AI Use Case

GenAI workloads are GPU-bound, not storage-bound. AWS Bedrock gives you
managed Claude / Llama / Mistral behind a single API; Azure OpenAI gives you
OpenAI models with enterprise compliance; Vertex AI gives you Gemini + custom
training. **The AI lens flips the cloud decision for net-new companies** —
"where is the best model API?" often beats "where is the cheapest CPU?"

### CTO / Principal Motivation

You will be asked "why AWS and not GCP?" in your first executive review. The
honest answer: "because our identity, our data, our talent, and our procurement
contracts are already here, and the cloud-migration savings are smaller than
the migration tax." Knowing this answer crisply, with numbers, is the line
between Senior and Staff.

---

## Lesson 2 — Cloud Storage

### Theory

Object storage (S3/GCS/ADLS) is the **default system of record** for analytics.
The mental model: an eventually-consistent key-value store with HTTP verbs
(GET/PUT/DELETE), 11 nines of durability, and tiered pricing based on access
frequency. The five things you must internalize:

1. **Buckets are global-ish, but namespaces are flat** — pick a naming
   convention early (env-team-domain-purpose-region).
2. **Storage classes trade cost for retrieval latency** — Standard (hot),
   IA (warm), Glacier Instant/DIY (cold).
3. **Partitioning is the dominant performance lever** — S3 scans linearly,
   so prefix organization (`s3://bucket/year=2026/month=09/day=28/`) is
   the single biggest query-cost control.
4. **Lifecycle policies automate the tier migration** — never write a cron
   to move data between classes; S3 does it natively.
5. **S3 is not a filesystem** — no append, no random write, no partial read
   of large objects; you rewrite or use multipart.

### Practical Example

A clickstream pipeline writes `s3://events/year=2026/month=09/day=28/hour=14/`
as Parquet. After 30 days, lifecycle moves to IA. After 90 days, to Glacier
Instant Retrieval. Querying a 30-day window scans ~3% of data. Monthly
storage cost for 500 TB at 30-day rolling: ~$7k Standard + ~$3k IA + ~$2k
Glacier = **~$12k/mo**, vs **~$11.5k/mo all-Standard** — but the difference
shows up when you query: Glacier Instant is 1 ms retrieval, Glacier Deep
Archive is 12 hours.

### AI Use Case

**S3 Vectors** (preview in 2026) lets you store and query embeddings directly
in S3 — sub-second vector search at $0.20/GB-month. This collapses the
"vector DB vs S3" debate: small datasets (<10M vectors) live in S3, large
ones move to Pinecone/OpenSearch. As a Principal, you'll decide whether the
company buys a vector DB at all.

### CTO / Principal Motivation

Storage is the largest line item in your AWS bill and the source of every
data-breach headline. Your job at the Principal level is to set the
**bucket-naming standard**, the **lifecycle default**, and the **data-classification
matrix** (public / internal / confidential / regulated). Those three artifacts
prevent 80% of cloud-storage incidents.

---

## Lesson 3 — Cloud Compute

### Theory

Compute in the cloud comes in three forms:

| Form                | What it is                 | Examples                | When to use |
|---------------------|----------------------------|-------------------------|-------------|
| Virtual machines    | EC2 — you own the OS       | EC2, GCE, Azure VM      | Stateful, legacy, custom kernels |
| Containers          | Managed Kubernetes / ECS   | EKS, GKE, AKS          | Microservices, ML serving |
| Serverless          | Code-as-a-function         | Lambda, Cloud Functions | Event handlers, glue, spiky workloads |
| Managed services    | You bring code, cloud runs it | Glue, EMR Serverless, Athena | Data engineering sweet spot |

**The cloud-compute mental model:** pay for *what runs*, not what you reserve.
Auto-scaling, auto-pausing, and serverless collapse idle cost to ~$0.

### Practical Example

A daily ETL job runs 4 hours/day on EC2 (`m5.4xlarge` reserved, ~$0.46/hr
on-demand, ~$0.30/hr 1-yr reserved). Annual cost: $0.30 × 4 × 365 = **$438/yr**.
On Lambda, the same 4 hours × 16 vCPU equivalent × pay-per-ms = **~$300/yr**
but cold starts add latency. Glue Serverless (DPU-hours billed by the second)
often wins for Spark jobs: **~$200/yr**. As a Principal, you make this call
based on team's familiarity with each runtime, not just cost.

### AI Use Case

**GPU economics.** A100s on AWS cost $32/hr reserved. A single fine-tune of a
7B model takes ~6 hours on 8×A100 = $1,500/run. Spot instances drop this to
$500. Bedrock's pay-per-token model eliminates this entirely for inference.
The Principal-level question: "do we own GPUs, rent them, or call an API?"
Each path has a 12-month cost curve you must model.

### CTO / Principal Motivation

Compute decisions compound. A team that defaults to long-lived EC2 will
spend 3× more than a team that uses serverless + spot. As CTO, you sign off
on the **compute default** ("this team uses serverless unless there's a
reason not to") and the **GPU budget envelope**. These are board-level
calls.

---

## Lesson 4 — IAM & Security

### Theory

IAM is **the** attack surface in AWS. The mental model:

- **Principals** (users, roles, services) **assume** roles via **trust policies**.
- **Permissions** are granted by **identity-based** or **resource-based**
  policies.
- **Effective permissions** = union of all policies minus any explicit deny.
- **The principle of least privilege** says: grant exactly what is needed,
  no more.
- **Service Control Policies (SCPs)** are org-wide guardrails that even
  admins cannot bypass.

The 2026 reality: every breach in the last five years (Capital One, Codecov,
Twilio) traced back to over-permissive IAM. **IAM hygiene is job-1 security.**

### Practical Example

A Lambda function reads from S3 and writes to DynamoDB. The role attached
to the function should have:
- `s3:GetObject` on `arn:aws:s3:::my-bucket/data/*`
- `dynamodb:PutItem` on `arn:aws:dynamodb:region:account:table/events`
- Nothing else.

The common anti-pattern: `s3:*` and `dynamodb:*` on `*`. That role, if
exfiltrated, deletes your entire account.

**Tools to enforce:** IAM Access Analyzer (finds unused permissions),
CloudTrail (audits every API call), AWS Config (detects policy drift).

### AI Use Case

**AI agents need scoped credentials.** A LangChain agent calling AWS APIs
should use a **short-lived STS token** (`sts:AssumeRole` with a 15-minute
session), not a long-lived access key. As AI agents proliferate, "machine
identity" becomes the dominant IAM challenge — humans use SSO, agents use
STS chains. This is a Principal-level concern: who in your org owns agent
identity?

### CTO / Principal Motivation

Every compliance audit (SOC 2, ISO 27001, HIPAA) opens with IAM evidence.
At the Principal/Director level, you own the **IAM standard**: how roles are
named, what the trust boundaries are, how break-glass access works, who can
escalate. The Principal who has never had an IAM audit finding is rare;
the one who has a documented, automated remediation is gold.

---

## Lesson 5 — Networking Basics

### Theory

Cloud networking is the plumbing of every data pipeline. The five things
to internalize:

1. **VPC** — your private network in the cloud. Subnets divide it into
   routable segments (public, private, isolated).
2. **Subnets** — AZ-scoped. One subnet lives in exactly one Availability
   Zone.
3. **Route tables** — decide which traffic goes where (local, NAT gateway,
   internet gateway, transit gateway, VPC peering).
4. **Security groups** — instance-level firewalls, stateful.
5. **NACLs** — subnet-level firewalls, stateless (rarely used in practice).

**Endpoints** (Gateway and Interface) keep traffic inside the AWS network
instead of traversing the public internet. For data engineering, **S3
Gateway Endpoints** are free and save NAT cost on heavy S3 workloads.

### Practical Example

A Glue job in a private subnet pulls data from S3. Without a VPC endpoint,
the traffic goes: Glue → NAT Gateway → Internet → S3. The NAT Gateway costs
$0.045/GB processed. At 100 TB/month that's **$4,500/mo** in NAT fees alone.
Add a Gateway Endpoint and the traffic stays inside AWS, NAT cost drops to
$0, query latency drops ~10 ms. One-line change, $54k/year savings.

### AI Use Case

**VPCs for AI workloads.** Bedrock calls happen over public endpoints by
default. For regulated workloads (PII, PHI), you need **Interface Endpoints**
(PrivateLink) into Bedrock, which adds $0.01/hour per ENI but keeps prompts
and responses inside your VPC. As a Principal, you decide: which AI
workloads require PrivateLink, and which can run over public endpoints.

### CTO / Principal Motivation

Network design is invisible when right and catastrophic when wrong. A
Principal-level engineer can read a VPC diagram and predict where the
chokepoints are. The CTO-level question: "if our AWS account is compromised
tonight, can the attacker reach our data warehouse?" The answer comes from
network segmentation. This is board-level risk language.

---

## Lesson 6 — Terraform Basics

### Theory

Terraform (and AWS CDK, Pulumi) treat infrastructure as **declarative
code**. The mental model:

- **State** — what Terraform thinks exists (stored in S3 with DynamoDB
  locking).
- **Plan** — diff between state and desired config.
- **Apply** — bring reality into alignment with config.
- **Modules** — reusable bundles of resources.

The 2026 standard: **all** production infrastructure is in Terraform. No
click-ops in the AWS console. The exception: one-off debugging, which is
**always reverted** by the next `terraform apply`.

### Practical Example

```hcl
resource "aws_s3_bucket" "data_lake" {
  bucket = "acme-data-lake-prod"
  tags = { Environment = "prod", Owner = "data-platform" }
}

resource "aws_s3_bucket_lifecycle_configuration" "tier" {
  bucket = aws_s3_bucket.data_lake.id
  rule {
    id     = "to-ia"
    status = "Enabled"
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
  }
}
```

This 25-line file replaces ~5 console clicks that take 10 minutes each.
Apply takes 30 seconds. Re-running it is idempotent — no surprises.

### AI Use Case

**Terraform + AI code review.** Tools like Kiro, Sourcery, and Claude Code
can review Terraform PRs for: missing encryption, public S3 buckets, IAM
wildcards, untagged resources. A Principal's leverage: "every PR to the
`infra/` folder gets AI-reviewed and human-approved." This catches the
80% of mistakes that humans miss on the 200th PR of the year.

### CTO / Principal Motivation

IaC is the prerequisite for **everything** that follows: reproducible
environments, blue/green deploys, drift detection, audit trails, cost
allocation by resource tag. The Principal-level deliverable is a Terraform
**module library** that new teams can adopt in hours. The CTO-level
question: "can a new engineer stand up a production-grade data pipeline in
their first week?" The answer comes from your IaC maturity.

---

## Lesson 7 — Quiz: Cloud Fundamentals

### Theory

The quiz is a checkpoint, not a lesson. Use it to validate that you can
defend **decisions**, not just recall facts. Each quiz question should
produce a one-paragraph answer a CTO would accept.

### Practical Example

For each module's quiz, write a 1-page cheat sheet: "If asked to pick
between X and Y, the decision tree is..." These become your interview
artifacts and your onboarding docs.

### AI Use Case

Use AI to generate flashcards from each quiz, then drill yourself with
spaced repetition. The retention curve from active recall beats passive
reading 3:1.

### CTO / Principal Motivation

The habit of self-testing compounds. Principals who quiz themselves on
fundamentals stay sharper than those who trust their title.

---

# Module 2 · AWS Data Engineering Stack (11 lessons)

## Lesson 1 — AWS Data Engineering Fundamentals (Video)

### Theory

This is the orientation video. The mental model: AWS data engineering is
five primitives stitched together:

```
Sources → Ingestion → Storage → Processing → Serving → Consumption
   │         │           │           │           │           │
 S3      Kinesis     S3/Iceberg   Glue/EMR    Redshift   Athena
 Kafka    Firehose    Lake FS      Athena      Athena     Quicksight
 DMS     SQS/SNS     DynamoDB     Lambda      OpenSearch Bedrock
```

Each primitive has a **cost-quality-latency** triangle; you pick the
vertex per workload.

### Practical Example

A clickstream pipeline: web SDK → Kinesis Data Streams → Lambda → S3 (raw)
→ Glue (Parquet, partitioned) → Athena (analyst queries) + Redshift
(BI dashboards) + Bedrock (NL→SQL chatbot).

### AI Use Case

Every primitive now has an AI flavor. Kinesis Data Streams can publish to
Bedrock for real-time classification. Glue jobs can be **generated from a
prompt** ("convert CSVs from S3 to Parquet partitioned by date"). Redshift
now has ML functions. Quicksight has natural-language Q. The Principal's
job: pick where AI actually adds value vs. where it's a demo.

### CTO / Principal Motivation

The architecture diagram is the **first deliverable** of any cloud
engagement. Principals can sketch it on a whiteboard in 10 minutes. The
CTO's job is to defend it to the board — *"this is our $4M/year data
platform, here's why each piece earns its cost."*

---

## Lesson 2 — AWS Fundamentals

### Theory

This article grounds the AWS service catalogue for data engineers. The
services you'll use 90% of the time:

- **Compute**: EC2, Lambda, ECS, EKS, Glue, EMR
- **Storage**: S3, EBS, EFS, FSx
- **Database**: RDS, DynamoDB, Aurora, Redshift
- **Analytics**: Athena, EMR, Glue, Kinesis, MSK, OpenSearch
- **ML/AI**: SageMaker, Bedrock, Rekognition, Comprehend
- **Orchestration**: Step Functions, MWAA (Airflow), EventBridge
- **Governance**: Glue Catalog, Lake Formation, IAM, KMS
- **Observability**: CloudWatch, X-Ray, CloudTrail

### Practical Example

A new data engineer should know: "I want to query S3 without spinning up
anything → Athena. I want to schedule a job → Step Functions or MWAA. I
want to stream data → Kinesis or MSK." These defaults are the difference
between a 1-day and 2-week architecture conversation.

### AI Use Case

The "I should use X" decision is increasingly AI-assisted. Tools like
**AWS Well-Architected Labs + Amazon Q** can review your architecture and
suggest services. The Principal's job is to verify the AI's suggestions
against cost and team skills.

### CTO / Principal Motivation

Service-selection literacy is the difference between a Senior and Staff
engineer. Staff engineers pick the right service for the problem; Principals
pick the right service for the **team and the trajectory**. "We use Athena
because we can't afford a Redshift team yet" is a Principal's answer.

---

## Lesson 3 — S3

### Theory

S3 is the data lake's substrate. Mental model:

- **Buckets** are flat namespaces; **prefixes** (`/year=2026/month=09/`)
  are your folder structure.
- **Storage classes** trade retrieval latency for cost.
- **Versioning** keeps every overwritten/deleted object recoverable.
- **Lifecycle policies** automate tier migration.
- **Replication** provides cross-region DR.
- **Event notifications** wire S3 into the rest of your architecture
  (SQS, SNS, Lambda, EventBridge).

### Practical Example

```python
# Producer writes Parquet partitioned by date
df.write.partitionBy("year", "month", "day").parquet(
    "s3://data-lake/events/"
)
```

Athena queries with partition pruning:

```sql
SELECT count(*) FROM events
WHERE year = 2026 AND month = 9 AND day = 28;
-- Scans only ~3 GB instead of 3 TB
```

### AI Use Case

S3 Vectors + Bedrock Knowledge Bases turn S3 into a **fully-managed RAG
backend**. Drop PDFs into a bucket, and Bedrock indexes them, embeds them,
and serves them via a managed retriever. No Pinecone, no Lambda glue.

### CTO / Principal Motivation

S3 is where your company's data lives. The Principal owns the **bucket
standard** (naming, encryption, lifecycle, replication, event routing) and
the **access pattern** (who can read raw vs. clean). This is the data
governance foundation.

---

## Lesson 4 — AWS Glue

### Theory

Glue is AWS's managed Spark service. It comes in three flavors:

1. **Glue ETL Jobs** — Spark scripts (PySpark/Scala) running on managed
   infrastructure.
2. **Glue Crawlers** — Schema discovery; populate the Glue Data Catalog.
3. **Glue Studio** — Visual ETL canvas.

**Glue Data Catalog** is the **Hive Metastore for AWS** — Athena, Redshift
Spectrum, EMR all consult it. A table in the catalog is what makes
`s3://…` queryable from Athena.

### Practical Example

```python
# Glue job: CSV → Parquet, partitioned, schema-on-write
from awsglue.context import GlueContext
from pyspark.context import SparkContext

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

dynamic_frame = glueContext.create_dynamic_frame.from_catalog(
    database="raw",
    table_name="events_csv"
)
# Cast types, dedupe, enrich
clean = dynamic_frame.resolveChoice(specs=[("id", "cast:int")])
# Write as Parquet partitioned by date
glueContext.write_dynamic_frame.from_options(
    frame=clean,
    connection_type="s3",
    connection_options={"path": "s3://clean/events/",
                       "partitionKeys": ["year", "month", "day"]},
    format="parquet"
)
```

### AI Use Case

**Glue Q (now in preview)** lets you describe a job in natural language
and get PySpark. "Convert CSV from S3 to Parquet partitioned by date" →
working script. As a Principal, you decide: which jobs to let AI generate
vs. require hand-written for compliance/review reasons.

### CTO / Principal Motivation

Glue is the "easy button" for Spark on AWS. The Principal-level question:
"why are we paying $X for Glue vs. $Y for EMR Serverless vs. $0 for
Lambda + pandas?" Each option has a different operational footprint. The
CTO's question: "is our data team's productivity bottlenecked by Glue's
limits, or by their PySpark skill?" Both are valid answers.

---

## Lesson 5 — Redshift

### Theory

Redshift is AWS's MPP columnar data warehouse. Mental model:

- **Leader node** — query planner.
- **Compute nodes** — actual storage + processing (each node has slices).
- **WLM (Workload Management)** — query queues; you assign queues to
  user groups.
- **Distribution styles** — KEY, ALL, EVEN; pick based on join keys.
- **Sort keys** — compound vs. interleaved; determines scan pruning.
- **Redshift Serverless** — no cluster to manage; pay per RPU-second.

### Practical Example

```sql
-- Sort key on event date, dist key on user_id
CREATE TABLE events (
    user_id        BIGINT       DISTKEY,
    event_time     TIMESTAMP    SORTKEY,
    event_type     VARCHAR(50),
    payload        SUPER
);

-- Vacuum and analyze maintain sort order
VACUUM SORT ONLY events;
ANALYZE events;
```

### AI Use Case

Redshift ML lets you train models **inside the warehouse** with SQL:

```sql
CREATE MODEL churn_model FROM (
    SELECT tenure, monthly_charges, total_charges,
           churn::int AS label
    FROM customers
) TARGET churn
FUNCTION predict_churn
IAM_ROLE 'arn:aws:iam::...:role/RedshiftML';
```

The Principal's call: when is "ML in the warehouse" the right answer?
(Small models, frequent retraining, no MLOps team.) When is SageMaker the
right answer? (Custom models, GPU training, model registry needed.)

### CTO / Principal Motivation

Redshift is the most expensive single AWS service for most companies after
S3. The Principal owns the **cluster sizing**, **WLM configuration**, and
**spend guardrails**. The CTO owns the Redshift-vs-BigQuery-vs-Snowflake
strategic call. That conversation lands at the board level when you cross
$1M/year on a single warehouse.

---

## Lesson 6 — EMR

### Theory

EMR (Elastic MapReduce) is the **unmanaged** cousin of Glue. You bring
your own Spark/Hive/Hadoop config and run it on EC2. Mental model:

- **Master, Core, Task nodes** — same as a Hadoop cluster.
- **Instance fleets** — mix Spot + On-Demand for cost.
- **EMR Serverless** — same as Glue but you choose the runtime version.
- **EMR on EKS** — Spark on Kubernetes.

**When to use EMR over Glue:** you need specific Spark/Hadoop versions, you
have large long-running clusters, or you want to use Hadoop ecosystem tools
(Hive, Presto, Flink, HBase).

### Practical Example

A 100-node Spark job on EMR with 70% Spot instances:

```python
# emr_launcher.py
emr = boto3.client("emr")
cluster = emr.run_job_flow(
    Name="nightly-aggregation",
    Instances={
        "InstanceGroups": [
            {"InstanceRole": "MASTER", "InstanceType": "m5.xlarge",
             "InstanceCount": 1},
            {"InstanceRole": "CORE", "InstanceType": "r5.4xlarge",
             "InstanceCount": 30,
             "Market": "SPOT", "BidPrice": "0.40"},
            {"InstanceRole": "TASK", "InstanceType": "r5.4xlarge",
             "InstanceCount": 70,
             "Market": "SPOT", "BidPrice": "0.40"},
        ],
        "KeepJobFlowAliveWhenNoSteps": False,
    },
    Applications=[{"Name": "Spark"}, {"Name": "Hadoop"}],
    Steps=[{"Name": "Run Spark", "ActionOnFailure": "TERMINATE",
            "HadoopJarStep": {"Jar": "command-runner.jar",
                              "Args": ["spark-submit", "s3://jobs/etl.py"]}}],
    ReleaseLabel="emr-7.0.0",
)
```

Cost: 30×$0.40 + 70×$0.40 = $40/hour × 4 hours = $160/run, vs $320 if all
on-demand.

### AI Use Case

EMR + Iceberg + SageMaker is the **modern ML feature pipeline**. Train
PyTorch on EMR, log to SageMaker Experiments, register model in SageMaker
Model Registry, deploy to SageMaker Endpoints. The Principal's job:
"feature store on EMR Iceberg, model training on SageMaker" — pick the
right tool for each stage.

### CTO / Principal Motivation

EMR is where the technical-debt signals show up first: oversized clusters,
Spot interruptions, OOM errors. The Principal's deliverable: **EMR right-sizing
automation** that adjusts instance types based on history. The CTO's
question: "do we need Spark at all, or is DuckDB / Athena / Polars enough?"
The answer determines whether your team builds ML pipelines or buys them.

---

## Lesson 7 — Lambda

### Theory

Lambda is the serverless compute primitive. Mental model:

- **Event-driven** — runs in response to S3, SQS, SNS, EventBridge, API
  Gateway, DynamoDB streams, Kinesis, MSK.
- **Pay per ms** — billed in 1 ms increments, minimum 100 ms cold start.
- **Limits** — 15-minute timeout, 10 GB memory, 512 MB /tmp storage
  (configurable up to 10 GB).
- **Concurrency** — default 1000 per region; can be reserved or provisioned.

### Practical Example

```python
# S3 trigger: resize images on upload
import boto3
from PIL import Image

s3 = boto3.client("s3")

def handler(event, context):
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]
        obj = s3.get_object(Bucket=bucket, Key=key)
        img = Image.open(obj["Body"])
        img.thumbnail((800, 800))
        out_key = key.replace("uploads/", "thumbs/")
        out_buf = io.BytesIO()
        img.save(out_buf, format="JPEG")
        s3.put_object(Bucket=bucket, Key=out_key, Body=out_buf.getvalue())
```

Cost: 1 million thumbnails/month × 200 ms × 512 MB = **~$3.30/month**.

### AI Use Case

**Lambda + Bedrock = AI agents.** A Lambda function calls Bedrock with a
prompt, gets a structured response, writes to DynamoDB. This is the
primitive for every serverless AI workflow. The Principal's call: which AI
agents are safe to be stateless (Lambda) vs. which need conversational
state (Step Functions + DynamoDB).

### CTO / Principal Motivation

Lambda is the unit of "decompose everything into events." Principals who
think in Lambda defaults ship 10× faster than teams stuck on EC2 mental
models. The CTO's lever: "we pay $0 for idle, our infra is shaped like
our traffic." That's the cloud-native pitch that lands at the board.

---

## Lesson 8 — Kinesis vs MSK

### Theory

Two managed streaming services:

| Aspect         | Kinesis Data Streams | MSK (Managed Kafka) |
|----------------|----------------------|---------------------|
| Protocol       | AWS-proprietary HTTP | Kafka (native)      |
| Ordering       | Per-shard            | Per-partition       |
| Retention      | Up to 365 days       | Unlimited (S3 sink) |
| Throughput     | Per-shard MB/s       | Per-broker MB/s     |
| Replay         | Yes                  | Yes                 |
| Ecosystem      | AWS-only             | Entire Kafka world  |
| Pricing        | Per shard hour       | Per broker hour     |

**Decision rule:** Kinesis for AWS-native, MSK for Kafka-skilled teams,
MSK Serverless for variable load.

### Practical Example

Clickstream ingestion:
- Kinesis Data Streams: 10 shards × $0.015/hr = $108/mo + $0.014/1000
  PUT payloads. At 100M events/mo = $1,400/mo.
- MSK: 3 × kafka.m5.large brokers × $0.21/hr = $453/mo. Higher floor,
  lower marginal cost at scale.

Break-even: ~500M events/month. Below: Kinesis wins. Above: MSK wins.

### AI Use Case

Streaming AI: Kinesis Data Streams → Lambda (with Bedrock call) → OpenSearch
(real-time search index) for "tag every new product review with sentiment
in real time." This is the ML-in-streaming pattern that justifies the
streaming spend.

### CTO / Principal Motivation

The Kinesis-vs-MSK call is made once and reversed at huge cost. The
Principal's deliverable: **a 1-page decision matrix** that any new team
can apply. The CTO's view: are we a Kafka shop or an AWS-native shop?
That answer shapes hiring, vendor selection, and architecture for years.

---

## Lesson 9 — Step Functions

### Theory

Step Functions is a **state-machine orchestrator** built into AWS. Mental
model:

- **State machines** are JSON definitions (ASL — Amazon States Language).
- **States** — Task, Choice, Parallel, Map, Wait, Pass, Fail, Succeed.
- **Service integrations** — Lambda, ECS, Glue, EMR, Athena, SageMaker,
  Bedrock, DynamoDB, SQS, SNS, EventBridge.
- **Express vs Standard** — Express for high-volume short workflows
  (sub-5-min), Standard for long-running durable workflows (up to 1 year).

### Practical Example

```json
{
  "Comment": "ETL pipeline",
  "StartAt": "Extract",
  "States": {
    "Extract": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {"FunctionName": "extract-from-s3"},
      "Next": "Transform"
    },
    "Transform": {
      "Type": "Task",
      "Resource": "arn:aws:states:::glue:startJobRun.sync",
      "Parameters": {
        "JobName": "transform-events"
      },
      "Next": "Load"
    },
    "Load": {
      "Type": "Task",
      "Resource": "arn:aws:states:::athena:startQueryExecution.sync",
      "Parameters": {
        "QueryString": "INSERT INTO cleaned.events SELECT ...",
        "WorkGroup": "primary"
      },
      "End": true
    }
  }
}
```

This state machine runs the ETL, retries on failure, surfaces errors in
the visual console, and is auditable per execution.

### AI Use Case

**Step Functions + Bedrock = agentic workflows.** Each state is a tool
call or LLM call; the state machine handles retries, branching, and human
approval. This is the dominant 2026 pattern for production AI agents.

### CTO / Principal Motivation

Step Functions is the **default orchestration** for AWS-native workloads.
Principals choose between Step Functions, MWAA (Airflow), and EventBridge
rules — and live with the choice. The CTO's question: "is our orchestration
standardized, or does every team roll their own?" Standardization = hiring
flexibility, auditability, and cost predictability.

---

## Lesson 10 — AWS Architecture

### Theory

This is the capstone architecture lesson. The mental model: every AWS
data architecture is a directed acyclic graph of services. The classic
three-tier pattern:

```
         ┌─────────────────────────────────────────────┐
         │       Sources (Apps, IoT, DB CDC, SaaS)     │
         └─────────────────────────────────────────────┘
                              │
                              ▼
         ┌─────────────────────────────────────────────┐
         │      Ingestion (Kinesis, MSK, DMS, AppFlow)│
         └─────────────────────────────────────────────┘
                              │
                              ▼
         ┌─────────────────────────────────────────────┐
         │   Storage (S3 in Iceberg / Lake Formation)  │
         └─────────────────────────────────────────────┘
                              │
                              ▼
         ┌─────────────────────────────────────────────┐
         │  Processing (Glue, EMR, Lambda, Athena)    │
         └─────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
         ┌────────┐      ┌─────────┐     ┌──────────┐
         │Redshift│      │ Athena  │     │ Bedrock  │
         │  (BI)  │      │(ad-hoc) │     │  (AI)    │
         └────────┘�      └─────────┘     └──────────┘
```

### Practical Example

A reference architecture for a 50-engineer company:
- **S3** as the lake, partitioned by domain/date.
- **Glue Catalog** as the metadata layer.
- **Athena** for analyst ad-hoc SQL.
- **Redshift** for BI dashboards and ML feature engineering.
- **Kinesis** for real-time clickstream.
- **Step Functions** orchestrating nightly ETL.
- **Lake Formation** for fine-grained access control.
- **Bedrock** for the NL→SQL chatbot and document Q&A.

### AI Use Case

The 2026 standard: every architecture includes an **AI tier** (Bedrock or
SageMaker). "Where does AI live in our architecture?" is the new CTO
question. Answering it requires a one-page diagram with the AI tier
explicitly called out.

### CTO / Principal Motivation

The architecture diagram is the **first artifact** a CTO shows to a new
board member, customer, or hire. If you cannot draw it on a whiteboard in
10 minutes, you don't understand your own platform. Principals own the
architecture. CTOs own the **story** the architecture tells.

---

## Lesson 11 — Quiz: AWS DE Stack

### Theory

The quiz validates service-selection literacy. The principle: **never
learn a service in isolation**; always learn it in relation to its
alternatives. The decision tree for every AWS data service:

- "Where does the data live?" → S3 / DynamoDB / RDS.
- "How does it get there?" → Kinesis / MSK / DMS / AppFlow.
- "How do we transform it?" → Glue / EMR / Lambda.
- "How do we serve it?" → Redshift / Athena / OpenSearch.
- "How do we schedule it?" → Step Functions / MWAA / EventBridge.
- "How do we govern it?" → Lake Formation / IAM / KMS.

### Practical Example

For each decision, write a one-sentence rule:
- *Redshift vs Athena:* "Use Redshift when you have <50 analysts with
  sub-second dashboard SLAs; Athena when you have <10 analysts with
  ad-hoc SQL needs."
- *Glue vs EMR:* "Glue for jobs <1 hr, <50 nodes; EMR for everything else."

### AI Use Case

These decision trees are **exactly what an AI assistant needs**. Encode
them in your team's internal docs and let AI surface them during code
review.

### CTO / Principal Motivation

Decision-tree literacy is what makes a Principal's meetings short. "We
use X because the rule says Y" is faster than "let me think." CTOs who
have these rules in their head move 5× faster than those who relitigate
each choice.

---

# Module 3 · Batch Pipelines on AWS (7 lessons)

## Lesson 1 — Ingesting Data

### Theory

Four canonical ingestion patterns:

| Pattern              | Tool               | Use case |
|----------------------|--------------------|----------|
| Change Data Capture  | DMS, Debezium      | Database → S3/Kinesis |
| File transfer        | Transfer Family    | SFTP/FTPS → S3 |
| SaaS connector       | AppFlow            | Salesforce/HubSpot → S3 |
| API + Lambda         | Lambda + EventBridge | Custom REST/GraphQL → S3 |

The decision tree: "Is the source a database? DMS. Is it SFTP? Transfer
Family. Is it SaaS? AppFlow. Is it custom? Lambda."

### Practical Example

DMS for PostgreSQL → S3:
- Source endpoint: RDS PostgreSQL.
- Target endpoint: S3 (Parquet).
- Replication instance: `dms.t3.medium` ($0.10/hr × 24 = $73/mo).
- Tasks: full load + ongoing CDC.

Cost: ~$200/mo for continuous CDC of a 1 TB database.

### AI Use Case

**AI-powered ingestion.** LLM-based schema inference can detect new
columns in source systems and **automatically update Glue Catalog** and
alert data owners. This is the 2026 frontier: ingestion that adapts.

### CTO / Principal Motivation

Ingestion is where data quality is born or killed. The Principal owns the
**ingestion SLA** ("freshness < 15 min for operational data") and the
**vendor decision** (DMS vs. Fivetran vs. Airbyte). The CTO's question:
"is our vendor concentration on data ingestion a single point of
failure?" Fivetran + Airbyte + AWS DMS are the three credible options at
enterprise scale.

---

## Lesson 2 — Athena

### Theory

Athena is **serverless Trino (PrestoSQL) on S3**. Mental model:

- **You bring the data** in S3.
- **You bring the schema** in Glue Catalog.
- **You pay per TB scanned**, $5/TB (Standard).
- **You get standard SQL** (ANSI-ish, with Presto extensions).

### Practical Example

```sql
-- Partitioned Parquet on S3
SELECT date_trunc('hour', event_time) AS hour,
       count(*) AS events,
       count(DISTINCT user_id) AS users
FROM events
WHERE year = 2026 AND month = 9 AND day >= 21
GROUP BY 1
ORDER BY 1;
```

Cost: scans 50 GB (1 week × 7 GB/day) × $5/TB = **$0.25 per query**.
Add columnar format (Parquet/ORC), partitioning, and Glue partition
projection, and the same query costs ~$0.02.

### AI Use Case

**Athena + Bedrock = NL→SQL on the lake.** A Lambda function translates
"how many users logged in last week?" to the SQL above, runs it via
Athena, returns the result. This is the cheap, serverless analytics
chatbot pattern.

### CTO / Principal Motivation

Athena's pay-per-query model is a **cost-control feature**. Redshift costs
$2k-$50k/month whether you use it or not; Athena costs $0 when idle.
Principals choose Athena when usage is spiky and unpredictable. CTOs love
the "we pay $0 when nobody's querying" story for the board.

---

## Lesson 3 — Lakehouse on AWS

### Theory

A **lakehouse** combines the flexibility of a data lake (S3, any format)
with the structure of a data warehouse (ACID transactions, schema
enforcement, time travel). On AWS, the standard is **Apache Iceberg**
(or Delta Lake/Hudi) on S3 with the **Glue Catalog**.

Why Iceberg won:
- **Open standard** (not vendor-locked to Databricks).
- **ACID** via snapshot isolation.
- **Time travel** via snapshot metadata.
- **Schema evolution** without rewriting data.
- **Hidden partitioning** — partition pruning is automatic.
- **Petabyte scale** proven at Netflix, Apple, LinkedIn.

### Practical Example

```python
# Write Iceberg table via PySpark
df.write.format("iceberg").mode("append").save(
    "s3://lake/clean/events/"
)
# Read with time travel
spark.read.option("snapshot-id", "1234567890").format("iceberg").load(
    "s3://lake/clean/events/"
)
```

```sql
-- Athena queries Iceberg directly
SELECT * FROM clean.events
FOR SYSTEM_TIME AS OF '2026-09-01 00:00:00';
```

### AI Use Case

**Iceberg + SageMaker = feature store.** Iceberg's time travel makes
point-in-time feature engineering correct by default. The Principal's
deliverable: "ML features as versioned Iceberg tables." This is the
lakehouse value-prop crystallized.

### CTO / Principal Motivation

Lakehouse is the **strategic bet** AWS made in 2025–2026 to counter
Databricks + Snowflake. Principals who can stand up an Iceberg lake
become the most valuable person in the room when the company asks
"why are we paying $X to Databricks?" The answer is usually "we don't
need to" — and that's a $500k/year win.

---

## Lesson 4 — Loading Redshift

### Theory

Two ingestion paths into Redshift:

| Path                    | Latency | Cost   | Use case |
|-------------------------|---------|--------|----------|
| `COPY` from S3          | Minutes | $      | Bulk loads |
| Kinesis Data Streams    | Seconds | $$$    | Real-time |
| Redshift Streaming Ingestion | Sub-second | $$$ | Clickstream, CDC |
| DMS continuous          | Seconds | $$     | Database CDC |

The principle: **use the slowest path you can afford**. Real-time is
expensive; nightly batches are cheap.

### Practical Example

```sql
COPY sales
FROM 's3://staging/sales/year=2026/month=09/'
IAM_ROLE 'arn:aws:iam::...:role/RedshiftCopy'
FORMAT AS PARQUET;
```

Sort/dist optimization post-load:

```sql
VACUUM SORT ONLY sales;
ANALYZE sales;
```

### AI Use Case

**Redshift ML for predictive loading.** Train a model to predict next-day
volume and **pre-warm Redshift concurrency** accordingly. Reduces query
queueing without over-provisioning.

### CTO / Principal Motivation

Redshift loading is the **hidden cost** that surprises CTOs. A team
loading via real-time Kinesis instead of nightly COPY can blow the budget
in a quarter. Principals own the **loading pattern standard** and the
**cost alarms**. CTOs ask "why is our Redshift bill up 40% this quarter?"
and expect an answer with a graph.

---

## Lesson 5 — Batch Orchestration

### Theory

Batch orchestration = "run jobs A, then B (after A succeeds), then C, on
this schedule." The three dominant tools on AWS:

| Tool              | Type             | When to use |
|-------------------|------------------|-------------|
| Step Functions    | Managed state machine | AWS-native, JSON-defined, <300 state transitions per run |
| MWAA (Airflow)    | Managed Airflow  | Complex DAGs, Python-defined, integrations heavy |
| EventBridge       | Event bus + rules | Cron-like triggers, glue between services |
| Glue Workflows    | Glue-native      | Simple Glue-to-Glue chains |

### Practical Example

A nightly Step Functions state machine:

```json
{
  "StartAt": "RunETL",
  "States": {
    "RunETL": {
      "Type": "Task",
      "Resource": "arn:aws:states:::glue:startJobRun.sync",
      "Parameters": {"JobName": "nightly-aggregates"},
      "Retry": [{"ErrorEquals": ["States.TaskFailed"], "MaxAttempts": 3}],
      "Catch": [{"ErrorEquals": ["States.TaskFailed"],
                 "Next": "AlertTeam"}],
      "Next": "RefreshDashboard"
    },
    "RefreshDashboard": {
      "Type": "Task",
      "Resource": "arn:aws:states:::athena:startQueryExecution.sync",
      "Parameters": {"QueryString": "REFRESH MATERIALIZED VIEW daily_kpi"},
      "End": true
    },
    "AlertTeam": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {"TopicArn": "arn:aws:sns:...:data-alerts",
                     "Message": "ETL failed"},
      "End": true
    }
  }
}
```

### AI Use Case

**AI-assisted DAG debugging.** A Lambda watches Step Functions history
events, calls Bedrock with the failure log, and posts a Slack message
"the nightly ETL failed because column X is missing from table Y — here's
the suggested fix." This reduces MTTR by 70%.

### CTO / Principal Motivation

Orchestration choice is **sticky** — moving from Step Functions to Airflow
(or vice versa) is a 6-month project. The Principal's job: pick right the
first time. The CTO's question: "if AWS has an outage, can we still run
our pipelines?" Multi-region, multi-cloud orchestration becomes a board
topic at certain company sizes.

---

## Lesson 6 — Batch Architecture

### Theory

A reference batch architecture on AWS:

```
S3 (raw) → Glue (clean, Iceberg) → S3 (curated) → Redshift / Athena
                                          │
                                          └──→ SageMaker (training)
                                          └──→ Bedrock (RAG index)
                                          └──→ QuickSight (dashboards)
```

Each box is a separate domain (Bronze / Silver / Gold in medallion
terminology). The architecture is **idempotent at every layer** — re-running
a job produces the same output.

### Practical Example

The **medallion pattern**:
- **Bronze** — raw, immutable, append-only S3.
- **Silver** — cleaned, deduplicated, conformed Iceberg.
- **Gold** — aggregated, business-logic-applied, BI-ready.

```python
# Bronze
df_raw = spark.read.json("s3://raw/events/")
df_raw.write.format("iceberg").mode("append").save("s3://bronze/events/")

# Silver
df_clean = (df_raw
    .dropDuplicates(["event_id"])
    .withColumn("event_time", to_timestamp("ts"))
    .filter(col("user_id").isNotNull()))
df_clean.write.format("iceberg").mode("merge").save("s3://silver/events/")

# Gold
df_gold = df_clean.groupBy("event_date", "country").agg(count("*"))
df_gold.write.format("iceberg").mode("overwrite").save("s3://gold/daily_kpi/")
```

### AI Use Case

The **gold layer is where AI adds value**. Pre-aggregated metrics power
faster LLM context, smaller embedding indexes, and more accurate RAG. The
Principal's deliverable: "the gold layer is curated by humans, augmented
by AI."

### CTO / Principal Motivation

The medallion architecture is **the** data architecture pattern in 2026.
Every Principal can defend it; every CTO can read it. The board-level
value: a clear separation of "what we collect" (bronze) from "what we
trust" (gold). This is the data-governance story.

---

## Lesson 7 — Quiz: Batch Pipelines on AWS

### Theory

The quiz validates architecture decisions. The principle: **every batch
pipeline is a DAG with three layers** (ingest → process → serve) and
**two characteristics** (idempotent, observable).

### Practical Example

For each pattern, write a one-sentence rule:
- *Raw storage format:* "Always use Parquet or Iceberg, never CSV or JSON,
  on S3. Compress with Snappy."
- *Orchestrator choice:* "Step Functions for AWS-only, MWAA for
  heterogeneous, neither if a cron + 3 Lambdas suffices."

### AI Use Case

Encode the rules in a `CLAUDE.md` / `copilot-instructions.md` so AI
assistants default to your team's conventions.

### CTO / Principal Motivation

Quiz yourself on the **failure modes**, not the happy paths. "What
happens if Glue fails on day 30 of 30?" "What happens if S3 has a 1%
packet loss during ingestion?" Principal-level engineers think in
failure modes; CTOs think in incident simulations.

---

# Module 4 · Streaming on AWS (6 lessons)

## Lesson 1 — Kinesis Data Streams Deep Dive

### Theory

Kinesis Data Streams (KDS) is the AWS-proprietary streaming primitive.
Mental model:

- **Shards** are units of capacity. Each shard: 1 MB/s write, 2 MB/s read,
  1000 records/s.
- **Partition keys** determine which shard a record lands on. Hot keys
  create hot shards.
- **Retention** up to 365 days (long retention was added 2024).
- **Enhanced fan-out** gives each consumer 2 MB/s dedicated throughput.
- **Kinesis Agent / KPL / SDK / Lambda** are the producers.
- **KCL / Lambda / Firehose / Flink** are the consumers.

### Practical Example

Capacity math:
- 10,000 events/sec × 1 KB/event = 10 MB/s write.
- Required shards: 10 (since 1 MB/s per shard) → round up to 10.
- Cost: 10 shards × $0.015/hr × 730 hr = **$110/mo**.
- PUT payload cost: 10K/s × 86400 s/day × 30 days × 1 KB = 25 TB
  × $0.014/1000 PUT = **$365/mo**.
- Total: ~$475/mo.

Hot key mitigation: add a random suffix to the partition key,
deduplicate downstream.

### AI Use Case

**Kinesis → Lambda → Bedrock** for real-time classification. Example: a
Kinesis stream of customer support tickets → Lambda → Bedrock → tags the
ticket sentiment → writes to OpenSearch. Sub-second end-to-end.

### CTO / Principal Motivation

Streaming capacity math is where over-provisioning happens. The Principal's
deliverable: a **shard auto-scaling script** based on CloudWatch metrics.
The CTO's question: "what's our streaming cost per million events?" That
unit-economics answer shapes product decisions.

---

## Lesson 2 — Kinesis Data Firehose

### Theory

Firehose is the **serverless delivery stream** — no shards to manage.
Mental model:

- **Producers** PUT records directly.
- **Buffers** in memory or on disk until size/time threshold.
- **Transforms** via Lambda (optional).
- **Destinations**: S3, Redshift, OpenSearch, Splunk, Datadog, HTTP
  endpoints, Iceberg (new in 2024).
- **Format conversion** to Parquet/ORC automatically.
- **Dynamic partitioning** by Lambda return value.

### Practical Example

```python
# Firehose delivery stream with dynamic partitioning
# Producer: any HTTP client PUTting JSON
import boto3, json
firehose = boto3.client("firehose")
firehose.put_record(
    DeliveryStreamName="clickstream",
    Record={"Data": json.dumps({"user_id": "u1",
                                "country": "US",
                                "ts": "2026-09-28T12:00:00Z"})}
)
```

Firehose buffers 5 MB or 60 seconds, then writes to
`s3://lake/clickstream/country=US/year=2026/month=09/day=28/`.

Cost: $0.029/GB ingested. At 1 TB/day = **$870/mo**. No shard math, no
provisioning.

### AI Use Case

**Firehose + Lambda transform = AI-enriched stream.** Lambda calls Bedrock
to summarize or classify each record before writing to S3. The Principal's
example: "every customer review is sentiment-tagged at ingest time and
lands tagged in the gold layer."

### CTO / Principal Motivation

Firehose's **zero-shard math** makes streaming accessible to teams that
can't operate KDS. The Principal's call: "this team uses Firehose because
they don't have streaming expertise; KDS would be cheaper but risky."
CTOs approve the team's tooling roadmap based on skill, not just cost.

---

## Lesson 3 — Event-Driven Patterns (SQS / SNS / EventBridge)

### Theory

Three messaging primitives:

| Service      | Pattern     | Delivery   | Use case |
|--------------|-------------|------------|----------|
| SQS          | Queue       | At-least-once, polling | Decouple producer/consumer |
| SNS          | Pub/Sub     | At-least-once, push | Fan-out to many consumers |
| EventBridge  | Event bus   | At-least-once, push | Cross-account / cross-service events |

**Decision rule:** "One consumer, want to buffer?" → SQS. "Many consumers,
want fan-out?" → SNS or EventBridge. "Want schema registry and replay?"
→ EventBridge.

### Practical Example

SQS visibility timeout — the cornerstone:

```python
# Receive message, hide it from other consumers for 60s
msg = sqs.receive_message(QueueUrl=url,
                          VisibilityTimeout=60)
# Process it (may take 30s)
process(msg)
# If processing succeeded, delete it
sqs.delete_message(QueueUrl=url, ReceiptHandle=msg["ReceiptHandle"])
# If processing failed, the message becomes visible again after 60s
```

**Anti-pattern:** setting VisibilityTimeout < processing time → duplicate
processing. Setting it too high → slow recovery from failures.

### AI Use Case

**EventBridge + Bedrock = reactive AI.** "User signed up" → EventBridge →
Lambda → Bedrock generates a personalized welcome email. No polling,
no cron, no batch.

### CTO / Principal Motivation

Event-driven is the **architectural style** that scales without adding
people. Principals who default to events ship 10× faster than teams stuck
on request-response. CTOs fund this style because every event-driven
service saves headcount.

---

## Lesson 4 — Managed Flink

### Theory

Managed Flink (formerly Kinesis Data Analytics) is the **serverless
Apache Flink** offering. Mental model:

- **Apache Flink** — true stream processing, exactly-once semantics,
  event-time processing, watermarks, stateful operators.
- **Managed Flink** — runs Flink jobs on AWS infrastructure; you bring
  the JAR or SQL.
- **Use case:** CEP (complex event processing), sessionization, anomaly
  detection on streams.

### Practical Example

```sql
-- Managed Flink SQL: tumbling window count per user
SELECT user_id, COUNT(*) AS events,
       TUMBLE_START(event_time, INTERVAL '1' MINUTE) AS window_start
FROM events_stream
GROUP BY user_id, TUMBLE(event_time, INTERVAL '1' MINUTE);
```

### AI Use Case

**Flink ML** is real-time ML scoring. Pre-trained model in S3, Flink
loads it, scores every event in the stream. The Principal's call:
"Flink for sub-second ML scoring, SageMaker for batch training,
Bedrock for generative AI."

### CTO / Principal Motivation

Flink is **expensive and powerful**. Most teams don't need it — they
need Kinesis + Lambda + DynamoDB. The Principal's job: "don't reach for
Flink until you can articulate why Lambda isn't enough." CTOs approve
the **streaming spend** and the **operational complexity** trade-off.

---

## Lesson 5 — Streaming Architecture

### Theory

A reference streaming architecture on AWS:

```
Source (App/IoT/CDC)
    ↓ Kinesis Data Streams (or MSK)
    ├──→ Lambda → DynamoDB (real-time state)
    ├──→ Firehose → S3 (durable history)
    └──→ Managed Flink → OpenSearch (complex analytics)
```

Each arrow is a separate consumer; KDS supports multiple consumer
applications.

### Practical Example

A ride-sharing app:
- Driver app → KDS (10K events/s).
- Consumer 1: Lambda → DynamoDB (live driver positions).
- Consumer 2: Firehose → S3 Iceberg (historical trip data).
- Consumer 3: Managed Flink → OpenSearch (anomaly detection on routes).

### AI Use Case

**AI at every layer.** Bedrock classifies support messages in real time.
SageMaker endpoints score churn risk per session. Bedrock generates
natural-language summaries for dashboards. The Principal's deliverable:
"our streaming layer has AI hooks at every consumer."

### CTO / Principal Motivation

Streaming architecture is the **most expensive** and **most differentiating**
data work a company does. Principals who can stand up this stack are
scarce and well-compensated. CTOs approve it because it unlocks product
features that batch-only competitors can't ship.

---

## Lesson 6 — Quiz: Streaming on AWS

### Theory

The quiz validates stream-selection literacy. The principle: **start
with the simplest primitive** (SQS, SNS) and only reach for KDS / MSK /
Flink when simpler options don't suffice.

### Practical Example

The "streaming decision tree":
1. "Do I need real-time?" → If no, use a nightly batch.
2. "Do I need event-time processing or windows?" → If no, use SQS + Lambda.
3. "Do I need fan-out to many consumers?" → If yes, use KDS or SNS.
4. "Do I need stateful stream processing?" → If yes, use Managed Flink.

### AI Use Case

Encode the decision tree in an internal tool so AI assistants can guide
new engineers.

### CTO / Principal Motivation

The cost of over-engineering streaming is 10× the cost of under-engineering
it. Principals who default to "the simplest queue" save their company
from $500k/year in unnecessary Kinesis spend.

---

# Module 5 · Running AWS Pipelines in Production (5 lessons)

## Lesson 1 — CloudWatch Monitoring

### Theory

CloudWatch is the **observability layer** of AWS. Mental model:

- **Metrics** — numeric time series (CPU, latency, error rate).
- **Logs** — structured text (Lambda logs, application logs).
- **Alarms** — thresholds on metrics; trigger SNS / Lambda / Auto Scaling.
- **Dashboards** — visualizations.
- **Logs Insights** — query logs with a SQL-like language.
- **Anomaly detection** — ML-based metric baselines (no static thresholds).

### Practical Example

A pipeline-freshness alarm (the most important alarm in data engineering):

```python
# Glue job writes success event to a "heartbeat" table
# CloudWatch alarm: time since last heartbeat > 30 minutes → page on-call
```

```python
import boto3
cloudwatch = boto3.client("cloudwatch")
cloudwatch.put_metric_alarm(
    AlarmName="etl-freshness",
    MetricName="LastHeartbeatAge",
    Namespace="DataPipeline",
    Statistic="Maximum",
    Period=300,
    EvaluationPeriods=1,
    Threshold=1800,  # 30 minutes
    ComparisonOperator="GreaterThanThreshold",
    AlarmActions=["arn:aws:sns:...:oncall"],
)
```

### AI Use Case

**AIOps on CloudWatch.** Use DevOps Guru (AWS ML service) or a custom
Bedrock analysis of CloudWatch Logs Insights queries. "Detect anomalies
in error rate across 100 Lambda functions and summarize in Slack." This
is the AI-on-AI pattern that's emerging in 2026.

### CTO / Principal Motivation

CloudWatch alarms are the **insurance policy** that pays for itself the
first time they fire. Principals own the **alarm standard** ("every
production pipeline has 5 alarms"). CTOs see the **MTTR dashboard**
(mean time to recovery) — that's a board metric.

---

## Lesson 2 — Cost Optimization

### Theory

The five cost levers on AWS, ranked by impact:

1. **Right-sizing** — bigger savings than Reserved Instances in most
   cases. Stop paying for 5 TB Redshift when 1 TB suffices.
2. **Storage tiering** — S3 lifecycle; move to IA/Glacier automatically.
3. **Spot instances** — 70% savings on fault-tolerant workloads (EMR,
   Glue transient, ECS batch).
4. **Reserved Instances / Savings Plans** — 30-60% discount for 1-yr or
   3-yr commitments.
5. **Cleanup orphaned resources** — unused EBS volumes, idle EIPs,
   abandoned snapshots.

The principle: **cost optimization is a continuous practice, not a
quarterly project**.

### Practical Example

```python
# AWS Cost Explorer + Trusted Advisor + custom script
# Find idle Redshift clusters
import boto3
redshift = boto3.client("redshift")
for cluster in redshift.describe_clusters()["Clusters"]:
    if cluster["DBConnections"] == 0 and cluster["TotalStorageInMegabytes"] > 100000:
        print(f"Idle cluster: {cluster['ClusterIdentifier']}")
        # Notify: should we downsize or pause?
```

A 100-node idle EMR cluster costs $10k/month. Pausing it saves the company
$120k/year — one engineer's afternoon.

### AI Use Case

**AI cost optimizers.** Tools like AWS Cost Anomaly Detection (built-in
ML) alert on cost spikes. Third-party tools (CloudHealth, Spot.io, Vantage)
use LLMs to recommend right-sizing. The Principal's call: which tool,
and what's the human review process.

### CTO / Principal Motivation

Cost optimization is the **most quantifiable** Principal contribution.
"$500k/year saved by right-sizing" is a promotion packet bullet. CTOs
fund cost-engineering roles because the ROI is obvious to the CFO.

---

## Lesson 3 — Pipeline Security

### Theory

Three pillars:

1. **Identity** — IAM roles, least privilege, short-lived STS tokens.
2. **Encryption** — at rest (KMS) and in transit (TLS).
3. **Network** — private subnets, VPC endpoints, PrivateLink.

**Defense in depth:** never rely on a single layer. Even if S3 is
public, the KMS key should reject unauthorized decryption.

### Practical Example

A secure Glue job:
- Runs in a **private subnet** with no NAT.
- Uses a **Gateway Endpoint** for S3.
- Has an **IAM role** scoped to specific tables.
- KMS-encrypts the S3 output with a customer-managed key.
- CloudTrail logs every API call.

### AI Use Case

**AI agents with scoped credentials.** As agents proliferate, "machine
identity" becomes the dominant security concern. The Principal's
deliverable: "every AI agent gets a unique IAM role, scoped to one
purpose, with a 15-minute session." This is the 2026 frontier.

### CTO / Principal Motivation

Security is the **non-negotiable**. Principals who ship insecure pipelines
get fired. CTOs who ignore security get breached. The Principal's
deliverable: a **security review checklist** that every pipeline must
pass before production.

---

## Lesson 4 — CI/CD for Pipelines

### Theory

CI/CD for data pipelines means:

1. **Version control** — code, IaC, configs in Git.
2. **Automated tests** — unit (functions), integration (small data),
   schema (column-level diffs).
3. **Staging environment** — mirror of production, isolated data.
4. **Deployment** — blue/green or canary on production pipelines.
5. **Observability** — same metrics in dev as in prod.

The tools: **GitHub Actions**, **AWS CodePipeline**, **CodeBuild**.

### Practical Example

```yaml
# .github/workflows/deploy-pipeline.yml
name: Deploy Data Pipeline
on:
  push:
    branches: [main]
    paths: ['pipelines/**']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with: {python-version: '3.11'}
      - run: pip install -r requirements.txt
      - run: pytest tests/unit/
      - run: pytest tests/integration/ --env=staging
      - name: Schema diff
        run: python scripts/schema_diff.py

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to prod
        run: |
          aws s3 sync pipelines/ s3://prod-pipelines/
          aws glue update-job --job-name nightly-etl \
            --job-update 'Command={ScriptLocation=s3://prod-pipelines/etl.py}'
```

### AI Use Case

**AI code review on Terraform / Glue scripts.** Use Bedrock or Claude
to review PRs for: missing encryption, hard-coded credentials, untagged
resources, missing IAM scopes. The Principal's deliverable: "every PR
to `data-platform/` is reviewed by AI + a human."

### CTO / Principal Motivation

CI/CD maturity is the **leading indicator** of platform reliability.
Teams with mature CI/CD have 5× fewer incidents than teams without.
Principals own the **pipeline-of-pipelines** (the meta-pipeline that
deploys pipelines). CTOs see the **deployment frequency** dashboard —
that's a DORA metric that the board understands.

---

## Lesson 5 — Quiz: Running AWS Pipelines in Production

### Theory

The production-readiness checklist:

| Aspect       | Question |
|--------------|----------|
| Monitoring   | Do we have alarms on freshness, error rate, latency, cost? |
| Security     | Least-privilege IAM? Encrypted at rest and in transit? |
| Cost         | Right-sized? Tiered storage? Reserved Instances? |
| Reliability  | Multi-AZ? Multi-region? Backup and restore tested? |
| CI/CD        | Every change reviewed, tested, deployable in <30 min? |
| Documentation | Runbook for every alarm? Architecture diagram current? |

### Practical Example

For each pipeline, maintain a **production-readiness scorecard**. The
goal: 100% green before declaring GA.

### AI Use Case

Use AI to auto-generate runbooks from CloudWatch alarms. "When this
alarm fires, here's the investigation checklist" — generated from the
last 5 incident retrospectives.

### CTO / Principal Motivation

Production readiness is a **cultural standard**. The Principal's
contribution: "no pipeline ships without 100% on the scorecard."
CTOs enforce this at the platform level. The board sees the **reliability
metric** — uptime, MTTR, incident count — and that's the data-platform
brand.

---

# Closing Notes

## The Promotion Path from this Course

| Level        | Skill unlocked by this course | Compensation signal |
|--------------|--------------------------------|---------------------|
| Senior DE    | Hands-on AWS data pipeline build/deploy | $150-200k |
| Staff DE     | Architecture decisions across the stack | $200-280k |
| Principal DE | Platform-level decisions; vendor selection; multi-team patterns | $280-400k |
| Director / VP | Org-level platform strategy; cost & headcount ownership | $350-500k+ |
| CTO          | Cloud strategy; board communication; vendor negotiation | $400-700k+ |

## The Single Most Important Habit

After each lesson, write a **1-page memo**: "If asked about this topic
in an executive review, here's what I would say." That habit — turning
technical knowledge into **defensible artifacts** — is what separates
engineers who plateau at Staff from engineers who make Principal and
beyond.

## Cross-References

- **AWS DE full article bodies** — `aws_de_full_detail.md` in this folder.
- **DE Foundations track** — `01_de_foundations_track.md`.
- **dbt track** — `08_dbt_course.md`.
- **Interview prep** — `05_de_interview_prep.md`.
