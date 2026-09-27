#!/usr/bin/env bash
# 01_register_csv.sh -- lab stage 1: stage the seed CSV as a Hive external table.
#
# The lab provisions a CSV at s3://$BUCKET/raw/orders/orders.csv. The first
# Athena step is to register that file as a Hive table so a SELECT against
# it is just a query -- no Iceberg metadata needed.
#
# Hive tables read any file format Athena's SerDe supports. CSV needs the
# OpenCSV SerDe plus column-by-column type declarations.
set -euo pipefail
: "${BUCKET:?Set BUCKET first -- see 00_set_lakehouse.sh}"
: "${DATABASE:?Set DATABASE first -- see 00_set_lakehouse.sh}"

echo "[lab-stage-1] dropping any pre-existing orders_csv (idempotent)"
aws athena start-query-execution \
    --query-string "DROP TABLE IF EXISTS ${DATABASE}.orders_csv" \
    --work-group "$WORKGROUP" \
    --output text >/dev/null
sleep 2

echo "[lab-stage-1] creating the Hive external table over the seed CSV"
SQL=$(cat <<EOF
CREATE EXTERNAL TABLE ${DATABASE}.orders_csv (
  order_id     bigint,
  customer_id  bigint,
  amount       string,
  currency     string,
  order_date   string,
  status       string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
  'separatorChar' = ',',
  'quoteChar'     = '\"',
  'escapeChar'    = '\\\\'
)
STORED AS TEXTFILE
LOCATION 's3://${BUCKET}/raw/orders/'
TBLPROPERTIES ('skip.header.line.count'='1')
EOF
)
aws athena start-query-execution \
    --query-string "$SQL" \
    --work-group "$WORKGROUP" \
    --output text >/dev/null
sleep 2

echo
echo "[lab-stage-1] SELECT count to confirm the table sees the CSV"
aws athena start-query-execution \
    --query-string "SELECT COUNT(*) AS n FROM ${DATABASE}.orders_csv" \
    --work-group "$WORKGROUP" \
    --output text | head
