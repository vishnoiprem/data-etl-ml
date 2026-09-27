#!/usr/bin/env bash
# 01_inspect_raw.sh -- lab stage 1: inspect the raw CSV in S3 + the catalog table.
#
# The lab provisions ``s3://$BUCKET/raw/sales_transactions.csv`` plus a Glue
# catalog table ``sales_db_xxxxx.raw_sales_transactions``. The catalog table
# is what Glue crawlers produce -- but in this lab it's pre-provisioned with
# every column typed as ``string`` because the raw CSV had no header schema.
set -euo pipefail
: "${BUCKET:?Set BUCKET first -- see 00_set_lab.sh}"
: "${DATABASE:?Set DATABASE first -- see 00_set_lab.sh}"

echo "[lab-stage-1] raw CSV in S3"
aws s3 ls "s3://${BUCKET}/raw/" --human-readable

echo
echo "[lab-stage-1] head of the file (first 5 lines)"
aws s3 cp "s3://${BUCKET}/raw/sales_transactions.csv" - | head -5

echo
echo "[lab-stage-1] Glue catalog table -- schema is ALL string"
aws glue get-table --database-name "$DATABASE" --name "raw_sales_transactions" \
    --query 'Table.StorageDescriptor.Columns[].[Name,Type]' \
    --output text

echo
echo "[lab-stage-1] catalog table location"
aws glue get-table --database-name "$DATABASE" --name "raw_sales_transactions" \
    --query 'Table.StorageDescriptor.Location' --output text
