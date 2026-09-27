#!/usr/bin/env bash
# 04_review_schemas.sh -- lab stage 4: walk each table's inferred schema.
#
# The lab's "trap" is on display here: orders.order_date is inferred as
# string (because one row has "N/A"), but it really should be date.
# Stage 5 fixes this.
set -euo pipefail
: "${DATABASE:?Set DATABASE first -- see 00_set_lab.sh}"

for TABLE in orders customers; do
    echo
    echo "[lab-stage-4] schema for ${TABLE}:"
    aws glue get-table --database-name "$DATABASE" --name "$TABLE" \
        --query 'Table.StorageDescriptor.Columns[].[Name,Type]' \
        --output text

    echo "[lab-stage-4] ${TABLE} is at:"
    aws glue get-table --database-name "$DATABASE" --name "$TABLE" \
        --query 'Table.StorageDescriptor.Location' --output text

    echo "[lab-stage-4] ${TABLE} uses SerDe:"
    aws glue get-table --database-name "$DATABASE" --name "$TABLE" \
        --query 'Table.StorageDescriptor.SerdeInfo.SerializationLibrary' \
        --output text
done

echo
echo "[lab-stage-4] spot the mis-inference:"
echo "    orders.order_date is likely 'string' due to the 'N/A' row 1009."
