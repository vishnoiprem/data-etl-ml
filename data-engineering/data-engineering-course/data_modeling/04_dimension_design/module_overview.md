# Module 04 — Dimension Design

> **3 lessons · 0 videos · ~1.5 hours**
>
> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;

A dimension is the *context* for a fact. The fact tells you what
happened; the dim tells you who, what, where, when, how. The
tricky part is that dimensions *change* over time — a user's
country changes, a product's category changes, a city's rate
card changes — and the schema has to decide how to handle those
changes.

This module covers the three big dimension patterns: SCD Types
1/2/3 (Lesson 21), conformed and role-playing dimensions
(Lesson 22), and junk / degenerate dimensions (Lesson 23).

---

## What this module covers

| # | Lesson | What you'll learn |
|---|---|---|
| [21](design/21_dimension_table_design.md) | Dimension Table Design | The anatomy of a dim: PK, NK, attributes, SCD flag, audit columns, and the wide-and-denormalized rule. |
| [22](design/22_slowly_changing_dimensions.md) | Slowly Changing Dimensions (SCDs) | SCD Type 1, 2, 3 deep dive; the temporal join. |
| [23](design/23_advanced_dimension_design_techniques.md) | Advanced Dimension Design Techniques | Conformed, role-playing, junk, degenerate, plus multi-valued dims and the bridge-table pattern. |

---

## How the code is organized

```
04_dimension_design/
├── code/
│   └── scd.py    # the three SCD implementations + helpers
└── tests/
    └── test_scd.py
```

Run the tests:

```bash
python3 -m unittest data_modeling/04_dimension_design/tests/test_scd.py
```

The tests pin down the behavior of each SCD type against an
in-memory SQLite table. You can read `code/scd.py` and see
exactly how SCD 1/2/3 work in practice.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
