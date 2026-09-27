#!/usr/bin/env bash
# 03_attach_redrive.sh -- lab stage 3: attach redrive policy to main queue.
#
# maxReceiveCount=3 means: after 3 failed receives, SQS parks the message
# in the DLQ. The policy is just JSON attached via set-queue-attributes.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/00_set_lab.sh"

MAIN_QUEUE="orders-main-queue"
DLQ="orders-dlq"
MAX_RECEIVE_COUNT=3

DLQ_URL=$(aws sqs get-queue-url --queue-name "$DLQ" \
            --query QueueUrl --output text --region "$AWS_REGION")
DLQ_ARN=$(aws sqs get-queue-attributes \
            --queue-url "$DLQ_URL" \
            --attribute-names QueueArn \
            --query Attributes.QueueArn --output text --region "$AWS_REGION")

REDRIVE_POLICY=$(jq -nc --arg arn "$DLQ_ARN" --argjson n "$MAX_RECEIVE_COUNT" \
    '{deadLetterTargetArn: $arn, maxReceiveCount: $n}')

echo "[lab-stage-3] attaching redrive policy to $MAIN_QUEUE"
echo "              -> $DLQ_ARN after $MAX_RECEIVE_COUNT retries"

aws sqs set-queue-attributes --queue-url "$( \
        aws sqs get-queue-url --queue-name "$MAIN_QUEUE" \
            --query QueueUrl --output text --region "$AWS_REGION")" \
    --attributes "{\"RedrivePolicy\":$(echo "$REDRIVE_POLICY" | jq -c .)}" \
    --region "$AWS_REGION"

echo
echo "[lab-stage-3] redrive policy attached."
aws sqs get-queue-attributes \
    --queue-url "$( \
        aws sqs get-queue-url --queue-name "$MAIN_QUEUE" \
            --query QueueUrl --output text --region "$AWS_REGION")" \
    --attribute-names RedrivePolicy --region "$AWS_REGION"
