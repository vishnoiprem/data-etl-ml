#!/usr/bin/env bash
# 01_inspect_catalog.sh -- lab stage 1: inspect the pre-crawled customers_raw table.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/00_set_lab.sh"

TABLE="customers_raw"

echo "[lab-stage-1] columns in $DATABASE.$TABLE (pre-crawled state):"
aws glue get-table --database-name "$DATABASE" --name "$TABLE" \
    --region "$AWS_REGION" \
    --query 'Table.StorageDescriptor.Columns[].[Name,Type]' \
    --output table

echo
echo "[lab-stage-1] location of the underlying data:"
aws glue get-table --database-name "$DATABASE" --name "$TABLE" \
    --region "$AWS_REGION" \
    --query 'Table.StorageDescriptor.Location' \
    --output text