#!/usr/bin/env bash
# 00_set_lab.sh -- lab stage 0: capture the provisioned resource names.
set -euo pipefail

echo "[lab-stage-0] exporting lab resource names (paste from the console)"
echo
echo "    BUCKET:    glue-etl-lab-bucket-XXXXX"
echo "    DATABASE:  sales_db_XXXXX"
echo "    ROLE_ARN:  arn:aws:iam::123456789012:role/GlueEtlLabRole-XXXXX"
echo "    WORKGROUP: <Athena workgroup from the lab panel>"
echo

: "${BUCKET:?Set BUCKET (the S3 bucket starting with glue-etl-lab-bucket-)}"
: "${DATABASE:?Set DATABASE (the Glue DB starting with sales_db_)}"
: "${ROLE_ARN:?Set ROLE_ARN (the GlueEtlLabRole ARN)}"
: "${AWS_REGION:=us-east-1}"

export BUCKET DATABASE ROLE_ARN AWS_REGION
echo "[lab-stage-0] BUCKET=$BUCKET"
echo "[lab-stage-0] DATABASE=$DATABASE"
echo "[lab-stage-0] ROLE_ARN=$ROLE_ARN"
