#!/usr/bin/env bash
# 05_fix_schema.sh -- lab stage 5: edit orders.order_date from string -> date.
#
# Glue's UpdateTable rewrites the table definition in the catalog without
# touching the S3 file. The S3 file still has "N/A" in row 1009 -- which
# means Athena will skip that row's date when the column is now typed
# date, OR it will fail to project that one row. In production the fix
# is two-step: edit the schema, then fix the row in the source data.
set -euo pipefail
: "${DATABASE:?Set DATABASE first -- see 00_set_lab.sh}"

echo "[lab-stage-5] before: orders.order_date type is..."
aws glue get-table --database-name "$DATABASE" --name "orders" \
    --query 'Table.StorageDescriptor.Columns[?Name==`order_date`].[Name,Type]' \
    --output text

echo
echo "[lab-stage-5] rewriting orders.order_date -> date"
# UpdateTable takes a full TableInput; we read-modify-write it here.
aws glue update-table \
    --database-name "$DATABASE" \
    --table-input "$(aws glue get-table --database-name "$DATABASE" \
                       --name "orders" \
                       --query 'Table' --output json | \
                   python3 -c '
import json, sys
t = json.load(sys.stdin)
sd = t["StorageDescriptor"]
for c in sd["Columns"]:
    if c["Name"] == "order_date":
        c["Type"] = "date"
t["StorageDescriptor"] = sd
print(json.dumps(t))
')"

echo
echo "[lab-stage-5] after: orders.order_date type is..."
aws glue get-table --database-name "$DATABASE" --name "orders" \
    --query 'Table.StorageDescriptor.Columns[?Name==`order_date`].[Name,Type]' \
    --output text

echo
echo "[lab-stage-5] S3 file is unchanged (still has N/A):"
aws s3 cp "s3://${BUCKET}/raw/orders/orders.csv" - | grep N/A || echo "    (no N/A in this build)"
