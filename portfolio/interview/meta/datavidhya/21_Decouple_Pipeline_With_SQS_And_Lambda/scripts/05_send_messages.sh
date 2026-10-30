#!/usr/bin/env bash
# 05_send_messages.sh -- lab stage 5: send 8 good messages + watch them flow.
#
# After this script finishes, check the CloudWatch Logs for the consumer
# function to see 2 batches (5 + 3 messages).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAB_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/00_set_lab.sh"

QUEUE_NAME="orders-main-queue"
QUEUE_URL=$(aws sqs get-queue-url --queue-name "$QUEUE_NAME" \
            --query QueueUrl --output text --region "$AWS_REGION")
ORDERS_FILE="$LAB_DIR/sample_data/orders.json"

echo "[lab-stage-5] sending 8 good orders from $ORDERS_FILE"
count=0
while IFS= read -r line; do
    [ -z "$line" ] && continue
    aws sqs send-message --queue-url "$QUEUE_URL" \
        --message-body "$line" --region "$AWS_REGION" >/dev/null
    count=$((count + 1))
done < <(grep -v '^#' "$ORDERS_FILE" | grep -v POISON_)
echo "[lab-stage-5] sent $count good messages"

echo
echo "[lab-stage-5] tailing consumer Lambda logs (Ctrl-C to exit):"
sleep 5       # give the ESM a few seconds to poll
FUNCTION_NAME="orders-consumer-q21"
aws logs tail "/aws/lambda/$FUNCTION_NAME" --since 1m --follow \
    --region "$AWS_REGION" || true
