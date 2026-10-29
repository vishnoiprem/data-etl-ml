# Section 5 Quiz — Testing, Snapshots, Assertions, CI/CD

> 10 questions, multi-choice. Answers hidden in collapsible blocks.

---

**Q1.** What does `Template.fromStack(stack)` return?

- A. The deployed CloudFormation stack
- B. A `Template` object holding the synthesized CFN template
- C. A JSON string
- D. A Jest snapshot

<details><summary>Show answer</summary>

**B — A `Template` object.** It holds the synthesized CFN template in memory; you then call assertion methods on it.

</details>

---

**Q2.** Is `hasResourceProperties('AWS::S3::Bucket', { VersioningConfiguration: { Status: 'Enabled' } })` an exact or subset match?

- A. Exact — every field of the resource must match
- B. Subset — the asserted fields must be present, others are wildcard
- C. Regex — it matches against the property name
- D. It only works for the bucket type

<details><summary>Show answer</summary>

**B — Subset.** That's the whole point: you assert the parts you care about; everything else is wildcard.

</details>

---

**Q3.** Which `Match` helper asserts a partial object match?

- A. `Match.exactValue`
- B. `Match.objectLike`
- C. `Match.partial`
- D. `Match.subset`

<details><summary>Show answer</summary>

**B — `Match.objectLike`.** It also has `arrayWith`, `arrayEquals`, `stringLikeRegexp`, `anyValue`, `serializedJson`, and `absent`.

</details>

---

**Q4.** Which flag updates Jest snapshots?

- A. `--refresh`
- B. `-u` / `--updateSnapshot`
- C. `--save`
- D. `--fix`

<details><summary>Show answer</summary>

**B — `-u` or `--updateSnapshot`.**

</details>

---

**Q5.** What's a downside of relying only on snapshot tests?

- A. They require an AWS account
- B. They are slow
- C. They produce noisy diffs during development and are easy to rubber-stamp
- D. They are deprecated

<details><summary>Show answer</summary>

**C — They produce noisy diffs and are easy to rubber-stamp.** The balanced approach is: explicit assertions for properties you care about + a single snapshot as a safety net.

</details>

---

**Q6.** Which matcher would you use to assert a state-machine definition (a stringified JSON)?

- A. `Match.stringLikeRegexp`
- B. `Match.serializedJson`
- C. `Match.jsonString`
- D. `Match.deepEqual`

<details><summary>Show answer</summary>

**B — `Match.serializedJson`.** It parses the string and matches the inner object against the inner matcher.

</details>

---

**Q7.** What's the main benefit of using OIDC for CI/CD instead of long-lived AWS access keys?

- A. OIDC is faster
- B. No long-lived secret; federated trust is scoped to the repo
- C. OIDC works without IAM roles
- D. OIDC lets you skip `cdk synth`

<details><summary>Show answer</summary>

**B — No long-lived secret.** The CI job assumes an IAM role via an OIDC trust scoped to the repo; no access key is ever stored in the CI.

</details>

---

**Q8.** Which command shows the diff between your local CDK code and the deployed stack?

- A. `cdk diff`
- B. `cdk synth`
- C. `cdk plan`
- D. `cdk compare`

<details><summary>Show answer</summary>

**A — `cdk diff`.** (Terraform uses `plan`; CDK uses `diff`.)

</details>

---

**Q9.** In a typical CI pipeline, when should you run `cdk deploy`?

- A. On every PR
- B. After merge to main, ideally with manual approval for prod
- C. Only at the end of a sprint
- D. Never — let humans deploy

<details><summary>Show answer</summary>

**B — After merge to main.** PRs run `synth` + `diff` + `test`; `deploy` happens on main (or on a manual approval for prod).

</details>

---

**Q10.** What does the `cdk doctor` command do?

- A. Diagnoses common CDK install / config issues
- B. Runs all tests
- C. Deploys a stack with `--no-approval`
- D. None — it doesn't exist

<details><summary>Show answer</summary>

**A — Diagnoses common CDK install / config issues** (wrong Node version, missing creds, etc).

</details>
