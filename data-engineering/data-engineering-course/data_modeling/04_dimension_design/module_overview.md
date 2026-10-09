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
| [21](design/21_scd_types.md) | Slowly Changing Dimensions: SCD Type 1, 2, 3 | The three SCD types, when to use each, and the SCD 2 temporal join. |
| [22](design/22_conformed_role_playing.md) | Conformed and Role-Playing Dimensions | The two patterns for sharing dims across facts. |
| [23](design/23_junk_degenerate.md) | Junk and Degenerate Dimensions | The two "exception" dims that don't quite fit the standard pattern. |

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
