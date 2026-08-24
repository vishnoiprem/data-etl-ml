"""Shared configuration: loads aws.env and exposes credentials + resource identifiers.

Everything the app and the provisioner need comes from here, so no credential or ARN
is ever hardcoded in a source file.
"""

import os

from dotenv import load_dotenv

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(PROJECT_DIR, "aws.env"))


def _require(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            "%s is not set. Add it to %s/aws.env" % (name, PROJECT_DIR)
        )
    return value


REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
ACCESS_KEY = _require("AWS_ACCESS_KEY_ID")
SECRET_KEY = _require("AWS_SECRET_ACCESS_KEY")

# boto3 kwargs shared by every client in the project
BOTO_KWARGS = {
    "region_name": REGION,
    "aws_access_key_id": ACCESS_KEY,
    "aws_secret_access_key": SECRET_KEY,
}

KNOWLEDGE_BASE_ID = os.environ.get("KNOWLEDGE_BASE_ID", "")
DATA_SOURCE_ID = os.environ.get("DATA_SOURCE_ID", "")
MODEL_ID = os.environ.get(
    "CLAUDE_INFERENCE_PROFILE_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0"
)
EMBEDDING_MODEL_ARN = os.environ.get(
    "EMBEDDING_MODEL_ARN",
    "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0",
)

AURORA_CLUSTER_ARN = os.environ.get("AURORA_CLUSTER_ARN", "")
AURORA_SECRET_ARN = os.environ.get("AURORA_SECRET_ARN", "")
AURORA_DATABASE = os.environ.get("AURORA_DATABASE", "VectorDatabase")
AURORA_TABLE = os.environ.get("AURORA_TABLE", "bedrock_integration.bedrock_kb")

S3_BUCKET = os.environ.get("S3_BUCKET", "")
S3_SOURCE_FILES = [
    os.path.join(PROJECT_DIR, part.strip())
    for part in os.environ.get("S3_SOURCE_FILES", "").split(",")
    if part.strip()
]

KB_EXECUTION_ROLE_ARN = os.environ.get("KB_EXECUTION_ROLE_ARN", "")
KB_NAME = os.environ.get("KB_NAME", "clab-knowledge-base")
DATA_SOURCE_NAME = os.environ.get("DATA_SOURCE_NAME", "clab-s3-source")
