---
lecture: L29
title: "CDK Aspects — organization-wide compliance tags"
duration: "12:00"
section: 6
prereqs: ["L28"]
---

# L29 — CDK Aspects — Organization-Wide Compliance Tags

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 6 — Real-World Patterns
> **Duration:** 12:00

## Prereqs

L28 — `cdk.context`

## Key terms

- **Aspect** — a class that implements `IAspect`. CDK calls
  `aspect.visit(node)` for every construct in the tree at synth
  time.
- **`Annotations.of(node).addWarning('...')`** — leave a warning
  in the synth output.
- **`Tag.add(node, 'key', 'value')`** — apply a tag to a resource
  or every resource under a node.
- **`Aspects.of(scope).add(new MyAspect())`** — register the
  aspect with a scope.

## Lecture

Aspects are CDK's answer to "I want every resource in every stack
to carry these tags / follow these rules." They run at synth time
and can mutate or annotate the construct tree.

A tag-everything aspect:

```ts
import { IAspect, Tag } from 'aws-cdk-lib';
import { IConstruct } from 'constructs';

export class RequiredTags implements IAspect {
  visit(node: IConstruct): void {
    if (Tag.isTaggable(node)) {
      Tag.add(node, 'Project', 'myapp');
      Tag.add(node, 'CostCenter', 'engineering');
    }
  }
}

// register at the App level so it walks every stack
Aspects.of(app).add(new RequiredTags());
```

The `IAspect` interface is dead simple: one method, `visit(node)`.
You can do anything inside it — but the common use cases are:

1. **Enforce tags** — every resource gets `Project`, `Owner`, etc.
2. **Warn on missing encryption** — if a bucket is unencrypted,
   `Annotations.of(node).addWarning('...')`.
3. **Remediate** — add a `BucketPolicy`, attach a `PermissionsBoundary`,
   etc.

`cdk synth` with an aspect that adds warnings:

```text
$ cdk synth
[Warning] /MyStack/MyBucket/Resource - Unencrypted S3 bucket
```

You can fail the synth on warnings:

```ts
Aspects.of(app).add({
  visit: (node) => {
    if (node instanceof s3.CfnBucket && !node.encryption) {
      Annotations.of(node).addError('Bucket must be encrypted');
    }
  },
});
// → cdk synth exits non-zero
```

## Hands-on

Add the `RequiredTags` aspect to your `hello-cdk` project:

```ts
// bin/hello-cdk.ts
import { Aspects } from 'aws-cdk-lib';
import { RequiredTags } from './required-tags';

const app = new cdk.App();
new HelloCdkStack(app, 'HelloCdkStack');
Aspects.of(app).add(new RequiredTags());
```

After synth, every resource will have `Project=myapp` and
`CostCenter=engineering` in its CFN properties.

## Quiz prep

- What's the `IAspect` interface? (one method: `visit(node)`)
- What's the difference between `addWarning` and `addError`?
  (warning = non-fatal, error = fail synth)
- How do you register an aspect with the App? (`Aspects.of(app).add(aspect)`)

## Further reading

- [CDK Aspects](https://docs.aws.amazon.com/cdk/v2/guide/aspects.html)
- Next up: **L30 — Course wrap-up**
