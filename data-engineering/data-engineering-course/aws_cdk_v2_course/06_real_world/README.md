# Section 6 — Real-World Patterns (L26–L30)

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **L-IDs:** L26–L30 | **Duration:** ~60 min | **Quizzes:** `quizzes/section_6.md`
> **Working artifact:** see `assignments/assignment_1_multi_stack.md`.

Section 6 is the closing arc. By now you can build a single stack.
The real world is **multi-stack**, **multi-region**, and
**multi-account**. This section teaches the patterns that make CDK
production-ready.

## Lectures

| L# | Title | Min | File |
|---|---|---|---|
| L26 | Multi-stack applications — shared VPC, network + app stacks | 12 | `lecture_scripts/L26_multi_stack.md` |
| L27 | Cross-region stacks — DR, global APIs, regional resources | 12 | `lecture_scripts/L27_cross_region.md` |
| L28 | `cdk.context` — environment values, lookups, `cdk.json` | 12 | `lecture_scripts/L28_cdk_context.md` |
| L29 | CDK Aspects — organization-wide compliance tags | 12 | `lecture_scripts/L29_aspects.md` |
| L30 | Course wrap-up — CDK vs CFN in 2026, when to reach for what | 12 | `lecture_scripts/L30_wrap_up.md` |

## Assignment

| File | Topic | Time |
|---|---|---|
| `../assignments/assignment_1_multi_stack.md` | Build a `NetworkStack` + `AppStack` pair sharing a VPC | 4–6h |
