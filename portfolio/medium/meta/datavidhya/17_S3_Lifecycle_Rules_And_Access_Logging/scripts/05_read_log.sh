#!/usr/bin/env bash
# 05_read_log.sh -- lab stage 5: download the example access log from the log
# bucket, format it as a table, and call out every field.
#
# Lab equivalent (console): click into the log bucket, open the seeded log
# file. This is what reading a real access log looks like.
set -euo pipefail
: "${LOG_BUCKET:?Run 00_set_buckets.sh first}"

echo "[lab-stage-5] list logs in $LOG_BUCKET"
aws s3 ls "s3://$LOG_BUCKET/" --recursive --human-readable

echo
echo "[lab-stage-5] open the example log"
LOG_KEY="$(aws s3 ls "s3://$LOG_BUCKET/" --recursive | awk '{print $4}' | head -n 1)"
if [[ -z "${LOG_KEY:-}" ]]; then
    echo "[ERROR] no log file found in the bucket." >&2
    exit 1
fi
echo "  log key: $LOG_KEY"
echo
aws s3 cp "s3://$LOG_BUCKET/$LOG_KEY" /tmp/access-log.txt

echo
echo "[lab-stage-5] first 3 access log records (one per request)"
head -n 3 /tmp/access-log.txt

echo
echo "[lab-stage-5] field-by-field reference (S3 server access log format)"
cat <<'MSG'
  Bucket Owner  Request Time           Remote IP    Requester               Operation     Key                                                Status  Bytes  TotalTime
  See:
    https://docs.aws.amazon.com/AmazonS3/latest/userguide/LogFormat.html
MSG
