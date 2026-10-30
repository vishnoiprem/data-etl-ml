#!/usr/bin/env bash
# 05_overwrite_recover.sh -- lab stage 5: overwrite the customers file with
# bad data, then recover the original from the previous version.
#
# Lab equivalent (console): upload a corrupt file, see two versions appear,
# download the older version. CLI does the same with three commands.
set -euo pipefail
: "${BUCKET:?Set BUCKET first -- see 00_set_bucket.sh}"
KEY="curated/customers/customers.json"

# Capture the original VersionId (would be the lab's "Note: this version"
# after a previous overwrite).
ORIGINAL_VERSION=$(aws s3api list-object-versions --bucket "$BUCKET" \
    --prefix "$KEY" --query 'Versions[-1].VersionId' --output text)

echo "[lab-stage-5] original VersionId = $ORIGINAL_VERSION"

echo
echo "[lab-stage-5] overwriting with deliberately bad data"
echo '[{"customer_id": 0, "name": "CORRUPT", "email": "BAD", "country": "??", "tier": "???"}]' \
    | aws s3 cp - "s3://$BUCKET/$KEY"

echo
echo "[lab-stage-5] all versions of $KEY"
aws s3api list-object-versions --bucket "$BUCKET" --prefix "$KEY" \
    --query 'Versions[].{Id: VersionId, IsLatest: IsLatest, LastModified: LastModified}'

echo
echo "[lab-stage-5] recovering the previous version"
aws s3api get-object --bucket "$BUCKET" --key "$KEY" --version-id "$ORIGINAL_VERSION" \
    recovered.json
echo "[lab-stage-5] recovered file written to ./recovered.json"
ls -l recovered.json
head -n 3 recovered.json
