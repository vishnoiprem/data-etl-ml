#!/usr/bin/env bash
# 04_versioning.sh -- lab stage 4: enable bucket versioning so every PutObject
# keeps the previous copy as v(n-1).
#
# Versioning is a BUCKET-level setting. Once on, it cannot be disabled -- only
# suspended. Existing objects become v1 on next write.
#
# Lab equivalent (console): bucket -> Properties -> Bucket Versioning -> Edit
# -> Enable.
set -euo pipefail
: "${BUCKET:?Set BUCKET first -- see 00_set_bucket.sh}"

echo "[lab-stage-4] current versioning status"
aws s3api get-bucket-versioning --bucket "$BUCKET" \
    --query 'Status' --output text
# Likely empty (never set) before this script runs.

echo
echo "[lab-stage-4] enabling versioning"
aws s3api put-bucket-versioning --bucket "$BUCKET" \
    --versioning-configuration Status=Enabled

echo
echo "[lab-stage-4] post-enable status (Expected: Enabled)"
aws s3api get-bucket-versioning --bucket "$BUCKET" \
    --query 'Status' --output text
