import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load .env from the SAME FOLDER as this script
script_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(script_dir, '.env')
load_dotenv(dotenv_path)

# Read from .env
role_name = os.getenv('ROLE_NAME', '')
access_key_id = os.getenv('AWS_ACCESS_KEY_ID', '')
secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY', '')
region = os.getenv('AWS_REGION', 'us-east-1')

# Validate
if not all([role_name, access_key_id, secret_access_key]):
    raise ValueError(
        f"Missing credentials in {dotenv_path}. "
        "Required: ROLE_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY"
    )

# Create IAM client
iam_client = boto3.client(
    "iam",
    region_name=region,
    aws_access_key_id=access_key_id,
    aws_secret_access_key=secret_access_key
)

try:
    role = iam_client.get_role(RoleName=role_name)
    print(f"Role '{role_name}' exists. ARN: {role['Role']['Arn']}")

except ClientError as e:
    error_code = e.response['Error']['Code']

    if error_code == 'NoSuchEntity':
        print(f"Role '{role_name}' does not exist. Creating...")
        setuproles()  # Make sure this function is defined
    elif error_code == 'AccessDenied':
        print(f"Access denied. Check your IAM permissions.")
    else:
        print(f"Error: {e}")