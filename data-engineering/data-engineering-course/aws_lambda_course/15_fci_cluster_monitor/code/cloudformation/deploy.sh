#!/usr/bin/env bash
#
# Deploy the FCI Cluster Monitor stack (CloudFormation).
#
# Usage:
#   ./deploy.sh                        # interactive — uses defaults
#   STACK_NAME=fci-monitor ./deploy.sh # override stack name
#   OPS_EMAIL=ops@example.com ./deploy.sh
#
# What it does:
#   1. Validates the CFN template locally.
#   2. Zips the Lambda handler into ../monitor_lambda/monitor_lambda.zip.
#   3. Runs `aws cloudformation package` to upload the zip to the
#      assets bucket and rewrite the template with the S3 location.
#   4. Runs `aws cloudformation deploy` with CAPABILITY_NAMED_IAM
#      (the template creates a role with a hardcoded name).
#
# Tear-down:
#   aws cloudformation delete-stack --stack-name ${STACK_NAME} \
#     --region ${AWS_REGION:-us-east-1}
#

set -euo pipefail

STACK_NAME="${STACK_NAME:-fci-monitor}"
REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
ASSET_BUCKET="${ASSET_BUCKET:-fci-monitor-cfn-assets-${ENVIRONMENT}-$(aws sts get-caller-identity --query Account --output text)-${REGION}}"
FSX_FILE_SYSTEM_ID="${FSX_FILE_SYSTEM_ID:-fs-0123456789abcdef0}"
THRESHOLD_GB="${THRESHOLD_GB:-100}"
GROW_FACTOR="${GROW_FACTOR:-1.2}"
COOLDOWN_SECONDS="${COOLDOWN_SECONDS:-1800}"
SCHEDULE_EXPRESSION="${SCHEDULE_EXPRESSION:-rate(5 minutes)}"
OPS_EMAIL="${OPS_EMAIL:?OPS_EMAIL is required (e.g. ops@example.com)}"

THIS_DIR="$(cd "$(dirname "$0")" && pwd)"
LAMBDA_SRC="${THIS_DIR}/../monitor_lambda/lambda_function.py"
ZIP_PATH="${THIS_DIR}/../monitor_lambda/monitor_lambda.zip"
TEMPLATE="${THIS_DIR}/fci_monitor_stack.yaml"
PACKAGED="/tmp/${STACK_NAME}-packaged-$(date +%s).yaml"

if [[ ! -f "${LAMBDA_SRC}" ]]; then
  echo "ERROR: cannot find Lambda source at ${LAMBDA_SRC}" >&2
  exit 1
fi

echo "==> zipping Lambda handler"
mkdir -p "$(dirname "${ZIP_PATH}")"
zip -j "${ZIP_PATH}" "${LAMBDA_SRC}"

echo "==> validating template ${TEMPLATE}"
aws cloudformation validate-template \
  --template-body "file://${TEMPLATE}" \
  --region "${REGION}"

echo "==> ensuring asset bucket exists (s3://${ASSET_BUCKET})"
aws s3 mb "s3://${ASSET_BUCKET}" --region "${REGION}" 2>/dev/null || true

echo "==> packaging template"
aws cloudformation package \
  --template-file "${TEMPLATE}" \
  --s3-bucket "${ASSET_BUCKET}" \
  --output-template-file "${PACKAGED}" \
  --region "${REGION}"

echo "==> deploying stack ${STACK_NAME} into ${REGION}"
aws cloudformation deploy \
  --stack-name "${STACK_NAME}" \
  --template-file "${PACKAGED}" \
  --region "${REGION}" \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
      FsxFileSystemId="${FSX_FILE_SYSTEM_ID}" \
      ThresholdGb="${THRESHOLD_GB}" \
      GrowFactor="${GROW_FACTOR}" \
      CooldownSeconds="${COOLDOWN_SECONDS}" \
      OpsEmail="${OPS_EMAIL}" \
      ScheduleExpression="${SCHEDULE_EXPRESSION}" \
      CodeS3Bucket="${ASSET_BUCKET}"

echo
echo "==> stack outputs:"
aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[*].[OutputKey,OutputValue]" \
  --output table

echo
echo "==> done. Ops must confirm the SNS email subscription at:"
echo "    https://${REGION}.console.aws.amazon.com/sns/v3/home?region=${REGION}#/topic/arn:aws:sns:${REGION}:$(aws sts get-caller-identity --query Account --output text):fci-monitor-alerts"
echo
echo "==> to tear down:"
echo "    aws cloudformation delete-stack --stack-name ${STACK_NAME} --region ${REGION}"
