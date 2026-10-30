#!/usr/bin/env bash
# 04_register_curated.sh -- lab stage 4: register the curated Parquet as a
# new Glue catalog table.
#
# Athena queries the catalog, not the S3 prefix directly. The curated
# Parquet is now in s3://$BUCKET/curated/sales/ but Athena can't see it
# until we add a catalog entry. Glue Crawlers can do this; the lab uses
# CreateTable directly because the schema is known.
set -euo pipefail
: "${BUCKET:?Set BUCKET first -- see 00_set_lab.sh}"
: "${DATABASE:?Set DATABASE first -- see 00_set_lab.sh}"

echo "[lab-stage-4] dropping pre-existing curated table (idempotent)"
aws glue delete-table --database-name "$DATABASE" --name "curated_sales" 2>/dev/null || true

echo "[lab-stage-4] creating the curated_sales table in the catalog"
aws glue create-table \
    --database-name "$DATABASE" \
    --table-input "$(cat <<EOF
{
  "Name": "curated_sales",
  "StorageDescriptor": {
    "Columns": [
      {"Name": "transaction_id", "Type": "string"},
      {"Name": "customer_id",    "Type": "string"},
      {"Name": "product_id",     "Type": "string"},
      {"Name": "quantity",       "Type": "int"},
      {"Name": "unit_price",     "Type": "double"},
      {"Name": "order_date",     "Type": "date"},
      {"Name": "total_amount",   "Type": "double"}
    ],
    "Location":         "s3://${BUCKET}/curated/sales/",
    "InputFormat":      "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
    "OutputFormat":     "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
    "SerdeInfo":        {"SerializationLibrary": "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"},
    "Compressed":       false,
    "NumberOfBuckets":  -1,
    "SerdeInfo": {
      "SerializationLibrary": "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }
  },
  "PartitionKeys": [
    {"Name": "order_date", "Type": "date"}
  ],
  "TableType": "EXTERNAL_TABLE"
}
EOF
)"

echo
echo "[lab-stage-4] curated_sales table is now in the catalog"
aws glue get-table --database-name "$DATABASE" --name "curated_sales" \
    --query 'Table.[Name,StorageDescriptor.Location,PartitionKeys]' \
    --output text
