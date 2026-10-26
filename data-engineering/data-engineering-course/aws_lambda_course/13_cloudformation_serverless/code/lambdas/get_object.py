"""GET /objects/{proxy+} — fetch an object from the configured S3 bucket.

Environment:
    BUCKET_NAME — the S3 bucket to read from. Set by CloudFormation.

Event:
    API Gateway proxy event with pathParameters.proxy = "<key>".

Response:
    200 + base64-encoded body if the key exists.
    404 if the key does not exist.
    400 if the key is missing.
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


def lambda_handler(event, context):
    LOGGER.info("event=%s", json.dumps(event))

    params = event.get("pathParameters") or {}
    key = params.get("proxy") or params.get("key")

    if not key:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "missing key in path"}),
        }

    try:
        resp = s3.get_object(Bucket=BUCKET, Key=key)
        body = resp["Body"].read()
        is_text = key.endswith((".txt", ".json", ".md", ".csv"))
        try:
            encoded = body.decode("utf-8") if is_text else base64.b64encode(body).decode("ascii")
        except UnicodeDecodeError:
            encoded = base64.b64encode(body).decode("ascii")
        return {
            "statusCode": 200,
            "headers": {"Content-Type": resp.get("ContentType", "application/octet-stream")},
            "body": json.dumps({"key": key, "data": encoded}),
        }
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        if code == "NoSuchKey":
            return {"statusCode": 404, "body": json.dumps({"error": f"key not found: {key}"})}
        LOGGER.exception("S3 get_object failed")
        return {"statusCode": 500, "body": json.dumps({"error": "internal error"})}
