#!/usr/bin/env bash
# 07_teardown.sh -- lab stage 7: delete event source mapping, function, queues.
#
# The lab session teardown handles the IAM role and the S3 bucket (if any).
# Local deletion order matters: ESM first (otherwise SQS keeps invoking
# a Lambda that's being deleted), then Lambda, then queues.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/00_set_lab.sh"

FUNCTION_NAME="orders-consumer-q21"
QUEUE_NAME="orders-main-queue"
DLQ="orders-dlq"

echo "[lab-stage-7] listing event source mappings for $FUNCTION_NAME"
UUID=$(aws lambda list-event-source-mappings \
        --function-name "$FUNCTION_NAME" --region "$AWS_REGION" \
        --query 'EventSourceMappings[0].UUID' --output text 2>/dev/null || echo "")
if [ -n "$UUID" ] && [ "$UUID" != "None" ]; then
    echo "[lab-stage-7] deleting event source mapping $UUID"
    aws lambda delete-event-source-mapping --uuid "$UUID" \
        --region "$AWS_REGION"
fi

echo
echo "[lab-stage-7] deleting Lambda function $FUNCTION_NAME"
aws lambda delete-function --function-name "$FUNCTION_NAME" \
    --region "$AWS_REGION"

echo
echo "[lab-stage-7] deleting queues"
for q in "$QUEUE_NAME" "$DLQ"; do
    URL=$(aws sqs get-queue-url --queue-name "$q" \
            --query QueueUrl --output text --region "$AWS_REGION" \
            2>/dev/null || echo "")
    if [ -n "$URL" ] && [ "$URL" != "None" ]; then
        aws sqs delete-queue --queue-url "$URL" --region "$AWS_REGION"
        echo "[lab-stage-7]   deleted $q"
    fi
done

echo
echo "[lab-stage-7] teardown complete."