#!/usr/bin/env bash
# 07_teardown.sh -- lab stage 7: drop the catalog tables.
#
# Glue tables are metadata-only; DROP TABLE removes the catalog entry and
# the S3 data survives. The lab session teardown handles bucket deletion.
set -euo pipefail
: "${DATABASE:?Set DATABASE first -- see 00_set_lab.sh}"

echo "[lab-stage-7] dropping catalog tables (S3 data is preserved)"
aws glue delete-table --database-name "$DATABASE" --name "orders"
aws glue delete-table --database-name "$DATABASE" --name "customers"

echo
echo "[lab-stage-7] catalog tables now:"
aws glue get-tables --database-name "$DATABASE" \
    --query 'TableList[].Name' --output text
echo "    (empty list above means both tables dropped)"

echo
echo "[lab-stage-7] S3 objects still present:"
aws s3 ls "s3://${BUCKET}/raw/" --recursive
