#!/usr/bin/env bash
# 03_storage_class.sh -- lab stage 3: change the storage class of the curated
# sales file from STANDARD to STANDARD_IA (Infrequent Access) to save money.
#
# Lab equivalent (console): select the object -> Properties -> Storage class
# -> Edit -> STANDARD_IA. The CLI version below does the same.
#
# Trap: archiving to GLACIER is even cheaper but minimum 180-day storage
# commitment on small objects. Lab only moves to STANDARD_IA.
set -euo pipefail
: "${BUCKET:?Set BUCKET first -- see 00_set_bucket.sh}"
KEY="curated/sales/january-sales.csv"

echo "[lab-stage-3] current storage class for $KEY"
aws s3api head-object --bucket "$BUCKET" --key "$KEY" \
    --query 'StorageClass' --output text
# Expected: STANDARD (the default at upload time).

echo
echo "[lab-stage-3] copying to STANDARD_IA (in-place would be rejected; copy + delete)"
aws s3 cp "s3://$BUCKET/$KEY" "s3://$BUCKET/$KEY" \
    --storage-class STANDARD_IA

echo
echo "[lab-stage-3] new storage class"
aws s3api head-object --bucket "$BUCKET" --key "$KEY" \
    --query 'StorageClass' --output text
# Expected: STANDARD_IA
