# Section 6 Quiz — Real-World Patterns

> 10 questions, multi-choice. Answers hidden in collapsible blocks.

---

**Q1.** In a multi-stack CDK app, what's the right way to pass a VPC from a network stack to an app stack?

- A. `appStackProps: { vpc: net.vpc }` typed as `ec2.Vpc` (the class)
- B. `appStackProps: { vpc: net.vpc }` typed as `ec2.IVpc` (the interface)
- C. Hardcode the VPC ID with `vpcId: 'vpc-0123...'` in the app stack
- D. Use a CloudFormation `CfnOutput` to look it up at deploy time

<details><summary>Show answer</summary>

**B — typed as `ec2.IVpc` (the interface).** It decouples the consumer from the VPC L2. The interface is what L2 constructs expose publicly, and it lets you swap in a different VPC L2 without changing the consumer.

</details>

---

**Q2.** How many regions can a single CDK Stack deploy to?

- A. As many as you specify in `env`
- B. Exactly one
- C. Two (primary + secondary)
- D. Unlimited — CDK fans out for you

<details><summary>Show answer</summary>

**B — Exactly one.** If you need resources in two regions, you need two stacks (and typically two `cdk deploy` invocations).

</details>

---

**Q3.** Which AWS service is **always** in `us-east-1` regardless of where you deploy other resources?

- A. Lambda
- B. DynamoDB
- C. IAM
- D. S3

<details><summary>Show answer</summary>

**C — IAM.** It's a global service; the API endpoint is global and the control plane is in `us-east-1`. Lambda, DynamoDB, and S3 are regional.

</details>

---

**Q4.** Where does `cdk.context` come from?

- A. `cdk.json`'s `context` block
- B. CLI flags: `cdk synth -c key=value`
- C. `cdk.context.json` (auto-generated, caches lookups)
- D. All of the above

<details><summary>Show answer</summary>

**D — All of the above.** They're three sources for the same key/value namespace.

</details>

---

**Q5.** What's the difference between `env: { region: 'us-east-1' }` and `this.node.tryGetContext('region')`?

- A. `env` is for AWS account/region; `context` is for arbitrary app config
- B. They are aliases for the same thing
- C. `env` is for the App; `context` is for the Stack
- D. `context` doesn't exist

<details><summary>Show answer</summary>

**A — `env` is for AWS account/region; `context` is for arbitrary app config.** Use `env` for the deployment target; use context for everything else (env name, version, feature flags).

</details>

---

**Q6.** Which flag prevents CDK from making AWS API calls at synth time?

- A. `--no-lookups`
- B. `--no-cli-import-lookups`
- C. `--offline`
- D. `--synth-only`

<details><summary>Show answer</summary>

**B — `--no-cli-import-lookups`.** It forces you to commit `cdk.context.json` for deterministic builds in CI.

</details>

---

**Q7.** What's the `IAspect` interface?

- A. A class that auto-generates IAM policies
- B. A class with one method, `visit(node)`, that CDK calls for every construct at synth time
- C. The CDK CLI
- D. A CloudFormation resource type

<details><summary>Show answer</summary>

**B — A class with one method, `visit(node)`.** CDK calls it for every construct in the tree at synth time. Common use cases: enforce tags, warn on missing encryption, add permissions boundaries.

</details>

---

**Q8.** What's the difference between `Annotations.of(node).addWarning(...)` and `addError(...)`?

- A. `addWarning` is non-fatal; `addError` fails the synth with a non-zero exit
- B. They are the same
- C. `addWarning` writes to stdout; `addError` writes to stderr
- D. `addError` is for production; `addWarning` is for dev

<details><summary>Show answer</summary>

**A — `addWarning` is non-fatal; `addError` fails the synth.** Use warnings for "you should look at this"; use errors for "this should not be allowed."

</details>

---

**Q9.** What's the recommended pattern for DR (disaster recovery) with CDK in 2026?

- A. One App, one Stack, cross-region resource references
- B. Two separate Apps (one per region), kept in sync via CI
- C. CDK doesn't support DR
- D. CloudFormation nested stacks

<details><summary>Show answer</summary>

**B — Two separate Apps.** Cross-region references in a single App introduce indirection that isn't worth it. Two apps are easier to reason about and easier to test.

</details>

---

**Q10.** Which library wraps a multi-stack CDK app into a self-mutating CI/CD pipeline?

- A. `aws-cdk-lib/pipelines`
- B. `aws-cdk-lib/cicd`
- C. `aws-cdk-lib/aws-codebuild`
- D. `aws-cdk-lib/aws-codepipeline`

<details><summary>Show answer</summary>

**A — `aws-cdk-lib/pipelines`.** The `CodePipeline` L3 construct + `ShellStep` / `CodeBuildStep` helpers. It's the canonical way to ship CDK to multiple environments with a single pipeline.

</details>
