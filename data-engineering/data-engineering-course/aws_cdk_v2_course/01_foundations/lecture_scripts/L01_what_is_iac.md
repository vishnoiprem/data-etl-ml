---
lecture: L01
title: "What is Infrastructure as Code (IaC)?"
duration: "12:00"
section: 1
prereqs: []
---

# L01 — What is Infrastructure as Code (IaC)?

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 1 — Foundations
> **Duration:** 12:00

## Prereqs

None. This is the very first lecture.

## Key terms

- **IaC (Infrastructure as Code)** — defining infrastructure in
  version-controlled text files instead of clicking through consoles.
- **Declarative vs imperative** — declarative says *what* you want
  (CloudFormation, Terraform); imperative says *how* to get there
  (CDK, Pulumi, a Python `boto3` script).
- **Idempotency** — running the same template twice produces the same
  end state, not a duplicate.
- **Drift** — when the actual state of a resource diverges from the
  declared state (someone changed it in the console).
- **Plan / diff** — a preview of what the tool is about to do, before
  it does it.

## Lecture

Infrastructure as Code is the practice of **defining your
infrastructure in version-controlled text files** instead of clicking
through the AWS console. The first time you hear this it sounds
overkill — surely the console is fine? — but the moment you have more
than one environment (dev, staging, prod), or more than one
engineer, the console becomes a liability. The same S3 bucket gets
created three different ways by three different people; nobody can
remember who owns which IAM role; nothing is reviewable; nothing
rolls back.

The three promises IaC makes are:

1. **Reproducible.** The same template, applied to two accounts,
   produces two identical environments. No more "works on my machine."
2. **Reviewable.** A change to a CloudFormation template is a pull
   request. Your team can discuss the change *before* it lands.
3. **Recoverable.** If a change breaks production, you revert the
   commit, not the resource.

```text
console (click) ──>  ad-hoc, undocumented, unreviewable
IaC (template)   ──>  reproducible, reviewable, recoverable
```

There are two flavors of IaC:

- **Declarative** tools — CloudFormation, Terraform — describe the
  *desired end state*. The tool figures out the steps.
- **Imperative** tools — CDK, Pulumi, a `boto3` script — describe
  the *order of operations* and the tool executes them. CDK is the
  hybrid: it *reads* like imperative code but *generates* a
  declarative CloudFormation template under the hood.

We'll spend the rest of this section on **AWS CDK v2**, which is the
imperative layer that compiles down to CloudFormation.

## Hands-on

```bash
# No lab — this is a concepts lecture.
# Read https://aws.amazon.com/cdk/ to skim the official overview.
```

## Quiz prep

- What is **drift**? (actual state diverging from declared state)
- What's the difference between **declarative** and **imperative** IaC?
- Name the 3 promises IaC makes. (reproducible, reviewable, recoverable)

## Further reading

- AWS docs: [What is IaC?](https://docs.aws.amazon.com/whitepapers/latest/introduction-devops-aws/infrastructure-as-code.html)
- Next up: **L02 — CDK vs CloudFormation vs Terraform**
