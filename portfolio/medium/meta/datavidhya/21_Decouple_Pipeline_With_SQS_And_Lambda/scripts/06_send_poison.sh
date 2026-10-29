#!/usr/bin/env bash
# 06_send_poison.sh -- lab stage 6: send 2 poison messages, watch retries -> DLQ.
#
# SQS retries failed messages up to maxReceiveCount (3). On the 4th
# poll, the redrive policy moves them to the DLQ.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAB_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/00_set_lab.sh"

QUEUE_NAME="orders-main-queue"
DLQ_NAME="orders-dlq"
QUEUE_URL=$(aws sqs get-queue-url --queue-name "$QUEUE_NAME" \
            --query QueueUrl --output text --region "$AWS_REGION")
DLQ_URL=$(aws sqs get-queue-url --queue-name "$DLQ_NAME" \
            --query QueueUrl --output text --region "$AWS_REGION")
ORDERS_FILE="$LAB_DIR/sample_data/orders.json"

echo "[lab-stage-6] sending 2 poison messages from $ORDERS_FILE"
while IFS= read -r line; do
    [ -z "$line" ] && continue
    echo "$line" | grep -q POISON_ || continue
    aws sqs send-message --queue-url "$QUEUE_URL" \
        --message-body "$line" --region "$AWS_REGION" >/dev/null
    echo "[lab-stage-6]   sent poison: $(echo "$line" | jq -r .order_id)"
done < "$ORDERS_FILE"

echo
echo "[lab-stage-6] waiting ~60s for SQS to retry maxReceiveCount=3 times..."
sleep 60

echo "[lab-stage-6] checking DLQ contents:"
aws sqs receive-message --queue-url "$DLQ_URL" \
    --max-number-of-messages 10 --visibility-timeout 30 \
    --region "$AWS_REGION" \
    --query 'Messages[].Body' --output table || true