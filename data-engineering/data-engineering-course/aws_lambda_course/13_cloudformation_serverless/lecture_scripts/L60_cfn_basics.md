# L60 — Optional — AWS CloudFormation Basics

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 13
> **Duration target:** 2:29
> **Lecture ID:** L60

## Prereqs

- AWS account + AWS CLI v2 configured.
- Familiarity with at least one AWS service (S3, IAM, Lambda, or API
  Gateway — we will use all of them in this section).

## Key terms

- **Stack** — a collection of AWS resources managed as a single unit.
  Created, updated, and deleted together.
- **Template** — a JSON or YAML file that describes the desired state
  of the stack.
- **Resource** — the smallest deployable unit in a template
  (e.g. `AWS::S3::Bucket`, `AWS::Lambda::Function`).
- **Change set** — a preview of the changes CloudFormation would make
  to a stack, before you actually apply them.
- **Drift** — the state where the real resources no longer match the
  template (usually because someone clicked in the console).

## Lecture

CloudFormation is AWS's native **Infrastructure as Code (IaC)**
service. You write a template that declares the AWS resources you
want; CloudFormation figures out the right order to create, update,
or delete them, and tracks the state so it can roll back if anything
fails.

A template has six top-level sections. You will use all of them in
this section.

| Section | Purpose |
|---|---|
| `AWSTemplateFormatVersion` | Optional. The template version. `2010-09-09` is current. |
| `Description` | Optional. A short human-readable summary. |
| `Parameters` | Inputs the user supplies at deploy time (e.g. `BucketName`, `StageName`). |
| `Mappings` | Static lookup tables (e.g. region → AMI). |
| `Conditions` | Boolean expressions that gate whether a resource is created. |
| `Resources` | **Required.** The actual AWS resources to provision. |
| `Outputs` | Values to surface back to the user (e.g. the API URL). |
| `Metadata` | Extra info for tools, the console wizard, or the `cfn-lint` plugin. |

**The six primitive building blocks** you will use in this section
are `Resources`, `Parameters`, `Outputs`, `Mappings`, `Conditions`,
and `Metadata`. Plus one workflow concept: **change sets**.

### Resources

Every resource is a typed block. The type name tells CloudFormation
which AWS service to call and which API to use.

```yaml
Resources:
  MyBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: my-cfn-bucket
```

The `Type` is fixed (the `AWS::S3::Bucket` part). The `Properties`
schema depends on the type — you can look it up in the
[CloudFormation Resource Specification](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-template-resource-spec.html).

### Parameters

Make the template reusable across environments. The user is prompted
for the value when they run `aws cloudformation deploy` (or click
through the console).

```yaml
Parameters:
  BucketName:
    Type: String
    Default: my-default-bucket
    AllowedPattern: "^[a-z0-9-]+$"
    Description: Lowercase S3 bucket name.
```

### Outputs

Surface values you care about (URLs, ARNs, IDs) so a CI script or
the console can read them back after deploy.

```yaml
Outputs:
  BucketArn:
    Value: !GetAtt MyBucket.Arn
    Export:
      Name: MyBucketArn
```

### Mappings and Conditions

`Mappings` are static lookup tables. `Conditions` are boolean
expressions (`!Equals`, `!And`, `!Or`, `!Not`, `!If`) you can use
to gate resource creation — e.g. only create a high-availability
resource when `Environment` is `prod`.

### Intrinsic functions

The `!Ref`, `!GetAtt`, `!Sub`, `!Join`, `!If`, `!FindInMap` family
lets you stitch resources together inside the template without
hard-coding values.

### Change sets

Before updating a live stack, generate a **change set** to preview
which resources will be added, modified, or replaced. This is the
IaC equivalent of a code diff.

```bash
aws cloudformation create-change-set \
  --stack-name my-stack \
  --template-body file://template.yaml \
  --change-set-name my-cs \
  --capabilities CAPABILITY_IAM

aws cloudformation describe-change-set \
  --stack-name my-stack \
  --change-set-name my-cs
```

If it looks good, `execute-change-set`. If not, `delete-change-set`
and edit the template.

## Hands-on

In this section's `code/` directory you will see eight templates
numbered 01–08. L62–L67 each introduce one resource type and ship a
standalone template that you can validate and deploy by itself:

```bash
cd 13_cloudformation_serverless/code
aws cloudformation validate-template \
  --template-body file://templates/01_minimal_s3_bucket.yaml
aws cloudformation deploy \
  --stack-name l60-sandbox \
  --template-file templates/01_minimal_s3_bucket.yaml
```

L68 wires them all together. L69 adds `Parameters`. L70 adds
`Metadata`.

## Quiz prep

- The six top-level template sections.
- The difference between `!Ref` and `!GetAtt`.
- What a change set is and when you would use one.

## Further reading

- [AWS CloudFormation User Guide](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/Welcome.html)
- [Resource Specification](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-template-resource-spec.html)
- [`cfn-lint` for VS Code](https://marketplace.visualstudio.com/items?itemName=kddejong.vscode-cfn-lint)
