#!/usr/bin/env bash
# 02_create_dlq.sh -- lab stage 2: create the dead-letter queue.
#
# The DLQ has NO redrive policy of its own -- it's a terminal parking lot.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/00_set_lab.sh"

DLQ="orders-dlq"

echo "[lab-stage-2] creating DLQ: $DLQ"
aws sqs create-queue --queue-name "$DLQ" --region "$AWS_REGION"

DLQ_URL=$(aws sqs get-queue-url --queue-name "$DLQ" \
            --query QueueUrl --output text --region "$AWS_REGION")
DLQ_ARN=$(aws sqs get-queue-attributes \
            --queue-url "$DLQ_URL" \
            --attribute-names QueueArn \
            --query Attributes.QueueArn --output text --region "$AWS_REGION")

echo
echo "[lab-stage-2] DLQ_URL=$DLQ_URL"
echo "[lab-stage-2] DLQ_ARN=$DLQ_ARN"
