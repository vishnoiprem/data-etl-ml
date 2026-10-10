# L69 — AWS CloudFormation — End to End with Parameters Section

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 13
> **Duration target:** 8:55
> **Lecture ID:** L69

## Prereqs

- L68 (full-stack template deploys end to end).

## Key terms

- **`Parameters`** — the section of a CFN template that declares
  inputs the user supplies at deploy time.
- **Type constraint** — `String`, `Number`, `List<Number>`,
  `CommaDelimitedList`, or one of the AWS-specific types like
  `AWS::EC2::VPC::Id` (which makes the console show a dropdown
  of your VPCs).
- **`Default`** — the value the console wizard and `deploy` will
  use if the user supplies nothing. Optional but very common.
- **`AllowedValues` / `AllowedPattern`** — validation. The deploy
  fails fast with a clear error if the value violates the rule.
- **`NoEcho`** — replaces the value with `***` in the console and
  in stack outputs. Use this for parameters that hold secrets.
- **Pseudo parameters** — `AWS::AccountId`, `AWS::Region`,
  `AWS::StackName`, `AWS::URLSuffix`. They are available in any
  template without being declared in `Parameters`.

## Lecture

The L68 template hard-codes the bucket name and stage. That
worked for one deploy. In real life you need the same template to
spin up `dev`, `staging`, and `prod` with different names — that
is the job of the `Parameters` section.

L69 introduces three parameters — `EnvironmentName`,
`BucketName`, and `StageName` — and threads them through the
template with `!Ref` and `!Sub`. The standalone template is
`templates/07_serverless_with_parameters.yaml`.

### The Parameters block

```yaml
Parameters:
  EnvironmentName:
    Type: String
    AllowedValues:
      - dev
      - staging
      - prod
    Default: dev
    Description: Deployment environment.

  BucketName:
    Type: String
    Description: S3 bucket the Lambda reads/writes.
    AllowedPattern: "^[a-z0-9][a-z0-9-]{2,62}$"
    ConstraintDescription: Lowercase letters, digits, and dashes. 3-63 chars.

  StageName:
    Type: String
    Default: prod
    AllowedPattern: "^[a-z0-9]+$"
    Description: API Gateway stage.
```

#### `EnvironmentName`

`Type: String` + `AllowedValues` is the simplest validation
pattern. The deploy command will fail with a clear "Parameter
EnvironmentName must be one of: dev, staging, prod" if the user
supplies `qa` or `Dev` (note: the check is case-sensitive).

#### `BucketName`

`AllowedPattern` is a regex the value must match. The pattern
above is the S3 bucket-naming rule: lowercase letters, digits,
dashes, 3–63 characters, must start with a letter or digit. If
the user supplies a value that violates it, CloudFormation
returns `ConstraintDescription` verbatim in the error message —
this is a great place to put a human-readable explanation.

For S3 you can also use `Type: String` with
`AllowedPattern: "^[a-z0-9][a-z0-9-]{2,62}$"` and a custom
error. We do not use `AWS::S3::Bucket::Name` (it does not exist
as a parameter type) so we keep the pattern.

#### `StageName`

`Default: prod` — if the user omits the parameter, the value
becomes `prod`. `AllowedPattern` enforces a single token
(lowercase alphanumerics) because API Gateway stage names cannot
contain `/` or uppercase letters.

#### `NoEcho` for secrets

If you add a parameter for a database password or third-party API
key, set `NoEcho: true`. The value is masked in the console and
in stack outputs. Note that `NoEcho` is **not** a security
control by itself — it just hides the value from casual viewing.
For real secrets, store them in AWS Secrets Manager or SSM
Parameter Store and reference the secret ARN, not the value.

### Threading parameters through the template

The rest of the template is a study in `!Ref` and `!Sub`.

#### Bucket name

```yaml
ServerlessBucket:
  Type: AWS::S3::Bucket
  Properties:
    BucketName: !Ref BucketName
```

`!Ref BucketName` resolves the parameter to a string and uses it
as the bucket name. If the bucket already exists (because
another stack in the same account owns the same name) the
deploy fails with `BucketAlreadyExists`.

#### IAM role and policy names

```yaml
RoleName: !Sub "serverless-${EnvironmentName}-lambda-exec"
PolicyName: !Sub "serverless-${EnvironmentName}-s3-policy"
```

