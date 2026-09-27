#!/usr/bin/env bash
# 00_set_lakehouse.sh -- lab stage 0: capture the provisioned resource names.
# AWS Skill Builder generates a random suffix per session, so the actual
# names land in env vars instead of being hard-coded.
#
# Run this ONCE at the start of the lab session, after the lab environment
# finishes provisioning. It reads the names out of the AWS console's
# "Lab resources" panel and exports them.
set -euo pipefail

echo "[lab-stage-0] exporting lab resource names (paste from the console)"
echo
echo "    BUCKET: athena-iceberg-lakehouse-bucket-XXXXX"
echo "    DATABASE: lakehouse_db_XXXXX"
echo "    WORKGROUP: iceberg-lakehouse-XXXXX"
echo

: "${BUCKET:?Set BUCKET (the S3 bucket starting with athena-iceberg-lakehouse-bucket-)}"
: "${DATABASE:?Set DATABASE (the Glue DB starting with lakehouse_db_)}"
: "${WORKGROUP:?Set WORKGROUP (the Athena workgroup starting with iceberg-lakehouse-)}"
: "${AWS_REGION:=us-east-1}"

export BUCKET DATABASE WORKGROUP AWS_REGION
echo "[lab-stage-0] BUCKET=$BUCKET  DATABASE=$DATABASE  WORKGROUP=$WORKGROUP"
