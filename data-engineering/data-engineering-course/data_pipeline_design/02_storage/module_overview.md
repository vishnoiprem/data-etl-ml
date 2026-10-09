# Module 02 — Storage

> **2 lessons · ~1.5 hours**

Where does data come from, where does it go, and what shape does it
have in between? Module 02 grounds the abstract pipeline patterns
from Module 01 in concrete storage primitives: the source on the
left, the sink on the right, and the abstractions that connect them.

Author: **Prem Vishnoi &lt;prem.vishnoi@example.com&gt;**

---

## Lessons

| # | Lesson | What you'll learn |
|---|---|---|
| 06 | [Data Sources](design/06_data_sources.md) | OLTP, APIs, files, event streams — when to use each. |
| 07 | [Data Destinations](design/07_data_destinations.md) | Warehouses, lakehouses, serving layers — when to use each. |

---

## Code

- [`code/storage_abstractions.py`](code/storage_abstractions.py) —
  `Source` / `Sink` abstractions, plus `CsvSource`, `SqliteSink`,
  `MemorySink`, and `BatchSink` implementations.
- [`tests/test_storage.py`](tests/test_storage.py) — 10 unit tests
  covering all four concrete classes plus the abstract base.

---

## What this module is

A pipeline is, at the lowest level, `read rows from somewhere` →
`do something to the rows` → `write rows to somewhere`. This module
makes the *somewhere* concrete: CSV files, SQLite tables, in-memory
lists, batched writers. These four classes appear in every later
module in this track — they're the substrate every other code
example builds on.

The design lessons (06, 07) are the *interview* version of the same
ideas: when you say "API source" in an interview, what tool are you
picking, what failure modes are you accepting, what SLA can you
promise?
