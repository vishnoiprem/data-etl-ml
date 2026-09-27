#!/usr/bin/env bash
# 00_set_buckets.sh -- set both bucket names for the lab.
#
# The lab provisions two buckets:
#   DATA = s3-lifecycle-data-bucket-XXXX   (configure lifecycle + logging)
#   LOG  = s3-lifecycle-logs-bucket-XXXX  (server access log destination)
#
# Export both at the start of the session, then run the stage scripts.
set -euo pipefail
if [[ $# -ge 1 ]]; then export DATA_BUCKET="$1"; fi
if [[ $# -ge 2 ]]; then export LOG_BUCKET="$2"; fi
if [[ -z "${DATA_BUCKET:-}" || -z "${LOG_BUCKET:-}" ]]; then
    echo "[ERROR] both buckets must be set." >&2
    echo "  Example: ./scripts/00_set_buckets.sh \\" >&2
    echo "    s3-lifecycle-data-bucket-a1b2c3 s3-lifecycle-logs-bucket-x7k2q9" >&2
    exit 1
fi
echo "DATA_BUCKET=$DATA_BUCKET"
echo "LOG_BUCKET=$LOG_BUCKET"
