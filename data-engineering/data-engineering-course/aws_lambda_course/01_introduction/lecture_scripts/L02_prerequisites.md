---
lecture: L02
title: "Course Pre-Requisites"
duration: "2:19"
section: 1
prereqs:
  - L01
---

# L02 — Course Pre-Requisites

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 1 — Introduction
> **Duration:** 2:19

## Prereqs

- Watched **L01 — Course Introduction** (recommended but not strictly
  required).

## Key terms

- **AWS account** — a container for all your AWS resources. You can sign
  up at `aws.amazon.com` with an email and a credit card; the **free
  tier** covers everything you need for the first half of this course.
- **IAM user with admin access** — an identity inside your AWS account
  that can create and manage resources. We do **not** use the root user
  for day-to-day work.
- **AWS CLI v2** — the official command-line tool for talking to AWS
  from your terminal. We use it to configure credentials, deploy CDK and
  CloudFormation stacks, and run `sam local invoke` for testing.
- **Region** — a geographic AWS data center (e.g. `us-east-1`,
  `eu-west-1`). Lambda, S3, DynamoDB, API Gateway, and Bedrock must all
  live in the same region for the hands-on use cases to work.

## Lecture

Welcome back. In the last lecture I gave you the course roadmap. Now I
want to make sure your laptop and your AWS account are ready before we
write our first Lambda function in section 2. The good news: the list is
short, and you almost certainly already have most of it.

### What you DO need

#### 1. An AWS account (free tier is enough)

Sign up at `aws.amazon.com` if you don't have one. The AWS free tier
covers:

- 1 million Lambda invocations per month
- 5 GB of S3 storage
- 25 GB of DynamoDB storage
- 1 million API Gateway calls per month

That's enough to do every lecture and every assignment in sections 1
through 11. You only need to start watching the billing dashboard once
we hit the Bedrock section (section 10) and the IaC sections (12 and
13).

#### 2. A non-root IAM user with admin access

Once your account is created:

1. Sign in as **root** and create an IAM user (e.g. `prem-dev`).
2. Attach the **`AdministratorAccess`** managed policy to that user.
3. Enable **MFA** on both root and the IAM user.
4. From this point on, **always sign in as the IAM user**, not root.

We'll refine this in section 2 (L07) when we talk about the **Lambda
execution role** — but for now, "an IAM user that can create
everything" is exactly what you need.

#### 3. Python 3.11+

We use Python 3.11 in every code sample. Earlier 3.x versions will
mostly work, but I'd rather you not debug a version mismatch on lecture
one.

```bash
python3 --version
# Python 3.11.x or newer expected
```

If you need to install or upgrade, use the official python.org
installer or your platform's package manager. I personally use
**pyenv** on macOS/Linux for per-project Python versions.

```bash
# macOS with Homebrew
brew install python@3.11

# Or with pyenv
pyenv install 3.11.9
pyenv global 3.11.9
```

#### 4. AWS CLI v2

The CLI is how we configure credentials, run `sam local invoke`, and
deploy CDK/CloudFormation stacks later in the course.

```bash
aws --version
# aws-cli/2.x.x expected
```

Then configure your credentials:

```bash
aws configure
# AWS Access Key ID:     <your IAM access key>
# AWS Secret Access Key: <your IAM secret key>
# Default region name:   us-east-1
# Default output format: json
```

#### 5. Region selection — `us-east-1` (N. Virginia)

**Strongly recommend `us-east-1`** as your default region for the entire
course. Two reasons:

- **Bedrock availability.** AWS Bedrock (and the Cohere foundational
  model in particular) is not enabled in every region. `us-east-1` is
  the safest default for section 10.
- **Cross-service consistency.** S3, Lambda, DynamoDB, API Gateway, and
  EventBridge are all available in `us-east-1`, and the CloudFormation
  and CDK templates in sections 12 and 13 assume `us-east-1`.

If you have a compliance reason to use another region, you can — but
expect to swap region codes in a few YAML files.

### What you do NOT need

I want to be explicit here, because I know prerequisites can be
intimidating:

- **No prior Lambda or serverless experience.** Section 2 starts with
  the evolution from physical servers to Lambda before we open the
  console.
- **No prior AWS experience required**, but it helps. If you've never
  used the AWS console at all, I'd skim the first two chapters of the
  AWS Getting Started docs before section 2. If you have used EC2 or
  S3 even casually, you're fine.
- **No prior Python background required.** We have a Python refresher
  in section 3 (L09–L10) and a deeper Python appendix in section 14
  (L78–L81). If you already write Python, you can skip both.
- **No credit card–burning assumptions.** The free tier covers
  sections 1–11. Sections 12 and 13 deploy real CloudFormation and CDK
  stacks — those cost pennies, not dollars, but I'll flag cost in every
  lecture.
- **No Docker required** (yet). We introduce Docker for `sam local
  invoke` in section 11. You can skip Docker for the first 10 sections
  if you don't have it.

### Quick preflight check

Before you move on, run this:

```bash
# 1. Python version
python3 --version

# 2. AWS CLI version
aws --version

# 3. CLI configured and reachable
aws sts get-caller-identity

# 4. (Optional) boto3 installed
python3 -m pip show boto3 | head -2
```

If the third command returns a JSON blob with your `Account` and
`Arn`, you're set. If it errors with `Unable to locate credentials`,
re-run `aws configure`.

## Hands-on

No code is written in this lecture. Your task before L03 is to make
sure the preflight check above passes on your machine.

## Quiz prep

For this lecture, the quiz tests whether you know **what you need** vs
**what you do not need**:

- Which region is recommended, and why?
- Why do we use an IAM user instead of root?
- Which two sections assume Python knowledge vs teach it from scratch?

## Further reading

- AWS Free Tier: <https://aws.amazon.com/free/>
- AWS CLI v2 install: <https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html>
- IAM best practices: <https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html>
- `../../downloads/lambda_cheat_sheet.pdf` — pin it to your desktop.

## What's next

That's it for section 1. Next stop: **section 2 — AWS Lambda Basic
Concepts (Part 1)**, starting with **L03 — Section Overview**, followed
by **L04 — Evolution from Physical Servers to AWS Lambda** and **L05 —
What is AWS Lambda and Use Cases**.

**Ready? Let's start with section 2 — Lambda basics.**
