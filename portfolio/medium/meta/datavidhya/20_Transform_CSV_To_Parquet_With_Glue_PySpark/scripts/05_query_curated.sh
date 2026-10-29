#!/usr/bin/env bash
# 05_query_curated.sh -- lab stage 5: query the curated Parquet via Athena.
#
# Athena reads Parquet via the catalog entry. Three queries:
#   1. row count (proves the curated output survived)
#   2. top customer by total spend
#   3. per-day revenue (proves partition pruning on order_date)
set -euo pipefail
: "${DATABASE:?Set DATABASE first -- see 00_set_lab.sh}"
: "${WORKGROUP:?Set WORKGROUP (Athena workgroup from the lab panel)}"

run_athena() {
    local sql="$1"
    aws athena start-query-execution \
        --query-string "$sql" \
        --work-group "$WORKGROUP" \
        --query-execution-context "Database=${DATABASE}" \
        --output text
    sleep 2
}

echo "[lab-stage-5] row count"
run_athena "SELECT COUNT(*) AS n FROM curated_sales"

echo
echo "[lab-stage-5] sample rows"
run_athena "SELECT transaction_id, customer_id, quantity, unit_price,
                   order_date, total_amount
            FROM curated_sales ORDER BY total_amount DESC LIMIT 5"

echo
echo "[lab-stage-5] top 5 customers by total spend"
run_athena "SELECT customer_id, COUNT(*) AS orders,
                   SUM(total_amount) AS spend
            FROM curated_sales
            GROUP BY customer_id
            ORDER BY spend DESC LIMIT 5"

echo
echo "[lab-stage-5] per-day revenue (partition pruning demo)"
run_athena "SELECT order_date, COUNT(*) AS orders, SUM(total_amount) AS revenue
            FROM curated_sales
            WHERE order_date BETWEEN DATE '2026-09-20' AND DATE '2026-09-22'
            GROUP BY order_date
            ORDER BY order_date"
