#!/usr/bin/env bash
# 00_set_lab.sh -- lab stage 0: capture the provisioned resource names.
#
# AWS Skill Builder generates a random suffix per session, so the actual
# bucket / DB / role / workgroup names land in env vars instead of being
# hard-coded.
set -euo pipefail

echo "[lab-stage-0] exporting lab resource names (paste from the console)"
echo
echo "    BUCKET:    glue-crawler-catalog-bucket-XXXXX"
echo "    DATABASE:  catalog_db_XXXXX"
echo "    ROLE_ARN:  arn:aws:iam::123456789012:role/GlueCrawlerLabRole-XXXXX"
echo "    WORKGROUP: crawler-catalog-XXXXX"
echo

: "${BUCKET:?Set BUCKET (the S3 bucket starting with glue-crawler-catalog-bucket-)}"
: "${DATABASE:?Set DATABASE (the Glue DB starting with catalog_db_)}"
: "${ROLE_ARN:?Set ROLE_ARN (the GlueCrawlerLabRole ARN)}"
: "${WORKGROUP:?Set WORKGROUP (the Athena workgroup starting with crawler-catalog-)}"
: "${AWS_REGION:=us-east-1}"

export BUCKET DATABASE ROLE_ARN WORKGROUP AWS_REGION
echo "[lab-stage-0] BUCKET=$BUCKET"
echo "[lab-stage-0] DATABASE=$DATABASE"
echo "[lab-stage-0] ROLE_ARN=$ROLE_ARN"
echo "[lab-stage-0] WORKGROUP=$WORKGROUP"
