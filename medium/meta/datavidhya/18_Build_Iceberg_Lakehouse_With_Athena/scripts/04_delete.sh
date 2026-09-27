#!/usr/bin/env bash
# 04_delete.sh -- lab stage 4: DELETE rows from the Iceberg table.
#
# DELETE is also DML on an Iceberg table. Underneath, Iceberg rewrites the
# affected data file with the deleted rows removed (and a delete-file
# recording which row positions are gone for metadata-only deletes). Either
# way the visible result is the same: matching rows are gone and a new
# snapshot is committed.
set -euo pipefail
: "${DATABASE:?Set DATABASE first -- see 00_set_lakehouse.sh}"

echo "[lab-stage-4] DELETE all cancelled orders"
aws athena start-query-execution \
    --query-string "DELETE FROM ${DATABASE}.orders_iceberg
                    WHERE status = 'cancelled'" \
    --work-group "$WORKGROUP" \
    --output text | head

echo
echo "[lab-stage-4] confirm row count"
aws athena start-query-execution \
    --query-string "SELECT COUNT(*) AS n FROM ${DATABASE}.orders_iceberg" \
    --work-group "$WORKGROUP" \
    --output text | head

echo
echo "[lab-stage-4] no cancelled rows remain"
aws athena start-query-execution \
    --query-string "SELECT COUNT(*) AS cancelled_rows
                    FROM ${DATABASE}.orders_iceberg
                    WHERE status = 'cancelled'" \
    --work-group "$WORKGROUP" \
    --output text | head
