# Assignment 5 — CloudFormation Template From Scratch (VPC + EC2 + IAM + S3)

> **Section:** 13 (CloudFormation) — but **do not open** any of the L60–L70 lecture files until after you submit your first draft.
> **Estimated time:** 6 hours
> **Deliverable:** A single `template.yaml` that provisions a VPC, public subnet, EC2 instance, IAM role, security group, and S3 bucket with a bucket policy. Plus `parameters.md` and `outputs.md` tables.
> **Author:** Prem Vishnoi <prem.vishnoi@example.com>

## Learning objectives

By the end of this assignment you will be able to:

1. Author a CloudFormation template from memory using only the [AWS resource specification](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-template-resource-type-ref.html) as a reference.
2. Wire **parameters** with `AllowedValues`, `Default`, `ConstraintDescription`, and `Type` correctly.
3. Wire **outputs** with `Export` names, `Description`, and `Value`.
4. Use **`Ref`**, **`Fn::GetAtt`**, **`!Sub`**, and **`Fn::Join`** to express dependencies.
5. Use **`Metadata`** to add `AWS::CloudFormation::Interface` for parameter group ordering in the console.
6. Validate the template with `cfn-lint` and `aws cloudformation validate-template` and deploy it.

## Background

Section 13 lectures L60–L70 show you how to use CloudFormation to express a serverless use case. This assignment is the inverse: you have to write a **non-serverless** template (VPC + EC2) from scratch. The point is to make sure you can reach for CloudFormation outside the serverless comfort zone.

The template must provision:

| Resource | Notes |
|---|---|
| **VPC** | `10.0.0.0/16`, DNS support + DNS hostnames enabled, tags. |
| **Public subnet** | `10.0.1.0/24`, in a single AZ, with `MapPublicIpOnLaunch: true`. |
| **Internet gateway** | attached to the VPC. |
| **Route table** | default route to the IGW, associated with the public subnet. |
| **Security group** | allows inbound 22 from a configurable CIDR, allows all outbound. |
| **IAM role** | EC2 assume role, managed policy `AmazonS3ReadOnlyAccess` attached. |
| **IAM instance profile** | wraps the role for EC2 use. |
| **EC2 instance** | `t3.micro`, Amazon Linux 2023, in the public subnet, with the profile, `UserData` that `aws s3 ls`s the bucket. |
| **S3 bucket** | name parameterised, versioning enabled, public access blocked, lifecycle rule (30d -> STANDARD_IA, 90d -> GLACIER). |
| **S3 bucket policy** | allows the EC2 role to `s3:GetObject` and `s3:ListBucket` on the bucket ARN. |

## Step-by-step tasks

### Step 1 — Set up the directory

```
cfn_from_scratch/
├── template.yaml
├── parameters.md
├── outputs.md
└── README.md
```

### Step 2 — Write `template.yaml` from scratch

Constraints:

- `AWSTemplateFormatVersion: '2010-09-09'`
- `Description:` line summarising what the stack creates.
- **Parameters** at the top:
  - `EnvironmentName` (String, default `dev`, allowed `dev`/`stg`/`prd`).
  - `InstanceType` (String, default `t3.micro`, allowed the `t3.*` family).
  - `BucketName` (String, must be lowercase, no underscores, 3-63 chars, regex constraint).
  - `SshCidr` (String, default `0.0.0.0/0`, ConstraintDescription warning).
  - `KeyPairName` (String, no default, description "EC2 KeyPair for SSH").
- **Metadata** block with `AWS::CloudFormation::Interface` so the console groups parameters in the right order and labels them.
- **Mappings** for AZ selection (use `AWS::Region` map of `us-east-1` -> `us-east-1a`, etc.).
- **Resources** as listed above. Use `!Ref` and `!GetAtt` for cross-references. Use `!Sub` for ARNs.
- **Outputs**:
  - `VpcId` (export `VpcId-<env>`)
  - `PublicSubnetId`
  - `InstanceId`
  - `InstancePublicIp`
  - `BucketName`
  - `RoleArn`

The `UserData` must use `Fn::Base64` and write `/var/log/user-data.log` for debugging. Use `aws --region ${AWS::Region} s3 ls s3://${BucketName}` as a smoke test.

### Step 3 — Validate

```bash
cfn-lint template.yaml
aws cloudformation validate-template --template-body file://template.yaml \
  --query 'Parameters[].ParameterKey'
```

`cfn-lint` must pass with **zero warnings**. `validate-template` must succeed.

### Step 4 — Deploy

