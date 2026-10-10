---
lecture: L23
title: "Jest snapshot tests with CDK"
duration: "11:00"
section: 5
prereqs: ["L22"]
---

# L23 — Jest Snapshot Tests with CDK

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 5 — Testing, Snapshots, Assertions, CI/CD
> **Duration:** 11:00

## Prereqs

L22 — `Template.fromStack`

## Key terms

- **Snapshot test** — a test that compares the output against a
  stored "expected" file (`__snapshots__/<file>.snap`).
- **`toMatchSnapshot()`** — the Jest matcher. On first run, the
  snapshot is created; on subsequent runs, the output must match.
- **Snapshot update** — `jest -u` or `npx jest --updateSnapshot` to
  refresh the stored file after an intentional change.

## Lecture

Snapshot tests are the cheapest test you can write for CDK: you
assert nothing explicit, you just store the synthesized template.
If anything changes, the test fails and you look at the diff.

```ts
import { Template } from 'aws-cdk-lib/assertions';

test('HelloCdkStack matches snapshot', () => {
  const app = new cdk.App();
  const stack = new HelloCdkStack(app, 'TestStack');
  const template = Template.fromStack(stack);
  expect(template.toJSON()).toMatchSnapshot();
});
```

The first run writes `test/__snapshots__/hello-cdk.test.ts.snap`:
the entire CloudFormation template, in JSON. Subsequent runs
compare.

When the snapshot test fails:

```text
› 1 snapshot test failed in 1 test suite.
 › HelloCdkStack matches snapshot
   › Snapshot: HelloCdkStack matches snapshot 1
   › Snapshot diff:
   ...
   +   "VersioningConfiguration": {
   +     "Status": "Enabled"
   +   }
```

The fix is one of:

1. **The change was unintentional** — revert your code.
2. **The change was intentional** — run `npx jest -u` to update the
   snapshot file, then commit both the code and the snapshot.

**Pros of snapshot tests:**

- Cheapest test to write (one line).
- Catches *any* unintended change.
- Documents the entire template as a checked-in artifact.

**Cons:**

- High noise during development (every change requires a snapshot
  update).
- Easy to rubber-stamp an update without reviewing it.
- The diff is huge if a single line changes.

**The balanced approach:** explicit assertions for properties you
care about (L22/L24) + a single snapshot test as a safety net.

## Hands-on

The snapshot demo in `code/snapshot-demo/` adds a second test
file alongside the existing one in `code/hello-cdk/test/`. Compare
the two styles:

```bash
# copy the snapshot demo into hello-cdk
cp 05_testing_cicd/code/snapshot-demo/hello-cdk.snapshot.test.ts \
   02_app_stack_construct/code/hello-cdk/test/

cd 02_app_stack_construct/code/hello-cdk
npm test                       # 5 + 1 tests now
ls test/__snapshots__/         # new .snap file
```

## Quiz prep

- What matcher does Jest use for snapshot tests? (`toMatchSnapshot`)
- What flag updates snapshots? (`-u` or `--updateSnapshot`)
- What's the main downside of snapshot tests? (high noise during
  development, easy to rubber-stamp updates)

## Further reading

- [Jest snapshot tests](https://jestjs.io/docs/snapshot-testing)
- Next up: **L24 — Fine-grained assertions**
