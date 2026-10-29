#!/usr/bin/env bash
# 06_teardown.sh -- delete every object (including all versions) and the
# bucket itself. Lab uses this at the end of the session; running it twice
# is safe (the second run is a no-op).
#
# Lab equivalent (console): Empty (with "include all versions" checkbox) ->
# Delete bucket.
set -euo pipefail
: "${BUCKET:?Set BUCKET first -- see 00_set_bucket.sh}"

echo "[lab-stage-6] deleting every object version (including delete-markers)"
aws s3api delete-objects --bucket "$BUCKET" --delete "$(aws s3api list-object-versions \
    --bucket "$BUCKET" --output json --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}')"
aws s3api delete-objects --bucket "$BUCKET" --delete "$(aws s3api list-object-versions \
    --bucket "$BUCKET" --output json --query '{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}')"

echo "[lab-stage-6] deleting the bucket"
aws s3api delete-bucket --bucket "$BUCKET"

echo "[lab-stage-6] done -- bucket $BUCKET no longer exists"
