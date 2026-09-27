#!/usr/bin/env bash
# 06_teardown.sh -- lab stage 6: drop the database + clean Athena results.
#
# The lab pre-creates the S3 bucket; the bucket is deleted when the lab
# session ends. We only drop the Glue database and Athena query-results.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/00_set_lab.sh"

echo "[lab-stage-6] dropping database $DATABASE (drops all tables in it)"
aws glue delete-database --name "$DATABASE" --region "$AWS_REGION"

echo
echo "[lab-stage-6] cleaning Athena query results:"
aws s3 ls "s3://$BUCKET/query-results/" --recursive \
    --region "$AWS_REGION" 2>/dev/null \
  | awk '{print $4}' \
  | while read -r key; do
        [ -z "$key" ] && continue
        aws s3 rm "s3://$BUCKET/$key" --region "$AWS_REGION" >/dev/null
    done
echo "[lab-stage-6] done."