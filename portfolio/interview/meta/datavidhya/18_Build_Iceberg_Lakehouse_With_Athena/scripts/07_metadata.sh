#!/usr/bin/env bash
# 07_metadata.sh -- lab stage 7: inspect Iceberg's metadata tables.
#
# Iceberg exposes several $-prefixed metadata tables that Athena can SELECT
# like any other table. The lab covers the four the AWS console highlights:
#
#   ${table}$snapshots  -- one row per commit (snapshot_id, ts, operation)
#   ${table}$history     -- same data as $snapshots, older name
#   ${table}$files       -- one row per data file (path, size, partition)
#   ${table}$manifests   -- one row per manifest list / manifest file
#
# These are virtual tables; they're computed on the fly from the metadata
# JSON in S3, not stored as data themselves.
set -euo pipefail
: "${DATABASE:?Set DATABASE first -- see 00_set_lakehouse.sh}"

echo "[lab-stage-7] snapshots metadata table"
aws athena start-query-execution \
    --query-string "SELECT snapshot_id, parent_snapshot_id,
                           FROM_UNIXTIME(timestamp_ms / 1000) AS committed_at,
                           operation, summary['total-records'] AS total_records
                    FROM ${DATABASE}.orders_iceberg\$snapshots
                    ORDER BY committed_at" \
    --work-group "$WORKGROUP" \
    --output text | head -20

echo
echo "[lab-stage-7] data files metadata table"
aws athena start-query-execution \
    --query-string "SELECT file_path, file_format, record_count,
                           file_size_in_bytes
                    FROM ${DATABASE}.orders_iceberg\$files
                    ORDER BY file_path" \
    --work-group "$WORKGROUP" \
    --output text | head -20

echo
echo "[lab-stage-7] manifests metadata table"
aws athena start-query-execution \
    --query-string "SELECT path, length, partition_spec_id,
                           added_snapshot_id
                    FROM ${DATABASE}.orders_iceberg\$manifests
                    ORDER BY added_snapshot_id" \
    --work-group "$WORKGROUP" \
    --output text | head -20
