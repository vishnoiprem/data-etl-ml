#!/usr/bin/env bash
# 02_create_database.sh -- lab stage 2: create the Athena database.
#
# Athena stores its catalogs in the Glue Data Catalog. Creating a database
# in Glue is what makes it queryable from Athena.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/00_set_lab.sh"

echo "[lab-stage-2] creating database: $DATABASE"
aws glue create-database \
    --database-input "{\"Name\":\"$DATABASE\"}" \
    --region "$AWS_REGION"

echo
echo "[lab-stage-2] verifying:"
aws glue get-database --name "$DATABASE" \
    --region "$AWS_REGION" \
    --query 'Database.[Name,LocationUri]' --output text