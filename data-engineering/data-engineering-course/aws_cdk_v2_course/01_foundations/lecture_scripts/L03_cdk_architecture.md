---
lecture: L03
title: "CDK v2 architecture — aws-cdk-lib, constructs, the CLI"
duration: "13:00"
section: 1
prereqs: ["L02"]
---

# L03 — CDK v2 Architecture — `aws-cdk-lib`, `constructs`, the CLI

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 1 — Foundations
> **Duration:** 13:00

## Prereqs

L02 — CDK vs CloudFormation vs Terraform

## Key terms

- **`aws-cdk-lib`** — the AWS-maintained npm package that ships every
  L2 construct. One package, no per-service libraries (in v2).
- **`constructs`** — the open-source library (`~10.3.0`) that
  provides the `Construct` base class. CDK is built on top of it.
- **`aws-cdk` (the CLI)** — the command-line tool you `npm install
  -g` once. Provides `cdk synth`, `cdk deploy`, `cdk diff`, etc.
- **`cdk.json`** — the per-project config file that points the CLI
  at your app entry (`bin/app.ts`).
- **App / Stack / Construct** — the three layers of the construct
  tree (covered in detail in L05).

## Lecture

The CDK v2 install footprint is small but has three distinct pieces.
Getting the model right here saves a lot of confusion later.

```text
                ┌──────────────────────────┐
                │   aws-cdk (the CLI)      │  global npm install
                │   $ cdk synth / deploy   │
                └──────────┬───────────────┘
                           │ runs
                           ▼
        ┌────────────────────────────────────┐
        │  Your CDK App (bin/app.ts)         │
        │  imports aws-cdk-lib + constructs  │
        └──────────┬─────────────────────────┘
                   │ at runtime
                   ▼
   ┌──────────────────────────────────────┐
   │  aws-cdk-lib          constructs     │  per-project npm install
   │  (L2 constructs,      (Construct     │
   │   CFN resources)       base class)   │
   └──────────────────────────────────────┘
```

Three things to internalize:

1. **`aws-cdk-lib` is one package.** In v1 each AWS service had its
   own npm package (`@aws-cdk/aws-s3`, `@aws-cdk/aws-lambda`, ...). v2
   unified them. You `import * as s3 from 'aws-cdk-lib/aws-s3'`.
2. **`constructs` is a separate package** because the construct
   pattern is generic — you can use it without CDK to build other
   tree-based config systems.
3. **The CLI is global, the library is per-project.** `npm install
   -g aws-cdk` once. Then `npm install aws-cdk-lib constructs` in
   every CDK project. This way different projects can pin different
   versions of the lib without colliding.

`cdk.json` ties the CLI to your code:

```json
{
  "app": "npx ts-node --prefer-ts-exts bin/hello-cdk.ts"
}
```

When you run `cdk synth`, the CLI shells out to that command to
produce the in-memory CDK app, then it asks the app to synthesize
its stacks into CloudFormation templates, and finally it writes them
to `cdk.out/`.

## Hands-on

```bash
# Verify the three pieces
cdk --version          # 2.x — the CLI
npm list aws-cdk-lib   # 2.x — the lib (in your project)
npm list constructs    # 10.x — the construct lib
```

## Quiz prep

- Name the three pieces of CDK v2. (CLI, `aws-cdk-lib`, `constructs`)
- Where does `cdk.json` live and what does it do?
- Is the CLI global or per-project?

## Further reading

- [CDK v2 packaging changes](https://aws.amazon.com/blogs/developer/aws-cdk-v2-developer-preview/)
- Next up: **L04 — Installing and bootstrapping CDK**
