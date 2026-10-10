# Section 5 — CloudFormation Templates (Lectures L39-L45)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
>
> This file bundles 7 lecture scripts (L39-L45) for Section 5.

---

## L39 — Section Overview (1:20)

> "Section 5 is the CloudFormation section. We take the 6 resources we've built by hand (2 S3 buckets, an IAM role, a Glue Job, 2 Crawlers) and re-create them as a CloudFormation template. The benefits: version control, reproducibility, peer review, rollback. By the end of this section, you'll have 3 templates — the 1st pipeline, the 2nd pipeline, and a 3rd pipeline — and you'll know how to deploy them via the AWS CLI."

---

## L40 — CloudFormation Templates 101 (0:59)

> "A CloudFormation template is a YAML or JSON file with 4 sections: Parameters (user inputs), Mappings (static lookup), Resources (the AWS resources to create), Outputs (values to export). The Resources section is the only required one. Each Resource has a Type (e.g., `AWS::S3::Bucket`, `AWS::IAM::Role`, `AWS::Glue::Job`) and a Properties block. The 4 key intrinsic functions: `!Ref`, `!Sub`, `!GetAtt`, `!Join`. We use these throughout the templates."

---

## L41 — First Glue Pipeline: CFN Templates (3:34)

> "Walkthrough of the first pipeline template. The template provisions: 1 S3 source bucket, 1 S3 target bucket, 1 IAM role (`GlueJobRole`), 1 Glue Job. The Resources section has 4 entries. The Parameters section lets the user override the bucket names. The Outputs section exports the bucket names and the Job name so other stacks can reference them. The template is in `downloads/glue_pipeline_stack.yaml`."

Lecture walks the viewer through the template line by line.

---

## L42 — Second Glue Pipeline: CFN Templates (3:16)

> "The second pipeline adds 2 Crawlers to the first pipeline. Same buckets + role + Job, plus a `crawler-source-csv` and a `crawler-target-parquet`. The Crawlers are type `AWS::Glue::Crawler`. The Crawler properties include the IAM role, the database, the data store path, and the schedule. The template is `downloads/glue_pipeline_stack_v2.yaml` (a separate file; not generated yet — see Assignment 02)."

---

## L43 — Glue Job 345: CFN Template (2:05)

> "The 3rd pipeline is a more advanced Glue Job that aggregates by `country`, `year`, and `month`, then writes Parquet partitioned by year + month. The CFN template is the same as the first pipeline, but the Glue Job's script is different (a more complex PySpark script). The template demonstrates how to parameterize the script location, the source bucket, the target bucket, and the Glue Job's worker count."

---

## L44 — Recap CFN Template Update (1:05)

> "Recap on the 3 templates. The pattern is: 1 template per pipeline. Each template is parameterized (bucket names, role name, Job name). Each template is *idempotent* — re-running with the same parameters is a no-op. To update a resource, edit the template and run `aws cloudformation update-stack`. To delete, `aws cloudformation delete-stack` (S3 buckets are not deleted by default if they have content; use `--retain` or empty the bucket first)."

---

## L45 — Upload CFN Templates to S3 (2:13)

> "Before deploying, upload the templates and the Glue script to S3. The stack expects the script at `s3://<source-bucket>/scripts/glue_job_aggregate_cities.py`. Upload both: `aws s3 cp glue_pipeline_stack.yaml s3://<source-bucket>/templates/` and `aws s3 cp glue_job_aggregate_cities.py s3://<source-bucket>/scripts/`. Now the stack can reference the script by its S3 URL."

Lab: upload the 2 files; verify with `aws s3 ls s3://<source>/templates/` and `aws s3 ls s3://<source>/scripts/`.

---

## Section 5 Quiz

5 questions, see `quizzes/section_5.md`.
