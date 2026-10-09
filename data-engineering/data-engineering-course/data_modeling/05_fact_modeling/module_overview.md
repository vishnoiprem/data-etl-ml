# Module 05 — Fact Data Modeling

> **4 lessons · 0 videos · ~1.5 hours**
>
> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;

A fact is a measurement. But not all facts are the same shape.
The Kimball taxonomy gives us four fact-table types, and the
choice of type drives the rest of the schema. This module
covers all four, with working SQLite examples for each.

---

## What this module covers

| # | Lesson | What you'll learn |
|---|---|---|
| [24](design/24_transactional.md) | Transactional Fact Tables | One row per event. The default. |
| [25](design/25_periodic_snapshot.md) | Periodic Snapshot Fact Tables | One row per (entity, period). For state at regular intervals. |
| [26](design/26_accumulating_snapshot.md) | Accumulating Snapshot Fact Tables | One row per lifecycle. For processes with milestones. |
| [27](design/27_factless.md) | Factless Fact Tables | One row per event, no measures. For "this happened" tracking. |

---

## How the code is organized

```
05_fact_modeling/
├── code/
│   └── fact_tables.py    # 4 build_*_fact(q) functions
└── tests/
    └── test_facts.py
```

Run the tests:

```bash
python3 -m unittest data_modeling/05_fact_modeling/tests/test_facts.py
```

Each test pins down one of the four fact types. The tests
verify the right shape (grain, columns, measures) and the
right data (additive vs semi-additive, factless vs numeric).

Run the demo:

```bash
python3 data_modeling/05_fact_modeling/code/fact_tables.py
```

This builds all 4 fact tables in `:memory:` SQLite and prints
the sample fact row from each.

---

## The four types at a glance

| Type | Grain | Mutability | When to use |
|---|---|---|---|
| Transactional | one row per event | append-only | atomic events (orders, clicks, payments) |
| Periodic snapshot | one row per (entity, period) | rebuilt each period | state at regular intervals (MRR, inventory) |
| Accumulating snapshot | one row per lifecycle | updated as lifecycle progresses | processes with milestones (orders, applications) |
| Factless | one row per event | append-only | "this happened" tracking (attendance, eligibility) |

The interview rule: pick the right type, then defend it in
one sentence. The candidate who says "transactional because
the events are atomic and append-only" is 4/4. The candidate
who says "transactional" without justification is 2/4.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
