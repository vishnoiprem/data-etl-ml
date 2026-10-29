#!/usr/bin/env bash
# 05_query_curated.sh -- lab stage 5: query the curated_customers table.
#
# Three queries: row count, top-3 by created_at, per-day grouping.
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
    echo "[lab-stage-5] $label -> QueryExecutionId=$exec_id"
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
            echo "[lab-stage-5] query $label ended in $STATE"
            aws athena get-query-execution \
                --query-execution-id "$exec_id" --region "$AWS_REGION" \
                --query 'QueryExecution.Status.StateChangeReason' --output text
            return 1
        fi
        sleep 2
    done
}

run_query "row count" \
    "SELECT COUNT(*) AS n FROM curated_customers"

run_query "top 3 newest customers" \
    "SELECT name, created_at FROM curated_customers
     ORDER BY created_at DESC LIMIT 3"

run_query "per-day active-customer counts" \
    "SELECT DATE(created_at) AS day, COUNT(*) AS n
     FROM curated_customers GROUP BY DATE(created_at) ORDER BY day"