# Section 3 — S3 + CLI Hands-on (Lectures L20-L24)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
>
> This file bundles 5 lecture scripts (L20-L24) for Section 3.

---

## L20 — Section Overview (0:39)

> "Section 3 is the S3 hands-on. We create the buckets, we configure the CLI, we upload the CSV. By the end of this section, you'll have 2 buckets, the `city_temperature.csv` uploaded, and your CLI configured for use in Sections 4-9."

---

## L21 — Course Materials (1:09)

> "The 4 downloadable resources for the course are: 1) `city_temperature.csv` — the sample data, 2) `glue_service_trust_policy.json` — the IAM trust policy, 3) `glue_pipeline_stack.yaml` — the full CloudFormation template, 4) `glue_job_aggregate_cities.py` — the Glue Job script. All 4 are in the course's `downloads/` directory. The CSV is 480 rows of city temperature data for 20 cities across 20 countries, 2 years (1995 and 2000). It's small enough to fit in memory but big enough to exercise the Glue Job in real time."

---

## L22 — Creating S3 Buckets (1:58)

> "Let me show you the bucket creation in the console. S3 → Buckets → Create bucket. Bucket name: `awsglueudemycourse-datasoup-gluejob2-source`. Note: bucket names are *globally unique* — if someone else has this name in any AWS account, you must pick a different one. AWS region: US East (N. Virginia) us-east-1. Under 'Block Public Access settings for this bucket', leave all 4 boxes checked. Under 'Bucket Versioning', enable. Under 'Default encryption', select 'Server-side encryption with Amazon S3 managed keys (SSE-S3)'. Click Create bucket. The bucket is now ready."

Acceptance: bucket exists; versioning enabled; encryption enabled; public access blocked.

---

## L23 — Uploading Data to S3 Buckets (2:38)

> "Now let's upload the CSV. You can drag-and-drop in the console, but the CLI is more reproducible. From your terminal, run: `aws s3 cp city_temperature.csv s3://<your-source-bucket>/input/`. The CLI returns `upload: city_temperature.csv to s3://<your-source-bucket>/input/city_temperature.csv`. To verify: `aws s3 ls s3://<your-source-bucket>/input/`. The file should appear. To download later: `aws s3 cp s3://<your-source-bucket>/input/city_temperature.csv ./`. The `cp` command is for single files; for directories, use `sync`."

Lab: upload the CSV; verify with `ls`.

---

## L24 — Upload city_temperature.csv file to bucket (1:30 lab)

The hands-on portion of L23, with the assignment to upload + verify + take a screenshot.

---

## Section 3 Quiz

5 questions, see `quizzes/section_3.md`.
