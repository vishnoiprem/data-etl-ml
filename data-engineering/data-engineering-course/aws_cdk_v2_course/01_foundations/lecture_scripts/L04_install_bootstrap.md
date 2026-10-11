---
lecture: L04
title: "Installing and bootstrapping CDK (Node, AWS CLI, cdk bootstrap)"
duration: "12:00"
section: 1
prereqs: ["L03"]
---

# L04 — Installing and Bootstrapping CDK

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 1 — Foundations
> **Duration:** 12:00

## Prereqs

L03 — CDK v2 architecture

## Key terms

- **`cdk bootstrap`** — a one-time command per AWS account/region
  that creates the S3 bucket + IAM role CDK uses to deploy templates.
- **Bootstrap stack** — the CloudFormation stack created by
  `cdk bootstrap`. Named `CDKToolkit` by default.
- **`aws sts get-caller-identity`** — the canonical sanity check
  for "are my AWS creds working?"
- **`cdk doctor`** — a built-in self-check that flags common
  misconfigurations (wrong Node version, missing creds, etc).

## Lecture

CDK has two install surfaces: the **CLI** (global) and the
**library** (per project). Get the CLI first; we'll create our first
project in L07.

```bash
# 1. Node 20+ (recommended) — install via nvm or your package manager
nvm install 20
node --version                      # v20.x

# 2. AWS CLI v2 + credentials
aws --version
aws configure                       # enter access key, secret, region
aws sts get-caller-identity         # must succeed

# 3. The CDK CLI itself
npm install -g aws-cdk
cdk --version                       # 2.140.x or later

# 4. Self-check
cdk doctor
```

Then the **bootstrap** step. CDK uses an S3 bucket + IAM role in
your account to hold the synthesized templates and the Lambda
functions that copy assets into S3 during deploy. The first time you
run `cdk deploy` against a new account/region, you'll be told the
environment isn't bootstrapped:

```bash
$ cdk deploy
# 👇 you do NOT see this; cdk will offer to run it for you
$ cdk bootstrap aws://123456789012/us-east-1
```

`cdk bootstrap` is **idempotent** — running it twice is a no-op. It
is also free (the bucket and role cost nothing).

```bash
# Tell CDK which account/region to bootstrap:
cdk bootstrap aws://<account-id>/<region>
# or just trust the CLI profile:
cdk bootstrap
```

After bootstrap, your account has a stack called `CDKToolkit` in the
region. Don't delete it; CDK won't be able to deploy until you
re-run bootstrap.

## Hands-on

```bash
# 1. Verify Node
node --version

# 2. Verify AWS creds
aws sts get-caller-identity

# 3. Install CDK CLI
npm install -g aws-cdk

# 4. Self-check
cdk doctor

# 5. Bootstrap your account/region
cdk bootstrap
```

If `cdk doctor` reports any red flags, fix them before continuing.
The most common one is "AWS credentials not configured" — run
`aws configure` again.

## Quiz prep

- What does `cdk bootstrap` create? (S3 bucket + IAM role)
- How do you check that AWS credentials are working?
- Is `cdk bootstrap` idempotent? (yes)
- What CLI command checks your CDK install? (`cdk doctor`)

## Further reading

- [CDK bootstrapping](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html)
- Next up: **Section 2 — App, Stack, Construct (L05+)**
