#!/usr/bin/env bash
# 01_inspect_s3.sh -- lab stage 1: list the seed CSV in S3 + head 3 rows.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/00_set_lab.sh"

CSV_KEY="taxi/yellow_taxi_sample.csv"

echo "[lab-stage-1] listing s3://$BUCKET/taxi/:"
aws s3 ls "s3://$BUCKET/taxi/" --region "$AWS_REGION"

echo
echo "[lab-stage-1] head 3 rows of $CSV_KEY:"
aws s3 cp "s3://$BUCKET/$CSV_KEY" - --region "$AWS_REGION" | head -3