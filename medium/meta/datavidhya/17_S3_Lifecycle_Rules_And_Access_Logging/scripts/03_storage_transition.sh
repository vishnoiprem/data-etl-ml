#!/usr/bin/env bash
# 03_storage_transition.sh -- lab stage 3: explain (and verify) the storage
# transitions you just configured.
#
# The rule will, for any object under raw/ in $DATA_BUCKET:
#   - At day 30  -> move to STANDARD_IA (~$0.0125/GB-month)
#   - At day 90  -> move to GLACIER_IR (~$0.004/GB-month)
#   - At day 365 -> delete
# S3 does NOT transition immediately. Tests that the rule is *attached* and
# *correct* need either Backblaze-style rules or a storage-class analysis
# tool -- not the lab.
#
# Lab equivalent (console): Management -> Lifecycle rules -> show rule ->
# confirm "Transition to Standard-IA after 30 days" appears.
set -euo pipefail
: "${DATA_BUCKET:?Run 00_set_buckets.sh first}"

echo "[lab-stage-3] current lifecycle rules"
aws s3api get-bucket-lifecycle-configuration --bucket "$DATA_BUCKET" \
    --query 'Rules[].{Id:ID, Status:Status, Prefix:Filter.Prefix,
                    Transitions:Transitions,
                    Expiration:Expiration}' \
    --output table

echo
echo "[lab-stage-3] summary"
cat <<'MSG'
  For raw/* objects:
    Day  0  :  STANDARD        ($0.023/GB-month)
    Day 30  :  STANDARD_IA     ($0.0125/GB-month)
    Day 90  :  GLACIER_IR      ($0.004 /GB-month, millisecond retrieval)
    Day 365 :  DELETED

  The "AgeOutRawAndCurated" rule above does exactly this.
MSG
