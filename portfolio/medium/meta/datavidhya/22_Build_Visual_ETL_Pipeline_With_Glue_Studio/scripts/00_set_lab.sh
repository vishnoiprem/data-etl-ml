#!/usr/bin/env bash
# 00_set_lab.sh -- paste the lab console's resource names into the env.
#
# The lab provisions these for you; you capture them once and reuse.
set -euo pipefail

: "${BUCKET:?Set BUCKET first -- e.g. export BUCKET=glue-studio-visual-etl-bucket-a1b2c3}"
: "${DATABASE:?Set DATABASE first -- e.g. export DATABASE=studio_db_a1b2c3}"
: "${ROLE_ARN:?Set ROLE_ARN first -- the lab's GlueStudioLabRole}"
: "${WORKGROUP:=studio-visual-etl-wg}"
: "${AWS_REGION:=us-east-1}"

export BUCKET DATABASE ROLE_ARN WORKGROUP AWS_REGION

echo "[lab-stage-0] BUCKET=$BUCKET"
echo "[lab-stage-0] DATABASE=$DATABASE"
echo "[lab-stage-0] ROLE_ARN=$ROLE_ARN"
echo "[lab-stage-0] WORKGROUP=$WORKGROUP"
echo "[lab-stage-0] AWS_REGION=$AWS_REGION"
