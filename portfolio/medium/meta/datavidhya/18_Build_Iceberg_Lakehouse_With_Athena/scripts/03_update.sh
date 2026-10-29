#!/usr/bin/env bash
# 03_update.sh -- lab stage 3: row-level UPDATE on the Iceberg table.
#
# Athena engine 3 supports DML against Iceberg tables. UPDATE compiles to a
# copy-on-write rewrite: Iceberg deletes the old data files for matching
# rows, writes a new Parquet data file with the new values, and commits a
# new snapshot. The visible result is one row changed; underneath, two
# snapshots are produced.
set -euo pipefail
: "${DATABASE:?Set DATABASE first -- see 00_set_lakehouse.sh}"

echo "[lab-stage-3] UPDATE order 1001: set status to 'shipped'"
aws athena start-query-execution \
    --query-string "UPDATE ${DATABASE}.orders_iceberg
                    SET status = 'shipped'
                    WHERE order_id = 1001" \
    --work-group "$WORKGROUP" \
    --output text | head

echo
echo "[lab-stage-3] verify row 1001"
aws athena start-query-execution \
    --query-string "SELECT order_id, status FROM ${DATABASE}.orders_iceberg
                    WHERE order_id = 1001" \
    --work-group "$WORKGROUP" \
    --output text | head

echo
echo "[lab-stage-3] inspect the snapshots metadata table"
aws athena start-query-execution \
    --query-string "SELECT snapshot_id, timestamp_ms, operation
                    FROM ${DATABASE}.orders_iceberg\$snapshots
                    ORDER BY timestamp_ms" \
    --work-group "$WORKGROUP" \
    --output text | head
