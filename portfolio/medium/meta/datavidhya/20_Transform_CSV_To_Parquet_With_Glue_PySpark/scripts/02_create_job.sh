#!/usr/bin/env bash
# 02_create_job.sh -- lab stage 2: define the Glue job.
#
# Glue's CreateJob takes:
#   - a name
#   - the IAM role
#   - the Spark runtime + Glue version
#   - the script location (S3 path of the .py file)
#   - default arguments: --input_path, --output_path, --job-language=python
#
# The script itself is the same file the offline driver imports
# (``glue_jobs/sales_etl_job.py``); we upload it to s3://$BUCKET/scripts/
# so Glue can fetch it.
set -euo pipefail
: "${BUCKET:?Set BUCKET first -- see 00_set_lab.sh}"
: "${ROLE_ARN:?Set ROLE_ARN first -- see 00_set_lab.sh}"

JOB="sales-etl-q20"
SCRIPT_BUCKET_PATH="s3://${BUCKET}/scripts/sales_etl_job.py"
LOCAL_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/glue_jobs/sales_etl_job.py"

echo "[lab-stage-2] uploading the ETL script to S3"
aws s3 cp "$LOCAL_SCRIPT" "$SCRIPT_BUCKET_PATH"

echo "[lab-stage-2] deleting any pre-existing job (idempotent)"
aws glue delete-job --job-name "$JOB" 2>/dev/null || true

echo "[lab-stage-2] creating the Glue job"
aws glue create-job \
    --name "$JOB" \
    --role "$ROLE_ARN" \
    --command "Name=glueetl,ScriptLocation=${SCRIPT_BUCKET_PATH},PythonVersion=3" \
    --default-arguments "{
        \"--input_path\":  \"s3://${BUCKET}/raw/sales_transactions.csv\",
        \"--output_path\": \"s3://${BUCKET}/curated/sales/\",
        \"--job-language\": \"python\",
        \"--job-bookmark-option\": \"job-bookmark-enable\"
    }" \
    --glue-version "4.0" \
    --worker-type "Standard" \
    --number-of-workers 2

echo
echo "[lab-stage-2] job definition:"
aws glue get-job --job-name "$JOB" \
    --query 'Job.[Name,Role,GlueVersion,WorkerType,NumberOfWorkers]' \
    --output text
