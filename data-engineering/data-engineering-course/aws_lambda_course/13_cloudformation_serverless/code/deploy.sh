#!/usr/bin/env bash
#
# Deploy the full serverless CloudFormation stack (template 08).
#
# Usage:
#   ./deploy.sh                 # uses defaults below
#   ./deploy.sh dev             # EnvironmentName=dev
#   ./deploy.sh prod            # EnvironmentName=prod
#   BUCKET=... ./deploy.sh prod # override bucket name
#
# After deploy, prints the API URL and smoke-tests PUT/GET.
#

set -euo pipefail

if [[ -z "${AWS_ACCOUNT_ID:-}" ]]; then
  AWS_ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
fi

ENVIRONMENT="${1:-dev}"
STACK_NAME="serverless-${ENVIRONMENT}"
ASSET_BUCKET="${ASSET_BUCKET:-serverless-cfn-assets-${ENVIRONMENT}-${AWS_ACCOUNT_ID}-${AWS_REGION:-us-east-1}}"
BUCKET_NAME="${BUCKET:-serverless-uc2-${ENVIRONMENT}-${AWS_ACCOUNT_ID}}"
STAGE="${STAGE:-${ENVIRONMENT}}"
REGION="${AWS_REGION:-us-east-1}"
ASSETS_DIR="$(cd "$(dirname "$0")" && pwd)/../lambdas_pkg"
TMP_PACKAGED="/tmp/$(basename "$0")-$(date +%s).yaml"

mkdir -p "${ASSETS_DIR}"
zip -j "${ASSETS_DIR}/get_object.zip" ../lambdas/get_object.py
zip -j "${ASSETS_DIR}/put_object.zip" ../lambdas/put_object.py

echo "==> validating template"
aws cloudformation validate-template \
  --template-body file://../templates/08_serverless_with_metadata.yaml \
  --region "${REGION}"

echo "==> ensuring asset bucket exists (s3://${ASSET_BUCKET})"
aws s3 mb "s3://${ASSET_BUCKET}" --region "${REGION}" || true

echo "==> packaging template"
aws cloudformation package \
  --template-file ../templates/08_serverless_with_metadata.yaml \
  --s3-bucket "${ASSET_BUCKET}" \
  --output-template-file "${TMP_PACKAGED}" \
  --region "${REGION}"

echo "==> deploying stack ${STACK_NAME}"
aws cloudformation deploy \
  --stack-name "${STACK_NAME}" \
  --template-file "${TMP_PACKAGED}" \
  --region "${REGION}" \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --parameter-overrides \
      EnvironmentName="${ENVIRONMENT}" \
      BucketName="${BUCKET_NAME}" \
      StageName="${STAGE}"

API_URL=$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
  --output text)

echo
echo "==> API URL: ${API_URL}"
echo "==> PUT /objects/hello.txt"
curl -fsS -X PUT --data "hello from section 13" \
     "${API_URL}/objects/hello.txt" && echo

echo "==> GET /objects/hello.txt"
curl -fsS "${API_URL}/objects/hello.txt" && echo

echo
echo "==> to tear down:"
echo "    aws cloudformation delete-stack --stack-name ${STACK_NAME} --region ${REGION}"
echo "    # The asset bucket has DeletionPolicy: Retain so it survives."
echo "    # Remove it explicitly when you are done:"
echo "    aws s3 rb s3://${ASSET_BUCKET} --force"
