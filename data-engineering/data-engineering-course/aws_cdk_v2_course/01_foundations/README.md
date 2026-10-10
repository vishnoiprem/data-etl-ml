# Section 1 — Foundations (L01–L04)

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **L-IDs:** L01–L04 | **Duration:** ~50 min | **Quizzes:** `quizzes/section_1.md`

Section 1 is the conceptual on-ramp. If you've never written
infrastructure-as-code before, this section gives you the vocabulary
and the "why" before we touch any TypeScript. If you have, you can
skim L01–L02 and focus on L03–L04 for the CDK-specific architecture.

## Lectures

| L# | Title | Min | File |
|---|---|---|---|
| L01 | What is Infrastructure as Code (IaC)? | 12 | `lecture_scripts/L01_what_is_iac.md` |
| L02 | CDK vs CloudFormation vs Terraform | 13 | `lecture_scripts/L02_cdk_vs_cfn_vs_tf.md` |
| L03 | CDK v2 architecture — `aws-cdk-lib`, `constructs`, the CLI | 13 | `lecture_scripts/L03_cdk_architecture.md` |
| L04 | Installing and bootstrapping CDK (Node, AWS CLI, `cdk bootstrap`) | 12 | `lecture_scripts/L04_install_bootstrap.md` |

## What you'll be able to do after Section 1

- Explain the difference between imperative and declarative IaC
- Pick the right IaC tool for a given project (CDK, CFN, Terraform)
- Describe the 3 layers of `aws-cdk-lib` and what `constructs` is for
- Run `cdk --version`, `cdk doctor`, and `cdk bootstrap` against your
  AWS account
