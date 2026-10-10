# Section 2 Quiz — App, Stack, Construct

> 12 questions, multi-choice. Answers hidden in collapsible blocks.

---

**Q1.** What is the parent of a `cdk.Stack`?

- A. The `cdk.App`
- B. The `cdk.Construct` directly
- C. A CloudFormation change set
- D. The CDK CLI

<details><summary>Show answer</summary>

**A — The `cdk.App`.** The App is the root of the construct tree. Every Stack is created with `new Stack(app, ...)`; every Construct is created with `new X(stack, ...)`.

</details>

---

**Q2.** Which construct level is a 1-to-1 mapping to a CloudFormation resource?

- A. L1 (`Cfn*`)
- B. L2 (`s3.Bucket`, `lambda.Function`, ...)
- C. L3 (`LambdaRestApi`, `ApplicationLoadBalancedFargateService`, ...)
- D. None — CDK only generates L2

<details><summary>Show answer</summary>

**A — L1.** `s3.CfnBucket` corresponds to `AWS::S3::Bucket`; `lambda.CfnFunction` corresponds to `AWS::Lambda::Function`. L1 gives you full control with no defaults.

</details>

---

**Q3.** Which construct level is recommended for the **bulk** of your code?

- A. L1
- B. L2
- C. L3
- D. Raw CloudFormation

<details><summary>Show answer</summary>

**B — L2.** L2 constructs come with sane defaults (encryption, public-access block) and helper methods (`grantX`, `metricX`). Use L1 only when an L2 doesn't exist or you need full control.

</details>

---

**Q4.** What does `cdk init app --language typescript` create?

- A. A CloudFormation template
- B. A new empty directory
- C. A TypeScript CDK project with `bin/`, `lib/`, `test/`, `cdk.json`, `package.json`
- D. A new AWS account

<details><summary>Show answer</summary>

**C — A TypeScript CDK project.** It writes the standard project layout so you don't have to start from scratch.

</details>

---

**Q5.** Where does the default stack file live after `cdk init`?

- A. `bin/app.ts`
- B. `lib/<project>-stack.ts`
- C. `cdk.json`
- D. `package.json`

<details><summary>Show answer</summary>

**B — `lib/<project>-stack.ts`.** The bin file is the App entry; the lib file is the Stack.

</details>

---

**Q6.** What does `cdk synth` do?

- A. Deploys your stack to AWS
- B. Emits CloudFormation templates to `cdk.out/`
- C. Runs your unit tests
- D. Initializes a new project

<details><summary>Show answer</summary>

**B — Emits CloudFormation templates to `cdk.out/`.** It doesn't deploy; use `cdk deploy` for that.

</details>

---

**Q7.** Which command previews the changes `cdk deploy` would make to the deployed stack?

- A. `cdk synth`
- B. `cdk diff`
- C. `cdk plan`
- D. `cdk preview`

<details><summary>Show answer</summary>

**B — `cdk diff`.** It shows the CloudFormation diff between your local code and the deployed stack. (Terraform calls this `plan`; CDK calls it `diff`.)

</details>

---

**Q8.** What's the primary purpose of an **escape hatch** in CDK?

- A. To allow you to break out of the L2 abstraction and modify the underlying L1
- B. To run `cdk deploy` from a CI pipeline
- C. To escape from a deadlock in the construct tree
- D. To back out of a failed `cdk deploy`

<details><summary>Show answer</summary>

**A — To allow you to break out of the L2 abstraction and modify the underlying L1.** Use cases include properties the L2 doesn't expose, or brand-new AWS service features not yet covered by an L2.

</details>

---

**Q9.** Which static helper finds the Stack a Construct belongs to?

- A. `Construct.stack`
- B. `cdk.Stack.of(scope)`
- C. `cdk.findStack(construct)`
- D. `scope.parentStack`

<details><summary>Show answer</summary>

**B — `cdk.Stack.of(scope)`.** It's the only stable way to get the stack from a construct reference; the others either don't exist or change between CDK versions.

</details>

---

**Q10.** What does `cdk destroy` do?

- A. Deletes the local project directory
- B. Deletes the CloudFormation stack and its resources (with DESTROY removal policy)
- C. Uninstalls the CDK CLI
- D. Removes the `cdk.out/` directory

<details><summary>Show answer</summary>

**B — Deletes the CloudFormation stack and its resources.** Resources with `removalPolicy: RETAIN` (the default for many) survive; resources with `DESTROY` are removed.

</details>

---

**Q11.** What is the purpose of `CfnOutput`?

- A. To print to stdout during synth
- B. To expose a value in the CloudFormation console and make it importable in another stack
- C. To log a value at deploy time
- D. To create a CloudWatch alarm

<details><summary>Show answer</summary>

**B — To expose a value in the CloudFormation console and make it importable in another stack.** `cdk output` reads it back; another stack can `Fn.importValue` it by `exportName`.

</details>

---

**Q12.** Why do construct IDs matter?

- A. They become CloudFormation logical IDs
- B. They are used by the CDK CLI's autocomplete
- C. They are the resource's IAM role name
- D. They don't matter — they can be anything

<details><summary>Show answer</summary>

**A — They become CloudFormation logical IDs.** The construct path is hashed to produce a stable CFN ID. Reordering the tree changes the ID, which causes CFN to **replace** the resource.

</details>
