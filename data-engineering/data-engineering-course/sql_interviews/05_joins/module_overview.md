# Module 05 — Joins

> **8 lessons · 0 videos · ~1.5 hours**
>
> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

Joins are how SQL combines tables. By the end of M05 you
should be able to draw the Venn diagram for any join
mentioned in an interview, write an anti-join in three
different syntactic forms, and know when the optimizer can
reorder your joins.

M05 is the most-revisited module in the track. Almost every
M07-M09 problem involves a join of some kind. Read it once,
then return to it as needed.

---

## What this module covers

| # | Lesson | What you'll learn |
|---|---|---|
| [28](design/28_inner_join.md) | INNER JOIN — row-by-row match | The default join. |
| [29](design/29_left_join.md) | LEFT JOIN — keep all left rows | The "include everything" join. |
| [30](design/30_self_joins.md) | Self-joins | Joining a table to itself. |
| [31](design/31_anti_joins.md) | Anti-joins (NOT IN, NOT EXISTS, LEFT JOIN ... IS NULL) | "In A but not in B" — three ways. |
| [32](design/32_cross_joins.md) | Cross joins and Cartesian products | Every-row-pairs join. |
| [33](design/33_multi_table_joins.md) | Multiple-table joins | Joining 3+ tables. |
| [34](design/34_join_order.md) | Join order and the optimizer | What the engine can and can't reorder. |
| [35](design/35_natural_vs_explicit.md) | Natural joins vs explicit joins | Why `NATURAL JOIN` is a code smell. |

---

## How to read this module

The lessons are short. Read them in order. Pay extra
attention to Lesson 31 (anti-joins) — the three syntactic
forms are not equivalent when NULLs are involved, and the
interviewers will ask.
