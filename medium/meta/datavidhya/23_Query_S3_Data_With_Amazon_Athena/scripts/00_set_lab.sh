#!/usr/bin/env bash
# 00_set_lab.sh -- paste the lab console's resource names into the env.
set -euo pipefail

: "${BUCKET:?Set BUCKET first -- e.g. export BUCKET=athena-taxi-playground-bucket-a1b2c3}"
: "${WORKGROUP:?Set WORKGROUP (Athena workgroup from the lab panel)}"
: "${DATABASE:=taxi_db}"
: "${AWS_REGION:=us-east-1}"

export BUCKET WORKGROUP DATABASE AWS_REGION

echo "[lab-stage-0] BUCKET=$BUCKET"
echo "[lab-stage-0] WORKGROUP=$WORKGROUP"
echo "[lab-stage-0] DATABASE=$DATABASE"
echo "[lab-stage-0] AWS_REGION=$AWS_REGION"
