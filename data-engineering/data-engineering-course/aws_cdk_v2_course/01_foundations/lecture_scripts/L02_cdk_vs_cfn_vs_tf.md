---
lecture: L02
title: "CDK vs CloudFormation vs Terraform"
duration: "13:00"
section: 1
prereqs: ["L01"]
---

# L02 — CDK vs CloudFormation vs Terraform

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 1 — Foundations
> **Duration:** 13:00

## Prereqs

L01 — What is IaC?

## Key terms

- **CloudFormation (CFN)** — AWS's native declarative IaC, JSON or
  YAML. Ships with AWS, supports every AWS resource, but verbose and
  hard to compose.
- **Terraform** — HashiCorp's declarative IaC, multi-cloud (AWS, GCP,
  Azure). HCL syntax, mature state management, large ecosystem.
- **CDK v2** — AWS's imperative IaC, written in TypeScript / Python /
  Java / Go / .NET / C++. Compiles to a CloudFormation template that
  CloudFormation then deploys.
- **State** — the file/database the IaC tool uses to know what's
  already deployed (Terraform stores it on disk or in S3; CFN stores
  it in the AWS-managed stack; CDK doesn't have a state of its own
  — it just queries CFN).

## Lecture

In 2026, on AWS, the realistic choice is between three IaC tools:

| Tool | Language | State | Strength | Weakness |
|---|---|---|---|---|
| **CloudFormation** | JSON / YAML | AWS-managed | Ships with AWS, supports every service, no extra tooling | Verbose, hard to compose, no abstraction layer |
| **CDK v2** | TypeScript / Python / Go / ... | AWS-managed (via CFN) | Composable, type-safe, refactorable, generates CFN | Slightly slower iteration loop (synth → deploy) |
| **Terraform** | HCL | Local or S3 backend | Multi-cloud, mature module ecosystem, large community | HCL is a new language, drift detection is opt-in, AWS service coverage lags AWS by days/weeks |

**When to pick what** (this is the framework I use with clients):

- **Single-cloud, AWS-only, small team, TypeScript-friendly** →
  **CDK v2** (this course).
- **Single-cloud, AWS-only, must be readable by ops, no code** →
  **CloudFormation** (YAML).
- **Multi-cloud, large enterprise, existing Terraform expertise** →
  **Terraform** (or **Pulumi** if you want to stay in a real
  programming language).
- **Quick demo / 1-page stack** → **CDK v2** wins on conciseness.

CDK's killer feature is **abstraction**: you can write a 5-line
`new s3.Bucket(...)` that expands to a 70-line CloudFormation
resource with sane defaults (encryption, public-access block, etc).
With raw CFN you'd write those 70 lines by hand.

## Hands-on

No code yet — this is a comparison lecture.

```bash
# Just to confirm CDK is on your machine (installed in L04):
cdk --version
```

## Quiz prep

- Which tool generates a CloudFormation template and then deploys it
  via CloudFormation? (CDK)
- Which tool keeps its own state file? (Terraform)
- Which tool is the easiest to *compose* (loops, conditionals, custom
  abstractions)? (CDK)

## Further reading

- [CDK vs Terraform in 2026](https://aws.amazon.com/cdk/) (AWS marketing)
- Next up: **L03 — CDK v2 architecture**
