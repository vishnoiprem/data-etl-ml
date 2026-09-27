#!/usr/bin/env bash
# 01_create_main_queue.sh -- lab stage 1: create the main SQS queue.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/00_set_lab.sh"

MAIN_QUEUE="orders-main-queue"

echo "[lab-stage-1] creating main queue: $MAIN_QUEUE"
aws sqs create-queue --queue-name "$MAIN_QUEUE" --region "$AWS_REGION"

MAIN_URL=$(aws sqs get-queue-url --queue-name "$MAIN_QUEUE" \
            --query QueueUrl --output text --region "$AWS_REGION")
MAIN_ARN=$(aws sqs get-queue-attributes \
            --queue-url "$MAIN_URL" \
            --attribute-names QueueArn \
            --query Attributes.QueueArn --output text --region "$AWS_REGION")

echo
echo "[lab-stage-1] MAIN_URL=$MAIN_URL"
echo "[lab-stage-1] MAIN_ARN=$MAIN_ARN"
