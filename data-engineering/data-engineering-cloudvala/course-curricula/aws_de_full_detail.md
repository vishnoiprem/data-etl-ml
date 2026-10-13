# AWS for Data Engineering — Full-Detail Course Content

**Source attribution:** Course content from Data Vidhya (https://datavidhya.com/)
by **Darshil Parmar (Founder & Lead Instructor, Data Vidhya)**.
Course URL: https://datavidhya.com/learn/aws-data-engineering/

**Coverage:** 5 modules • 36 lessons
**Last updated on Data Vidhya:** Jul 10, 2026
**Reproduced in `data-enginnering-cloudvala/course-curricula/`** as a
study-path reference. Full-detail versions of the deep-dive articles are
included where the full body was extractable from the public page.

> **Note on coverage:** This file contains the complete 36-lesson curriculum
> (titles, formats, descriptions) plus the full article bodies for the
> deep-dive lessons that were extractable from the public pages
> (S3 for DE, Amazon Athena, CloudWatch Monitoring, Kinesis Data Streams,
> Ingesting Data into AWS). The remaining articles are JS-rendered and
> require a logged-in browser session to extract. Their descriptions are
> included below as abstracts.

---

## Module 1: Cloud Fundamentals — 7 lessons

### 1. AWS vs GCP vs Azure — *Article*
A comparison of the three major cloud providers across compute, storage, and
data-engineering relevant services. *Abstract only — JS-rendered.*

### 2. Cloud Storage — *Article*
An overview of cloud object storage models — durability, access patterns,
cost, and consistency. *Abstract only.*

### 3. Cloud Compute — *Article*
An introduction to cloud compute primitives (instances, containers, serverless)
and how each maps to data-engineering workloads. *Abstract only.*

### 4. IAM & Security — *Article*
An article covering AWS Identity & Access Management policies, roles, and
least-privilege patterns for data engineers. *Abstract only.*

### 5. Networking Basics — *Article*
A primer on VPCs, subnets, security groups, and private connectivity for
data pipelines. *Abstract only.*

### 6. Terraform Basics — *Article*
An article on using Terraform to declare AWS infrastructure as code. *Abstract only.*

### 7. Module Quiz — *Article*
A short assessment covering the cloud-fundamentals module. *Abstract only.*

---

## Module 2: AWS Data Engineering Stack — 11 lessons

### 1. AWS Data Engineering Fundamentals — *Video*
A video orientation to the AWS data stack: storage, catalog, compute, and
orchestration services.

### 2. AWS Fundamentals — *Article*
An article outlining the AWS services data engineers use most. *Abstract only.*

### 3. S3 for Data Engineers — *Article*  *(full body included below)*

### 4. AWS Glue — *Article*
A walkthrough of Glue's catalog, crawlers, and ETL jobs. *Abstract only.*

### 5. Amazon Redshift — *Article*
An article on Redshift's architecture, WLM, sort keys, and the spectrum
extension for lake queries. *Abstract only.*

### 6. Amazon EMR — *Article*
An article covering EMR's managed Hadoop/Spark clusters, when to pick EMR
over Glue, and cost considerations. *Abstract only.*

### 7. AWS Lambda for Data Pipelines — *Article*
An article on Lambda execution model, layers, event source mappings, and
production patterns for data engineering. *Abstract only.*

### 8. Kinesis vs MSK — *Article*
A side-by-side comparison of managed streaming options on AWS. *Abstract only.*

### 9. Step Functions — *Article*
An article on orchestrating multi-step pipelines with state machines and
retry/branch logic. *Abstract only.*

### 10. AWS Pipeline Architecture — *Article*
A reference architecture tying S3, Glue, Athena, Redshift, Lambda, and
Step Functions into end-to-end pipelines. *Abstract only.*

### 11. Module Quiz — *Article*
An assessment covering the AWS data stack module. *Abstract only.*

---

## Module 3: Batch Pipelines on AWS — 7 lessons

### 1. Ingesting Data into AWS — *Article*  *(full body included below)*

### 2. Amazon Athena — *Article*  *(full body included below)*

### 3. Lakehouse on AWS (Lake Formation + Iceberg) — *Article*
An article on building a transactional lakehouse with Iceberg tables,
Lake Formation governance, and Glue catalog. *Abstract only.*

### 4. Loading Redshift — *Article*
An article on loading patterns from S3 into Redshift (COPY, Kinesis
delivery streams, federated queries). *Abstract only.*

### 5. Orchestrating Batch Pipelines — *Article*
An article on choosing between Step Functions, MWAA (Managed Airflow),
and EventBridge schedules for batch jobs. *Abstract only.*

### 6. Batch Pipeline Architecture — *Article*
A walkthrough of an end-to-end batch architecture. *Abstract only.*

### 7. Module Quiz — *Article*
An assessment covering batch pipelines. *Abstract only.*

---

## Module 4: Streaming on AWS — 6 lessons

### 1. Kinesis Data Streams — *Article*  *(full body included below)*

### 2. Kinesis Data Firehose — *Article*
An article on Firehose's zero-ops delivery to S3, Redshift, and Splunk,
including batching and format conversion. *Abstract only.*

### 3. SQS / SNS / Lambda Event-Driven Patterns — *Article*
An article on combining SQS, SNS, and Lambda for decoupled fan-out and
event-driven processing. *Abstract only.*

### 4. Managed Flink — *Article*
An article on Kinesis Data Analytics / Managed Flink for stateful
stream processing on AWS. *Abstract only.*

### 5. Streaming Architecture — *Article*
A reference streaming architecture with Kinesis, Lambda, Flink, and
downstream sinks. *Abstract only.*

### 6. Module Quiz — *Article*
An assessment covering streaming on AWS. *Abstract only.*

---

## Module 5: Running AWS Pipelines in Production — 5 lessons

### 1. CloudWatch Monitoring — *Article*  *(full body included below)*

### 2. Cost Optimization — *Article*
An article on AWS cost levers: S3 storage class transitions, Athena scan
reduction, Redshift sizing, and Reserved Instance planning. *Abstract only.*

### 3. Pipeline Security — *Article*
An article on encryption, IAM boundaries, VPC isolation, KMS, and audit
logging for data pipelines. *Abstract only.*

### 4. CI/CD for Pipelines — *Article*
An article on deploying pipeline code through GitHub Actions / CodePipeline
to test sandboxes before production promotion. *Abstract only.*

### 5. Module Quiz — *Article*
An assessment covering production-pipeline concerns. *Abstract only.*

---

# Full Article Bodies

## Module 2 · Lesson 3: S3 for Data Engineers

*Written by Darshil Parmar, Founder & Lead Instructor, Data Vidhya.
Published Mar 16, 2026.
Course URL: https://datavidhya.com/learn/aws-data-engineering/aws-data-stack/s3-for-de/*

> **Key Insight** — S3 is not just storage; it is the backbone of the AWS
> data platform. Every design decision you make about how data lands in S3
> (partitioning, file size, format) has a direct and measurable impact on
> downstream query performance and cost.

### S3 as a Data Lake Foundation

S3 offers 11 nines (99.999999999%) of durability. That means if you store
10 million objects, you can statistically expect to lose one object every
10,000 years. For practical purposes, S3 does not lose data.

The pricing model is what makes it a data lake default:

| Storage Class | Cost per GB/month | Use Case |
|---|---|---|
| S3 Standard | $0.023 | Hot data, frequently queried |
| S3 Infrequent Access (IA) | $0.0125 | Data accessed monthly or less |
| S3 Glacier Instant Retrieval | $0.004 | Archive with millisecond access |
| S3 Glacier Deep Archive | $0.00099 | Long-term compliance storage |

At $0.023/GB/month, storing 1 TB of hot data costs about $23/month.
Storing that same data in Redshift costs $250+/month. This is why the
modern pattern is: store everything in S3, compute only what you need.

### Partitioning Strategies

Partitioning is the single most impactful decision you make for S3-based
data lakes. A well-partitioned dataset lets query engines like Athena,
Spark, and Redshift Spectrum skip irrelevant data entirely — this is
called **partition pruning**.

#### Hive-Style Partitioning

The standard pattern uses key=value directory naming:

```
s3://my-data-lake/events/
  year=2025/month=01/day=15/
  year=2025/month=01/day=16/
  year=2025/month=02/day=01/
```

When Athena sees `WHERE year = 2025 AND month = 01`, it reads only the
matching prefixes and skips everything else. On a 5 TB dataset partitioned
by date, a single-day query might scan only 15 GB instead of the full
5 TB — that is a 99.7% reduction in data scanned, which directly
translates to cost savings (Athena charges $5/TB scanned).

#### Common Partitioning Schemes

| Data Type | Recommended Partitioning | Why |
|---|---|---|
| Event/clickstream data | `year/month/day/hour` | High volume, time-series queries dominate |
| Transaction data | `year/month/day` | Daily batch processing, moderate volume |
| Customer data | `region/year/month` | Often filtered by region first |
| Log data | `service/year/month/day` | Multi-service environments need service-level filtering |

#### The Over-Partitioning Trap

Here is where junior engineers get into trouble. More partitions are not
always better.

If you partition clickstream data by
`year/month/day/hour/minute/user_id`, you end up with millions of tiny
directories, each containing a handful of small files. This is worse
than no partitioning at all because:

1. **S3 listing operations become expensive** — listing millions of
   prefixes adds significant latency.
2. **Small files kill query performance** — opening and reading 100,000
   tiny files is far slower than reading 100 well-sized files.
3. **Glue Crawler goes haywire** — it takes hours to catalog millions
   of partitions.

> **Over-Partitioning Is a Production Killer** — A team I worked with
> partitioned user events by `user_id`. They ended up with 15 million
> S3 prefixes. Athena queries that should have taken 10 seconds were
> timing out after 5 minutes. The fix was re-partitioning by
> `year/month/day` only, compacting files to 256 MB each, and the same
> queries dropped to under 15 seconds. That is a 95% improvement from
> fixing partitioning alone.

### File Sizing: The 128 MB to 1 GB Sweet Spot

S3 has no minimum file size, but every query engine has an optimal file
size range. The sweet spot is **128 MB to 1 GB** for columnar formats
like Parquet or ORC.

Why this range matters:

- **Too small (under 1 MB)**: The overhead of opening each file, reading
  metadata, and establishing connections dominates actual data reading.
  Processing 1 million 1 KB files is dramatically slower than processing
  one 1 GB file.
- **Too large (over 5 GB)**: Individual tasks cannot be parallelized
  efficiently, and retry costs are high if a single file read fails.
- **The sweet spot (128 MB - 1 GB)**: Balances parallelism, read
  efficiency, and retry cost.

#### Compaction Strategy

In production, upstream systems often produce small files — a Lambda
function writing one file per event, a Kafka consumer flushing every
30 seconds, or a micro-batch Spark job. You need a **compaction job**
that periodically merges small files into optimally-sized ones.

```python
# Simple Spark compaction job
df = spark.read.parquet("s3://lake/events/year=2025/month=01/day=15/")
df.coalesce(target_file_count).write.mode("overwrite").parquet(
    "s3://lake/events-compacted/year=2025/month=01/day=15/"
)
```

A good rule of thumb: if your partition has more than 100 files or most
files are under 10 MB, you need compaction.

### Lifecycle Policies for Cost Optimization

Data has a temperature. Yesterday's data is hot — everyone queries it.
Last month's data is warm. Last year's data is cold but might be needed
for compliance. Five-year-old data is frozen but legally required.

S3 Lifecycle Policies automate transitions between storage classes:

```json
{
  "Rules": [
    {
      "ID": "OptimizeStorageCosts",
      "Status": "Enabled",
      "Transitions": [
        { "Days": 30, "StorageClass": "STANDARD_IA" },
        { "Days": 90, "StorageClass": "GLACIER_IR" },
        { "Days": 365, "StorageClass": "DEEP_ARCHIVE" }
      ]
    }
  ]
}
```

**Real cost impact**: A 10 TB data lake with no lifecycle policy costs
~$230/month. With lifecycle transitions moving 70% of data to IA after
30 days and 50% to Glacier after 90 days, the same lake costs ~$80/month.
That is a 65% savings with zero code changes to your pipeline.

> **Pro Tip** — Set lifecycle policies on day one, not after your S3 bill
> surprises you. The most common mistake is storing years of historical
> data in S3 Standard when it is only queried during annual audits.

### Event-Driven Pipelines

S3 is not just passive storage — it is an event source. Every time a file
lands in S3, it can trigger downstream processing automatically.

#### S3 Event Notifications

S3 can send notifications to Lambda, SQS, or SNS when objects are
created, deleted, or restored:

```
S3 PutObject → S3 Event Notification → Lambda Function → Start Glue Job
```

This is the foundation of event-driven data pipelines. Instead of
polling S3 every 5 minutes to check if new files have arrived, you let
S3 tell you.

#### EventBridge Integration

For more complex routing, S3 integrates with Amazon EventBridge, which
supports filtering, transformation, and multi-target routing:

```
S3 PutObject → EventBridge Rule (filter by prefix/suffix) → Multiple targets:
  → Lambda (lightweight validation)
  → Step Functions (complex workflow)
  → SQS (buffered processing)
```

EventBridge is the better choice when you need to route events based on
file path patterns, fan out to multiple consumers, or apply complex
filtering logic.

#### The SQS Buffer Pattern

For high-volume pipelines, sending S3 events directly to Lambda can
cause throttling. The production pattern is:

```
S3 → SQS Queue → Lambda (polls SQS in batches)
```

SQS acts as a buffer. If 10,000 files land simultaneously, SQS absorbs
the burst and Lambda processes them at a controlled rate. This prevents
Lambda concurrency limits from causing dropped events.

### S3 Security for Data Engineers

Security is not optional — it is a job requirement.

- **Bucket policies**: Control access at the bucket level. Default to
  denying all public access.
- **IAM roles**: Grant least-privilege access. Your Glue job should have
  read access to source buckets and write access to destination buckets
  — nothing more.
- **S3 encryption**: Enable SSE-S3 (default) or SSE-KMS for
  compliance-sensitive data. Since January 2023, all new S3 objects are
  encrypted by default.
- **VPC endpoints**: Route S3 traffic through your VPC to avoid data
  traversing the public internet. This is a requirement for most
  compliance frameworks.
- **Access logging**: Enable S3 server access logging for audit trails.

### Common Mistakes

1. **No partitioning**: Storing all data in a flat prefix. Every query
   scans everything.
2. **Over-partitioning**: Too many partition columns creating millions
   of tiny directories.
3. **Small files**: Not running compaction, leading to millions of
   files under 1 MB.
4. **No lifecycle policies**: Paying Standard pricing for data that has
   not been accessed in years.
5. **Public buckets**: Misconfigured bucket policies exposing sensitive
   data. AWS now blocks public access by default, but legacy buckets
   remain a risk.
6. **Ignoring request costs**: S3 GET requests cost $0.0004 per 1,000.
   Scanning millions of small files generates millions of GET requests,
   and the request cost can exceed the storage cost.
7. **Not using Parquet/ORC**: Storing data as CSV or JSON instead of
   columnar formats. Parquet typically achieves 75–90% compression over
   JSON and supports predicate pushdown.

### In an Interview

> **Interview Relevance** — S3 questions appear in virtually every AWS
> data engineering interview. Here is how they typically surface by level:
>
> **Junior/Mid Level**: "How would you organize data in S3 for a data
> lake?" Talk about Hive-style partitioning, choosing the right partition
> keys based on query patterns, and file formats (Parquet over CSV).
> Mention the 128 MB – 1 GB file size sweet spot.
>
> **Senior Level**: "We have a 10 TB data lake and Athena queries are
> slow. How would you diagnose and fix it?" Walk through: check
> partitioning strategy, check file sizes (small file problem), check if
> queries align with partition keys, check if columnar format is used,
> and discuss compaction. Mention the real cost: Athena charges $5/TB
> scanned, so reducing scan from 10 TB to 100 GB saves $49.50 per query.
>
> **Staff+ Level**: "Design an event-driven ingestion pipeline on S3."
> Describe the full pattern: S3 events to EventBridge for routing, SQS
> for buffering, Lambda for lightweight validation, Step Functions or
> Glue for heavy processing. Discuss idempotency (what happens when the
> same file triggers twice), exactly-once processing guarantees, and
> cross-account data sharing with bucket policies and IAM roles.
>
> Companies that ask this: Amazon, Netflix, Airbnb, any company with a
> data lake on AWS.

---

## Module 3 · Lesson 2: Amazon Athena

*Written by Darshil Parmar, Founder & Lead Instructor, Data Vidhya.
Published Jul 10, 2026.
Course URL: https://datavidhya.com/learn/aws-data-engineering/batch-pipelines/amazon-athena/*

Your ingestion pipelines are landing files in S3, and within a day someone
from analytics asks the obvious question: "Can I query this?" The old
answer involved standing up a database, writing load jobs, and waiting a
sprint. The naive modern answer is to download files and poke at them
with pandas, which works until the data is 40 GB and the analyst's
laptop starts sounding like a jet engine.

The right answer is Amazon Athena: you write SQL, Athena runs it directly
against the files in S3, and you pay only for the data the query reads.
No cluster, no loading step, no server to size. It is the fastest path
from "files in a bucket" to "answers in a dashboard," and for a lot of
teams it quietly becomes the primary query engine for the entire lake.

But Athena has one economic rule that dominates everything else about it,
and teams that do not internalize it end up with five-figure monthly bills
for queries that should cost cents. This lesson is about how Athena
executes, and how that one rule should shape every table you create.

### How a query actually executes

Athena is a managed, serverless deployment of **Trino** (the engine
formerly called Presto). When you submit a query:

1. Athena parses your SQL and asks the **Glue Data Catalog** what the
   table means: which S3 location, which file format, which columns,
   which partitions. Athena stores no data and no schema itself; the
   catalog you met in the Glue lesson is the single source of truth.
2. The planner works out which S3 objects it actually needs to read,
   using partition values and file metadata to skip everything irrelevant.
3. A fleet of workers AWS manages for you reads those objects in
   parallel, executes the query, and writes the result set to an S3
   output location you configure.
4. You get charged **$5 per TB of data scanned**, with a 10 MB minimum
   per query. Not per hour, not per query, not per row returned. Per byte
   read from S3.

That pricing model is the rule that dominates everything. A query that
returns 5 rows can cost $25 if it had to read 5 TB to find them. The
entire craft of using Athena well is making queries read less.

### File format and partitioning are the whole game

Two decisions control scan volume: how files are laid out in S3, and what
format they are in. Here is a worked example with real numbers.

Say your clickstream ingestion lands 5 GB of JSON per day, and you have
a year of history: roughly 1.8 TB of raw JSON at `s3://raw/events/`. An
analyst wants yesterday's checkout events:

```sql
SELECT user_id, event_type, ts
FROM raw_events
WHERE date(from_iso8601_timestamp(ts)) = date '2026-07-09'
  AND event_type = 'checkout';
```

Against raw JSON with no partitions, Athena has no way to know which
files contain July 9. It reads all of them, and JSON gives it no way to
read just three columns out of forty either, because a JSON file has to
be parsed line by line in full. **Scan: 1.8 TB. Cost: $9.00.** For one
query. Run a dashboard with ten of these on a refresh schedule and you
are at hundreds of dollars a day.

Now the same data, stored properly: partitioned by date and converted to
Parquet.

```
s3://lake/events/dt=2026-07-08/part-0001.parquet
s3://lake/events/dt=2026-07-09/part-0001.parquet
s3://lake/events/dt=2026-07-09/part-0002.parquet
```

```sql
SELECT user_id, event_type, ts
FROM events
WHERE dt = '2026-07-09'
  AND event_type = 'checkout';
```

Two things happen. **Partition pruning:** because `dt` is a partition
column, the planner reads only the `dt=2026-07-09/` prefix. That alone
cuts 1.8 TB to about 5 GB. **Columnar reads:** Parquet stores each column
separately with min/max statistics per block, so Athena reads just the
three columns the query touches, and compression shrinks them further.
Realistic scan for this query: around 150 MB. **Cost: about $0.00075.**
Call it a tenth of a cent.

| Layout | Data scanned | Cost per query | Cost for 100 queries/day, monthly |
| --- | --- | --- | --- |
| Raw JSON, no partitions | 1.8 TB | $9.00 | $27,000 |
| JSON, date-partitioned | 5 GB | $0.025 | $75 |
| Parquet, date-partitioned | ~150 MB | ~$0.0008 | ~$2.40 |

Same data, same query, same answer. A 10,000× cost difference, decided
entirely by storage layout. This is why the raw zone from the ingestion
lesson is only a landing area: the first transformation job in any serious
pipeline converts raw files to partitioned Parquet (or Iceberg, next
lesson) before analysts ever touch them.

#### You are not tuning queries, you are tuning tables

On Athena, 90% of performance and cost work happens before any query
runs: partition on the columns people filter by (usually date), store in
Parquet, and keep files between roughly 128 MB and 1 GB so workers
parallelize well without drowning in per-file overhead. A well-laid-out
table makes every future query cheap; a badly laid-out one cannot be
saved by clever SQL.

### Partition projection: skip the catalog bookkeeping

Classic Hive-style partitioning has an annoying chore attached: the Glue
Catalog has to know every partition exists. Your pipeline writes
`dt=2026-07-10/` to S3, but Athena will not see it until someone
registers the partition with `ALTER TABLE ADD PARTITION`, a
`BatchCreatePartition` call, or the sledgehammer `MSCK REPAIR TABLE`
(which lists the entire prefix and gets painfully slow at scale). Forget
the registration step and you get the classic support ticket: "the data
is in S3 but the query returns nothing."

**Partition projection** removes the chore. You tell Athena the pattern
the partitions follow, and it computes which prefixes should exist
instead of asking the catalog:

```sql
ALTER TABLE events SET TBLPROPERTIES (
  'projection.enabled' = 'true',
  'projection.dt.type' = 'date',
  'projection.dt.range' = '2024-01-01,NOW',
  'projection.dt.format' = 'yyyy-MM-dd',
  'storage.location.template' = 's3://lake/events/dt=${dt}/'
);
```

Now `WHERE dt = '2026-07-10'` resolves to an S3 prefix by pure
computation. No partition registration, ever again, and queries against
tables with hundreds of thousands of partitions actually get faster
because the planner skips the catalog lookup. For date-partitioned
pipeline output, I turn this on by default.

### CTAS and INSERT INTO: Athena as a transformation engine

Athena is not just for reading. `CREATE TABLE AS SELECT` writes query
results back to S3 as a new table, which makes Athena a legitimate
lightweight ETL engine. Converting that raw JSON table to partitioned
Parquet is one statement:

```sql
CREATE TABLE events
WITH (
  format = 'PARQUET',
  parquet_compression = 'SNAPPY',
  external_location = 's3://lake/events/',
  partitioned_by = ARRAY['dt']
) AS
SELECT user_id, event_type, ts,
       date_format(from_iso8601_timestamp(ts), '%Y-%m-%d') AS dt
FROM raw_events;
```

For the daily incremental run,
`INSERT INTO events SELECT ... WHERE dt = '2026-07-10'` appends just the
new partition. A scheduled Athena query is a perfectly respectable
transformation step for small and mid-sized tables, and it costs exactly
what it scans. Where it stops being the right tool: complex multi-step
logic, very large joins that hit query limits, or anything needing
Python. That is Glue's job.

Two CTAS limits to know: a single INSERT INTO or CTAS writes at most 100
partitions per statement, and CTAS cannot write to a location that
already has data.

### Workgroups: the cost circuit breaker

Athena's pay-per-scan model means one careless `SELECT *` over an
unpartitioned table can cost more than your entire month of
well-behaved queries. **Workgroups** are the guardrail. A workgroup
bundles queries with their own output location, metrics, and, most
usefully, scan limits:

- **Per-query limit:** kill any query that scans more than, say,
  100 GB. The analyst gets an error instead of the company getting a bill.
- **Per-workgroup limit:** cap total scan per hour or day across the
  whole group.

The setup that has saved me real money: separate workgroups for
`analysts`, `dashboards`, and `pipelines`, each with limits that fit
their job, and CloudWatch alarms on scan volume. Ten minutes of
configuration, and the worst-case blast radius of a bad query drops from
"budget meeting" to "one failed query."

> **Set scan limits before you invite analysts in** — The expensive
> Athena story always starts the same way: the lake gets opened up,
> someone points a BI tool at the raw zone, and the tool helpfully runs
> `SELECT *` to preview the table. Create workgroups with per-query
> scan limits on day one, not after the first surprising invoice.

### What Athena will not do

Being serverless SQL over files comes with real constraints, and
pretending otherwise leads to bad architecture decisions:

- **No indexes.** There is no way to make point lookups fast.
  `WHERE user_id = 123` on a non-partition column reads every file the
  partition filter left behind. Athena is a scan engine; layout is your
  only index.
- **Partition freshness is your problem** unless you use partition
  projection or Iceberg. Data in S3 that the catalog does not know about
  is invisible.
- **Concurrency quotas.** Active query limits are soft account quotas
  (defaults in the low hundreds of DML queries, raisable via support).
  Fine for analytics teams; wrong for anything user-facing that might fire
  thousands of concurrent queries.
- **Latency floor.** Even a trivial query takes a second or two of
  planning and scheduling. Sub-second dashboard interactions on hot data
  want a warehouse.
- **No real workload isolation.** Heavy queries and light ones share
  capacity. Workgroups limit spend, not interference.

### Athena or Redshift?

This comes up constantly, both in architecture reviews and interviews.

| Question | Points to Athena | Points to Redshift |
| --- | --- | --- |
| Query pattern | Ad-hoc, exploratory, irregular | Repeated, predictable, dashboard-driven |
| Latency needs | Seconds are fine | Sub-second, high-concurrency BI |
| Data location | Already in S3, want zero loading | Worth loading into a serving layer |
| Usage volume | Occasional; idle most of the day | Heavy daily use where flat-rate compute wins |
| Cost shape | $5/TB scanned, $0 when idle | Cluster or serverless RPUs, cheaper per query at high volume |
| Ops appetite | None | Some (sizing, WLM, vacuuming) |

The pattern most mature teams converge on is **both**: Athena over the
lake for exploration, data science, and infrequent queries, plus a
Redshift mart for the hot, high-concurrency BI workload. That is exactly
the shape we will build in the end-to-end architecture lesson.

One rule of thumb for the crossover point: if a workload scans the same
tables all day, every day, multiply the daily scan volume by $5/TB and
compare it to a small Redshift Serverless setup. When the Athena math
passes a few hundred dollars a month for one predictable workload,
loading that data into a warehouse starts paying for itself.

Athena over plain Parquet still leaves problems open: no updates, no
deletes, no safe schema changes. Fixing those is what table formats are
for, and that is the next lesson: building a real lakehouse with Iceberg,
the Glue Catalog, and Lake Formation.

---

## Module 3 · Lesson 1: Ingesting Data into AWS

*Written by Darshil Parmar, Founder & Lead Instructor, Data Vidhya.
Published July 10, 2026.
Course URL: https://datavidhya.com/learn/aws-data-engineering/batch-pipelines/ingesting-data/*

"Every pipeline diagram you have ever seen starts with a box labeled
'sources' and an arrow pointing at S3."

The author presents four common ingestion scenarios:

- **OLTP databases** (Postgres, MySQL, SQL Server, Oracle) where direct
  querying is forbidden
- **SFTP feeds** from vendors (banks, logistics providers, ad networks,
  insurance partners)
- **SaaS tools** like Salesforce, Zendesk, HubSpot, and Google Ads
- **Internal REST APIs** for services like inventory systems

"Four sources, four completely different ingestion problems. The naive
move is to write one Python script per source, run them all on cron, and
call it done."

### Databases: AWS DMS

AWS Database Migration Service (DMS) is described as a continuous
replication engine that reads from source databases and writes changes
to S3.

Two modes used together:

- **Full load**: copies existing rows, chunked by primary key ranges
- **CDC (change data capture)**: reads transaction logs (WAL in
  Postgres, binlog in MySQL)

Production gotchas:

- **LOB handling**: large objects are truncated silently in limited LOB mode
- **Task sizing**: undersized replication instances cause lag
- Logical replication must be enabled on source (`wal_level = logical`,
  `binlog_format = ROW`)
- Tables without primary keys make CDC updates ambiguous

DMS configuration example:

```json
{
  "TargetMetadata": {
    "SupportLobs": true,
    "LimitedSizeLobMode": true,
    "LobMaxSize": 32
  },
  "FullLoadSettings": {
    "MaxFullLoadSubTasks": 8,
    "CommitRate": 10000
  }
}
```

Cost figures provided: `dms.t3.medium` at ~$60/month, `r5.large` at
~$155/month, DMS Serverless at ~$0.09 per DCU-hour.

### SFTP feeds: Transfer Family

"Transfer Family deletes all of that: it is a managed SFTP endpoint where
the backing storage is S3."

Configuration includes per-vendor users mapped to S3 prefixes, SSH key
or Lambda-based authentication, and S3 event notifications to trigger
pipelines.

Pricing: ~$216/month per endpoint plus $0.04 per GB transferred.

### SaaS tools: AppFlow

Amazon AppFlow handles Salesforce, Zendesk, Slack, ServiceNow, Google
Analytics, SAP connectors with OAuth, incremental pulls, and retries.

Cost: ~$0.001 per flow run plus $0.02 per GB processed.

### API to Lambda to S3 pattern

Sample handler for paginated extraction:

```python
import boto3, json, urllib3
from datetime import datetime, timezone

http = urllib3.PoolManager()
s3 = boto3.client("s3")

def handler(event, context):
    run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    page, batch = 1, []
    while True:
        resp = http.request(
            "GET", "https://api.internal.co/v1/inventory",
            fields={"page": page, "per_page": 500},
            headers={"Authorization": f"Bearer {get_token()}"},
        )
        if resp.status == 429:
            raise Exception("rate limited, let Lambda retry")
        items = json.loads(resp.data)["items"]
        if not items:
            break
        batch.extend(items)
        page += 1

    s3.put_object(
        Bucket="raw",
        Key=f"inventory_api/dt={run_date}/inventory.json",
        Body="\n".join(json.dumps(i) for i in batch),
    )
```

Production rules stated:

- Land raw JSON exactly as returned
- Loop until the API reports no more pages
- Fail loudly on 429 to let retry policies handle backoff
- Use date-partitioned keys (`dt=YYYY-MM-DD/`) for idempotency

### Decision Table

| Source type | Service | Approximate cost | Watch out for |
|-------------|---------|------------------|---------------|
| OLTP database | DMS full load + CDC | $60 to $155/month | LOB truncation, missing primary keys, sizing |
| Vendor pushes via SFTP | Transfer Family | ~$216/month + $0.04/GB | Flat fee even when idle |
| Vendor hosts SFTP, small feed | Lambda with paramiko | Under $1/month | You own retries and credential rotation |
| SaaS with connector | AppFlow | ~$0.001/run + $0.02/GB | Console flows get messy; use Terraform |
| SaaS or API, no connector | Lambda (or Glue/Fargate) | Under $1/month | Pagination bugs, rate limits, 15-minute cap |
| Files too big for Lambda | Glue Python shell or Fargate | A few $/month | Same idempotency rules |

The article's closing heuristic: "use the managed service whenever one
exists for your source type."

---

## Module 4 · Lesson 1: Kinesis Data Streams

*Written by Darshil Parmar, Founder & Lead Instructor, Data Vidhya.
Published Jul 10, 2026.
Course URL: https://datavidhya.com/learn/aws-data-engineering/streaming-on-aws/kinesis-data-streams/*

Your team just shipped a mobile app, and product wants order events
available to the data platform within seconds, not tomorrow morning after
the batch run. Someone stands up a Kinesis stream, points the app at it,
wires a Lambda to the other end, and it works. Three weeks later, during
a promotion, half the events start failing with
`WriteProvisionedThroughputExceeded`, the dashboard goes stale, and
nobody on the team can explain why a "fully managed" service is dropping
data.

This happens because Kinesis is managed, not magic. It has a very
explicit capacity model, and if you do not understand it, the service
will teach it to you in production.

### Shards are the unit of everything

A Kinesis stream is not one big pipe. It is a set of parallel lanes
called **shards**, and every capacity number, every cost number, and
every ordering guarantee is per shard:

- **Writes**: 1 MB/s or 1,000 records/s per shard, whichever limit
  you hit first
- **Reads**: 2 MB/s per shard, shared across all standard consumers
- **Ordering**: records with the same partition key land on the same
  shard and stay in write order

When you put a record, you provide a partition key. Kinesis hashes it,
and the hash decides which shard the record lands on. All events for
`user_42` hash to the same shard, so a consumer reads that user's events
in order. Across shards there is no ordering at all: an event on shard 1
can be read before an older event on shard 3. If your processing logic
assumes global order across the whole stream, Kinesis will quietly break
it.

### Capacity math: a worked example

Say your app produces 4,000 events/s at peak, each event around 2 KB
after JSON serialization.

- Throughput: 4,000 × 2 KB = 8 MB/s. At 1 MB/s per shard, you need 8 shards.
- Record count: 4,000 records/s. At 1,000 records/s per shard, you need 4 shards.
- Take the larger: 8 shards. Add headroom for spikes and imperfect key
  distribution: provision 10.

That last step matters more than it looks. The 1 MB/s limit assumes
perfectly even distribution across shards, and real traffic never
distributes perfectly. Provisioning at exactly the math means the
busiest shard throttles first while the others sit half idle. I plan
for 20 to 30 percent headroom on top of peak.

### Hot shards: the partition key trap

The most common Kinesis production incident I have seen is not
underprovisioning, it is a bad partition key. Imagine you key
clickstream events by `tenant_id` and one enterprise tenant generates
40 percent of your traffic. All of that tenant's events hash to a
single shard. That shard needs 3.2 MB/s of a 1 MB/s lane. The other
nine shards are nearly empty, your total provisioned capacity is fine on
paper, and you are still throttling.

How you detect it:

- `WriteProvisionedThroughputExceeded` climbing while total
  `IncomingBytes` is well under stream capacity is the signature of a
  hot shard.
- Enable enhanced shard-level metrics (an extra CloudWatch cost, worth
  it during an incident) to see `IncomingBytes` per shard and find the
  hot one.

How you fix it: pick a higher-cardinality key. Key by `user_id` instead
of `tenant_id`, or compose keys like `tenant_id#session_id`. If you
genuinely need per-tenant ordering for a whale tenant, that tenant's
ceiling is one shard, 1 MB/s, and no amount of scaling changes it. That
is a design conversation, not a scaling knob.

> **Your partition key is a capacity decision** — Choosing a partition
> key feels like a data modeling detail, but it is really a throughput
> decision. The maximum rate for any single key value is one shard:
> 1 MB/s in, 1,000 records/s. Pick the finest-grained key that still
> preserves the ordering your consumers actually need, and nothing coarser.

### On-demand vs provisioned mode

Kinesis has two capacity modes, and the pricing models are completely
different.

**Provisioned**: you declare a shard count and pay per shard-hour plus
per record.

**On-demand**: AWS manages shards for you, scaling to double your
previous 30-day peak automatically, and you pay per GB moved.

| | Provisioned | On-demand |
|---|---|---|
| Shard/stream hours | $0.015 per shard-hour | $0.04 per stream-hour |
| Data in | $0.014 per million PUT units (25 KB) | $0.08 per GB |
| Data out | Included (standard consumers) | $0.04 per GB |
| Scaling | You resplit/merge shards | Automatic |
| Hot shard risk | Yours to manage | Still yours (keys still hash to shards) |

Run the numbers for the 8 MB/s workload above, steady around the clock:

- **Provisioned, 10 shards**: 10 × $0.015 × 730 hours = about
  $110/month, plus PUT units. 4,000 records/s is roughly 10.4 billion
  records/month, each under 25 KB so one PUT unit each: about $145/month.
  Total around **$255/month**.
- **On-demand**: 8 MB/s is roughly 20 TB ingested per month. 20,000 GB
  × $0.08 = $1,600, plus stream hours and egress. Total around
  **$1,800/month**.

Seven times the price for the same steady workload. On-demand earns its
premium when traffic is spiky or unknown: a new product, 10× flash-sale
bursts, anything where paging someone to resplit shards costs more than
the bill. My rule: start on-demand while you learn your traffic shape,
then switch to provisioned once the load is steady and predictable.
Switching modes is a single API call and takes effect without downtime.

### Producers: batch or bleed money

The naive producer calls `PutRecord` once per event. At 4,000 events/s
that is 4,000 HTTP round trips per second, and your producer spends
more time on TLS handshakes than on real work. Two techniques fix this.

**Batching with `PutRecords`** sends up to 500 records per request:

```python
import boto3, json

kinesis = boto3.client("kinesis")

def send_batch(events):
    records = [
        {"Data": json.dumps(e).encode(), "PartitionKey": e["user_id"]}
        for e in events
    ]
    resp = kinesis.put_records(StreamName="orders", Records=records)
    if resp["FailedRecordCount"] > 0:
        retry = [r for r, out in zip(records, resp["Records"])
                 if "ErrorCode" in out]
        # back off, then resend only the failures
        return retry
    return []
```

That failure-handling block is not optional. `PutRecords` is partially
successful by design: some records in a batch can throttle while others
succeed. If you do not check `FailedRecordCount` and retry the failed
subset, you are silently dropping data during every traffic spike.

**Aggregation** goes one step further. Remember, billing counts 25 KB PUT
units and shards count records/s. If your events are 500 bytes each,
sending them one per record wastes both. The Kinesis Producer Library
(KPL) packs many small events into one Kinesis record up to the 25 KB
boundary, and the consumer-side KCL unpacks them transparently. Fifty
500-byte events become one record: one fiftieth the record count against
the 1,000 records/s limit, and far fewer PUT units. If you cannot run
the KPL (it is a Java daemon), the aggregation format is open, and
libraries exist for Python and Go.

### Consumers: Lambda first, KCL when you outgrow it

For most data engineering teams, the first consumer is Lambda through an
event source mapping. The event source mapping polls each shard and
invokes your function with batches:

```yaml
# The settings that actually matter on the event source mapping
BatchSize: 400                     # records per invocation, up to 10,000
MaximumBatchingWindowInSeconds: 5  # wait up to 5s to fill a batch
ParallelizationFactor: 4           # concurrent invocations per shard
BisectBatchOnFunctionError: true   # split failing batches to isolate bad records
MaximumRetryAttempts: 3
DestinationConfig:
  OnFailure:
    Destination: arn:aws:sqs:us-east-1:123456789012:orders-dlq
```

Three of these deserve explanation:

- **ParallelizationFactor**: by default Lambda runs one invocation per
  shard at a time, to preserve order. A factor of 4 runs four concurrent
  invocations per shard, still preserving order per partition key. This
  is the cheapest way to add consumer throughput without resharding.
- **Bisect on error**: by default, a failing batch retries whole, forever,
  until the records expire. One poison record can block a shard for
  24 hours. Bisect splits the failing batch in half repeatedly until the
  bad record is isolated, and with an on-failure destination, that
  record's metadata goes to SQS for inspection while the shard keeps
  moving.
- **MaximumRetryAttempts**: without a cap, retries block the shard. With
  a cap plus a failure destination, you trade "at least once, maybe
  stuck" for "keep flowing, investigate failures async". For most
  pipelines that is the right trade.

> **One bad record can stall a whole shard** — The default Lambda retry
> behavior on streams is retry-until-expiry, in order. A single malformed
> record blocks every record behind it on that shard. Always set
> `BisectBatchOnFunctionError`, a bounded `MaximumRetryAttempts`, and an
> on-failure destination before you go to production, not after your
> first stuck shard.

When Lambda is not enough, you step up to the **Kinesis Client Library
(KCL)** running on EC2, ECS, or EKS: long-lived consumers with a
DynamoDB lease table coordinating which worker owns which shard. You
take on more ops for more control: no 15-minute execution ceiling,
in-memory state between records, custom checkpointing.

And when you have multiple consumers, you hit the read limit: 2 MB/s
per shard shared among all standard consumers. Three consumers on one
stream get about 660 KB/s each, and polling latency degrades.
**Enhanced fan-out** fixes this by giving each registered consumer its
own dedicated 2 MB/s per shard, pushed over HTTP/2 with around 70 ms
latency instead of polling. It costs extra ($0.015 per consumer-shard-hour
plus $0.013/GB retrieved), so use it when you have two or more consumers
that both need low latency, and not before.

### Retention and replay

By default a stream keeps records for 24 hours. You can extend to 7 days
($0.02 per shard-hour extra) or up to 365 days ($0.023/GB-month for
long-term). This is the feature batch people underrate: the stream is a
replayable log, not a conveyor belt. When you deploy a bug that corrupts
three hours of output, you fix the code, restart the consumer with an
iterator positioned `AT_TIMESTAMP` three hours back, and reprocess. No
begging the upstream team to resend. I default to 7 days of retention on
anything important: it is cheap insurance, and it means a consumer
outage on Friday night does not become data loss by Saturday.

### Iterator age: the metric that matters

If you watch a single CloudWatch metric on a Kinesis pipeline, make it
`GetRecords.IteratorAgeMilliseconds`. It measures the age of the last
record your consumer read: how far behind the tip of the stream you are.
Near zero means real time. Climbing steadily means your consumer
processes slower than producers write, and you are heading toward
retention expiry, where records fall off the back of the stream unread.
That is silent data loss with no error message.

Alarm on it. A sensible starting threshold is a few minutes for a
real-time pipeline, and always well under your retention window. When it
climbs, your levers are in this order: raise `ParallelizationFactor`,
make the consumer faster (batch its downstream writes), then reshard.

Kinesis Data Streams gives you the durable, ordered, replayable pipe.
But a lot of the time the only thing on the other end of that pipe is
"put the events in S3 as Parquet", and writing a consumer for that is
undifferentiated work. Next lesson: Kinesis Data Firehose, the zero-ops
delivery service that does it for you.

---

## Module 5 · Lesson 1: CloudWatch Monitoring

*Written by Darshil Parmar, Founder & Lead Instructor, Data Vidhya.
Published (latest content).
Course URL: https://datavidhya.com/learn/aws-data-engineering/production-pipelines/cloudwatch-monitoring/*

It is 9:15 on a Monday morning and the head of sales messages you:
"The revenue dashboard still shows Friday's numbers. Is something
broken?" You open the Glue console and there it is, a red FAILED on
Saturday night's run. The pipeline has been down for 36 hours, the
data is two days stale, and the person who found out first was not you.
It was a stakeholder who now trusts your platform a little less.

The naive approach is exactly what you were doing: check the console
when someone complains. It feels fine when you own two pipelines. By the
time you own twenty, spread across Glue, Lambda, Step Functions, and a
Kinesis stream, you physically cannot check them all every morning. And
the worst failures do not even show up as red. A job that "succeeds"
but writes zero rows will never trip a status check.

The real solution is to make the pipelines report on themselves:
metrics that describe their health, logs you can actually query, and
alarms that page you before the stakeholder does. On AWS, all three
live in CloudWatch, and every service you have used in this course
already sends data there. You just have to wire it up.

### The three primitives

CloudWatch gives you three building blocks, and every pattern in this
lesson is a combination of them:

- **Metrics**: numeric time series. Every AWS service emits them
  automatically (Lambda error counts, Glue task failures), and you can
  publish your own (rows written, null rate).
- **Logs**: whatever your jobs print, collected into log groups.
  Queryable with a SQL-like language called Logs Insights.
- **Alarms**: watch a metric, and when it crosses a threshold, fire an
  action, usually an SNS notification.

Metrics tell you _that_ something is wrong, logs tell you _why_, alarms
make sure you _hear about it_. Most teams have logs by accident and
neither of the other two on purpose.

### What to actually monitor, service by service

The mistake I see most often is alarming on everything, then muting the
noise, then missing the real failure. Each service in your stack has
two or three metrics that genuinely predict trouble. Start with these:

| Service | Metric | What it tells you |
|---------|--------|-------------------|
| Glue | `glue.driver.aggregate.numFailedTasks` | Spark tasks dying inside a "running" job, usually memory or bad data |
| Glue | Job duration (from job run metrics) | A 20-minute job now taking 3 hours means input blew up or a join went cross-product |
| Lambda | `Errors`, `Throttles` | Code failures, and invocations rejected because you hit concurrency limits |
| Lambda | `IteratorAge` | For stream consumers: how far behind the Kinesis stream your function is running |
| Kinesis | `GetRecords.IteratorAgeMilliseconds` | Consumer lag at the stream level; growing means you read slower than producers write |
| Kinesis | `WriteProvisionedThroughputExceeded` | Producers being rejected, you need more shards or better partition keys |
| Step Functions | `ExecutionsFailed` | Your orchestration is failing; one alarm here covers every step inside |
| Redshift | `QueryQueueLength` (WLM queue) | Queries piling up waiting for slots; dashboards feel slow before anything errors |
| Redshift | `PercentageDiskSpaceUsed` | Above 80 percent, vacuum and query performance degrade fast, and at 100 the cluster stops accepting writes |

Two habits worth building. First, alarm on _trends_, not just failures:
a Glue job whose duration doubles week over week is telling you
something even though every run is green. Second, prefer one alarm at
the orchestrator level (`ExecutionsFailed` on the state machine) over
ten alarms on individual steps. The state machine already knows when
any step fails.

### Structured logging from your Python jobs

Here is a log line I have grepped through at 2 AM:
`Processing batch... done. Some records skipped.` How many records?
Which batch? Which run? Useless.

Print JSON instead. CloudWatch treats each line as an event, and if the
line is JSON, Logs Insights can filter and aggregate on any field
inside it:

```python
import json, time

def log(level, message, **fields):
    print(json.dumps({
        "timestamp": int(time.time() * 1000),
        "level": level,
        "message": message,
        **fields,
    }))

log("INFO", "batch_complete",
    job="orders_daily",
    run_id=run_id,
    rows_read=184_223,
    rows_written=183_890,
    rows_skipped=333,
    duration_sec=412)
```

That is the whole trick: one helper function, no logging framework
required. Glue and Lambda both ship stdout to CloudWatch Logs
automatically. Now, when something looks off, you query it instead of
scrolling:

```
fields @timestamp, run_id, rows_written, rows_skipped
| filter job = "orders_daily" and level = "INFO"
| filter rows_skipped > 0
| sort @timestamp desc
| limit 20
```

Logs Insights runs this across every log stream in the group, over any
time range, in seconds. Compare that to opening forty log streams by
hand in the console. Once your jobs log structured events, questions
like "when did skip counts start rising" become a ten second query
instead of an afternoon.

### Custom metrics: monitoring the data, not just the job

Everything so far monitors _infrastructure_. But the failure mode that
actually burns data teams is a job that runs green while the data inside
it rots: the upstream export silently dropped a column, row counts fell
90 percent, null rates spiked. AWS has no metric for "your data is
wrong." You have to publish it yourself.

The direct way is `put_metric_data`:

```python
import boto3

cloudwatch = boto3.client("cloudwatch")

cloudwatch.put_metric_data(
    Namespace="DataPipelines",
    MetricData=[
        {
            "MetricName": "RowsWritten",
            "Dimensions": [{"Name": "Job", "Value": "orders_daily"}],
            "Value": rows_written,
            "Unit": "Count",
        },
        {
            "MetricName": "NullRateCustomerId",
            "Dimensions": [{"Name": "Job", "Value": "orders_daily"}],
            "Value": null_rate,
            "Unit": "Percent",
        },
    ],
)
```

Call this at the end of every run and you get time series you can alarm
on: `RowsWritten < 50000` catches the silent 90 percent drop that a
status check never will.

The neater way, if you are already logging JSON, is the embedded metric
format (EMF). You add a small `_aws` block to a log line and CloudWatch
extracts metrics from it automatically, no extra API call, no boto3
client:

```python
print(json.dumps({
    "_aws": {
        "Timestamp": int(time.time() * 1000),
        "CloudWatchMetrics": [{
            "Namespace": "DataPipelines",
            "Dimensions": [["Job"]],
            "Metrics": [{"Name": "RowsWritten", "Unit": "Count"}],
        }],
    },
    "Job": "orders_daily",
    "RowsWritten": rows_written,
}))
```

Same log line serves as both a searchable event and a metric. For
high-frequency Lambda functions, EMF is the better choice because
`put_metric_data` calls add latency and API cost per invocation.

> **Monitor outcomes, not just execution** — Job status answers "did
> the code run." Row counts, null rates, and freshness answer "did the
> data arrive correctly." Every serious data incident I have seen
> slipped past the first kind of monitoring and would have been caught
> by the second. Publish at least one outcome metric per pipeline.

### Alarms: thresholds, anomaly detection, and cutting noise

An alarm watches one metric against one condition. The design question
is what condition.

**Static thresholds** work when you know the number: `ExecutionsFailed
>= 1`, `PercentageDiskSpaceUsed > 80`, `IteratorAgeMilliseconds >
300000` (five minutes behind). Use these for anything with a hard,
obvious limit.

**Anomaly detection** works when "normal" moves around. Your row count
is 2 million on weekdays and 400k on weekends; any static threshold
either misses weekday drops or false-alarms every Sunday. Anomaly
detection trains a model on the metric's history and alarms when the
value leaves the expected band. It is the right tool for volume and
duration metrics with daily or weekly seasonality. Give it two weeks of
history before trusting it.

**Composite alarms** exist because one root cause often trips five
alarms at once. Kinesis backs up, so `IteratorAge` fires, then Lambda
`Errors` fires, then the freshness alarm fires, and you get paged three
times for one problem. A composite alarm combines child alarms with
AND/OR logic and only notifies on the combined state, so "stream
consumer unhealthy" pages you once, whichever symptom shows first.

Route every alarm through an SNS topic rather than emailing individuals.
The topic is the stable interface: subscribe a Lambda that posts to
Slack for warnings, subscribe PagerDuty's endpoint for the topics that
should wake someone. Two topics, `data-alerts-warning` and
`data-alerts-critical`, cover most teams. Be honest about which alarms
deserve critical. If everything pages, nothing does, and within a month
the channel is muted.

### The one dashboard worth building

Skip the giant wall of forty charts. Build one **pipeline health
dashboard** a person can read in thirty seconds:

- One row per pipeline: last run status, duration trend over 14 days,
  rows written trend.
- A freshness widget: hours since data landed, per critical table.
- The shared infrastructure corner: Kinesis iterator age, Redshift
  queue length and disk.

That is it. Its job is to answer "is everything okay" at a glance during
incidents and before you head into a Monday standup. Anything deeper,
you investigate with Logs Insights, not with more widgets.

### The freshness canary

Here is the failure mode that no error metric will ever catch: the
EventBridge schedule got disabled during a deploy, or the trigger's
cron expression was wrong, or the upstream vendor simply stopped
delivering files. Nothing errored. Nothing ran. Every alarm on
failures stays green precisely because there were no executions to
fail.

The fix is a canary that watches the _data_ instead of the jobs. A
tiny scheduled Lambda queries the freshest timestamp in each critical
table, via Athena for the lake or a direct query for Redshift, and
publishes the age as a metric:

```python
def handler(event, context):
    age_hours = get_hours_since_latest("gold.orders")  # Athena query
    cloudwatch.put_metric_data(
        Namespace="DataPipelines",
        MetricData=[{
            "MetricName": "DataAgeHours",
            "Dimensions": [{"Name": "Table", "Value": "gold.orders"}],
            "Value": age_hours,
        }],
    )
```

Then one alarm: `DataAgeHours > 26` for a daily table. Now it does not
matter _why_ nothing ran. Disabled schedule, dead trigger, vendor
outage, a bug that made the job exit early with success. If fresh
data did not land, you get paged. If I could keep only one alarm across
an entire platform, it would be this one.

> **The silent failure is the expensive one** — Loud failures get fixed
> in hours. Silent ones, where the schedule never fired or the job
> wrote zero rows with exit code 0, get discovered by stakeholders
> days later, and rebuilding trust costs more than rebuilding the data.
> The freshness canary exists for exactly this class of failure.

### What CloudWatch itself costs

Monitoring is not free, and I have seen CloudWatch quietly become a
top-five line item on a data team's bill. The prices that matter
(us-east-1, approximate):

| Item | Price | Where it bites |
|------|-------|----------------|
| Logs ingestion | $0.50 per GB | Chatty Spark jobs; a Glue job in DEBUG can emit gigabytes per run |
| Logs storage | $0.03 per GB-month | Log groups with no retention policy, growing forever |
| Logs Insights queries | $0.005 per GB scanned | Careless queries over "all time" |
| Custom metrics | $0.30 per metric per month | High-cardinality dimensions: per-run or per-customer dimensions each create a new metric |
| Standard alarm | $0.10 per month | Rarely a problem |
| Anomaly detection alarm | $0.30 per month | Fine in moderation |
| Dashboard | $3.00 per month after 3 free | Dashboard sprawl |

Three habits keep this sane. Set retention on every log group (30 to 90
days is plenty for pipeline logs; the default is _never expire_). Log at
INFO in production, not DEBUG. And keep custom metric dimensions
low-cardinality: dimension by job name, never by run ID, or you will
mint thousands of billable metrics that each hold one data point.

Ingestion cost is also a feature in disguise: if your logging bill
spikes, some job started screaming, and that is usually worth
investigating anyway.

---

## Module 4 · Lesson 2: Kinesis Data Firehose

*Written by Darshil Parmar, Founder & Lead Instructor, Data Vidhya.
Published Jul 10, 2026.
Course URL: https://datavidhya.com/learn/aws-data-engineering/streaming-on-aws/kinesis-firehose/*

> **Here is the ticket you will get within a month of any streaming
> project:** "Can we get the raw events into S3 so analytics can query
> them?" Nobody is asking for stateful processing or millisecond
> latency. They just want the events, in the lake, in a queryable format.

The naive answer is to write it yourself: a Lambda consumer on the
stream that batches records and writes objects to S3. It works in the
demo. Then real life arrives. Your Lambda writes one small file per
invocation, so within a week you have two million 40 KB JSON files and
Athena queries crawl. You add buffering logic, then retry logic, then a
dead-letter path, then GZIP, then someone asks for Parquet and you are
maintaining a schema conversion layer. You have rebuilt, badly, a
service AWS already runs for you.

That service is Amazon Data Firehose (everyone still calls it Kinesis
Data Firehose). It is not a stream you consume from. It is a delivery
pipe: events go in one end, and buffered, batched, optionally
transformed and format-converted files come out the other end into S3,
Redshift, OpenSearch, or an HTTP endpoint. No shards to size, no
consumers to write, no servers. You configure it and it runs.

### Buffering: the trade-off you are actually configuring

Firehose collects incoming records into a buffer and flushes to the
destination when the buffer hits a size limit or a time limit, whichever
comes first. For S3, size is 1 to 128 MB and time is 0 to 900 seconds.
These two knobs are the whole personality of your delivery stream,
because they set three things at once:

| Buffer setting | Latency to S3 | File sizes | Downstream query cost |
|---|---|---|---|
| 1 MB / 60s | About a minute | Tiny at low traffic | High (many small files) |
| 64 MB / 300s | Up to 5 minutes | Good | Low |
| 128 MB / 900s | Up to 15 minutes | Best | Lowest |

The tension: analysts want fresh data (small buffers), but the query
engine wants big files (large buffers). Athena's performance and cost
degrade badly with many small files, because every object means an S3
GET and scan overhead.

> **Buffer size is a data lake decision, not a streaming decision** —
> Every Firehose buffer setting is really answering: "what file sizes
> will Athena scan for the next five years?" Optimize for the thousands
> of future queries, not the one dashboard that wants data 4 minutes
> sooner. Aim for files of at least 64 MB, and 128 MB where freshness
> allows.

### Format conversion: land Parquet, not JSON

Firehose can convert incoming JSON to Parquet (or ORC) on the fly, using
a schema you register in the Glue Data Catalog. This is one checkbox that
removes an entire downstream job: no nightly "compact and convert the
raw JSON" Glue job, no window where analysts query expensive raw JSON.
Events land columnar, compressed, and typed.

The catch is that conversion needs a schema, so your events must be JSON
that matches a Glue table definition. When a record does not parse or
does not match, Firehose does not drop it: it writes the failure to an
error prefix in S3 with the reason attached. Watch that prefix; a schema
drift upstream shows up there before anyone notices missing rows.

### Dynamic partitioning: fold the partitioner into the pipe

By default Firehose writes to a prefix organized by arrival time:
`year/month/day/hour`. That is processing time, and it is often not how
people query. If analysts filter by `event_type` or `tenant`, you want
the data physically partitioned that way.

Dynamic partitioning extracts fields from each record (with JQ
expressions) and routes records into per-partition buffers:

```json
{
  "Prefix": "events/type=!{partitionKeyFromQuery:event_type}/dt=!{timestamp:yyyy-MM-dd}/",
  "ErrorOutputPrefix": "firehose-errors/!{firehose:error-output-type}/"
}
```

Now `type=order_placed/dt=2026-07-10/` is a real S3 partition and Athena
prunes it. Two costs to respect. First, the direct money: dynamic
partitioning is billed extra, about $0.02/GB plus a small per-object
delivery charge. Second, the sneaky one: each active partition gets its
own buffer, so partitioning by a high-cardinality field multiplies your
small-file count by the number of active partitions. Partition by fields
with tens of values (event type, region), never by thousands (user ID).

### Inline Lambda transforms

Firehose can pass each buffered batch through a Lambda function before
delivery. The function receives records and returns them marked `Ok`
(deliver, possibly modified), `Dropped` (filter out), or
`ProcessingFailed` (send to the error prefix):

```python
import base64, json

def handler(event, context):
    out = []
    for r in event["records"]:
        data = json.loads(base64.b64decode(r["data"]))
        if data.get("event_type") == "heartbeat":
            out.append({"recordId": r["recordId"], "result": "Dropped"})
            continue
        data["email"] = "REDACTED"          # mask PII before it touches the lake
        data["region"] = data.get("region", "unknown")
        out.append({
            "recordId": r["recordId"],
            "result": "Ok",
            "data": base64.b64encode(json.dumps(data).encode()).decode(),
        })
    return {"records": out}
```

The sweet spot is light, stateless, per-record work: dropping noise
events, masking PII before it is ever written, normalizing field names,
adding a static enrichment. The moment your transform needs a database
lookup per record, state across records, or joins, stop. That is stream
processing, and it belongs in Flink, not in a transform hook.

### Destinations and what happens when they fail

S3 is the destination for data engineering work ninety percent of the
time, but know the others:

- **Redshift**: Firehose stages files in S3 and issues a `COPY` into
  your table. You get micro-batch loading without writing the loader.
- **OpenSearch**: for log search and operational dashboards.
- **HTTP endpoints**: Datadog, Splunk, New Relic, or your own API.
- **Iceberg tables**: the newest and, for lakehouse builds, the most
  interesting. Firehose writes directly into Apache Iceberg tables in
  S3, committing through the Glue catalog, and can even route records
  to different tables based on content.

Failure handling is where Firehose quietly earns its keep. If the
destination is down (Redshift maintenance window, OpenSearch red
cluster), Firehose retries for a configurable period, up to 7,200
seconds, and then writes the undeliverable records to a backup S3 bucket
rather than dropping them. For S3 destinations you can also enable full
source backup: every raw record is copied to a backup prefix regardless
of transform outcomes, which gives you a replay path when your transform
Lambda turns out to have a bug.

> **Always configure the backup bucket before launch** — The error and
> backup prefixes are your only recovery story. A transform bug that
> marks records `ProcessingFailed`, a schema mismatch in Parquet
> conversion, a destination outage that outlasts retries: all of these
> land data in the backup location instead of losing it, but only if you
> configured one and put an alarm on it. An empty backup config plus a
> long outage equals permanent loss.

### Direct PUT vs reading from a stream

Firehose accepts data two ways, and the choice changes your architecture:

- **Direct PUT**: producers call the Firehose API (`PutRecord`/
  `PutRecordBatch`) directly. Simplest possible setup, no Kinesis
  stream to pay for or size. But Firehose is the only consumer, there
  is no replay (records live in the buffer minutes, not days), and
  throughput has per-stream quotas you must request increases for.
- **Kinesis Data Stream as source**: producers write to a stream, and
  Firehose attaches as one consumer among many. You keep replay,
  retention, and the option of adding a Flink or Lambda consumer beside
  it.

The rule I use: if the only thing anyone will ever do with these events
is land them in storage, Direct PUT and done. If anything real-time
might ever read the same events, put a stream in front. In practice,
most pipelines that matter end up as stream plus Firehose.

### Firehose vs writing your own Lambda consumer

| | Firehose | Your own Lambda consumer |
|---|---|---|
| Code to maintain | None (config only) | Batching, retry, DLQ, file writing |
| File sizing | Built-in buffering to 128 MB | You implement buffering, and Lambda's 15-min limit fights you |
| Parquet conversion | Checkbox plus Glue schema | You bundle and run a writer library |
| Destination retries/backup | Built in | You build it |
| Latency floor | Tens of seconds to minutes | Seconds |
| Per-record custom logic | Limited (transform hook) | Anything |
| Exotic destinations | Fixed list | Anywhere |
| Cost at low volume | Per GB, no idle cost | Invocations plus your time |

Firehose wins whenever the job is "deliver events to a supported
destination in good-sized files". Your own consumer wins when you need
second-level latency, an unsupported destination, or per-record logic
beyond a simple transform.

### What it costs

Firehose pricing is per GB ingested, with add-ons for the features you
enable. Approximate us-east-1 numbers:

| Component | Price |
|---|---|
| Ingestion, Direct PUT or stream source | $0.029/GB (first 500 TB/month) |
| Format conversion to Parquet | $0.018/GB |
| Dynamic partitioning | $0.020/GB plus $0.005 per 1,000 objects |
| Ingestion into Iceberg tables | roughly $0.045/GB |

Worked example: clickstream at a steady 2 MB/s, about 5 TB/month,
converting JSON to Parquet, no dynamic partitioning:

- Ingestion: 5,000 GB × $0.029 = $145
- Conversion: 5,000 GB × $0.018 = $90
- Total: about **$235/month**, plus S3 storage and a Lambda transform
  if you add one

---

## Module 4 · Lesson 3: SQS, SNS & Lambda Event-Driven Patterns

*Written by Darshil Parmar, Founder & Lead Instructor, Data Vidhya.
Published (latest content).
Course URL: https://datavidhya.com/learn/aws-data-engineering/streaming-on-aws/sqs-sns-lambda/*

A vendor drops a CSV into your S3 bucket somewhere between 2 AM and 6
AM, whenever their system feels like it. Your current solution is a
cron job at 6:30 that lists the bucket and hopes the file arrived. Some
mornings it did not, the job processes nothing, and you find out from
an analyst at 10. Other mornings the vendor drops three files and your
job, written for one, silently processes only the first.

Polling on a schedule for something that happens at an unpredictable
time is the wrong shape. The right shape is event-driven: the file
landing is the trigger. AWS has three messaging services for building
this, and mixing up what each is for causes real production pain, so
get the mental model straight first.

### Queues vs topics vs streams

- **SQS** is a queue. Producers put messages in, consumers pull them
  out, and a processed message is deleted. A queue is a to-do list:
  each item gets done once, by whoever picks it up.
- **SNS** is a topic. A publisher sends one message and every
  subscriber gets a copy immediately. Nothing is stored; a topic is an
  announcement, not a to-do list.
- **Kinesis** is a stream: an ordered, replayable log where each
  consumer tracks its own position.

| | SQS | SNS | Kinesis Data Streams |
|---|---|---|---|
| Model | Queue (pull) | Pub/sub (push) | Log (pull) |
| Consumers per message | One | Every subscriber | Every consumer, own position |
| Ordering | FIFO queues only | FIFO topics only | Per partition key |
| Replay old messages | No | No | Yes, within retention |
| Retention | Up to 14 days (until consumed) | None | 1 to 365 days |
| Throughput | Nearly unlimited (standard) | Nearly unlimited | Per shard |
| Cost model | $0.40/million requests | $0.50/million publishes | Shard-hours or per GB |
| Typical DE use | Buffer work items | Fan out notifications | High-volume event data |

The one-line decision: high-volume analytical event data goes to
Kinesis, discrete units of work go to SQS, and "several systems need to
hear about this" goes to SNS. They compose; the best patterns use two
or three together.

### S3 events, and why SQS goes in the middle

S3 can emit an event whenever an object is created, and that event can
invoke Lambda directly. That is the foundational serverless pipeline
pattern. Direct S3-to-Lambda is fine for light work. But for anything
production-grade, put an SQS queue between them: S3 event to SQS, Lambda
consuming the queue. Three reasons.

**Buffering.** The vendor drops 500 files at once at month-end. Direct
invocation means 500 concurrent Lambdas slamming your downstream
database. With a queue in between, the files wait politely, and you
control drain rate with Lambda's `maximum_concurrency` on the event
source mapping (settable as low as 2).

**Retries you control.** If a direct-invoked Lambda fails, S3's async
invoke retries twice and gives up. With SQS, a failed message returns to
the queue and retries until it succeeds or exhausts `maxReceiveCount`,
at which point it goes to a dead-letter queue instead of vanishing.

**Visibility.** A queue depth is a number you can see and alarm on.
"How far behind are we?" becomes a CloudWatch metric
(`ApproximateNumberOfMessagesVisible`) instead of a shrug.

```python
def handler(event, context):
    for record in event["Records"]:                       # SQS batch
        body = json.loads(record["body"])
        for s3_event in body.get("Records", []):          # S3 event inside
            bucket = s3_event["s3"]["bucket"]["name"]
            key = urllib.parse.unquote_plus(s3_event["s3"]["object"]["key"])
            validate_and_load(bucket, key)
```

Two working notes from that snippet: the S3 event arrives wrapped
inside the SQS message body, and keys with spaces arrive URL-encoded,
so always `unquote_plus`. Both bite everyone exactly once.

### SNS fan-out

An S3 bucket allows only one notification target per event pattern,
and one queue means one consumer. The moment a second team wants the
same event ("we also want to index new files"), point the S3
notification at an SNS topic instead, and subscribe a queue per
consumer. Each queue gets its own copy, retries independently, and one
slow consumer cannot block another. Adding consumer number five is a
subscription, not a change to the producer. This topic-with-queues-
subscribed pattern is the standard fan-out on AWS; enable raw message
delivery on the subscriptions so consumers do not have to unwrap an
extra SNS envelope.

### FIFO queues, and whether you need them

Standard SQS makes two loose promises: at-least-once delivery
(occasional duplicates) and best-effort ordering (occasional
reordering). FIFO queues tighten both: strict order within a message
group and exactly-once delivery within a five-minute dedup window, in
exchange for a throughput ceiling (300 msgs/s per group, thousands per
queue with batching and high-throughput mode) and slightly higher price
($0.50 vs $0.40 per million).

Most file-processing pipelines do not need FIFO. Processing
`sales_west.csv` before `sales_east.csv` changes nothing. Reach for
FIFO when operations on the same entity must apply in order, the
classic case being CDC: `UPDATE` then `DELETE` for the same row must
not swap. Then the message group ID is your ordering key (table name
or primary key), the same role the partition key plays in Kinesis. If
you cannot name the specific pair of messages that would corrupt data
by swapping, use standard.

### Dead-letter queues and redrive

Every production queue needs a dead-letter queue. The redrive policy
says: after a message has been received `maxReceiveCount` times without
being deleted, move it to the DLQ.

```json
{
  "deadLetterTargetArn": "arn:aws:sqs:us-east-1:123456789012:file-events-dlq",
  "maxReceiveCount": 5
}
```

Without a DLQ, a poison message (malformed file reference, record your
parser chokes on) cycles forever, burning Lambda invocations and
clogging metrics. With one, it gets five attempts and then steps aside.
Alarm on the DLQ depth: anything above zero means a human should look.
The nice part is recovery: SQS has a redrive button that moves DLQ
messages back to the source queue, so after you fix the parser bug, the
failed work re-runs with no custom scripts.

### Idempotent consumers, because duplicates are coming

At-least-once delivery means your consumer will eventually receive the
same message twice. Not might, will. If processing a message twice
double-inserts rows or double-sends alerts, the bug is in your consumer,
not in SQS.

The fix is idempotency: design processing so that doing it twice equals
doing it once.

- **Natural idempotency** where possible: overwriting
  `s3://curated/date=2026-07-10/vendor_a.parquet` twice yields the same
  lake state. Prefer deterministic overwrites over appends.
- **Dedup keys** where not: derive a stable ID (the S3 object key plus
  version, an `event_id` field) and record it transactionally with the
  work, using a conditional write.

```python
try:
    dedup_table.put_item(
        Item={"event_id": event_id, "processed_at": now},
        ConditionExpression="attribute_not_exists(event_id)",
    )
except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
    return  # already processed, exit quietly
process(message)
```

> **Idempotency is the price of admission** — Every event-driven system
> on AWS is at-least-once somewhere: SQS redelivers, Lambda retries, S3
> occasionally emits duplicate notifications, and you will redrive a DLQ
> someday. Write every consumer assuming its input will repeat.

### The visibility timeout gotcha

When a consumer receives an SQS message, the message is not deleted, it
is hidden for the visibility timeout (default 30 seconds). If the
consumer finishes and deletes it in time, done. If not, the message
reappears and another consumer picks it up.

Here is the classic incident: your Lambda takes 2 minutes to validate a
large file, but the queue's visibility timeout is 30 seconds. At second
30, the message becomes visible again while the first Lambda is still
working. A second Lambda starts processing the same file. Both finish,
both load the data, and you have duplicates that idempotency had better
catch.

The rule: **visibility timeout of at least 6x your Lambda timeout** when
using an event source mapping. At minimum, make it comfortably longer
than your worst-case processing time. And if processing legitimately
takes many minutes, a consumer can extend the timeout on the fly with
`ChangeMessageVisibility` as a heartbeat.

### EventBridge: the router

S3 events, SQS, and SNS cover point-to-point plumbing. EventBridge
sits a level above: a serverless event bus where AWS services, SaaS
apps, and your own code publish events, and rules pattern-match on
event content to route them to targets.

For data engineering it shows up in two places. First, reacting to
service events without glue code: "when this Glue crawler succeeds,
start that Step Functions state machine" is one rule. Second, as a
smarter S3 event source: EventBridge can receive all S3 events for a
bucket and route by key pattern, so `raw/vendor_a/*` goes to one queue
and `raw/vendor_b/*` to another, without cramming logic into bucket
notification config.

### Putting it together: the vendor file pipeline

1. The vendor file lands in `s3://raw/vendor_a/`. S3 emits an event to
   the `file-events` SQS queue.
2. A Lambda consumes the queue with `maximum_concurrency: 10`,
   validates the file, converts to Parquet, writes to the curated
   bucket keyed deterministically by file.
3. Bad file? The message retries 5 times and lands in the DLQ, which
   pages you with the exact S3 key attached.
4. On success, the Lambda publishes to the `file-processed` SNS topic.
   One subscribed queue feeds the warehouse loader, another Lambda
   posts to Slack.

---

## Module 5 · Lesson 2: Pipeline Security

*Written by Darshil Parmar, Founder & Lead Instructor, Data Vidhya.
Published (latest content).
Course URL: https://datavidhya.com/learn/aws-data-engineering/production-pipelines/pipeline-security/*

Your pipeline is a week from launch and the security team schedules a
review. They ask three questions: which identities can read the
customer table, is the data encrypted with a key you control, and if a
credential leaked yesterday, how would you know? You realize you can
confidently answer none of them. The pipeline works. That was never the
question.

Or the darker version: a data scientist's long-lived access key sits in
a notebook that gets pushed to a public repo. The key had `s3:*` because
that was easier during a debugging session two years ago. Within hours,
someone is listing every bucket in the account.

### One role per pipeline stage

The single highest-leverage pattern: every stage of the pipeline gets
its own IAM role, scoped to exactly what that stage does. Not one shared
`data-pipeline-role` that every Glue job, Lambda, and Step Function
assumes.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadRawOrders",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::acme-lake-raw",
        "arn:aws:s3:::acme-lake-raw/orders/*"
      ]
    },
    {
      "Sid": "WriteSilverOrders",
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::acme-lake-silver/orders/*"
    }
  ]
}
```

Define all of it in Terraform so the roles are reviewable in a pull
request rather than hand-edited in the console.

### Kill every long-lived access key

Access keys (`AKIA...`) never expire, work from anywhere on the
internet, and end up in notebooks, `.env` files, and shell histories.
Every leaked-credential incident I have seen started with one. The goal
is zero of them, and AWS gives you an alternative for every case where
people think they need one:

| "But I need a key for..." | What to use instead |
|---|---|
| Glue, Lambda, EMR, ECS jobs | The service's IAM role, attached at creation |
| GitHub Actions deploying to AWS | OIDC federation |
| Engineers on laptops | AWS SSO / Identity Center |
| A vendor tool that truly only accepts keys | A dedicated IAM user with a minimal policy, rotated on a schedule |

### Encrypting the lake: SSE-S3 vs SSE-KMS

Every production bucket should have two things set before it holds a
single byte: Block Public Access turned on at the account level, and
default encryption.

- **SSE-S3** encrypts with keys AWS manages entirely. Free, zero
  configuration, invisible.
- **SSE-KMS** encrypts with a key in AWS KMS that you control. The key
  costs $1/month, and each encrypt/decrypt call costs $0.03 per 10,000
  requests.

Enable S3 Bucket Keys on the bucket to cut KMS request cost by over 90
percent. Then make encryption and transport non-optional with a bucket
policy that denies `aws:SecureTransport = false`.

### Keep pipeline traffic off the public internet

VPC endpoints fix the default internet path: a gateway endpoint for S3
(free) and interface endpoints for Glue, KMS, and Secrets Manager route
traffic over the AWS private network.

### Secrets: where the database password lives

Pipelines talk to things with passwords. Those credentials belong in
exactly two places: Secrets Manager and SSM Parameter Store.

```python
import boto3, json

secret = json.loads(
    boto3.client("secretsmanager")
    .get_secret_value(SecretId="prod/orders-db")["SecretString"]
)
# secret["username"], secret["password"], secret["host"]
```

### Lake Formation: when bucket-level access is not enough

IAM speaks in buckets, prefixes, and objects. Consumers speak in
tables, columns, and rows. Lake Formation closes the gap by putting a
grant layer on top of the Glue catalog:

```sql
GRANT SELECT (order_id, order_date, region, amount)
ON TABLE silver.orders TO ROLE analytics_team;
```

The email column simply does not exist for that team, in Athena,
Redshift Spectrum, or EMR.

### Common incidents, and the control that prevents each

| Incident | Root cause | Prevention |
|---|---|---|
| Credential leaked via public repo | Long-lived access key with broad policy | No access keys: roles for services, OIDC for CI, SSO for humans |
| Data lake bucket found publicly readable | Bucket ACL or policy misconfigured | Account-level Block Public Access |
| Contractor reads customer emails | Table-level grant where column-level was needed | Lake Formation column grants |
| Attacker uses a database password from an old wiki page | Static credential, never rotated | Secrets Manager with 30-day rotation |
| Post-incident: no record of what was read | Data events never enabled | CloudTrail data events on sensitive buckets |
| Pipeline traffic intercepted | Public internet path, no network condition | VPC endpoints plus `aws:sourceVpce` conditions |

---

## Module 5 · Lesson 2: Cost Optimization

*Written by Darshil Parmar, Founder & Lead Instructor, Data Vidhya.
Published Jul 10, 2026.
Course URL: https://datavidhya.com/learn/aws-data-engineering/production-pipelines/cost-optimization/*

The message arrives from your engineering manager with a screenshot
attached: last month's AWS bill was $6,100, up from $3,200 two months
ago, and finance wants an explanation by Friday. Nobody changed
anything big. No new pipelines launched. The bill just... doubled.

The naive response is to guess. The real approach has two parts. First,
measure: get the bill broken down by service and by pipeline, because
the top line item is rarely what you would guess. Second, work through
each service with its specific levers.

### Where DE money actually goes

Every stack is different, but after the bill crosses a few thousand
dollars a month, data platforms tend to converge on a similar shape:

| Category | Typical share | Usual culprit |
|---|---|---|
| Compute that runs when nothing needs it | 30 to 40 percent | Always-on EMR, dev Redshift running weekends, oversized MWAA |
| Query engines scanning too much | 20 to 30 percent | Athena over unpartitioned CSV/JSON, `SELECT *` everywhere |
| Over-provisioned job compute | 15 to 20 percent | Glue jobs with 10 DPUs doing 2 DPUs of work |
| Storage that never gets cleaned | 10 to 15 percent | No lifecycle rules, versioning bloat, failed multipart uploads |
| Streaming capacity mismatch | 5 to 10 percent | On-demand Kinesis at steady load, or idle provisioned shards |

### S3: cheap per gigabyte, expensive by neglect

Lifecycle rules are the big lever. Your bronze layer from 2023 has not
been queried in a year, but it is still paying Standard rates. A
lifecycle rule that moves objects to Standard-IA ($0.0125/GB) after 90
days and Glacier Instant Retrieval ($0.004/GB) after a year cuts
old-data cost by 80 percent with one policy:

```json
{
  "Rules": [{
    "ID": "age-out-bronze",
    "Filter": { "Prefix": "bronze/" },
    "Status": "Enabled",
    "Transitions": [
      { "Days": 90, "StorageClass": "STANDARD_IA" },
      { "Days": 365, "StorageClass": "GLACIER_IR" }
    ],
    "AbortIncompleteMultipartUpload": { "DaysAfterInitiation": 7 }
  }]
}
```

### Athena: you pay for what you scan

Athena charges $5 per TB scanned, and the difference between a naive
query and a tuned one on the same data is routinely 100x. Three levers,
in order of impact: partitioning, Parquet over CSV/JSON, and select
only what you need.

| Query on 2 TB of raw events | Data scanned | Cost |
|---|---|---|
| `SELECT *` on unpartitioned JSON | 2,000 GB | $10.00 |
| Same data as partitioned Parquet, `SELECT *`, one day | 8 GB | $0.04 |
| Partitioned Parquet, 3 columns, one day | 1.2 GB | $0.006 |

### Glue: right-size, then go flex

Glue bills $0.44 per DPU-hour, and the default is 10 DPUs. Most jobs
get created with the default and never touched. Open the job's metrics:
if executors sit mostly idle and the run is short, drop to 2 or 4 DPUs
and watch whether duration actually changes.

**Flex execution** runs your job on spare capacity at $0.29 per
DPU-hour, about a third off. Startup can be delayed a few minutes,
which is irrelevant for a nightly batch.

### EMR: spot instances and auto-termination

EMR waste comes in two flavors: paying on-demand prices for
interruptible work, and paying anything at all for idle clusters.

**Spot** gives you 60 to 90 percent off EC2 for capacity AWS can
reclaim. Keep the master and core nodes on on-demand, and run task nodes
on spot.

**Auto-termination** is the bigger one. Set
`--auto-termination-policy '{"IdleTimeout": 3600}'` and a forgotten
cluster shuts itself down after an hour of idleness.

### Kinesis: the on-demand vs provisioned crossover

On-demand Kinesis charges about $0.04 per stream-hour (roughly
$29/month baseline) plus $0.08 per GB ingested. Provisioned charges
$0.015 per shard-hour (about $11/month per shard) plus $0.014 per
million PUT payload units.

The rough math: one provisioned shard handles 1 MB/s in, which is about
2.5 TB/month at full utilization. The same 2.5 TB through on-demand
costs about $200 in ingestion alone. Start new streams on-demand, look
at the actual throughput after a month, and switch to provisioned once
the pattern is boring.

### Redshift, Lambda, MWAA: the quick hits

**Redshift** is often the single biggest line item. Dev and staging
clusters do not need to run at 3 AM or on weekends: a scheduled
pause/resume on an RA3 cluster cuts compute cost by roughly 65
percent.

**Lambda** cost is memory times duration, and the memory setting also
controls CPU. Counterintuitively, more memory can be cheaper: a function
that takes 10 seconds at 512 MB might take 2 seconds at 2048 MB.

**MWAA** bills per environment-hour: a small environment runs about
$350/month before workers, a medium about $700.

### Seeing the bill: tags, Cost Explorer, and budgets

**Tag everything** with a small, enforced set: `team`, `pipeline`,
`env`. Put the tags in your Terraform as `default_tags` on the provider
so nothing ships untagged.

**Budget alarms** close the loop. An AWS Budget with an SNS notification
at 80 and 100 percent of expected monthly spend turns "finance noticed
after six weeks" into "Slack pinged us on day three."

### A worked example: $6,000 to $2,400

| Item | Before | Change | After |
|---|---|---|---|
| EMR (backfill cluster left running 24/7) | $1,800 | Transient clusters, task nodes on spot, 1-hour idle auto-termination | $500 |
| Redshift (prod + dev RA3, both 24/7) | $1,600 | Pause dev nights and weekends; 1-year RI on prod | $900 |
| Athena (unpartitioned JSON, `SELECT *`) | $900 | Partitioned Parquet, column pruning, 100 GB workgroup limit | $150 |
| Glue (every job at default 10 DPUs) | $700 | Right-sized to 2 to 4 DPUs, flex on nightly jobs | $400 |
| S3 (no lifecycle, versioning bloat) | $600 | Lifecycle to IA/Glacier IR, noncurrent version expiry | $250 |
| Kinesis (on-demand at steady 0.8 MB/s) | $250 | Switched to 2 provisioned shards | $80 |
| CloudWatch and misc | $150 | Log retention set to 60 days, dropped DEBUG logging | $120 |
| **Total** | **$6,000** | | **$2,400** |

Sixty percent off, no pipeline deleted, no SLA missed. Find the waste
before you touch anything that works.

---

## Module 1 · Lesson 1: AWS vs GCP vs Azure

*Written by Darshil Parmar, Founder & Lead Instructor, Data Vidhya.
Published Mar 16, 2026.
Course URL: https://datavidhya.com/learn/aws-data-engineering/cloud-fundamentals/aws-vs-gcp-vs-azure/*

You've decided to learn cloud. You open three browser tabs — AWS, GCP,
Azure — and within five minutes you're drowning. AWS has 200+ services.
GCP has BigQuery, which everyone raves about. Azure has... Microsoft
enterprise contracts. You close all three tabs and go back to watching
YouTube tutorials about pandas.

This is the wrong approach. Cloud platform selection for data
engineering is not a research project — it's a career decision that you
can make in about ten minutes with the right framework. Let me give you
that framework.

### The Cloud Market in 2025

Before we talk about data engineering specifically, here's where the
market stands:

| Provider | Global Market Share | DE Job Listings (approx.) | Strongest Signal |
|----------|---------------------|---------------------------|------------------|
| AWS | ~32% | ~60% of cloud DE roles | Default for startups and most tech companies |
| Azure | ~23% | ~25% of cloud DE roles | Dominant in enterprise, Fortune 500, healthcare |
| GCP | ~12% | ~15% of cloud DE roles | Strongest DE/ML tooling, BigQuery is best-in-class |

These numbers matter because your goal isn't to pick the "best" cloud —
it's to pick the cloud that maximizes your career options. And right
now, that's AWS by a wide margin in terms of raw job availability.

> **The 60% Rule** — Roughly 60% of data engineering job listings
> mention AWS. That doesn't mean AWS is technically superior — it means
> more companies use it, so more companies hire for it.

### Head-to-Head: Data Engineering Service Comparison

Here's where it gets interesting. The three clouds have roughly
equivalent services for everything, but the quality and developer
experience vary enormously for DE-specific workloads.

| Capability | AWS | GCP | Azure |
|------------|-----|-----|-------|
| Object Storage | S3 (gold standard) | GCS (excellent) | ADLS Gen2 (good) |
| Data Warehouse | Redshift | BigQuery (best-in-class) | Synapse Analytics |
| Serverless ETL | Glue | Dataflow (Beam) | Data Factory |
| Managed Spark | EMR | Dataproc | HDInsight / Databricks |
| Streaming | Kinesis / MSK | Pub/Sub + Dataflow | Event Hubs |
| Orchestration | Step Functions / MWAA | Cloud Composer | Data Factory pipelines |
| Data Catalog | Glue Data Catalog | Data Catalog | Purview |
| Serverless Compute | Lambda | Cloud Functions | Azure Functions |
| ML Platform | SageMaker | Vertex AI | Azure ML |

#### Where Each Cloud Wins for DEs

**AWS wins on breadth and ecosystem.** S3 is the de facto standard for
data lakes. Every open-source tool integrates with AWS first. Glue is
serviceable but clunky. EMR is powerful but requires cluster management
expertise.

**GCP wins on data engineering experience.** BigQuery is genuinely the
best serverless data warehouse — no cluster management, no tuning, just
SQL that scales to petabytes. Dataflow (Apache Beam) provides true
unified batch and streaming. Pub/Sub is simpler than Kafka for most use
cases.

**Azure wins on enterprise integration.** If your company runs on
Microsoft (Active Directory, Office 365, Power BI), Azure is the
natural choice. Azure Databricks is arguably the best Databricks
experience.

> **The BigQuery Exception** — Even if you learn AWS as your primary
> cloud, learn BigQuery from GCP. It's that good. Many companies use a
> multi-cloud approach specifically to leverage BigQuery for analytics
> while running infrastructure on AWS.

### The Decision Framework

Stop overthinking this. Here's the decision tree:

- **Are you learning cloud for the first time?** Learn AWS.
- **Are you already employed?** Learn whatever your company uses.
- **Are you focused on analytics engineering (dbt, SQL-heavy)?** Learn
  GCP/BigQuery.
- **Are you in enterprise / Fortune 500 / healthcare?** Learn Azure.
- **Are you targeting ML engineering + DE?** GCP's Vertex AI + BigQuery
  ML is the most cohesive ML platform.

#### The Opinionated Default for 80% of Aspiring DEs

Learn AWS first. Get comfortable with S3, IAM, Glue, Redshift, and
Lambda. Then learn BigQuery from GCP — it takes a weekend, and it will
come up in interviews constantly.

### The Multi-Cloud Reality

Most companies above 500 employees use more than one cloud:

- **Acquisitions**: Company A runs on AWS, acquires Company B which
  runs on GCP.
- **Best-of-breed**: Run infrastructure on AWS, analytics on BigQuery,
  ML on Vertex AI.
- **Vendor leverage**: Using two clouds gives you negotiating power on
  pricing.
- **Compliance**: Some regulated industries require data residency in
  specific regions.

The implication: learning one cloud deeply and a second cloud at a
surface level is more valuable than learning one cloud exhaustively.

### Cost Comparison: 100GB/Day Pipeline

| Component | AWS | GCP | Azure |
|-----------|-----|-----|-------|
| Object Storage (3TB stored) | S3: $69/mo | GCS: $60/mo | ADLS: $62/mo |
| ETL Processing (serverless) | Glue: $220/mo | Dataflow: $180/mo | Data Factory: $200/mo |
| Data Warehouse (3TB, moderate queries) | Redshift Serverless: $450/mo | BigQuery on-demand: $300/mo | Synapse Serverless: $400/mo |
| Orchestration | MWAA: $350/mo | Composer: $400/mo | Data Factory: included |
| Monitoring | CloudWatch: $30/mo | Cloud Monitoring: $25/mo | Monitor: $30/mo |
| **Total** | **~$1,120/mo** | **~$965/mo** | **~$692/mo** |

The real cost difference isn't in list prices — it's in operational
overhead. BigQuery requires zero cluster management. Factor in
engineering time and GCP often wins on total cost of ownership for
analytics workloads.

### Common Mistakes

**Mistake 1: Spending months "researching" before starting.** Pick one
and start building.

**Mistake 2: Learning all three clouds at surface level.** Depth beats
breadth.

**Mistake 3: Ignoring the free tier.**
- AWS: 12-month free tier with 5GB S3, 750 hours EC2 t2.micro
- GCP: $300 credit for 90 days + always-free tier (1TB BigQuery
  queries/month)
- Azure: $200 credit for 30 days + 12-month free services

**Mistake 4: Thinking certification equals competence.** Get the cert
after you've built something.

**Mistake 5: Dismissing a cloud because of online opinions.** All three
clouds are reliable.

### In an Interview

**Junior / Mid-Level**: Name the primary DE services on at least one
cloud. Know the rough equivalents across clouds.

**Senior**: Discuss tradeoffs between clouds for specific use cases.
Know cost implications.

**Staff+**: Make multi-cloud architecture decisions. Handle data
gravity. Address cross-cloud IAM strategy.

The most common trap: saying "it depends" without following up with
specific criteria.

---

## Module 1 · Lesson 2: Cloud Storage for Data Engineers (S3, GCS, ADLS)

*Written by Darshil Parmar, Founder & Lead Instructor, Data Vidhya.
Published Mar 16, 2026.
Course URL: https://datavidhya.com/learn/aws-data-engineering/cloud-fundamentals/cloud-storage/*

Every data pipeline starts and ends with storage. Your Spark job reads
from storage. Your dbt models materialize to storage. Your ML models
train on data sitting in storage. If compute is the brain of your
pipeline, storage is the bloodstream — everything flows through it.

And yet, most data engineers treat object storage as a solved problem.
"Just throw it in S3" is the default answer. That attitude works until
you get a $14,000 monthly bill because nobody configured lifecycle
policies, or your pipeline takes 45 minutes because you're reading
50,000 tiny JSON files instead of 500 Parquet files.

Object storage is the most important primitive in cloud data
engineering. Let's learn it properly.

### Object Storage: The Foundational Primitive

Object storage is fundamentally different from the file systems you're
used to. There are no directories — just keys and values. When you see
`s3://my-bucket/data/2025/01/events.parquet`, that entire path including
"directories" is one flat key. The "folders" are an illusion that the UI
creates for you.

This matters because:

- **Listing operations are expensive.** `ls` on a "directory" with
  100,000 objects can take seconds and cost money (S3 charges $0.005
  per 1,000 LIST requests).
- **There's no rename operation.** "Renaming" a file is a copy +
  delete. Renaming a "directory" means copying every object
  individually.
- **Consistency is eventual (mostly).** S3 now offers strong
  read-after-write consistency, but GCS and ADLS have had this for
  longer. Know your cloud's consistency model.

> "Think of object storage as a giant hash map: the key is the full
> path, the value is the file contents plus metadata."

### S3 for Data Engineers

Amazon S3 is the gold standard. It was launched in 2006 and basically
invented cloud object storage. Every tool in the data ecosystem supports
S3, often before other storage systems.

#### What DEs Need to Know About S3

**Storage Classes** — S3 offers multiple storage tiers, and choosing
the right one is free money:

| Storage Class | Cost (per GB/mo) | Use Case |
| --- | --- | --- |
| S3 Standard | $0.023 | Hot data, frequent access |
| S3 Infrequent Access (IA) | $0.0125 | Data accessed monthly or less |
| S3 Glacier Instant Retrieval | $0.004 | Archival with rare but immediate needs |
| S3 Glacier Deep Archive | $0.00099 | Long-term compliance, accessed yearly |

**The math is simple**: if you have 10TB of data older than 90 days
that's rarely accessed, moving it from Standard to IA saves $105/month.
Moving it to Glacier Deep Archive saves $220/month. For 100TB, that's
$2,200/month — $26,400 per year — just from a lifecycle policy.

**Partitioning Strategy** — How you organize data in S3 determines
your query performance:

```
# Good: Hive-style partitioning for time-series data
s3://data-lake/events/year=2025/month=01/day=15/events.parquet

# Bad: Flat dump
s3://data-lake/events/events_20250115.parquet

# Worse: One giant file
s3://data-lake/events/all_events.parquet
```

Hive-style partitioning lets query engines (Athena, Spark, Presto) skip
entire partitions — a query for January data never touches February's
files.

**File Sizing** — This is where most teams get burned. S3 performs
best with files between 128MB and 1GB. Too many small files (the
"small files problem") destroys performance because each file requires
a separate HTTP request to open, read headers, and process.

### GCS for Data Engineers

Google Cloud Storage is functionally equivalent to S3 with a few
DE-relevant differences:

- **Stronger consistency**: GCS has offered strong consistency since
  launch. No worrying about read-after-write delays.
- **Simpler storage classes**: Standard, Nearline (30-day minimum),
  Coldline (90-day minimum), Archive (365-day minimum).
- **Native BigQuery integration**: Loading data from GCS to BigQuery is
  seamless and free (you pay for storage, not the load operation).
- **gsutil is excellent**: Google's CLI tool for GCS is arguably better
  than the AWS CLI for bulk operations.

The pricing is competitive with S3:

| Storage Class | Cost (per GB/mo) |
| --- | --- |
| Standard | $0.020 |
| Nearline | $0.010 |
| Coldline | $0.004 |
| Archive | $0.0012 |

> "Loading data from GCS into BigQuery is free — you only pay for the
> GCS storage and the BigQuery storage after loading."

### ADLS Gen2 for Data Engineers

Azure Data Lake Storage Gen2 is Azure's answer to S3/GCS, built on top
of Azure Blob Storage with a hierarchical namespace — meaning it
actually has real directories, unlike S3 and GCS.

Key differences for DEs:

- **Hierarchical namespace**: Real directories mean rename operations
  are atomic and fast. This matters for Spark, which writes to
  temporary directories and renames them on completion.
- **Azure AD integration**: Permissions use the same Azure Active
  Directory as everything else in a Microsoft shop.
- **Databricks optimized**: ADLS Gen2 + Azure Databricks is one of the
  tightest storage-compute integrations available.
- **Pricing**: $0.021/GB/month for hot tier, competitive with S3/GCS.

The tradeoff: ADLS Gen2 is excellent within the Azure ecosystem but
has weaker support from open-source tools compared to S3.

### File Formats: The Decision That Matters Most

Choosing the right file format has a bigger impact on pipeline
performance than almost any other storage decision. Here's the honest
breakdown:

| Format | Type | Compression | Schema | Best For |
| --- | --- | --- | --- | --- |
| **Parquet** | Columnar | Excellent (Snappy/Zstd) | Embedded | Analytics, warehousing — **default choice** |
| **Avro** | Row-based | Good (Deflate/Snappy) | Embedded | Streaming, write-heavy, schema evolution |
| **ORC** | Columnar | Excellent (Zlib/Snappy) | Embedded | Hive ecosystem specifically |
| **JSON** | Row-based | Poor | None | APIs, human-readable interchange |
| **CSV** | Row-based | None | None | Legacy systems, spreadsheet people |
| **Delta Lake** | Columnar (Parquet + log) | Excellent | Embedded + evolution | ACID on data lakes, time travel |
| **Apache Iceberg** | Columnar (Parquet + metadata) | Excellent | Embedded + evolution | Open table format, multi-engine |

#### The Opinionated Guide

**Use Parquet for 90% of your work.** It's the industry standard for
analytics. Columnar layout means queries that touch 5 out of 50 columns
only read 10% of the data. Snappy compression typically reduces file
size by 60-80% compared to raw CSV.

**Use Avro for streaming ingestion.** When you're writing lots of small
records quickly (Kafka consumers, CDC streams), Avro's row-based format
and schema registry integration make it the better choice. Convert to
Parquet in your batch layer.

**Use Delta Lake or Iceberg for your lakehouse layer.** These add ACID
transactions, time travel, and schema evolution on top of Parquet. If
you're building a data lakehouse, you need one of these. Iceberg is
gaining momentum as the vendor-neutral choice, but Delta Lake has a
head start in Databricks shops.

**Stop using CSV in pipelines.** Seriously. Switching from CSV to
Parquet typically drops storage by 70% and query time by 90%. CSV has
no schema, no compression, no column pruning. The only acceptable use
of CSV is as an input format from external systems you don't control.

> "A team storing 1TB of CSV in S3 Standard pays $23/month in storage.
> The same data in Parquet with Snappy compression: roughly 300GB,
> costing $6.90/month."

### Storage Cost Deep Dive

Storage costs seem cheap until they're not. Here's how costs accumulate
for a typical data pipeline:

#### The Hidden Costs

**Egress charges** are the silent killer. Downloading data from S3 to
the internet costs $0.09/GB. Moving 10TB out of AWS per month: $900.
Moving data between AWS regions: $0.02/GB. These costs are invisible
until the bill arrives.

**API request costs** add up with small files. S3 charges $0.005 per
1,000 GET requests. If your pipeline reads 1 million small files per
day, that's $5/day just in GET requests — $150/month — for a cost you
could eliminate by compacting files.

**Versioning without lifecycle policies** is a storage bomb. S3
versioning keeps every version of every object. Without a policy to
expire old versions, your storage grows silently. I've seen teams
paying for 5x their actual data volume because of unmanaged versions.

#### Lifecycle Policies Are Free Money

Every cloud offers lifecycle policies that automatically transition
data between storage tiers. Set them up on day one:

```
# Example S3 lifecycle policy logic:
# - After 30 days: move to Infrequent Access
# - After 90 days: move to Glacier Instant Retrieval
# - After 365 days: move to Glacier Deep Archive
# - After 7 years: delete (if compliance allows)
```

This single configuration can reduce storage costs by 60-80% for
historical data with zero impact on your pipeline, because your
pipeline only processes recent data.

### Common Mistakes

**Mistake 1: Ignoring the small files problem.** Ingesting one file
per Kafka message creates millions of tiny files. Compact them. Use a
scheduled job that merges small files into 128MB-1GB Parquet files.
This alone can make your queries 10-50x faster.

**Mistake 2: Not setting lifecycle policies.** Every bucket should
have a lifecycle policy from day one. Even a simple "move to IA after
90 days" saves meaningful money at scale.

**Mistake 3: Using the wrong storage class.** Putting archival data
in S3 Standard because "it's easier" wastes money linearly with data
volume. At 100TB, the difference between Standard and Glacier Deep
Archive is $2,200/month.

**Mistake 4: Not partitioning data.** A flat bucket of Parquet files
forces full scans. Partitioning by date (and optionally by a
high-cardinality dimension) is almost always the right starting point.

**Mistake 5: Treating object storage like a file system.** Don't build
pipelines that depend on listing directories, renaming files, or
checking file existence in tight loops. These operations are slow and
expensive on object storage. Use manifest files or metadata catalogs
instead.

### In an Interview

Storage questions reveal whether a candidate has actually built
pipelines or just read about them.

**Junior / Mid-Level**: You should know what S3/GCS is and how to
read/write data from it. Explain the difference between Parquet and CSV
and why Parquet is preferred. Know that partitioning exists and why it
helps. Understand at a high level what storage classes are and that
lifecycle policies save money.

**Senior**: You should be able to design a storage layer for a
pipeline. What partitioning scheme? What file format and compression?
What file sizes? How do you handle the small files problem? What
lifecycle policies? What's your cost estimate for 1TB/day ingestion?
Be able to calculate rough storage costs and explain the tradeoffs
between storage tiers.

**Staff+**: You should be able to discuss storage strategy at the
organizational level. How do you enforce partitioning standards across
teams? How do you handle cross-account or cross-region data access?
What's your table format strategy (Delta vs Iceberg)? How do you
manage data lake governance — who can write to which paths, how do you
prevent schema drift in storage? What's your approach to data
compaction at petabyte scale?

A great answer to "How would you set up storage for a new data
pipeline?" covers: bucket structure, partitioning scheme, file format
(Parquet), target file size (128MB-1GB), lifecycle policy, and access
controls — all in under two minutes.

---

## Module 2 · Lesson 2: AWS Fundamentals

*Written by Darshil Parmar, Founder & Lead Instructor, Data Vidhya.
Published Jun 19, 2026.
Course URL: https://datavidhya.com/learn/aws-data-engineering/aws-data-stack/aws-fundamentals/*

AWS has a service for almost everything in a data pipeline — which is
exactly what makes it overwhelming when you start. This lesson gives
you the mental map: the core AWS data services, what each one is for,
and how they connect from raw data to a query-ready warehouse.

### The AWS data stack at a glance

Every data pipeline does four things — ingest, store, process, and
serve. Here's where the main AWS services land:

- **Storage (the foundation):** Amazon S3 — your data lake. Almost
  every AWS pipeline reads from and writes to S3.
- **Ingestion & streaming:** Kinesis / MSK for real-time event streams,
  Lambda for lightweight event-driven ingestion.
- **Processing & transformation:** AWS Glue (serverless Spark + Data
  Catalog) and Amazon EMR (managed Spark/Hadoop clusters) for heavier
  workloads.
- **Warehouse & serving:** Amazon Redshift for fast analytical
  queries; query S3 directly with Athena.
- **Orchestration:** Step Functions (and MWAA/Airflow) to wire the steps
  together with retries and error handling.

### How the pieces fit together

A typical batch pipeline on AWS looks like this:

1. Raw data lands in **S3** (from an app, an API, or a database
   export).
2. **Glue** or **EMR** reads it, cleans and transforms it, and writes
   curated tables back to **S3**.
3. **Redshift** (or **Athena** over S3) serves those tables to
   dashboards and analysts.
4. **Step Functions** orchestrates the whole flow; **Lambda** handles
   the small event-driven glue in between.

The rest of this module goes service by service. The goal isn't to
memorize every option — it's to know which tool to reach for at each
stage, and the cost and scaling trade-offs that come with it.

### What comes next

Start with S3 for Data Engineers — it's the foundation everything else
builds on — then work through Glue, Redshift, EMR, and the rest in
order.
