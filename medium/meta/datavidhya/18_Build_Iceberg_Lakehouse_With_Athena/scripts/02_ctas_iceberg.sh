#!/usr/bin/env bash
# 02_ctas_iceberg.sh -- lab stage 2: CREATE TABLE AS SELECT into an Iceberg table.
#
# Athena's CTAS syntax: "CREATE TABLE <db>.<t> AS SELECT ..." with
# table_properties that specify 'table_type=ICEBERG'. The new table is
# born an Iceberg table -- no Hive -> Iceberg conversion needed.
#
# The lab picks status = 'placed' as the filter so the Iceberg table starts
# with a curated subset (11 rows) rather than the full 12. This is the
# "raw -> curated" pattern from the lab 16 data-lake lab.
set -euo pipefail
: "${BUCKET:?Set BUCKET first -- see 00_set_lakehouse.sh}"
: "${DATABASE:?Set DATABASE first -- see 00_set_lakehouse.sh}"

echo "[lab-stage-2] dropping pre-existing orders_iceberg (idempotent)"
aws athena start-query-execution \
    --query-string "DROP TABLE IF EXISTS ${DATABASE}.orders_iceberg" \
    --work-group "$WORKGROUP" \
    --output text >/dev/null
sleep 2

echo "[lab-stage-2] CTAS into an Iceberg table (only placed orders)"
SQL=$(cat <<EOF
CREATE TABLE ${DATABASE}.orders_iceberg
WITH (
  table_type    = 'ICEBERG',
  format        = 'PARQUET',
  write_compression = 'SNAPPY',
  location      = 's3://${BUCKET}/iceberg-warehouse/orders_iceberg/'
) AS
SELECT order_id, customer_id, amount, currency, order_date, status
FROM ${DATABASE}.orders_csv
WHERE status = 'placed'
EOF
)
aws athena start-query-execution \
    --query-string "$SQL" \
    --work-group "$WORKGROUP" \
    --output text | head

echo
echo "[lab-stage-2] show tables in the database"
aws athena start-query-execution \
    --query-string "SHOW TABLES IN ${DATABASE}" \
    --work-group "$WORKGROUP" \
    --output text | head
