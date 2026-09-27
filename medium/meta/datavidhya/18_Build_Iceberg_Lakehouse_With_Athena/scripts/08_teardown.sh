#!/usr/bin/env bash
# 08_teardown.sh -- lab stage 8: drop the tables; leave the bucket for the next session.
#
# Athena keeps the underlying Parquet data files in S3 until you drop the
# table -- DROP TABLE removes both the metadata and the data files for
# Iceberg tables (because they're "managed" by the catalog). For Hive
# external tables the data stays in S3 after a DROP because the table is
# external by definition.
set -euo pipefail
: "${DATABASE:?Set DATABASE first -- see 00_set_lakehouse.sh}"

echo "[lab-stage-8] dropping the Iceberg table (deletes data + metadata)"
aws athena start-query-execution \
    --query-string "DROP TABLE ${DATABASE}.orders_iceberg" \
    --work-group "$WORKGROUP" \
    --output text >/dev/null

echo "[lab-stage-8] dropping the Hive external table (CSV stays in S3)"
aws athena start-query-execution \
    --query-string "DROP TABLE ${DATABASE}.orders_csv" \
    --work-group "$WORKGROUP" \
    --output text >/dev/null

echo
echo "[lab-stage-8] lab session clean. CSV files at s3://\$BUCKET/raw/orders/"
echo "[lab-stage-8] remain in S3 because they're external; they'll be"
echo "[lab-stage-8] cleaned up when the lab session ends."
