#!/usr/bin/env bash
# 05_challenge_query.sh -- lab stage 5: write a query yourself.
#
# The lab's challenge: write a query that finds the busiest pickup-zone
# to dropoff-zone pairs (excluding zero-passenger trips).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/00_set_lab.sh"

SQL="SELECT pickup_zone, dropoff_zone, COUNT(*) AS trips,
             ROUND(AVG(trip_distance), 2) AS avg_miles
      FROM taxi_trips
      WHERE passenger_count > 0
      GROUP BY pickup_zone, dropoff_zone
      ORDER BY trips DESC
      LIMIT 5"

echo "[lab-stage-5] challenge query:"
echo "              $SQL"
echo

EXEC_ID=$(aws athena start-query-execution \
    --work-group "$WORKGROUP" \
    --query-execution-context "Database=$DATABASE" \
    --query-string "$SQL" \
    --region "$AWS_REGION" \
    --query 'QueryExecutionId' --output text)
echo "[lab-stage-5] QueryExecutionId=$EXEC_ID"

for _ in $(seq 1 30); do
    STATE=$(aws athena get-query-execution \
              --query-execution-id "$EXEC_ID" \
              --region "$AWS_REGION" \
              --query 'QueryExecution.Status.State' --output text)
    if [ "$STATE" = "SUCCEEDED" ]; then
        aws athena get-query-results \
            --query-execution-id "$EXEC_ID" \
            --region "$AWS_REGION" \
            --query 'ResultSet.Rows[*].Data[*].VarCharValue' \
            --output table
        break
    elif [ "$STATE" = "FAILED" ] || [ "$STATE" = "CANCELLED" ]; then
        echo "[lab-stage-5] query ended in $STATE"
        aws athena get-query-execution \
            --query-execution-id "$EXEC_ID" --region "$AWS_REGION" \
            --query 'QueryExecution.Status.StateChangeReason' --output text
        exit 1
    fi
    sleep 2
done