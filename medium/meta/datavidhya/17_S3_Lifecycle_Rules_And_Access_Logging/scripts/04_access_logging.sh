#!/usr/bin/env bash
# 04_access_logging.sh -- lab stage 4: turn on S3 server access logging on the
# data bucket, pointing to the log bucket.
#
# Log bucket needs a bucket policy that grants the S3 log delivery service
# permission to PutObject into it. See sample_data/log-bucket-policy.json.
# The lab usually has this pre-applied; we re-apply here for completeness.
#
# Lab equivalent (console):
#   data bucket -> Properties -> Server access logging -> Enable
#       Target bucket: <log-bucket>
#       Target prefix: logs/
set -euo pipefail
: "${DATA_BUCKET:?Run 00_set_buckets.sh first}"
: "${LOG_BUCKET:?Run 00_set_buckets.sh first}"

HERE="$(cd "$(dirname "$0")" && pwd)"

echo "[lab-stage-4] applying log-bucket policy (so logging.s3.amazonaws.com can write)"
# Replace the placeholder with the real log bucket name.
tmp_policy="$(mktemp)"
sed "s|s3-lifecycle-logs-bucket-XXXX|$LOG_BUCKET|g" \
    "$HERE/../sample_data/log-bucket-policy.json" > "$tmp_policy"
aws s3api put-bucket-policy --bucket "$LOG_BUCKET" --policy "file://$tmp_policy"
rm -f "$tmp_policy"

echo
echo "[lab-stage-4] enabling server access logging on the data bucket"
aws s3api put-bucket-logging --bucket "$DATA_BUCKET" \
    --bucket-logging-status "{
        \"LoggingEnabled\": {
            \"TargetBucket\": \"$LOG_BUCKET\",
            \"TargetPrefix\": \"logs/\"
        }
    }"

echo
echo "[lab-stage-4] verify"
aws s3api get-bucket-logging --bucket "$DATA_BUCKET"
