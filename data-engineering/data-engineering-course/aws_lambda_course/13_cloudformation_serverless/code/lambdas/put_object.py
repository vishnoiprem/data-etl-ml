"""PUT /objects/{proxy+} — write an object to the configured S3 bucket.

Environment:
    BUCKET_NAME — the S3 bucket to write to. Set by CloudFormation.

Event:
    API Gateway proxy event with:
        pathParameters.proxy = "<key>"
        body = base64-encoded or UTF-8 string payload.

Response:
    200 + {key, etag, size} on success.
    400 on missing key.
    500 on any other failure.
"""

import base64
import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

s3 = boto3.client("s3")
BUCKET = os.environ["BUCKET_NAME"]


def _decode_body(body: str, is_base64: bool) -> bytes:
    if not body:
        return b""
    if is_base64:
        return base64.b64decode(body)
    return body.encode("utf-8")


def lambda_handler(event, context):
    LOGGER.info("event=%s", json.dumps(event))

    params = event.get("pathParameters") or {}
    key = params.get("proxy") or params.get("key")

    if not key:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "missing key in path"}),
        }

    is_b64 = event.get("isBase64Encoded", False)
    payload = _decode_body(event.get("body", ""), is_b64)

    try:
        resp = s3.put_object(Bucket=BUCKET, Key=key, Body=payload)
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "key": key,
                    "etag": resp.get("ETag"),
                    "size": len(payload),
                }
            ),
        }
    except ClientError:
        LOGGER.exception("S3 put_object failed")
        return {"statusCode": 500, "body": json.dumps({"error": "put_object failed"})}
