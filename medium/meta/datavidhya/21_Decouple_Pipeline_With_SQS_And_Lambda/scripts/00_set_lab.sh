#!/usr/bin/env bash
# 00_set_lab.sh -- paste the lab console's resource names into the env.
#
# The lab provisions these for you; you capture them once and reuse.
set -euo pipefail

: "${BUCKET:?Set BUCKET first -- e.g. export BUCKET=sqs-decouple-lab-bucket-a1b2c3}"
: "${DATABASE:?Set DATABASE first -- e.g. export DATABASE=sqs_decouple_db}"
: "${ROLE_ARN:?Set ROLE_ARN first -- the lab's Lambda execution role}"
: "${AWS_REGION:=us-east-1}"

export BUCKET DATABASE ROLE_ARN AWS_REGION

echo "[lab-stage-0] BUCKET=$BUCKET"
echo "[lab-stage-0] DATABASE=$DATABASE"
echo "[lab-stage-0] ROLE_ARN=$ROLE_ARN"
echo "[lab-stage-0] AWS_REGION=$AWS_REGION"
