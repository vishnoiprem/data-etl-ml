#!/usr/bin/env bash
# 00_set_bucket.sh -- set the bucket name env-var used by all other scripts.
#
# The lab provisions a bucket whose name looks like
#   s3-intro-data-lake-bucket-x7k2q9
# Capture it once and export it. Other scripts read $BUCKET.
#
# Usage:
#   export BUCKET=s3-intro-data-lake-bucket-XXXX
#   ./scripts/00_set_bucket.sh                # print current value
#   ./scripts/00_set_bucket.sh my-bucket-name # set and print
set -euo pipefail
if [[ $# -ge 1 ]]; then
    export BUCKET="$1"
fi
if [[ -z "${BUCKET:-}" ]]; then
    echo "[ERROR] BUCKET is empty. Either export it or pass as the first arg." >&2
    echo "  Example: ./scripts/00_set_bucket.sh s3-intro-data-lake-bucket-x7k2q9" >&2
    exit 1
fi
echo "BUCKET=$BUCKET"
