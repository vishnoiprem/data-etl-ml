# AWS Glue — The Complete Masterclass

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
>
> **Source title:** *AWS Glue - The Complete Masterclass*
> **Subtitle:** Master building complete AWS Glue ETL Pipelines, Glue Data Quality, Glue Data Brew along with other AWS resources
> **Instructor:** pvishnoi
> **Format:** 11 sections, 78 lectures, 4h 11m total
> **Includes:** 3 role plays, 4 downloadable resources, assignments, quiz per section

This is the **author's source material** for the Udemy course. The repo
ships the full course as markdown so it can be version-controlled, diffed
in PRs, and rebuilt into slides / video / audio at any time.

## Course content map

| Section | Folder | Lectures | What it covers |
|---|---|---|---|
| 1. Introduction | `01_introduction/` | 1-6 | Course overview, glue pipeline resources preview, IAM/KMS/SNS/Glue Catalog at 30,000 ft |
| 2. IAM, KMS, SNS | `02_iam_kms_sns/` | 7-12 | Authentication vs authorization, IAM users/groups/roles/policies, KMS encryption keys, SNS pub/sub |
| 3. S3 + CLI | `03_s3_cli/` | 13-21 | S3 101, AWS CLI 101, CLI config, CloudFormation 101, hands-on S3 bucket creation + upload |
| 4. Glue Catalog + Crawler + Job | `04_glue_catalog_crawler/` | 22-37 | Glue Catalog, Crawler, Classifier, 5 crawlers hands-on, Glue Job, Trigger, Workflow |
| 5. CloudFormation Templates | `05_glue_cfn_templates/` | 38-44 | CFN 101, 3 CFN template walkthroughs, upload to S3 |
| 6. Glue Pipeline Lab | `06_glue_pipeline_lab/` | 45-54 | Deploy stack via CFN, debug, analyze Glue Job script, verify output |
| 7. Glue Pipeline Debug | `07_glue_pipeline_debug/` | 55-62 | Fix script retrieval, launch error, glue argument, resource policy, identity policy, workflow |
| 8. Glue Streaming | `08_glue_streaming/` | 63-71 | Streaming pipeline, generator job, loading job, transforming job, run all 3 |
| 9. Glue Data Quality | `09_glue_data_quality/` | 72-79 | DQ 101, rule set, Glue Job with DQ, CloudWatch metrics, alerts |
| 10. DataBrew | `10_databrew/` | 80-85 | DataBrew 101, profile data, project, recipe, job |
| 11. Role Plays | `11_role_plays/` | 3 scenarios | Diagnose trust misconfig / streaming job falling behind / pitch DQ to manager |

(The exact mapping to Udemy's 78 lectures is in `SYLLABUS.md`.)

## Asset map

| Asset | Path | Format |
|---|---|---|
| Course README (this file) | `aws_glue_course/README.md` | markdown |
| Lecture-to-file map | `aws_glue_course/SYLLABUS.md` | markdown |
| 78 lecture scripts | `aws_glue_course/0X_*/lecture_scripts/L*.md` | markdown |
| 11 section quizzes | `aws_glue_course/quizzes/section_X.md` | markdown (Q + answer + explanation) |
| 6 assignment prompts | `aws_glue_course/assignments/*.md` | markdown (objective + steps + deliverable) |
| 4 downloadable resources | `aws_glue_course/downloads/*.csv / *.json / *.yaml / *.py` | runnable |
| 3 role plays | `aws_glue_course/11_role_plays/*.md` | persona + script + success criteria |

## Downloadable resources (the 4)

1. **`downloads/city_temperature.csv`** — sample data for the Glue Job lab (Section 6). City, country, date, avg_temperature, avg_temperature_uncertainty columns, ~500 rows.
2. **`downloads/glue_service_trust_policy.json`** — the trust policy you attach to the `GlueJobRole` IAM role so Glue can assume it. Pairs with Section 2 lecture on IAM roles.
3. **`downloads/glue_pipeline_stack.yaml`** — full CloudFormation template that provisions source S3 + target S3 + Glue Job + IAM role in one stack. Pairs with Section 6 lecture.
4. **`downloads/glue_job_aggregate_cities.py`** — the Python Glue script that aggregates `city_temperature.csv` by country and writes Parquet to the target bucket. Pairs with Section 6.

## Role plays (the 3)

1. **"Diagnose Glue Job Failure: Role/Trust Misconfig (Glue Can't Assume Role)"** — you (DE) + a junior DevOps engineer. Glue Job fails with `AccessDenied`. Walk through trust policy + identity policy together.
2. **"Glue Streaming Job is Falling Behind"** — you (DE) + a manager. Streaming job's batch latency p99 has degraded from 30s to 4 min. Diagnose, propose fix, get sign-off.
3. **"Pitch Glue Data Quality to a Skeptic Manager"** — you (DE) + a manager who's worried about rule-set maintenance. Pitch the DQ + CloudWatch + alerting stack.

All 3 scripts are in `11_role_plays/`.

## How to use this repo

- **Authoring:** edit lecture scripts in markdown, commit, push.
- **Recording:** each lecture script is self-contained — read it as narration, run the labs as you go.
- **Udemy upload:** zip the 4 files in `downloads/` for the 4 "downloadable resources" field.

## Source

- **Title:** AWS Glue - The Complete Masterclass
- **Instructor:** pvishnoi (Prem Vishnoi)
- **Contact:** prem.vishnoi@example.com
