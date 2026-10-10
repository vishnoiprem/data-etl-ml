---
lecture: L09
title: "Escape hatches and Stack.of(scope)"
duration: "10:00"
section: 2
prereqs: ["L08"]
---

# L09 — Escape Hatches and `Stack.of(scope)`

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 2 — App, Stack, Construct
> **Duration:** 10:00

## Prereqs

L08 — `cdk synth`

## Key terms

- **Escape hatch** — a method like `bucket.node.defaultChild` or
  `bucket.addPropertyOverride()` that lets you reach *inside* the L2
  construct and modify the underlying CloudFormation.
- **`Stack.of(scope)`** — the static helper that finds which Stack a
  given Construct belongs to.
- **`Resource.getAtt()` / `Resource.ref`** — CloudFormation intrinsic
  functions, often used via escape hatches.

## Lecture

Sometimes the L2 doesn't expose a property you need. Maybe the L2
was written before an AWS API change, or you want a property nobody
ever asked for. The escape hatch lets you reach inside without
giving up the L2 entirely.

Three common escape hatches:

```ts
// 1. The underlying CFN resource (L1)
const cfnBucket = bucket.node.defaultChild as s3.CfnBucket;
cfnBucket.ownershipControls = {
  rules: [{ objectOwnership: s3.ObjectOwnership.BUCKET_OWNER_PREFERRED }],
};

// 2. A simple property override
cfnBucket.addPropertyOverride('ObjectLockEnabled', true);
cfnBucket.addPropertyDeletionOverride('PublicAccessBlockConfiguration');

// 3. Get the stack a construct lives in
const myStack = cdk.Stack.of(this);      // `this` is a Construct
const region = cdk.Stack.of(this).region;
```

The convention is:

1. **Start at L2.** Use it for 95% of properties.
2. **Escape hatch when needed.** Document why you escaped, because
   the next person reading your code will wonder.
3. **Drop to L1 only when the L2 doesn't exist.** E.g., a brand-new
   AWS service that CDK hasn't shipped an L2 for yet.

`Stack.of(scope)` is the right way to ask "which CloudFormation stack
does this construct belong to?" — never reach for
`scope.stack` or `(scope as any).stack` (those don't exist or are
unstable across CDK versions).

## Hands-on

Open `code/hello-cdk/lib/hello-cdk-stack.ts`, add the first escape
hatch from above, then run `npm test` — it should still pass.

```bash
cd 02_app_stack_construct/code/hello-cdk
npm test
```

## Quiz prep

- What does an escape hatch let you do? (modify the L1 under an L2)
- Which static helper finds the Stack a Construct lives in?
  (`Stack.of(scope)`)

## Further reading

- [`EscapeHatch` pattern](https://docs.aws.amazon.com/cdk/v2/guide/cfn_layer.html)
- Next up: **L10 — `cdk deploy` + `cdk destroy`**
