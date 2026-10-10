# L63 — AWS CloudFormation — Lambda Execution Role

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 13
> **Duration target:** 6:09
> **Lecture ID:** L63

## Prereqs

- L60 (CFN basics).
- L62 (S3 bucket) — so you understand the bucket we will grant
  access to.
- Familiarity with IAM concepts (trust policies vs permission
  policies) from section 2.

## Key terms

- **`AWS::IAM::Role`** — declares an IAM role. The
  `AssumeRolePolicyDocument` is the *trust* policy: who can use the
  role.
- **`AWS::IAM::Policy`** — declares an *inline* managed policy
  attached to one or more roles. For a small serverless app this is
  the simplest shape; for a big org you would use
  `AWS::IAM::ManagedPolicy` or attach an existing customer-managed
  policy.
- **`CAPABILITY_IAM`** — the CloudFormation capability flag you must
  pass when a template creates or modifies IAM resources. It
  confirms you know the template will be granting permissions.
- **Least privilege** — the principle of granting only the
  permissions the workload needs, scoped to the specific resource
  ARNs it needs them on.

## Lecture

L63 declares the IAM role that the Lambda function (L64) will
assume when it runs. The role has two halves:

1. **Trust policy** — "the `lambda.amazonaws.com` service principal
   is allowed to call `sts:AssumeRole` on this role." This is what
   lets Lambda's runtime swap the role's credentials into the
   container before invoking your handler.
2. **Permission policy** — "the role is allowed to call
   `s3:GetObject`, `s3:PutObject`, and `s3:ListBucket` on **one
   specific bucket** (and its objects), plus the CloudWatch Logs
   actions Lambda needs to write to a log group."

### The role

```yaml
LambdaExecutionRole:
  Type: AWS::IAM::Role
  Properties:
    RoleName: l63-lambda-exec-role
    AssumeRolePolicyDocument:
      Version: "2012-10-17"
      Statement:
        - Effect: Allow
          Principal:
            Service: lambda.amazonaws.com
          Action: sts:AssumeRole
```

`AssumeRolePolicyDocument` is a single-statement trust policy. The
`Service: lambda.amazonaws.com` is the magic value — the Lambda
service itself will call `sts:AssumeRole` when it spins up your
container, in exchange for temporary credentials that boto3 picks
up from the environment.

If you forget the `Service` principal and use `AWS: <account-id>`
or `AWS: "*"`, the deploy will succeed but the Lambda will fail at
runtime with `AccessDenied` when it tries to assume the role.

### The permission policy

```yaml
LambdaS3Policy:
  Type: AWS::IAM::Policy
  Properties:
    PolicyName: l63-lambda-s3-policy
    Roles:
      - !Ref LambdaExecutionRole
    PolicyDocument:
      Version: "2012-10-17"
      Statement:
        - Effect: Allow
          Action:
            - s3:GetObject
            - s3:PutObject
            - s3:ListBucket
          Resource:
            - !Sub "arn:aws:s3:::${BucketName}"
            - !Sub "arn:aws:s3:::${BucketName}/*"
        - Effect: Allow
          Action:
            - logs:CreateLogGroup
            - logs:CreateLogStream
            - logs:PutLogEvents
          Resource: "*"
```

#### Two-statement design

- **Statement 1 — S3 access, scoped to one bucket.** The
  `Resource` list is the canonical "bucket + objects" ARN pair
  (`arn:aws:s3:::name` for the bucket itself, `arn:aws:s3:::name/*`
  for the objects inside). You cannot put both actions and both
  resources in one statement and have IAM understand it; you have
  to list them out.
- **Statement 2 — CloudWatch Logs.** Lambda always needs
  `logs:CreateLogGroup`, `logs:CreateLogStream`, and
  `logs:PutLogEvents` or the runtime will refuse to start. We
  scope the resource to `"*"` because log groups are created on
  demand and you cannot predict the ARN in advance. This is the one
  place where `Resource: "*"` is the accepted industry pattern.

#### !Sub and the parameter

`!Sub "arn:aws:s3:::${BucketName}"` is a string-substitution
intrinsic function. At deploy time CloudFormation will replace
`${BucketName}` with the value of the `BucketName` parameter. This
is how you can re-use the same template against different buckets
in different environments.

`!Sub` also supports `${SomeResource}` and `${SomeResource.Attr}`
to inline other resource attributes. We use this trick in the
full-stack template.

### `CAPABILITY_IAM`

CloudFormation refuses to deploy a template that touches IAM
unless you explicitly opt in. This is a safety net — it forces you
to acknowledge that you are granting permissions.

```bash
aws cloudformation deploy \
  --stack-name l63-sandbox \
  --template-file templates/02_lambda_execution_role.yaml \
  --capabilities CAPABILITY_IAM
```

For the full-stack template (L68) we will need both
`CAPABILITY_IAM` and `CAPABILITY_NAMED_IAM` because we use
`RoleName:` and `PolicyName:` (named IAM resources).

### Validate the role by attaching it to a real Lambda

You cannot really test the role in isolation — IAM is a permission
boundary, not a behavior. We will see it work in L64 when we
attach it to a Lambda and invoke the function against a real
bucket.

If you want to be thorough between L63 and L64, you can attach
the role to a manually-created Lambda in the console and invoke
it with a test event. The deploy will succeed even if the role
later turns out to be wrong, which is why we write the Lambda
*and* the role in the same stack.

## Hands-on

1. `aws cloudformation validate-template --template-body file://templates/02_lambda_execution_role.yaml`
2. `aws cloudformation deploy --stack-name l63-sandbox --template-file templates/02_lambda_execution_role.yaml --capabilities CAPABILITY_IAM`
3. `aws iam get-role --role-name l63-lambda-exec-role` — confirm
   the role exists.
4. `aws iam list-attached-role-policies --role-name l63-lambda-exec-role` —
   the inline policy is not shown by `list-attached-role-policies`
   (that only shows AWS-managed and customer-managed attached
   policies). Use `aws iam list-role-policies --role-name l63-lambda-exec-role`
   to see the inline policy name `l63-lambda-s3-policy`.
5. Tear it down: `aws cloudformation delete-stack --stack-name l63-sandbox`

## Quiz prep

- The difference between `AssumeRolePolicyDocument` (trust policy)
  and `PolicyDocument` (permission policy).
- Why we need `CAPABILITY_IAM` (and `CAPABILITY_NAMED_IAM`) when
  deploying templates that touch IAM.
- The two-resource ARN pattern for S3 (`bucket` and `bucket/*`).
- Why the `logs:*` actions have `Resource: "*"`.

## Further reading

- [`AWS::IAM::Role` reference](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-iam-role.html)
- [Lambda execution role](https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html)
- [IAM least privilege](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#grant-least-privilege)
