---
title: L71 — (Optional) Introduction to AWS Cloud Development Kit (CDK)
author: Prem Vishnoi <pvishnoi@avilx.com>
section: 12
duration: 7:23
---

# L71 — (Optional) Introduction to AWS Cloud Development Kit (CDK)

> **Section:** 12 — AWS CDK v2
> **Duration target:** 7:23
> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

## Prereqs

- Comfortable writing Lambda functions (Section 2 onwards).
- Hands-on with API Gateway + S3 (Sections 7 and 8).
- Node.js 20 installed (we cover installation in L72).
- AWS account with a configured CLI profile (`aws configure`).

## Key terms

- **CDK (Cloud Development Kit)** — an open-source framework from AWS for
  defining cloud infrastructure in a familiar programming language
  (TypeScript, Python, Java, Go, .NET, etc.).
- **Construct** — the unit of composition in CDK. A construct encapsulates
  one or more AWS resources plus the wiring between them. The
  `aws-cdk-lib` library ships L2 (curated) constructs; teams can build L1
  (raw CFN) and L3 (patterns) constructs on top.
- **App** — the root CDK object. You instantiate one or more stacks inside
  the app.
- **Stack** — the unit of deployment. One stack maps to exactly one
  CloudFormation stack.
- **Synth (synthesize)** — `cdk synth` walks the construct tree, evaluates
  your code, and emits a CloudFormation template (JSON or YAML) under
  `cdk.out/`.
- **Bootstrap** — a one-time per-account/region setup that creates the S3
  bucket and IAM roles CDK needs to deploy assets (Lambda zip files, Docker
  images, etc.).

## Lecture

### Why CDK exists

If you have worked through section 13, you have seen what
"infrastructure as code" looks like in raw CloudFormation: a single ~400-line
YAML file that lists every resource, every property, every dependency by
hand. It works. It is also painful — there is no type checking, no
auto-complete, no loops, no helper functions, and one missing comma can
fail an entire deploy.

The **AWS Cloud Development Kit (CDK)** solves those pain points. Instead of
declaring resources in JSON/YAML, you write code in a real programming
language. That code calls high-level **constructs** that look like
TypeScript classes:

```ts
const bucket = new s3.Bucket(this, 'MyBucket', {
  versioned: true,
  encryption: s3.BucketEncryption.S3_MANAGED,
});
```

Under the hood, CDK runs the code, walks the construct tree, and emits a
**CloudFormation template** that AWS then deploys exactly the way it would
deploy any hand-written template. You get the safety net of CloudFormation
(rollback, drift detection, change sets) plus the developer ergonomics of a
typed language.

### CDK vs CloudFormation vs SAM vs Terraform

| Dimension | CloudFormation | SAM | CDK | Terraform |
|---|---|---|---|---|
| Authored in | JSON / YAML | JSON / YAML (CFN + transforms) | TypeScript, Python, Java, Go, .NET, ... | HCL (HashiCorp) |
| Abstraction level | L1 (raw) | Higher (serverless shortcuts) | L1 + curated L2 + L3 patterns | HCL modules |
| Type safety / IDE | None | None | Yes (full IntelliSense) | Limited (HCL is loosely typed) |
| Synthesizes to | — | CloudFormation | CloudFormation | Terraform plan / state |
| Multi-cloud | No (AWS only) | No (AWS only) | No (AWS only) | Yes (3000+ providers) |
| State management | None (AWS-owned) | None (AWS-owned) | None (AWS-owned) | Yes (local or remote state file) |
| Local debugging | Limited | `sam local` | `cdk synth` to inspect CFN | `terraform plan` |
| Best for | Pure AWS, small stacks | Quick serverless prototypes | Production AWS, large reusable stacks | Multi-cloud or non-AWS providers |

A few takeaways:

- **SAM is essentially CloudFormation with a `Transform` and a few extra
  resource types.** It is great for small serverless projects but offers
  none of the type safety or abstraction power of CDK.
- **Terraform is multi-cloud** and has a different state model. If you are
  AWS-only and want first-class AWS idioms, CDK is usually the better fit.
- **CDK still deploys through CloudFormation.** That means everything you
  know about change sets, drift detection, and stack policies still applies.
  CDK is a *better authoring experience* on top of CFN, not a replacement
  for the engine.

### How CDK synthesizes to CloudFormation

This is the single most important concept in the entire section:

1. You write `lib/serverless-stack.ts` in TypeScript.
2. The `bin/serverless-app.ts` entry point instantiates the stack.
3. You run `npx cdk synth`. CDK:
   - Resolves the construct tree.
   - Produces a CloudFormation template (JSON) in `cdk.out/<Stack>.template.json`.
   - Produces asset bundles (Lambda zips, Docker images) if needed.
4. You run `npx cdk deploy`. CDK uploads the assets, calls
   `CreateStack`/`UpdateStack` on CloudFormation, and tails the events so
   you can watch the deploy in real time.

So when you "write CDK" you are really still writing CloudFormation — just
in a much nicer language, with a curated library of defaults that match AWS
best practices.

### The CDK app / stack / construct model

```
App
 └── Stack
      ├── Construct (e.g. s3.Bucket)
      │     └── 1+ CloudFormation resources
      ├── Construct (e.g. iam.Role)
      │     └── 1+ CloudFormation resources
      └── Construct (e.g. lambda.Function)
            └── 1+ CloudFormation resources + asset zip
```

A single CDK app can contain many stacks. A single stack can contain many
constructs. A single construct can produce many CloudFormation resources
(an L2 `lambda.Function` produces the function, the IAM role, the log
group, and a few outputs).

In this course we keep things simple: **one app, one stack**. That maps
cleanly to the CloudFormation template in section 13, which is also a
single stack.

## Hands-on

> Nothing to deploy yet — this lecture is purely conceptual. We install the
> CDK toolkit in L72 and start writing constructs in L74.

Open `code/` and skim the file tree. Notice:

- `bin/serverless-app.ts` — the entry point. One line instantiates the
  stack.
- `lib/serverless-stack.ts` — every construct lives here.
- `lambda/` — the two handler source files that get bundled into the
  Lambda zip assets by CDK at synth time.

## Quiz prep

- What does `cdk synth` do, and where does it write the output?
- Why is CDK considered "CloudFormation with a better authoring experience"
  rather than a replacement for CloudFormation?
- Name two concrete advantages CDK has over raw CloudFormation.
- Which of the four IaC tools in the table above is multi-cloud?

## Further reading

- [AWS CDK Developer Guide — What is the AWS CDK?](https://docs.aws.amazon.com/cdk/v2/guide/home.html)
- [CDK Concepts](https://docs.aws.amazon.com/cdk/v2/guide/core_concepts.html)
- [aws-cdk-lib API reference (L2 constructs)](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib-readme.html)
- Section 13 of this course (L60–L70) for the same architecture in raw CFN.
