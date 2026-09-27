#!/usr/bin/env bash
# 03_create_table.sh -- lab stage 3: create the EXTERNAL TABLE (schema on read).
#
# The CREATE EXTERNAL TABLE DDL just describes the CSV's columns. No data
# is copied. Athena reads s3://$BUCKET/taxi/yellow_taxi_sample.csv at
# query time.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/00_set_lab.sh"

DDL=$(cat <<EOF
CREATE EXTERNAL TABLE taxi_trips (
    vendor_id          INT,
    pickup_datetime    TIMESTAMP,
    dropoff_datetime   TIMESTAMP,
    passenger_count    INT,
    trip_distance      DOUBLE,
    pickup_zone        STRING,
    dropoff_zone       STRING,
    ratecode_id        INT,
    payment_type       STRING,
    fare_amount        DOUBLE,
    extra              DOUBLE,
    mta_tax            DOUBLE,
    tip_amount         DOUBLE,
    tolls_amount       DOUBLE,
    total_amount       DOUBLE
)
ROW FORMAT DELIMITED
    FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://$BUCKET/taxi/'
TBLPROPERTIES ('skip.header.line.count'='1')
EOF
)

echo "[lab-stage-3] running CREATE EXTERNAL TABLE ..."
EXEC_ID=$(aws athena start-query-execution \
    --work-group "$WORKGROUP" \
    --query-execution-context "Database=$DATABASE" \
    --query-string "$DDL" \
    --region "$AWS_REGION" \
    --query 'QueryExecutionId' --output text)
echo "[lab-stage-3] QueryExecutionId=$EXEC_ID"

for _ in $(seq 1 30); do
    STATE=$(aws athena get-query-execution \
              --query-execution-id "$EXEC_ID" \
              --region "$AWS_REGION" \
              --query 'QueryExecution.Status.State' --output text)
    case "$STATE" in
        SUCCEEDED) echo "[lab-stage-3] table created."; break ;;
        FAILED|CANCELLED)
            echo "[lab-stage-3] CREATE TABLE ended in $STATE"
            aws athena get-query-execution \
                --query-execution-id "$EXEC_ID" --region "$AWS_REGION" \
                --query 'QueryExecution.Status.StateChangeReason' --output text
            exit 1 ;;
    esac
    sleep 2
done

echo
echo "[lab-stage-3] verifying columns:"
aws glue get-table --database-name "$DATABASE" --name "taxi_trips" \
    --region "$AWS_REGION" \
    --query 'Table.StorageDescriptor.Columns[].[Name,Type]' --output table