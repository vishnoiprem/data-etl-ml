#!/usr/bin/env bash
# 06_insert.sh -- lab stage 6: INSERT INTO the Iceberg table.
#
# INSERT adds rows; under the hood Iceberg writes a new Parquet data file
# and commits a new snapshot. The metadata table '$snapshots' will grow by
# one row after this statement commits.
set -euo pipefail
: "${DATABASE:?Set DATABASE first -- see 00_set_lakehouse.sh}"

echo "[lab-stage-6] INSERT two new rows"
aws athena start-query-execution \
    --query-string "INSERT INTO ${DATABASE}.orders_iceberg
                    VALUES
                      (2001, 42, '500.00', 'USD', '2026-09-27', 'placed'),
                      (2002, 88, '75.00',  'EUR', '2026-09-27', 'placed')" \
    --work-group "$WORKGROUP" \
    --output text | head

echo
echo "[lab-stage-6] confirm the new rows are visible"
aws athena start-query-execution \
    --query-string "SELECT order_id, customer_id, currency, status
                    FROM ${DATABASE}.orders_iceberg
                    WHERE order_id IN (2001, 2002)
                    ORDER BY order_id" \
    --work-group "$WORKGROUP" \
    --output text | head

echo
echo "[lab-stage-6] new row count"
aws athena start-query-execution \
    --query-string "SELECT COUNT(*) AS n FROM ${DATABASE}.orders_iceberg" \
    --work-group "$WORKGROUP" \
    --output text | head

echo
echo "[lab-stage-6] the snapshots table grew by one row"
aws athena start-query-execution \
    --query-string "SELECT COUNT(*) AS snapshots
                    FROM ${DATABASE}.orders_iceberg\$snapshots" \
    --work-group "$WORKGROUP" \
    --output text | head
