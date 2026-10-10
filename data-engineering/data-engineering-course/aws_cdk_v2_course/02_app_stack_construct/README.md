# Section 2 — App, Stack, Construct (L05–L10)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **L-IDs:** L05–L10 | **Duration:** ~65 min | **Quizzes:** `quizzes/section_2.md`
> **Working artifact:** `code/hello-cdk/` — minimal S3 bucket stack.

Section 2 is where CDK becomes concrete. You learn the **construct
tree** (App → Stack → Construct), the 3 construct levels (L1/L2/L3),
and the **synth → deploy** lifecycle. By the end you'll have a
working `hello-cdk` project.

## Lectures

| L# | Title | Min | File |
|---|---|---|---|
| L05 | The CDK construct tree — App → Stack → Construct | 11 | `lecture_scripts/L05_construct_tree.md` |
| L06 | L1, L2, L3 constructs — when to use which | 12 | `lecture_scripts/L06_l1_l2_l3.md` |
| L07 | `cdk init` — the TypeScript project template | 10 | `lecture_scripts/L07_cdk_init.md` |
| L08 | `cdk synth` — turning TypeScript into a CloudFormation template | 12 | `lecture_scripts/L08_cdk_synth.md` |
| L09 | Escape hatches and `Stack.of(scope)` | 10 | `lecture_scripts/L09_escape_hatches.md` |
| L10 | `cdk deploy` + `cdk destroy` + stack outputs | 10 | `lecture_scripts/L10_cdk_deploy_destroy.md` |

## Working code

| Project | Stack summary | Tests |
|---|---|---|
| `code/hello-cdk/` | 1 S3 bucket + `CfnOutput` | 5 Jest assertions on the synthesized template |
