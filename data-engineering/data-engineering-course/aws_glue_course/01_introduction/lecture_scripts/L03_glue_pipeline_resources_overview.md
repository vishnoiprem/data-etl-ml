# L03 — Glue Pipeline Resources (Section 2, 3, and 5) Overview

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 1 — Introduction
> **Duration target:** 3:01

## What this lecture covers

- A preview of the **3 production-grade pipelines** you'll build in Sections 2, 3, and 5.
- The shared resources: source S3, target S3, IAM role, Glue Job.

## Narration

> "Before we get into IAM and S3, let me show you the 3 pipelines you'll build. The first is the *GlueJob2-Country-Aggregate* pipeline — it reads the `city_temperature.csv` from the source bucket, aggregates by country, and writes Parquet to the target bucket. The second is a streaming pipeline — it generates synthetic events, sends them to Kinesis, and runs 2 streaming jobs (a loading job and a transforming job) to write to S3. The third is a Data Quality pipeline — it adds 3 DQ rules to the batch job, publishes CloudWatch metrics, and fires an alarm on failure. All 3 share the same AWS resources pattern: a source bucket, a target bucket, an IAM role, and a Glue Job. The pattern is what you'll learn in this section."

## The shared resources pattern

```
source-bucket (CSV)  →  GlueJobRole (IAM)  →  Glue Job  →  target-bucket (Parquet)
```

- **Source bucket**: where the input data lives.
- **GlueJobRole**: the IAM role Glue assumes to run the Job. Must have `s3:GetObject` on source, `s3:PutObject` on target, and the `AWSGlueServiceRole` managed policy.
- **Glue Job**: the Spark script that does the transform.
- **Target bucket**: where the output is written.

## On-screen

- A diagram of the 3-pipeline pattern with shared resources highlighted.