```bash
aws cloudformation create-stack \
  --stack-name cfn-from-scratch \
  --template-body file://template.yaml \
  --parameters \
      ParameterKey=EnvironmentName,ParameterValue=dev \
      ParameterKey=BucketName,ParameterValue=cfnfs-dev-<your-initials>-2026 \
      ParameterKey=KeyPairName,ParameterValue=<your-keypair> \
  --tags Purpose=CourseAssignment Owner=<you> \
  --capabilities CAPABILITY_NAMED_IAM
aws cloudformation wait stack-create-complete --stack-name cfn-from-scratch
```

### Step 5 — Verify

```bash
aws ec2 describe-instances \
  --filters Name=tag:aws:cloudformation:stack-name,Values=cfn-from-scratch \
  --query 'Reservations[].Instances[].[InstanceId,PublicIpAddress,State.Name]'
aws s3api get-bucket-versioning --bucket cfnfs-dev-<initials>-2026
aws s3api get-bucket-policy --bucket cfnfs-dev-<initials>-2026
```

Then SSH into the instance and run:

```bash
aws s3 ls s3://cfnfs-dev-<initials>-2026
# must succeed (proves the IAM role + bucket policy are wired)
```

### Step 6 — Document parameters and outputs

`parameters.md`: a table with `LogicalId`, `Type`, `Default`, `AllowedValues` (if any), `Description`, `ConstraintDescription` (if any).

`outputs.md`: a table with `LogicalId`, `Description`, `Value` (use `!Sub` placeholders), `Export.Name`.

### Step 7 — Change-set discipline

Edit the template to change the `InstanceType` from `t3.micro` to `t3.small`. **Do not create a new stack.** Use a change set:

```bash
aws cloudformation create-change-set \
  --stack-name cfn-from-scratch \
  --change-set-name bump-instance-type \
  --template-body file://template.yaml \
  --parameters ParameterKey=InstanceType,UsePreviousValue=false,ParameterValue=t3.small \
               ParameterKey=EnvironmentName,UsePreviousValue=true \
               ParameterKey=BucketName,UsePreviousValue=true \
               ParameterKey=KeyPairName,UsePreviousValue=true
aws cloudformation describe-change-set --stack-name cfn-from-scratch --change-set-name bump-instance-type
aws cloudformation execute-change-set --stack-name cfn-from-scratch --change-set-name bump-instance-type
aws cloudformation wait stack-update-complete --stack-name cfn-from-scratch
```

Note: `BucketName` cannot be changed without replacement; the change set will report `No replacement` for `InstanceType` and a `Replacement: False` action.

### Step 8 — Cleanup

```bash
aws cloudformation delete-stack --stack-name cfn-from-scratch
aws s3 rb s3://cfnfs-dev-<initials>-2026 --force   # if non-empty
```

## Deliverables

- [ ] `template.yaml` (single file, < 400 lines, no `TODO`).
- [ ] `parameters.md` (table).
- [ ] `outputs.md` (table).
- [ ] `README.md` (Architecture, Prereqs, Deploy, Verify, Change-set example, Cleanup).
- [ ] `cfn-lint` output (must show "no violations").
- [ ] `aws cloudformation describe-stack-events` tail showing `CREATE_COMPLETE` and `UPDATE_COMPLETE`.

## Grading rubric (100 points)

| Category | Points | What we look for |
|---|---|---|
| Template validity (cfn-lint) | 20 | Zero warnings. |
| Resource coverage | 25 | All nine resources present and correctly wired. |
| Parameters | 15 | All five parameters with the right constraints and Metadata grouping. |
| Outputs + Exports | 10 | All six outputs, with `Export.Name` and `Description`. |
| Bucket policy | 10 | Allows the EC2 role to read, denies anonymous access. |
| Change-set exercise | 10 | `bump-instance-type` change set executes without error. |
| README + tables | 10 | Has all sections, parameters and outputs in tabular form. |

Deductions:

- `-10` per missing resource from the table.
- `-5` if `Parameters` are not grouped via `AWS::CloudFormation::Interface`.
- `-5` per `TODO` or `placeholder` comment.

## Stretch goals (optional, +10 each, capped at +20)

- Add a **WaitCondition** that the EC2 instance signals when the `aws s3 ls` smoke test passes; fail the stack if it doesn't signal in 5 minutes.
- Add a **NestedStack** that owns the IAM role and bucket policy; reference its outputs from the parent.
- Add a **custom resource** (Lambda-backed) that posts the instance ID to a webhook (e.g., a Discord channel) on every create/update.
- Parameterize the **AMI ID** via an `SSM Parameter` lookup (`{{resolve:ssm:/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.1-x86_64}}`).
