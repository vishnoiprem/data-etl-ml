#!/usr/bin/env bash
# 06_teardown.sh -- lab stage 6: drop catalog table + delete the Glue job.
#
# Curated Parquet in S3 is NOT deleted (it's "external"). The lab session
# teardown handles the bucket + role when the session ends.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/00_set_lab.sh"

JOB_NAME="customer-visual-etl-q22"
TABLE="curated_customers"

echo "[lab-stage-6] dropping the $TABLE catalog table"
aws glue delete-table --database-name "$DATABASE" \
    --name "$TABLE" --region "$AWS_REGION"

echo
echo "[lab-stage-6] deleting the Glue job: $JOB_NAME"
aws glue delete-job --job-name "$JOB_NAME" --region "$AWS_REGION"

echo
echo "[lab-stage-6] remaining objects in the curated S3 prefix (data is preserved):"
aws s3 ls "s3://${BUCKET}/curated/customers/" --recursive --human-readable