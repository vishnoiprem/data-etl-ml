#!/usr/bin/env bash
# 06_query_join.sh -- lab stage 6: Athena queries on both catalog tables.
#
# Athena uses the Glue catalog as its metadata layer. A ``SELECT * FROM
# catalog_db_xxx.orders`` reads the Glue table's schema + location, then
# pulls the rows from S3 using the recorded SerDe (OpenCSVSerde for the
# CSV, JsonSerDe for the JSON).
set -euo pipefail
: "${DATABASE:?Set DATABASE first -- see 00_set_lab.sh}"
: "${WORKGROUP:?Set WORKGROUP first -- see 00_set_lab.sh}"

run_athena() {
    local sql="$1"
    aws athena start-query-execution \
        --query-string "$sql" \
        --work-group "$WORKGROUP" \
        --query-execution-context "Database=${DATABASE}" \
        --output text
    sleep 2
}

echo "[lab-stage-6] row count on orders"
run_athena "SELECT COUNT(*) AS n FROM orders"

echo
echo "[lab-stage-6] row count on customers"
run_athena "SELECT COUNT(*) AS n FROM customers"

echo
echo "[lab-stage-6] top 5 orders by amount"
run_athena "SELECT order_id, customer_id, amount, currency, status
            FROM orders ORDER BY CAST(amount AS double) DESC LIMIT 5"

echo
echo "[lab-stage-6] JOIN: top 5 customers by total order value"
run_athena "SELECT c.name, c.tier, COUNT(*) AS orders, SUM(CAST(o.amount AS double)) AS total
            FROM orders o JOIN customers c
              ON o.customer_id = c.customer_id
            GROUP BY c.name, c.tier
            ORDER BY total DESC LIMIT 5"
