q#!/usr/bin/env bash
# 02_create_zones.sh -- lab stage 2: create the curated/ and processed/ folders
# and copy the raw files into curated/. (processed/ gets populated by later ETL.)
#
# "Folders" in S3 are really just key prefixes. S3 has no real directory
# tree. Creating "curated/" is just PutObject with a key ending in "/", which
# makes the console render a folder icon.
set -euo pipefail
: "${BUCKET:?Set BUCKET first -- see 00_set_bucket.sh}"

echo "[lab-stage-2] creating zone prefixes"
# The lab does this by clicking "Create folder". CLI equivalent:
aws s3api put-object --bucket "$BUCKET" --key "curated/"
aws s3api put-object --bucket "$BUCKET" --key "processed/"

echo
echo "[lab-stage-2] copying raw into curated/ (raw customers + a curated sales snapshot)"
aws s3 cp "s3://$BUCKET/raw/customers/customers.json" \
          "s3://$BUCKET/curated/customers/customers.json"
aws s3 cp "s3://$BUCKET/raw/sales/january-sales.csv" \
          "s3://$BUCKET/curated/sales/january-sales.csv"

echo
echo "[lab-stage-2] bucket now contains:"
aws s3 ls "s3://$BUCKET/" --recursive --human-readable
