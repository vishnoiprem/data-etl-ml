#!/usr/bin/env bash
# 06_teardown.sh -- lab stage 6: drop the curated table + job.
#
# Curated Parquet in S3 is NOT deleted (it's "external"). The lab session
# teardown handles bucket deletion when the session ends.
set -euo pipefail
: "${DATABASE:?Set DATABASE first -- see 00_set_lab.sh}"

echo "[lab-stage-6] dropping the curated_sales catalog table"
aws glue delete-table --database-name "$DATABASE" --name "curated_sales"

echo
echo "[lab-stage-6] deleting the Glue job"
aws glue delete-job --job-name "sales-etl-q20"

echo
echo "[lab-stage-6] remaining objects in the curated S3 prefix (data is preserved):"
aws s3 ls "s3://${BUCKET}/curated/sales/" --recursive --human-readable
