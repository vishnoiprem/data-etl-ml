#!/usr/bin/env bash
# 01_inspect_bucket.sh -- lab stage 1: confirm the seed data is in the bucket.
#
# The lab provisions two S3 prefixes, each with a different file format:
#
#   s3://$BUCKET/raw/orders/orders.csv        (CSV)
#   s3://$BUCKET/raw/customers/customers.json (JSON array)
#
# A Glue crawler will create one catalog table per prefix. We just confirm
# the lab's seed files are where they should be.
set -euo pipefail
: "${BUCKET:?Set BUCKET first -- see 00_set_lab.sh}"

echo "[lab-stage-1] listing objects in the lab bucket"
aws s3 ls "s3://${BUCKET}/" --recursive --human-readable

echo
echo "[lab-stage-1] spot-check each seed file exists"
aws s3api head-object --bucket "$BUCKET" --key "raw/orders/orders.csv"        >/dev/null
echo "    raw/orders/orders.csv        OK"
aws s3api head-object --bucket "$BUCKET" --key "raw/customers/customers.json" >/dev/null
echo "    raw/customers/customers.json OK"

echo
echo "[lab-stage-1] confirm the Glue database already exists"
aws glue get-database --name "$DATABASE" --query 'Database.Name' --output text
