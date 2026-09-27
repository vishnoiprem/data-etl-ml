#!/usr/bin/env bash
# 04_create_lambda.sh -- lab stage 4: package + create the consumer Lambda,
# then wire it to the main queue via an event source mapping.
#
# The function code lives in ../lambda_function/app.py -- this script
# bundles it into a zip, creates the function, and attaches the ESM.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAB_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/00_set_lab.sh"

FUNCTION_NAME="orders-consumer-q21"
QUEUE_NAME="orders-main-queue"
RUNTIME="python3.12"
HANDLER="app.lambda_handler"
TIMEOUT=30
MEMORY=256

# ---- package the handler
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
(cd "$LAB_DIR/lambda_function" && zip -qr "$TMP/function.zip" app.py)
echo "[lab-stage-4] packaged $LAB_DIR/lambda_function/app.py"

# ---- create the function (lab provisions the IAM role)
echo "[lab-stage-4] creating Lambda function: $FUNCTION_NAME"
aws lambda create-function \
    --function-name "$FUNCTION_NAME" \
    --runtime "$RUNTIME" \
    --handler "$HANDLER" \
    --role "$ROLE_ARN" \
    --zip-file "fileb://$TMP/function.zip" \
    --timeout "$TIMEOUT" \
    --memory-size "$MEMORY" \
    --region "$AWS_REGION"

# ---- wire the event source mapping (SQS -> Lambda poll)
QUEUE_ARN=$(aws sqs get-queue-attributes \
    --queue-url "$( \
        aws sqs get-queue-url --queue-name "$QUEUE_NAME" \
            --query QueueUrl --output text --region "$AWS_REGION")" \
    --attribute-names QueueArn --query Attributes.QueueArn --output text \
    --region "$AWS_REGION")

echo "[lab-stage-4] creating event source mapping: $QUEUE_ARN -> $FUNCTION_NAME"
aws lambda create-event-source-mapping \
    --function-name "$FUNCTION_NAME" \
    --event-source-arn "$QUEUE_ARN" \
    --batch-size 5 \
    --region "$AWS_REGION"

echo
echo "[lab-stage-4] event source mapping created.  The Lambda will now"
echo "              poll $QUEUE_NAME in batches of 5."
