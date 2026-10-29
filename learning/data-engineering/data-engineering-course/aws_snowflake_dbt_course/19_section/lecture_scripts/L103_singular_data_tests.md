---
l_id: L103
title: Singular data tests
duration: "4:45"
prereqs: [L102]
downloads: []
---

# L103 — Singular data tests

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 19 — Tests, Snapshots, Microbatch, Advanced, Final Exam
> **Duration:** ~4:45

## Prereqs

Watch **L102** first.

## Lecture

This lecture covers **Singular data tests** as part of the **Tests, Snapshots, Microbatch, Advanced, Final Exam** section.

Singular data tests is one of the official dbt Analytics Engineer exam topics
mapped to this section. We work through it in the context of the
shared Ethereum dbt project at `dbt_project/`.

### What you'll learn

- The exam objective this lecture maps to.
- The dbt project files you add or modify.
- The Snowflake-side configuration involved (if any).
- How the concept appears in the final exam.

### Demo

Run through the relevant dbt project files for this lecture. Each
lecture that introduces a new dbt artifact adds it to `dbt_project/`;
isolated experiments live under this section's `code/`.

## Hands-on

Apply the concept to the Ethereum dbt project. The exact lab is
documented in the lecture slide deck (see `downloads/`).

## Quiz prep

Make sure you can answer:

- What dbt concept does this lecture introduce?
- How is it configured in `dbt_project.yml` or via a config block?
- What's the relevant Snowflake or dbt CLI command?

The section quiz in `quizzes/section_19.md` tests these.

## Further reading

- `../../dbt_project/` — the shared runnable dbt project.
- `../../SYLLABUS.md` — authoritative lecture-to-file map.
- dbt docs: <https://docs.getdbt.com/>

## What's next

Next up is **L104 — Generic data tests - Part 1**.
