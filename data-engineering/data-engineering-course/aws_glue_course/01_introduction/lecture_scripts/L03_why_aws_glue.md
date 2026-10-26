# L03 — Why AWS Glue (and who uses it)

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 1 — Introduction
> **Duration target:** 4:00

## What this lecture covers

- The 30,000-foot view of AWS Glue: what it is, who uses it, and why it matters.
- The 3 categories of ETL: batch, streaming, and data quality.

## Narration

> "Why AWS Glue? Let me give you the 30-second answer first: AWS Glue is the serverless ETL service from AWS. You write a Python or Scala script, point it at a source (an S3 bucket, a JDBC database, a Kinesis stream), and Glue runs the script on a managed Spark cluster. You don't manage servers. You don't patch Spark. You don't provision EC2 instances. You just write the script and run the job. Companies like JPMorgan, Vanguard, Capital One, FINRA — they all run petabyte-scale ETL on Glue every day. The top use cases: data lakes (move raw data from S3 to a curated zone in Parquet), data warehousing (move data from operational databases to Redshift), streaming analytics (process Kinesis or Kafka streams in near real-time), and data quality (enforce schema and value constraints on the data). The 3 categories of ETL we'll cover: batch (Section 7, run on a schedule), streaming (Section 9, run continuously), and data quality (Section 10, run as a post-step on a Glue Job). The course covers all 3 with real working code. The 4 downloadable resources — the sample data, the CloudFormation template, the trust policy, and the Glue script — are real, runnable, and not toy examples. You can copy them into your own account and they will work."

## Key bullets

- AWS Glue is **serverless** — no servers to manage.
- The 3 categories: **batch** (Section 7), **streaming** (Section 9), **data quality** (Section 10).
- Glue runs Spark 3.3 + Python 3.10 (Glue 4.0) or Spark 2.4 + Python 3.7 (Glue 3.0).
- The course is hands-on: every section has at least one lab; the 4 downloadable resources are real, runnable code.

## On-screen

- A pie chart: 60% batch ETL, 25% streaming ETL, 15% data quality (rough industry split per AWS marketing material).
- A screenshot of the Glue console home (optional).