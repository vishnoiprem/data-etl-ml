---
lecture: L28
title: "cdk.context — environment values, lookups, cdk.json"
duration: "12:00"
section: 6
prereqs: ["L27"]
---

# L28 — `cdk.context` — Environment Values, Lookups, `cdk.json`

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 6 — Real-World Patterns
> **Duration:** 12:00

## Prereqs

L27 — Cross-region

## Key terms

- **`cdk.json` / `cdk.context`** — the per-project config object.
  Used for feature flags, environment values, and lookups.
- **Context value** — a key you can read in code with
  `this.node.tryGetContext('key')`. Comes from `cdk.json`, CLI
  `-c key=value`, or `cdk.context.json`.
- **Lookup** — at synth time, CDK may call the AWS API to fetch
  values (VPC IDs, AMI IDs, route53 zone IDs). The result is
  cached in `cdk.context.json`.
- **`-c key=value`** — pass a context value from the CLI.
- **`--no-cli-import-lookups`** — never call AWS APIs at synth
  time. Forces you to commit `cdk.context.json` for deterministic
  builds.

## Lecture

`cdk.context` is the escape hatch for "I want to pass a value to
my stack at synth time, not hardcode it." Three sources:

1. **`cdk.json`** — the `context` object. Stays with the code.
2. **CLI flags** — `cdk synth -c env=prod -c version=2`.
3. **`cdk.context.json`** — auto-generated; caches lookups.

Reading a context value in code:

```ts
const env = this.node.tryGetContext('env') ?? 'dev';
const version = this.node.tryGetContext('version') ?? '1.0.0';
```

For environment-specific values (account ID, region), use the
`StackProps.env` instead — context is for *anything else*.

For lookups, the most common one is the default VPC:

```ts
import * as ec2 from 'aws-cdk-lib/aws-ec2';

const vpc = ec2.Vpc.fromLookup(this, 'Vpc', {
  vpcId: this.node.tryGetContext('vpcId'),
});
// or, the dangerous one that calls the AWS API:
const defaultVpc = ec2.Vpc.fromLookup(this, 'Vpc', { isDefault: true });
```

The second form makes a **runtime API call** at synth time. That's
fine in dev, terrible in CI (slow + needs AWS creds + non-deterministic).
The fix is `--no-cli-import-lookups` and a committed
`cdk.context.json`.

```bash
cdk synth --no-cli-import-lookups
# → fail with a clear error if a context value is missing
```

## Hands-on

Open `code/hello-cdk/cdk.json`. Add a `context` block:

```json
{
  "context": {
    "course": "aws-cdk-v2-crash-course",
    "env": "dev"
  }
}
```

Read it in your stack:

```ts
const env = this.node.tryGetContext('env') ?? 'dev';
new cdk.CfnOutput(this, 'Env', { value: env });
```

Re-run `npx cdk synth --quiet | jq '.Outputs'`.

## Quiz prep

- What's the difference between `env: { region }` and
  `this.node.tryGetContext('region')`? (env is for the AWS
  account/region; context is for arbitrary app config)
- Why is `cdk.context.json` checked in? (deterministic synth in CI)
- Which flag prevents CDK from calling AWS APIs at synth time?
  (`--no-cli-import-lookups`)

## Further reading

- [Contexts in CDK](https://docs.aws.amazon.com/cdk/v2/guide/contexts.html)
- Next up: **L29 — CDK Aspects**
