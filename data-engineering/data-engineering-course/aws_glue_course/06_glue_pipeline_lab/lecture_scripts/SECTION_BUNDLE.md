# Section 6 — Glue Pipeline Lab (Lectures L46-L51)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
>
> This file bundles 6 lecture scripts (L46-L51) for Section 6.

---

## L46 — Section Overview (1:21)

> "Section 6 is the pipeline lab. We deploy the full CloudFormation template, run the Glue Job, and verify the Parquet output. By the end of this section, you will have a working pipeline end-to-end."

---

## L47 — Getting Ready For Glue Pipeline Creation (2:41)

> "Pre-flight check: 3 things to verify before deploying the stack. One: the source and target S3 buckets exist. Two: the Glue Job script is uploaded to `s3://<source-bucket>/scripts/`. Three: the IAM role `GlueJobRole` is created (Section 1 lab). The CFN template will create or update these as needed, but having them pre-existing means fewer surprises on the first deploy."

Pre-deploy checklist:
1. Source bucket exists, CSV uploaded.
2. Script uploaded to `s3://<source>/scripts/`.
3. `GlueJobRole` exists with the right trust + identity policies.
4. CFN template uploaded to `s3://<source>/templates/`.

---

## L48 — Deploying Glue Pipeline Stack Using CloudFormation (5:46)

> "Deploy the stack. From the console: CloudFormation → Create stack → With new resources (standard) → Template is ready → Upload a template file → Choose `glue_pipeline_stack.yaml` → Next. Give the stack a name (`glue-course-pipeline`). Set the parameter values (source bucket, target bucket, script key, Job name). Next. Configure stack options (tags optional). Next. Review. Acknowledge the IAM capabilities checkbox (`CAPABILITY_NAMED_IAM` because we're creating `GlueJobRole` as a named resource). Create stack. The stack takes 1-2 minutes to create. Watch the Events tab — every resource creation is logged. If any resource fails, the Events tab shows the reason."

Lab: deploy the stack; wait for CREATE_COMPLETE.

---

## L49 — CloudFormation Template Deployment Debugging (6:41)

> "Common stack deployment failures. 1) `EntityAlreadyExists: Role with name GlueJobRole already exists` — the role was left over from a previous deployment; delete the role manually or rename. 2) `AccessDenied: User ... is not authorized to perform: iam:CreateRole` — your IAM user is missing the `iam:CreateRole` permission; attach `AdministratorAccess` for this lab. 3) `Bucket name already exists` — S3 bucket names are globally unique; pick a different name. 4) `Resource limit exceeded` — you've hit the Glue concurrent job run limit; wait for previous runs to complete. The fix for every one of these: read the Events tab carefully; the error message tells you the resource and the cause."

Lab: intentionally break the stack (e.g., rename the role) and watch it fail; read the error; fix it.

---

## L50 — Analyzing Glue Job Script And Running The Job (5:17)

> "Now run the Glue Job. From the Glue console, click 'Jobs', click `GlueJob2-Country-Aggregate`, click 'Run job'. The Job takes 2-3 minutes to start (provisioning DPU workers) and 1-2 minutes to run. Total: 3-5 minutes. The script is `downloads/glue_job_aggregate_cities.py` — walk through it line by line. The script: 1) creates a SparkSession, 2) reads the CSV from `s3://<source-bucket>/input/city_temperature.csv` with the explicit schema, 3) filters out nulls in `avg_temperature`, 4) aggregates by `(country, year, month)` computing mean/min/max + n_cities, 5) writes Parquet partitioned by `year` and `month` to `s3://<target-bucket>/output/by_country_year_month/`. 6) calls `job.commit()`."

Lab: run the Job; wait for SUCCEEDED.

---

## L51 — Going Through the Log And Verifying Job Output (4:06)

> "Once the Job succeeds, verify the output. 1) S3: `aws s3 ls s3://<target-bucket>/output/by_country_year_month/ --recursive`. You should see `year=YYYY/month=MM/part-*.parquet` files. 2) Glue Data Catalog: open the `by_country_year_month` table. The schema has 5 columns: country, mean_avg_temperature, min_avg_temperature, max_avg_temperature, n_cities, plus the partition columns year + month. 3) Athena: run `SELECT * FROM by_country_year_month LIMIT 10;` in the Athena console. You should see 10 rows of country, year, month, mean temperature, etc. 4) CloudWatch Logs: the Job's stdout is in `/aws-glue/jobs/logs-v2/`. The log shows the Spark plan, the executor timeline, and any errors."

Lab: verify S3 output, verify Catalog table, query Athena.

---

## Section 6 Quiz

5 questions, see `quizzes/section_6.md`.
