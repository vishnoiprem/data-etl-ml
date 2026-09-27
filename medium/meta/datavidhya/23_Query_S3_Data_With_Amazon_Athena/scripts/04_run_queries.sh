#!/usr/bin/env bash
# 04_run_queries.sh -- lab stage 4: run the 5 analytical Athena queries.
#
# Each query polls QueryExecution.State until SUCCEEDED, then fetches
# rows. Mirrors slot 20's poll+fetch pattern.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/00_set_lab.sh"

run_query() {
    local label="$1" sql="$2"
    local exec_id
    exec_id=$(aws athena start-query-execution \
        --work-group "$WORKGROUP" \
        --query-execution-context "Database=$DATABASE" \
        --query-string "$sql" \
        --region "$AWS_REGION" \
        --query 'QueryExecutionId' --output text)
    echo
    echo "[lab-stage-4] $label -> QueryExecutionId=$exec_id"
    for _ in $(seq 1 30); do
        STATE=$(aws athena get-query-execution \
                  --query-execution-id "$exec_id" \
                  --region "$AWS_REGION" \
                  --query 'QueryExecution.Status.State' --output text)
        if [ "$STATE" = "SUCCEEDED" ]; then
            aws athena get-query-results \
                --query-execution-id "$exec_id" \
                --region "$AWS_REGION" \
                --query 'ResultSet.Rows[*].Data[*].VarCharValue' \
                --output text
            return
        elif [ "$STATE" = "FAILED" ] || [ "$STATE" = "CANCELLED" ]; then
            echo "[lab-stage-4] query $label ended in $STATE"
            aws athena get-query-execution \
                --query-execution-id "$exec_id" --region "$AWS_REGION" \
                --query 'QueryExecution.Status.StateChangeReason' --output text
            return 1
        fi
        sleep 2
    done
    echo "[lab-stage-4] query $label timed out"
    return 1
}

run_query "Q1: total trip count" \
    "SELECT COUNT(*) AS n FROM taxi_trips"

run_query "Q2: payment-type breakdown" \
    "SELECT payment_type, COUNT(*) AS trips,
            ROUND(AVG(fare_amount), 2) AS avg_fare,
            ROUND(AVG(tip_amount), 2)  AS avg_tip
     FROM taxi_trips GROUP BY payment_type ORDER BY trips DESC"

run_query "Q3: top 5 pickup zones by revenue" \
    "SELECT pickup_zone, ROUND(SUM(total_amount), 2) AS revenue
     FROM taxi_trips GROUP BY pickup_zone ORDER BY revenue DESC LIMIT 5"

run_query "Q4: per-day distribution" \
    "SELECT DATE(pickup_datetime) AS day, COUNT(*) AS trips
     FROM taxi_trips GROUP BY day ORDER BY day"

run_query "Q5: cash trips with zero tips" \
    "SELECT COUNT(*) AS cash_zero_tip
     FROM taxi_trips WHERE payment_type='CSH' AND tip_amount=0"