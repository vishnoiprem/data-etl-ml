# Section 6 Quiz — First Glue Pipeline Lab

> 5 questions, multi-choice, single answer. The answer key is at the bottom.

---

**Q1.** You launch `downloads/glue_pipeline_stack.yaml` for the first time and the stack goes to `CREATE_FAILED` with `EntityAlreadyExists: Role with name GlueJobRole already exists`. What is the most likely cause?

- A. The `AWS::Region` parameter is wrong, so CFN tried to create it in the wrong partition.
- B. A previous deployment of the same stack was deleted, but CloudFormation does **not** delete IAM roles by default, so the leftover `GlueJobRole` collides with the new one.
- C. The `GlueJobRole` resource declaration is malformed YAML and was interpreted twice.
- D. The S3 bucket names in `Parameters` were already taken globally.

---

**Q2.** After the Job has run successfully, where can you find the Job's logs?

- A. Only in CloudWatch Logs under `/aws-glue/jobs/logs-v2/`.
- B. Only in S3 under the Job's `--spark-logs` prefix (e.g. `spark-logs/`).
- C. Only on the EC2 instance that ran the Job (you must SSH in).
- D. All of the above — CloudWatch Logs at `/aws-glue/jobs/logs-v2/`, S3 Spark UI logs in `spark-logs/`, and the Glue console's **Run history** tab.

---

**Q3.** The Job's IAM policy grants `s3:GetObject` only on `arn:aws:s3:::${source}/scripts/*`. What does this imply about running the Job?

- A. The script is read directly from a URL passed via `--extra-py-files`, so the bucket key doesn't matter.
- B. You must upload `glue_job_aggregate_cities.py` to `s3://${source}/scripts/glue_job_aggregate_cities.py` (the `GlueScriptS3Key` parameter, default `scripts/glue_job_aggregate_cities.py`) **before** the Job can start, or `s3:GetObject` will be denied.
- C. The script is bundled into the Glue container image at build time and never read from S3.
- D. The script is read from a public Glue samples bucket automatically.

---

**Q4.** The script writes the result as partitioned Parquet. What is the output path and partition scheme?

- A. `s3://${target}/flat/all_cities.parquet` — single file, no partitions.
- B. `s3://${target}/output/by_country_year_month/year=YYYY/month=MM/` — partitioned by `year` and `month`, with `country` encoded in the path components.
- C. `s3://${source}/output/by_country_year_month/` — written back to the source bucket.
- D. `s3://${target}/output/` — partitioned only by ingestion date.

---

**Q5.** The Job shows `SUCCEEDED` in the Glue console, but `s3://${target}/output/` is empty. Which is the most likely root cause?

- A. The Job's bookmark is paused, so it skipped every partition because it thought it had already run.
- B. The `--target_bucket` `DefaultArgument` in `GlueJob` properties is wrong (or missing), so the script wrote to a non-existent / unwritable location.
- C. The `GlueJobRole` is missing `s3:PutObject` on the target bucket, so writes silently failed.
- D. All of the above are plausible; the first things to check are the `--target_bucket` argument and the IAM `s3:PutObject` permission on `${target}/*`.

---

# Answer Key

1. **B** — CloudFormation does not delete IAM roles by default when a stack is deleted; a previous deploy of the same template leaves `GlueJobRole` behind, and the next deploy hits `EntityAlreadyExists` on the `AWS::IAM::Role` named `GlueJobRole`. Delete the leftover role (or enable `Retain` policies) and re-deploy.
2. **D** — All three. Driver/stdout/stderr land in CloudWatch Logs under `/aws-glue/jobs/logs-v2/`, the Spark event logs land in the `--spark-logs` S3 prefix (e.g. `s3://${target}/spark-logs/`) for the Spark UI, and a summary view is on the Glue console's **Job run history** tab.
3. **B** — The script must be uploaded to `s3://${source}/scripts/glue_job_aggregate_cities.py` (the `GlueScriptS3Key` parameter, default `scripts/glue_job_aggregate_cities.py`) before the Job runs. The IAM policy in the stack only grants `s3:GetObject` on `${source}/scripts/*`, so uploading to a different key (or skipping the upload) will cause `AccessDenied` when Glue fetches the script.
4. **B** — The script writes partitioned Parquet to `s3://${target}/output/by_country_year_month/`, partitioned by `year` and `month` (with `country` encoded in the path components). See `glue_job_aggregate_cities.py` for the `partitionBy` call.
5. **D** — All three are plausible. The script writes to `s3://${target}/output/...`, so a wrong `DefaultArguments.--target_bucket` (a CFN parameter on the `GlueJob` resource) or missing `s3:PutObject` on `${target}/*` in the `GlueJobRole` inline policy will both produce an empty `output/`. A stale bookmark can also skip work. Start by checking `--target_bucket` and the IAM `s3:PutObject` grant on the target bucket.
