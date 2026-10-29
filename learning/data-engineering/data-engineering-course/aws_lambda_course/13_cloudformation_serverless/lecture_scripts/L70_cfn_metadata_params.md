# L70 — AWS CloudFormation — End to End with Metadata and Parameters Section

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 13
> **Duration target:** 4:34
> **Lecture ID:** L70

## Prereqs

- L69 (parameters working).

## Key terms

- **`Metadata`** — top-level template section for information that
  is not part of the resource graph. Used by tools, the console
  wizard, and `cfn-lint`.
- **`AWS::CloudFormation::Interface`** — the most common
  metadata key. Tells the console how to group + label parameters
  in the "Specify stack details" wizard.
- **`ParameterGroups`** — the order and grouping. Each group is
  rendered as a collapsible section with a `Label`.
- **`ParameterLabels`** — overrides the `Description` text in the
  console with a friendlier label.

## Lecture

The L69 template works perfectly when you deploy with
`--parameter-overrides` (or a parameter file). But if a human
runs it through the console, they get a flat list of three
parameters with their `Description` strings. Hard to scan, easy
to put a value in the wrong field.

L70 adds the `Metadata` section with
`AWS::CloudFormation::Interface` to:

1. Group the parameters into collapsible sections.
2. Override the inline `Description` with a friendlier label.
3. Establish a sensible order (`Environment` first, `Storage`
   second).

This is a **cosmetic** change. The deployed resources are
identical. The improvement is the human experience of running
the template in the console wizard.

### The Metadata block

```yaml
Metadata:
  AWS::CloudFormation::Interface:
    ParameterGroups:
      - Label:
          default: "Environment"
        Parameters:
          - EnvironmentName
          - StageName
      - Label:
          default: "Storage"
        Parameters:
          - BucketName
    ParameterLabels:
      EnvironmentName:
        default: "Which environment is this?"
      BucketName:
        default: "S3 bucket for the Lambda"
      StageName:
        default: "API Gateway stage"
```

#### `ParameterGroups`

Each entry in `ParameterGroups` is one collapsible section in the
console. The `Label.default` is the section heading (a plain
string, not a reference). The `Parameters` list is the parameters
that go inside.

Groups are rendered **in the order they are listed**, and
parameters are rendered in the order they appear inside each
group. So the wizard order becomes:

1. **Environment**
   - EnvironmentName
   - StageName
2. **Storage**
   - BucketName

Compare to L69 where the order is just the order in which the
parameters were declared (a less semantic ordering).

#### `ParameterLabels`

The `ParameterLabels` map overrides the `Description` of each
parameter in the console with a friendlier label. We still keep
the `Description` in the parameter declaration because:

- The label is the *prompt* the user sees next to the field.
- The description is the *helper text* that appears below the
  field.

In template 08 we have both: the `Description` in the
`Parameters` block stays as the formal documentation, and the
`ParameterLabels` override adds a more conversational prompt
in the console.

#### Other metadata keys

`AWS::CloudFormation::Interface` is the only metadata key AWS
itself reads. Other keys are tool-specific:

- `cfn-lint` reads metadata to apply custom rules.
- Custom CI scripts sometimes read metadata to surface stack
  documentation in pull-request bots.
- `Metadata: Comment` is a free-form key you can use to drop
  notes in the template.

You do not need any of these for this course, but it is good to
know they exist.

### Deploy

The deploy is the same as L69 — Metadata is purely a
console/UI directive:

```bash
aws cloudformation package \
  --template-file templates/08_serverless_with_metadata.yaml \
  --s3-bucket <cfn-assets-bucket> \
  --output-template-file /tmp/08.pkg.yaml

aws cloudformation deploy \
  --stack-name serverless-stack-metadata \
  --template-file /tmp/08.pkg.yaml \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --parameter-overrides \
      EnvironmentName=dev \
      BucketName=serverless-uc2-dev-<your-initials> \
      StageName=dev
```

To see the metadata effect:

1. Open the CloudFormation console.
2. Click "Create stack" -> "With new resources (standard)".
3. Upload `templates/08_serverless_with_metadata.yaml`.
4. Click "Next" — the "Specify stack details" page will show the
   two grouped sections with the labels we set.

### When to bother with Metadata

- **Always** for templates that humans run through the console
  (Quick Starts, internal tooling).
- **Optional** for templates that are 100% CLI/CI — the labels do
  not appear in `--parameter-overrides` mode.
- **Skip** for templates with only one or two parameters — the
  grouping adds value only when there are several.

### The complete template pack

After L70 you have a full progression:

| Template | What it adds |
|---|---|
| 01 | L62 standalone — S3 bucket only |
| 02 | L63 standalone — IAM role + policy only |
| 03 | L64 standalone — Lambda function (with role + bucket as params) |
| 04 | L65 standalone — REST API + 2 resources |
| 05 | L66 + L67 standalone — full method + deployment + permission |
| 06 | L68 — full e2e stack, hard-coded bucket name |
| 07 | L69 — full stack + Parameters |
| 08 | L70 — full stack + Parameters + Metadata |

Templates 06–08 are deployable end-to-end. Templates 01–05 are
*teaching* artifacts. The `code/deploy.sh` script targets
template 08 by default.

## Hands-on

1. Open `templates/08_serverless_with_metadata.yaml` and re-read
   the `Metadata` block.
2. Run `code/deploy.sh` end-to-end against this template.
3. Re-open the template in the console wizard to see the grouped
   parameters.
4. Try removing the `Metadata` block and re-loading the
   template — observe the difference in the wizard.
5. Tear the stack down.

## Quiz prep

- The two halves of `AWS::CloudFormation::Interface`
  (`ParameterGroups` and `ParameterLabels`).
- Why `Metadata` is a UX/console feature and not a resource
  declaration.
- The difference between `Label` (group heading) and
  `ParameterLabels` (per-parameter prompt).
- When to skip `Metadata` (single-parameter or CLI-only
  templates).

## Further reading

- [AWS::CloudFormation::Interface metadata key](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-cloudformation-interface.html)
- [Template anatomy — Metadata](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-anatomy.html)
