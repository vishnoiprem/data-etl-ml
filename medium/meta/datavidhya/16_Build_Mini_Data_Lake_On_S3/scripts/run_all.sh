#!/usr/bin/env bash
# run_all.sh -- execute the six lab stages in order. Useful when reproducing
# the lab in the AWS console user-interface but scripted via CLI.
#
# Set BUCKET first:
#   export BUCKET=s3-intro-data-lake-bucket-XXXX
#   ./scripts/run_all.sh
#
# This script is OPTIONAL. Most learners will run each stage interactively.
# For offline correctness, run `pytest tests/` instead -- it uses moto to
# simulate S3 in-process and needs no AWS account.
set -euo pipefail
: "${BUCKET:?Set BUCKET first -- see 00_set_bucket.sh}"
HERE="$(cd "$(dirname "$0")" && pwd)"

# Lab stages 1-5 are read-only or in-place edits. Stage 0 just prints the
# bucket; stage 6 tears the lab down. Skip stage 6 here -- the user invokes
# it manually when they're done.
"$HERE/00_set_bucket.sh"
"$HERE/01_inspect_objects.sh"
"$HERE/02_create_zones.sh"
"$HERE/03_storage_class.sh"
"$HERE/04_versioning.sh"
"$HERE/05_overwrite_recover.sh"

echo
echo "[ok] stages 0-5 complete; run 06_teardown.sh when you're done with the lab."
