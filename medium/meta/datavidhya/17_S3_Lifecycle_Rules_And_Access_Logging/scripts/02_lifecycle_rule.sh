#!/usr/bin/env bash
# 02_lifecycle_rule.sh -- lab stage 2: attach a lifecycle rule to the data
# bucket. The rule moves aging raw/ objects to STANDARD_IA at 30 days,
# GLACIER_IR at 90 days, and deletes them at 365.
#
# Lab equivalent (console): bucket -> Management -> Lifecycle rules ->
# Create rule -> prefix raw/ -> transitions + expiration.
set -euo pipefail
: "${DATA_BUCKET:?Run 00_set_buckets.sh first}"

HERE="$(cd "$(dirname "$0")" && pwd)"

echo "[lab-stage-2] attaching lifecycle rule to $DATA_BUCKET"
aws s3api put-bucket-lifecycle-configuration \
    --bucket "$DATA_BUCKET" \
    --lifecycle-configuration "file://$HERE/../sample_data/lifecycle-rule.json"

echo
echo "[lab-stage-2] verify"
aws s3api get-bucket-lifecycle-configuration --bucket "$DATA_BUCKET"
