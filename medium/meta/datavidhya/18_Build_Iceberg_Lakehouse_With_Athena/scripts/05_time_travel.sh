#!/usr/bin/env bash
# 05_time_travel.sh -- lab stage 5: FOR SYSTEM_TIME / FOR SYSTEM_VERSION AS OF.
#
# Athena engine 3 supports both snapshot-id and timestamp-based time travel
# against Iceberg tables. This is the killer feature: a query can read the
# table "as it was" at any earlier snapshot, regardless of what writes
# have happened since.
#
# Two flavours:
#   FOR SYSTEM_VERSION AS OF '<snapshot-id>'   -- exact snapshot
#   FOR SYSTEM_TIME    AS OF '<iso8601-ts>'   -- nearest earlier snapshot
set -euo pipefail
: "${DATABASE:?Set DATABASE first -- see 00_set_lakehouse.sh}"

echo "[lab-stage-5] list available snapshots + timestamps"
aws athena start-query-execution \
    --query-string "SELECT snapshot_id, timestamp_ms,
                           FROM_UNIXTIME(timestamp_ms / 1000) AS ts_iso
                    FROM ${DATABASE}.orders_iceberg\$snapshots
                    ORDER BY timestamp_ms" \
    --work-group "$WORKGROUP" \
    --output text | head

echo
echo "[lab-stage-5] pick the first snapshot's id and read the table at it"
FIRST_SNAP=$(aws athena start-query-execution \
    --query-string "SELECT snapshot_id FROM ${DATABASE}.orders_iceberg\$snapshots
                    ORDER BY timestamp_ms ASC LIMIT 1" \
    --work-group "$WORKGROUP" --output text | tail -1)
echo "    first snapshot id = $FIRST_SNAP"

echo
echo "[lab-stage-5] FOR SYSTEM_VERSION AS OF '<snapshot-1>'"
aws athena start-query-execution \
    --query-string "SELECT COUNT(*) AS rows_at_snapshot_1
                    FROM ${DATABASE}.orders_iceberg
                    FOR SYSTEM_VERSION AS OF '$FIRST_SNAP'" \
    --work-group "$WORKGROUP" \
    --output text | head

echo
echo "[lab-stage-5] row 1001 at snapshot 1 is still 'placed'"
aws athena start-query-execution \
    --query-string "SELECT order_id, status FROM ${DATABASE}.orders_iceberg
                    WHERE order_id = 1001
                    FOR SYSTEM_VERSION AS OF '$FIRST_SNAP'" \
    --work-group "$WORKGROUP" \
    --output text | head
