# AWS Glue — The Complete Masterclass

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
>
> **Source title:** *AWS Glue - The Complete Masterclass*
> **Subtitle:** Master building complete AWS Glue ETL Pipelines, Glue Data Quality, Glue Data Brew along with other AWS resources
> **Instructor:** pvishnoi (Prem Vishnoi)
> **Format:** 11 sections, 81 lectures, 4h 11m total
> **Includes:** 3 role plays, 4 downloadable resources, 6 assignments, 11 quizzes

This is the **author's source material** for the Udemy course. The repo
ships the full course as markdown so it can be version-controlled, diffed
in PRs, and rebuilt into slides / video / audio at any time.

## What you'll learn (the 8 outcomes)

1. Understanding of AWS Glue Data Catalog and creating AWS Glue Database, Glue Tables and Crawlers.
2. Using AWS Glue Studio, creating the ETL pipeline along with scheduled triggers, conditional triggers and glue workflow.
3. KMS, IAM Role, SNS, S3 and other associated AWS resources associated with Glue. Understanding and creation of all the resources.
4. Understanding of AWS Glue Data Quality and creating the associated Glue ETL pipeline.
5. Understanding AWS Glue Data Brew, creating the recipe, project and job to curate the dataset.
6. Understanding the AWS Glue streaming, creating the stream using the Python shell job and load the stream using the Spark streaming.
7. Different ways AWS Glue job can fail and debugging the failure and fix.
8. Creating the AWS resources for AWS Glue Pipeline using the AWS console and cloudformation.

## Course content (11 sections, 81 lectures, 4h 11m)

| # | Section | Lectures | Min | Folder |
|---|---|---|---|---|
| 1 | Introduction | L01–L03 | 12 | `01_introduction/` |
| 2 | Glue Resources Setup Part 1 — IAM, KMS, SNS | L04–L11 | 21 | `02_iam_kms_sns/` |
| 3 | Glue Resources Setup Part 2 — S3, AWS CLI, CloudFormation, CloudWatch | L12–L16 | 16 | `03_s3_cli_cloudformation/` |
| 4 | Creating Bucket And Uploading Data For the Course | L17–L20 | 6 | `04_s3_buckets_data/` |
| 5 | Glue Resources SetUp Part 3 — Glue Catalog, Crawler | L21–L35 | 58 | `05_glue_catalog_crawler/` |
| 6 | CloudFormation Templates | L36–L42 | 15 | `06_cloudformation_templates/` |
| 7 | First AWS Glue Pipeline Creation | L43–L48 | 25 | `07_first_glue_pipeline/` |
| 8 | AWS Glue Job Debugging | L49–L57 | 27 | `08_glue_job_debug/` |
| 9 | Glue Streaming Job | L58–L67 | 28 | `09_glue_streaming/` |
| 10 | Glue Data Quality | L68–L75 | 21 | `10_glue_data_quality/` |
| 11 | Glue Data Brew | L76–L81 | 22 | `11_glue_databrew/` |

The 3 role plays are L57 in Section 8, plus 2 referenced in `assignments/`.

## Asset map

| Asset | Path |
|---|---|
| Course README (this file) | `aws_glue_course/README.md` |
| Lecture-to-file map | `aws_glue_course/SYLLABUS.md` |
| 81 lecture scripts | `aws_glue_course/0X_*/lecture_scripts/L*.md` |
| 11 section quizzes | `aws_glue_course/quizzes/section_X.md` |
| 6 assignment prompts | `aws_glue_course/assignments/*.md` |
| 4 downloadable resources | `aws_glue_course/downloads/*.csv / *.json / *.yaml / *.py` |
| 3 role plays | `08_glue_job_debug/lecture_scripts/L57_*.md` + 2 in `assignments/` |

## Downloadable resources (the 4)

1. **`downloads/city_temperature.csv`** — 480 rows × 10 cols, 20 cities × 2 years. Sample data for the Glue Job lab in Section 7.
2. **`downloads/glue_service_trust_policy.json`** — the IAM trust policy you attach to the `GlueJobRole` so `glue.amazonaws.com` can assume it. Pairs with Section 2 lecture L11.
3. **`downloads/glue_pipeline_stack.yaml`** — full CloudFormation template: source S3, target S3, `GlueJobRole`, and a Spark (glueetl) Glue Job. Pairs with Section 7.
4. **`downloads/glue_job_aggregate_cities.py`** — the PySpark Glue script that aggregates `city_temperature.csv` by (country, year, month) and writes partitioned Parquet. Pairs with Section 7.

## Role plays (the 3)

1. **L57 — "Diagnose Glue Job Failure: Role/Trust Misconfig (Glue Can't Assume Role)"** in `08_glue_job_debug/lecture_scripts/L57_role_play_trust_misconfig.md`. You (DE) + a junior DevOps engineer. Glue Job fails with `AccessDeniedException`. Walk through trust policy + identity policy together.
2. **Assignment 04 — "Glue Streaming Job is Falling Behind"** in `assignments/04_streaming.md`. You (DE) + a manager. Diagnose the 4-minute p99 vs 30-second baseline. Mitigate vs remediate.
3. **Assignment 05 — "Pitch Glue Data Quality to a Skeptic Manager"** in `assignments/05_data_quality.md`. You (DE) + a manager. Scope the pitch to a pilot with measurable success.

## How to use this repo

- **Authoring:** edit lecture scripts in markdown, commit, push.
- **Recording:** each lecture script is self-contained — read it as narration, run the labs as you go.
- **Udemy upload:** zip the 4 files in `downloads/` for the 4 "downloadable resources" field.

## Source

- **Title:** AWS Glue - The Complete Masterclass
- **Instructor:** pvishnoi (Prem Vishnoi)
- **Contact:** prem.vishnoi@example.com