`!Sub` is the only way to mix static strings and parameter
references. The result for `EnvironmentName=prod` is
`serverless-prod-lambda-exec`.

#### Lambda function names

```yaml
FunctionName: !Sub "serverless-${EnvironmentName}-get-object"
```

Same trick. Each environment gets its own Lambda, its own IAM
role, its own role policy, its own S3 bucket, its own API — all
from one template.

#### Lambda env var

```yaml
Environment:
  Variables:
    BUCKET_NAME: !Ref ServerlessBucket
    ENVIRONMENT: !Ref EnvironmentName
```

The Lambda reads `BUCKET_NAME` at runtime via `os.environ` to
know which bucket to read/write. We also pass `ENVIRONMENT` so
the handler can log it (and so downstream services can
distinguish dev vs prod traffic in CloudWatch).

#### Asset bucket

```yaml
CodeAssetsBucket:
  Type: AWS::S3::Bucket
  Properties:
    BucketName: !Sub "serverless-cfn-assets-${EnvironmentName}-${AWS::AccountId}-${AWS::Region}"
```

`AWS::AccountId` and `AWS::Region` are pseudo-parameters —
always available, no need to declare them. Including them in
the asset-bucket name guarantees uniqueness across accounts and
regions.

#### Tags

```yaml
Tags:
  - Key: environment
    Value: !Ref EnvironmentName
  - Key: course
    Value: aws-lambda-serverless
```

Every resource that accepts a `Tags` block gets an `environment`
tag. This is how AWS billing groups cost by environment, and how
the Resource Groups console can filter by environment.

### Deploying to multiple environments

The point of parameters is being able to deploy the same template
many times:

```bash
# dev
aws cloudformation deploy --stack-name serverless-dev \
  --template-file /tmp/07.pkg.yaml \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --parameter-overrides \
      EnvironmentName=dev \
      BucketName=serverless-uc2-dev-<initials> \
      StageName=dev

# prod
aws cloudformation deploy --stack-name serverless-prod \
  --template-file /tmp/07.pkg.yaml \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --parameter-overrides \
      EnvironmentName=prod \
      BucketName=serverless-uc2-prod-<initials> \
      StageName=prod
```

You now have two stacks with completely separate resources but
identical topology. That is the whole point of IaC.

### Parameter files (CI/CD)

For a CI pipeline you can also pass a file:

```bash
aws cloudformation deploy --stack-name serverless-prod \
  --template-file /tmp/07.pkg.yaml \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --parameters-file prod-params.json
```

`prod-params.json`:

```json
[
  {"ParameterKey": "EnvironmentName", "ParameterValue": "prod"},
  {"ParameterKey": "BucketName",      "ParameterValue": "serverless-uc2-prod"},
  {"ParameterKey": "StageName",       "ParameterValue": "prod"}
]
```

This is the canonical way to wire the template to a CI/CD
pipeline that already has the parameter values from a secrets
store.

## Hands-on

1. Deploy `07_serverless_with_parameters.yaml` to `dev` with a
   bucket name that includes your initials.
2. Deploy it again to `prod` with a different bucket name and
   the `prod` stage. Confirm both stacks are visible in
   `aws cloudformation list-stacks`.
3. Compare the two stack outputs — `ApiUrl`, `BucketName`,
   `EnvironmentName` — they will all be different.
4. Try deploying with `EnvironmentName=qa` and confirm the
   `AllowedValues` validation rejects it.
5. Tear both stacks down. The two buckets are not auto-deleted
   if they are non-empty; empty them first or pass
   `--force-delete-bucket` if you used the asset-bucket trick.

## Quiz prep

- The four parameter properties most commonly used (`Type`,
  `Default`, `AllowedValues`, `AllowedPattern`).
- The difference between `!Ref` and `!Sub` in a property value.
- Why `AWS::AccountId` and `AWS::Region` are pseudo-parameters.
- Why `NoEcho` is a UX feature, not a security control.
- How parameters and parameter files interact with
  `aws cloudformation deploy`.

## Further reading

- [Parameters](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/parameters-section-structure.html)
- [AWS-specific parameter types](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/parameters-section-structure.html#parameters-section-structure-attribute-type)
- [Pseudo parameters](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-ref.html#intrinsic-function-reference-ref-params)
