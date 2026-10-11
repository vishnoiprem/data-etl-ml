# Section 13 — working code

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Companion to:** `../lecture_scripts/` (L60–L70)

This directory contains every CloudFormation template and the
Lambda handler source for section 13. Everything is runnable
end-to-end against a fresh AWS account.

## Layout

```
code/
├── README.md                              ← you are here
├── templates/
│   ├── 01_minimal_s3_bucket.yaml          ← L62 standalone
│   ├── 02_lambda_execution_role.yaml      ← L63 standalone
│   ├── 03_lambda_function.yaml            ← L64 standalone
│   ├── 04_rest_api_resources.yaml         ← L65 standalone
│   ├── 05_method_deployment.yaml          ← L66+L67 standalone
│   ├── 06_serverless_full_stack.yaml      ← L68 — the full e2e stack
│   ├── 07_serverless_with_parameters.yaml ← L69 — adds Parameters
│   └── 08_serverless_with_metadata.yaml   ← L70 — adds Metadata
├── lambdas/
│   ├── get_object.py                       ← packaged as zip
│   └── put_object.py                       ← packaged as zip
└── deploy.sh                              ← bash deploy script
```

## Prerequisites

- AWS account + AWS CLI v2 configured (`aws configure`).
- Python 3.11+ (just for the Lambda runtime — your local Python
  is only used for `zip` and `python -c yaml.safe_load` checks).
- `zip` CLI (`brew install zip` on macOS, `apt install zip` on
  Linux).
- An S3 bucket for CFN assets. The deploy script will create
  one if it does not exist.

## Quickstart — deploy the full stack

```bash
cd code
chmod +x deploy.sh
./deploy.sh dev
```

The script will:

1. Zip `lambdas/get_object.py` and `lambdas/put_object.py`.
2. `validate-template` on `08_serverless_with_metadata.yaml`.
3. Ensure the asset bucket exists.
4. `package` the template (uploads the zips to the asset bucket).
5. `deploy` with `EnvironmentName=dev`, an auto-generated
   `BucketName`, and `StageName=dev`.
6. Print the API URL and smoke-test PUT/GET on
   `/objects/hello.txt`.

### Deploy to staging or prod

```bash
./deploy.sh staging
./deploy.sh prod
```

Each invocation creates a separate stack with its own resources.

### Override the bucket name or region

```bash
BUCKET=serverless-uc2-prod-myname AWS_REGION=us-west-2 ./deploy.sh prod
```

The bucket name must be globally unique across AWS.

## Manual deploy (no helper script)

If you want to mirror what `deploy.sh` does:

```bash
cd code

# 1. zip the handlers
mkdir -p lambdas_pkg
zip -j lambdas_pkg/get_object.zip lambdas/get_object.py
zip -j lambdas_pkg/put_object.zip lambdas/put_object.py

# 2. validate
aws cloudformation validate-template \
  --template-body file://templates/08_serverless_with_metadata.yaml

# 3. ensure asset bucket
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
ASSET_BUCKET=serverless-cfn-assets-${ACCOUNT}-${AWS_REGION:-us-east-1}
aws s3 mb s3://${ASSET_BUCKET} || true

# 4. package
aws cloudformation package \
  --template-file templates/08_serverless_with_metadata.yaml \
  --s3-bucket ${ASSET_BUCKET} \
  --output-template-file /tmp/08.pkg.yaml

# 5. deploy
aws cloudformation deploy \
  --stack-name serverless-dev \
  --template-file /tmp/08.pkg.yaml \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --parameter-overrides \
      EnvironmentName=dev \
      BucketName=serverless-uc2-dev-<your-initials> \
      StageName=dev
```

## Teardown

```bash
# delete the stack (CFN will remove every resource except the
# asset bucket, which has DeletionPolicy: Retain)
aws cloudformation delete-stack \
  --stack-name serverless-dev

# optionally clean up the retained asset bucket
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
aws s3 rb s3://serverless-cfn-assets-${ACCOUNT}-${AWS_REGION:-us-east-1} --force
```

Repeat for each environment you deployed (`staging`, `prod`, etc.).

## Validating YAML locally (no AWS account needed)

If you want to sanity-check a template without hitting AWS:

```bash
python3 -c "import yaml,sys; yaml.safe_load(open('templates/08_serverless_with_metadata.yaml'))"
```

No output means it parsed. The deploy scripts also call
`validate-template` for a stricter (server-side) syntax check.

## Walk-through order

If you are following the lectures, deploy in order:

| Lecture | Deploy | Why |
|---|---|---|
| L62 | `templates/01_minimal_s3_bucket.yaml` | See the bucket exist |
| L63 | `templates/02_lambda_execution_role.yaml` --capabilities CAPABILITY_IAM | See the role + policy |
| L64 | `templates/03_lambda_function.yaml` --capabilities CAPABILITY_IAM | See the function |
| L65 | `templates/04_rest_api_resources.yaml` | See the resource tree |
| L66+L67 | `templates/05_method_deployment.yaml` --capabilities CAPABILITY_IAM | See the methods + permissions |
| L68 | `templates/06_serverless_full_stack.yaml` --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM | The full stack |
| L69 | `templates/07_serverless_with_parameters.yaml` --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM | Parameter-driven |
| L70 | `templates/08_serverless_with_metadata.yaml` --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM | Parameter-driven + Metadata |

After each deploy you can `aws cloudformation delete-stack
--stack-name <name>` to clean up. L68+ is the recommended end
state — L62–L67 are teaching artifacts.

## Customizing

- Change the region by exporting `AWS_REGION=...` before any
  command (the CLI default is `us-east-1`).
- Change runtime versions by editing the `Runtime: python3.11`
  field in `templates/03` and `06`–`08`. Lambda supports many
  runtimes.
- Add CORS by setting `AllowOrigins`, `AllowMethods`, and
  `AllowHeaders` on the API or by adding an
  `AWS::ApiGateway::Method` with `HttpMethod: OPTIONS`. The
  exercise in section 8 sets this up — it is a small addition.
- Add API Key + Usage Plan by adding an
  `AWS::ApiGateway::ApiKey` and `AWS::ApiGateway::UsagePlan` —
  the lecture in section 8 (L34) has the equivalent Lambda
  console walkthrough.

## License

Code MIT. Templates are CC-BY-4.0 for re-use in your own
projects.
