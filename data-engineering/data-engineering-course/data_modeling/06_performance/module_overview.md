# Module 06 — Performance Optimization

> **3 lessons · 0 videos · ~1 hour**
>
> **Author:** Prem Vishnoi <prem.vishnoi@example.com>

You drew the star schema. You picked the fact type. You defined
the SCDs. Now: will the queries actually run?

A schema that scores a 4/4 in the modeling round scores a 1/4
in the performance round if you can't justify your indexing
strategy, your partitioning key, or your materialized-view
choice. This module closes that gap with three lessons and
working SQLite code for each.

---

## What this module covers

| # | Lesson | What you'll learn |
|---|---|---|
| [28](design/28_indexing.md) | Indexing Strategies | B-tree vs bitmap vs partial — pick by cardinality. |
| [29](design/29_partitioning.md) | Partitioning | Range, hash, list — and why date is usually wrong. |
| [30](design/30_materialized_views.md) | Materialized Views | Pre-compute the expensive join; refresh on a schedule. |

---

## How the code is organized

```
06_performance/
├── code/
│   ├── indexing.py             # 3 demo queries, B-tree/bitmap/partial
│   ├── partitioning.py         # range vs hash partitions on date+region
│   └── materialized_views.py   # MView + refresh strategies
└── tests/
    └── test_performance.py
```

Run the tests:

```bash
python3 -m unittest data_modeling/06_performance/tests/test_performance.py
```

Run the demos:

```bash
python3 data_modeling/06_performance/code/indexing.py
python3 data_modeling/06_performance/code/partitioning.py
python3 data_modeling/06_performance/code/materialized_views.py
```

Each script seeds the same 100k fact-table fixture, runs the
demonstration query, prints the plan + the elapsed time, and
asserts that the chosen strategy is the fastest of the three.

---

## The interview rule

Performance questions are *always* trade-off questions:

- **"Would you index this?"** → *it depends on the cardinality
  of the column and the read/write ratio of the table.*
- **"Would you partition by date?"** → *only if the queries
  always filter on a contiguous date range; otherwise you're
  paying partition-pruning overhead for nothing.*
- **"Would you pre-aggregate?"** → *only if the query runs
  more often than the underlying data changes; otherwise the
  refresh cost dominates.*

The candidate who gives one of these answers is 4/4. The
candidate who says "yes, index everything, partition by date,
and pre-aggregate" is 1/4 — they're describing the default
configuration, not a design choice.

---

*Author: Prem Vishnoi <prem.vishnoi@example.com>*