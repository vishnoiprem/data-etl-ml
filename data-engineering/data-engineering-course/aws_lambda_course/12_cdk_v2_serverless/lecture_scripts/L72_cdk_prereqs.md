---
title: L72 — AWS CDK v2 — Pre-requisites
author: Prem Vishnoi <pvishnoi@avilx.com>
section: 12
duration: 9:27
---

# L72 — AWS CDK v2 — Pre-requisites

> **Section:** 12 — AWS CDK v2
> **Duration target:** 9:27
> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

## Prereqs

- L71 — understand what CDK is, what `cdk synth` does, and what the
  app/stack/construct model looks like.
- An AWS account you can deploy into (free tier is enough).
- A working terminal on macOS, Linux, or Windows (we use bash in the
  examples; PowerShell equivalents are noted where they matter).

## Key terms

- **Node.js** — JavaScript runtime. CDK requires Node 18+; this course
  uses Node 20 LTS because the Lambda runtime is also Node 20.
- **npm** — the Node package manager that ships with Node.
- **AWS CDK CLI (`aws-cdk` or `cdk`)** — the command-line tool that runs
  `synth`, `bootstrap`, `deploy`, `diff`, and `destroy`.
- **`cdk bootstrap`** — one-time command that creates the
  `cdk-<account>-<region>-assets` S3 bucket and the
  `cdk-<account>-<region>-file-publishing-role` IAM role. Without
  bootstrap, `cdk deploy` fails the first time.
- **Credentials chain** — the order in which the SDK/CDK looks for
  credentials: environment variables → `~/.aws/credentials` profile → EC2
  instance profile → ECS task role → EKS Pod Identity.

## Lecture

### The four pre-requisites, in order

1. **Node.js 20 LTS and npm 10+.** CDK v2 runs on Node 18+ but Node 20 is
   the current LTS and matches the Lambda runtime we use in section 12.
2. **The AWS CDK CLI** — `npm install -g aws-cdk`. This installs the
   `cdk` binary (or `aws-cdk` on some systems) on your `PATH`.
3. **AWS credentials** in the `default` profile (or whichever profile
   you point CDK at). Easiest: `aws configure sso` for AWS IAM Identity
   Center, or `aws configure` for long-lived access keys.
4. **`cdk bootstrap`** — one-time, per AWS account and per region. We
   run it in `us-east-1` to match the default region the project ships
   with.

### Step 1 — Install Node.js 20

Check what is already installed:

```bash
node --version    # expect v20.x or higher
npm --version     # expect 10.x or higher
```

If you do not have Node 20, install it with the official installer from
[nodejs.org](https://nodejs.org/) or with a version manager:

```bash
# macOS / Linux (nvm)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
nvm install 20
nvm use 20
nvm alias default 20

# macOS (Homebrew)
brew install node@20
brew link --overwrite --force node@20
```

Verify:

```bash
node --version    # v20.x.x
npm --version     # 10.x.x
```

### Step 2 — Install the AWS CDK v2 CLI

```bash
npm install -g aws-cdk
cdk --version     # 2.x.x
```

Two important things to know:

- **You do not need to `npm install -g aws-cdk` inside every project.**
  The global install provides the `cdk` binary; each project then
  installs the matching `aws-cdk-lib` as a local dependency.
- **Match versions.** The CLI version and `aws-cdk-lib` version should
  be within one or two minor versions of each other to avoid "context"
  errors. The `package.json` we ship in `code/` pins `aws-cdk-lib` to
  the same version line as the CLI you just installed.

### Step 3 — Configure AWS credentials

Pick **one** of the two patterns below.

**Pattern A — short-lived access keys (simplest for a personal account):**

```bash
aws configure
# AWS Access Key ID:     AKIA...
# AWS Secret Access Key: *****
# Default region:        us-east-1
# Default output:        json
```

**Pattern B — IAM Identity Center (recommended for organizations):**

```bash
aws configure sso
# SSO session name: my-sso
# SSO start URL:    https://my-org.awsapps.com/start
# SSO region:       us-east-1
# Account:          pick from the list
# Role:             pick from the list
# CLI default client Region: us-east-1
# CLI default output: json
# CLI profile name: dev

export AWS_PROFILE=dev
aws sts get-caller-identity
```

Verify the credentials work:

```bash
aws sts get-caller-identity
# {
#     "UserId": "AROA...",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/..."
# }
```

If the `Account` field matches the AWS account you intend to deploy into,
you are good.

### Step 4 — `cdk bootstrap`

Bootstrap creates three resources in your account:

- An S3 bucket named `cdk-<account>-<region>-assets-<hash>` — CDK uploads
  Lambda zips, Docker images, and other assets here.
- An IAM role `cdk-<account>-<region>-file-publishing-role` — CDK uses
  this to upload assets.
- An IAM role `cdk-<account>-<region>-image-publishing-role` — used for
  Docker image assets.

```bash
npx cdk bootstrap aws://123456789012/us-east-1
# OR if your default profile is already set:
npx cdk bootstrap
```

You should see output ending with something like:

```
✅  Environment aws://123456789012/us-east-1 bootstrapped.
```

> **Idempotent.** Running `cdk bootstrap` twice in a row is safe — CDK
> detects the existing resources and exits with a success.

> **Per-account, per-region.** If you later deploy to `eu-west-1`, you
> must bootstrap that region too.

### Sanity check — an empty synth

From the `code/` directory of this section, run:

```bash
cd code
npm install            # pulls aws-cdk-lib + typescript + @aws-sdk/*
npx cdk synth          # synthesizes the stack to cdk.out/
ls cdk.out/            # ServerlessStack.template.json + asset zips
```

If `cdk synth` exits 0 and prints a CloudFormation template, you have a
fully working CDK toolchain and are ready for L74.

## Hands-on

Run every step from this lecture. Confirm that at the end:

1. `node --version` shows `v20.x`.
2. `cdk --version` shows `2.x`.
3. `aws sts get-caller-identity` returns your account.
4. `npx cdk bootstrap` printed `Environment ... bootstrapped.`
5. `npx cdk synth` produced a template under `cdk.out/`.

If any of those fail, **do not proceed to L74 yet** — fix the toolchain
first.

## Quiz prep

- What is the purpose of `cdk bootstrap`, and which two resources does it
  create?
- Why do we install the CDK CLI globally but `aws-cdk-lib` per project?
- Which Node.js major versions does the AWS CDK v2 support?
- What is the difference between `aws configure` and `aws configure sso`?

## Further reading

- [AWS CDK — Getting started](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html)
- [AWS CDK — Bootstrap](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html)
- [AWS CDK — Credentials](https://docs.aws.amazon.com/cdk/v2/guide/credentials.html)
- [Node.js 20 LTS](https://nodejs.org/en/about/previous-releases)
