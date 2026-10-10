---
lecture: L21
title: "Why test CDK stacks — synth vs deploy safety net"
duration: "10:00"
section: 5
prereqs: ["L20"]
---

# L21 — Why Test CDK Stacks

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 5 — Testing, Snapshots, Assertions, CI/CD
> **Duration:** 10:00

## Prereqs

L20 — Wire AppSync → SFN → EventBridge

## Key terms

- **Synth** — produces a CloudFormation template; runs locally.
- **Deploy** — sends that template to CloudFormation; costs money
  and touches real AWS resources.
- **Test pyramid for CDK** — `unit` (assertions) > `snapshot`
  (golden file) > `integration` (deploy to a sandbox account).

## Lecture

`synth` succeeds doesn't mean your stack is correct. Two reasons:

1. **Synth can succeed with garbage.** You can `new s3.Bucket(this,
   'Foo')` in a Stack that has no App, and synth will still produce a
   template. The error won't surface until deploy.
2. **CDK has silent defaults.** L2 constructs have opinionated
   defaults. A change in CDK's defaults between versions can change
   your stack's behavior with no compile error.

```text
   synth OK     deploy OK    what we want
      │             │              │
      ▼             ▼              ▼
  ┌────────┐  ┌────────┐  ┌──────────────────┐
  │ cdk    │  │ cdk    │  │ "the template    │
  │ synth  │──▶ deploy │  │  matches my       │
  │        │  │        │  │  intent"          │
  └────────┘  └────────┘  └──────────────────┘
       ▲                       ▲
       │                       │
   catches                   tests catch
   type errors               semantic errors
```

The test pyramid:

```text
   unit (Template.fromStack + hasResourceProperties)
   │  • fast (ms)
   │  • no AWS account
   │  • catches "I broke a property"
   │
   ▼
   snapshot (toMatchSnapshot)
   │  • fast (ms)
   │  • no AWS account
   │  • catches "I changed a property I didn't mean to"
   │
   ▼
   integration (cdk deploy to a sandbox account)
      • slow (minutes)
      • costs money
      • catches "I don't have permission" / "the API has a bug"
```

The bulk of your tests should be at the **unit** level. Snapshots
are the safety net for "anything I forgot to assert explicitly."
Integration tests are for release day.

## Hands-on

```bash
cd 02_app_stack_construct/code/hello-cdk
npm test                       # runs 5 unit assertions
```

## Quiz prep

- What's the unit-level CDK test entry point? (`Template.fromStack`)
- Which test level catches "I forgot to update the snapshot"?
  (snapshot test failure)
- Which test level needs an AWS account? (integration)

## Further reading

- [Testing CDK apps](https://docs.aws.amazon.com/cdk/v2/guide/testing.html)
- Next up: **L22 — `aws-cdk-lib/assertions`**
