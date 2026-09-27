#!/usr/bin/env bash
# 01_inspect_buckets.sh -- lab stage 1: list the two pre-created buckets and
# their contents, and confirm the log bucket has its example access log.
set -euo pipefail
: "${DATA_BUCKET:?Run 00_set_buckets.sh first}"
: "${LOG_BUCKET:?Run 00_set_buckets.sh first}"

echo "[lab-stage-1] data bucket contents (typically empty before stage 2)"
aws s3 ls "s3://$DATA_BUCKET/" --recursive --human-readable || true

echo
echo "[lab-stage-1] log bucket contents (lab seeds example-access-log.txt)"
aws s3 ls "s3://$LOG_BUCKET/" --recursive --human-readable

echo
echo "[lab-stage-1] current lifecycle configuration on data bucket (likely absent)"
aws s3api get-bucket-lifecycle-configuration --bucket "$DATA_BUCKET" 2>&1 | head -n 5 || true

echo
echo "[lab-stage-1] current logging configuration on data bucket (likely disabled)"
aws s3api get-bucket-logging --bucket "$DATA_BUCKET" 2>&1 | head -n 5 || true
