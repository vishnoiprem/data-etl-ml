#!/usr/bin/env bash
# 04_register_curated.sh -- lab stage 4: register the curated Parquet output.
#
# Glue Studio registers catalog tables automatically when you configure
# the target node's "Update schema in Data Catalog" option. If you opted
# out, run this script to register the curated_customers table manually.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/00_set_lab.sh"

TABLE="curated_customers"
S3_PATH="s3://$BUCKET/curated/customers/"

echo "[lab-stage-4] registering $DATABASE.$TABLE -> $S3_PATH"
aws glue create-table \
    --database-name "$DATABASE" \
    --table-input "{
        \"Name\": \"$TABLE\",
        \"StorageDescriptor\": {
            \"Columns\": [
                {\"Name\": \"customer_id\", \"Type\": \"string\"},
                {\"Name\": \"name\",        \"Type\": \"string\"},
                {\"Name\": \"email\",       \"Type\": \"string\"},
                {\"Name\": \"created_at\",  \"Type\": \"timestamp\"}
            ],
            \"Location\":     \"$S3_PATH\",
            \"InputFormat\":  \"org.apache.hadoop.mapred.TextInputFormat\",
            \"OutputFormat\": \"org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat\",
            \"SerdeInfo\": {
                \"SerializationLibrary\": \"org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe\",
                \"Parameters\":           {\"serialization.format\": \"1\"}
            }
        },
        \"TableType\": \"EXTERNAL_TABLE\",
        \"Parameters\": {\"classification\": \"parquet\", \"compressionType\": \"snappy\"}
    }" \
    --region "$AWS_REGION"

echo
echo "[lab-stage-4] registered.  Confirm with:"
echo "              aws glue get-table --database-name $DATABASE --name $TABLE"