# `data-engineering/` directory — curated paths

> **Purpose.** This is a curated map of the projects under
> `data-engineering/`. The repo has 18+ subdirectories, most of
> which fall into one of three audiences: (1) a bank-audit /
> fintech-compliance client, (2) a data-engineering hiring
> manager, (3) a course student. The map below shows which
> project serves which audience.

---

## Path 1: "I'm a bank-audit / AML client — show me your serious work"

The path a Standard Chartered-style client should walk in 3 clicks:

1. **[Banking-AML-Data/](./Banking-AML-Data/)** — the headline
   project. AML transaction monitoring, rule engine, case
   management, audit trail. The work most directly relevant to
   a regulated-bank engagement.
2. **[scb_aml_platform/](./scb_aml_platform/)** — Standard
   Chartered Bank–style AML platform scaffold. The
   production-shape variant of #1.
3. **[event-sourced-audit/](./event-sourced-audit/)** — the
   *append-only audit log* pattern, with hash chain. The thing
   regulators actually want to see.
4. **[multi-tenant-isolation/](./multi-tenant-isolation/)** —
   per-tenant data isolation (Postgres RLS, key per tenant).
   The compliance story for SaaS-on-banking.
5. **[cqrs-ledger/](./cqrs-ledger/)** — double-entry ledger with
   CQRS. The accounting primitive a bank audit always asks about.
6. **[financial-reporting-platform/](./financial-reporting-platform/)**
   — IFRS-style financial reporting. The dashboard a CFO sees.
7. **[activity-volume-olap/](./activity-volume-olap/)** — OLAP
   cubes for transaction-volume reporting.

That's a 7-link curated tour that a bank audit client can read
in 30 minutes and walk away with: "this person has built the
specific things we need."

---

## Path 2: "I'm hiring a senior data engineer"

The path a hiring manager walks in 5 clicks:

1. **[activity-volume-olap/](./activity-volume-olap/)** — a
   realistic OLAP build (Kafka → Flink → Druid/Cube.js). Shows
   the streaming-OLAP shape.
2. **[edge-analytics-workers/](./edge-analytics-workers/)** —
   edge / Workers-style analytics. Shows the serverless-elt shape.
3. **[bloomberg-symbology/](./bloomberg-symbology/)** — canonical
   instrument ID + 6-way identifier mapping. Shows the
   "vendor-data quality" problem solved correctly.
4. **[keystone-iceberg-ops/](./keystone-iceberg-ops/)** — Apache
   Iceberg table-format operations. The lakehouse primitive.
5. **[ontology-data-fabric/](./ontology-data-fabric/)** —
   semantic-layer / data-fabric pattern. Shows the
   "consistent metrics across warehouses" problem.
6. **[Banking-AML-Data/](./Banking-AML-Data/)** — the production-
   shape deliverable.

That's 6 links. A staff / principal hiring manager who clicks
them in order sees: streaming OLAP → edge → data quality →
lakehouse → semantic layer → production domain. That's a
*complete* senior-DE picture.

---

## Path 3: "I'm a course student / interview candidate"

This is the *content* side of the directory — the prep material:

- **[data-engineering-course/](./data-engineering-course/)** —
  the comprehensive DE course (2,277 tracked files, 438 SQL,
  1,507 markdown, 6 notebooks). The big study library.
- **[data-engineering-cloudvala/](./data-engineering-cloudvala/)**
  — interview-prep Q&A (Spark / Snowflake / Python top-50) +
  course curricula outlines. (Renamed 2026-10-13 to fix the
  "enginnering" typo.)
- **[clp_projects/](./clp_projects/)** — 3 small reference
  projects (data_qa, forecasting, supplier_llm). End-to-end
  with full code; designed for portfolio use.

---

## The "structural" projects (audience-independent)

These are the *infrastructure pattern* projects — useful in any
conversation, not tied to a specific audience:

- **[e-commerce-end-2end/](./e-commerce-end-2end/)** — full
  e-commerce data pipeline.
- **[data-engineering/](./README.md)** — this directory's
  top-level README.

---

## What was cleaned in 2026-10-13

Two changes to make the directory easier to navigate:

1. **Removed the empty `data-engineering/data-engineering/`
   wrapper.** It contained a single subdirectory and nothing
   tracked. The "course lives at `data-engineering/data-
   engineering/data-engineering-course/`" nesting was a
   navigation trap; now the course is at
   `data-engineering/data-engineering-course/` (one level
   shallower).
2. **Renamed `data-enginnering-cloudvala/` →
   `data-engineering-cloudvala/`** (typo fix: "enginnering"
   → "engineering"). History is preserved; the rename is
   recorded as a `git mv` so file history is unbroken.

---

**Last updated:** 2026-10-13  
**License:** MIT — use freely in your own courses, prototypes, and products.  
