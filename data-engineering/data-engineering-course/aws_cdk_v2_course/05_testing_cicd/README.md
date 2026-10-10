# Section 5 — Testing, Snapshots, Assertions, CI/CD (L21–L25)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **L-IDs:** L21–L25 | **Duration:** ~55 min | **Quizzes:** `quizzes/section_5.md`
> **Working demo:** `code/snapshot-demo/` — Jest snapshot test for `hello-cdk`.

Section 5 turns "I can synth" into "I have CI/CD that proves the
synth is correct." This is the difference between a hobby project
and a production one.

## Lectures

| L# | Title | Min | File |
|---|---|---|---|
| L21 | Why test CDK stacks — synth vs deploy safety net | 10 | `lecture_scripts/L21_why_test.md` |
| L22 | `aws-cdk-lib/assertions` — `Template.fromStack` | 12 | `lecture_scripts/L22_assertions.md` |
| L23 | Jest snapshot tests with CDK | 11 | `lecture_scripts/L23_snapshots.md` |
| L24 | Fine-grained assertions — `hasResourceProperties`, `objectLike` | 12 | `lecture_scripts/L24_fine_grained.md` |
| L25 | CI/CD for CDK — `cdk diff` in PRs, GitHub Actions, OIDC | 10 | `lecture_scripts/L25_cicd.md` |

## Working demo

| Folder | What it shows |
|---|---|
| `code/snapshot-demo/` | A second test file for `hello-cdk` that uses **snapshot testing** (the L23 pattern) instead of `Template.fromStack` |

The `hello-cdk/` stack already has 5 fine-grained assertions (L24
style) in its own test file; the snapshot demo adds an alternative
style for comparison.
