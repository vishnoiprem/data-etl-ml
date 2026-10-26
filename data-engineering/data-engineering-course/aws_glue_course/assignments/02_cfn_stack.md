# Assignment 02 — CloudFormation Stack Deployment

> **Section:** 5 (CFN templates) + 6 (Glue pipeline lab)
> **Due:** End of week 2
> **Deliverable:** Stack deployed + Glue Job run successfully + Parquet output in the target bucket.

## Objective

Use the `downloads/glue_pipeline_stack.yaml` CloudFormation template to deploy the full pipeline (source bucket, target bucket, IAM role, Glue Job) in one stack. The deliverable proves you can:
- Deploy a CloudFormation template via the AWS console or the CLI.
- Diagnose stack deployment failures.
- Run the Glue Job and verify the output.

## Steps

1. **Upload the Glue script** to the source bucket (the stack expects it there):
   ```
   aws s3 cp downloads/glue_job_aggregate_cities.py s3://<your-source-bucket>/scripts/
   ```
2. **Deploy the stack** via the CLI:
   ```
   aws cloudformation create-stack \
     --stack-name glue-course-pipeline \
     --template-body file://downloads/glue_pipeline_stack.yaml \
     --parameters ParameterKey=SourceBucketName,ParameterValue=<your-source-bucket> \
                  ParameterKey=TargetBucketName,ParameterValue=<your-target-bucket> \
     --capabilities CAPABILITY_NAMED_IAM
   ```
3. **Wait for CREATE_COMPLETE**:
   ```
   aws cloudformation wait stack-create-complete --stack-name glue-course-pipeline
   ```
4. **Run the Glue Job** from the console or CLI.
5. **Verify the Parquet output**:
   ```
   aws s3 ls s3://<your-target-bucket>/output/by_country_year_month/ --recursive | head -20
   ```

## Acceptance criteria

- Stack is in `CREATE_COMPLETE` state.
- Glue Job run is in `SUCCEEDED` state.
- Target bucket has Parquet files in `output/by_country_year_month/`.
- The Parquet files are partitioned by `year` and `month`.

## Stretch (optional, 30 min)

- Add a Glue Trigger that runs the Job on a schedule (every day at 2am UTC).
- Add an SNS topic that notifies you when the Job succeeds or fails.
- Use `aws cloudformation delete-stack` to clean up; verify the Glue Job is deleted but the S3 buckets are retained (CFN does not delete non-empty buckets by default).
