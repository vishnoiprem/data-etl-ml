#!/usr/bin/env bash
# 01_inspect_objects.sh -- lab stage 1: list raw/ contents and peek at each file.
#
# Lab equivalent (console): click into the bucket, click into raw/, click
# into sales/ and customers/, open each file. This script does the same
# via the AWS CLI.
set -euo pipefail
: "${BUCKET:?Set BUCKET first -- see 00_set_bucket.sh}"

echo "[lab-stage-1] listing raw zone of $BUCKET"
aws s3 ls "s3://$BUCKET/raw/" --recursive --human-readable

echo
echo "[lab-stage-1] first 5 lines of raw/sales/january-sales.csv"
aws s3 cp "s3://$BUCKET/raw/sales/january-sales.csv" - | head -n 5

echo
echo "[lab-stage-1] customers.json (pretty-printed, head only)"
aws s3 cp "s3://$BUCKET/raw/customers/customers.json" - | python3 -m json.tool | head -n 12
