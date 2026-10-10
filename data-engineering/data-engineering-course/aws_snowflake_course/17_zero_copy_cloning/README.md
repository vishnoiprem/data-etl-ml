# Section 17 — Zero-Copy Cloning

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Lectures:** L116–L121
> **Duration:** ~28 min

Section 16 finished the safety-net story (Time Travel + Fail Safe +
table types). Section 17 introduces the Snowflake feature that turns
all of that storage into an *asset* instead of a cost: **Zero-Copy
Cloning**. The headline is wild enough that it's worth restating —
Snowflake can clone a multi-terabyte table in **under a second**, and
the clone initially costs **zero extra storage**. The copy only
materializes when the source and clone diverge.

We start with the **concept** (L116) — how Snowflake's micro-partition
metadata makes this possible, and why zero-copy is not the same as
"free forever". **Cloning tables** (L117) shows the actual
`CREATE TABLE ... CLONE` syntax on single tables. **Cloning schemas &
databases** (L118) lifts the same idea to entire logical containers.
**Cloning with time travel** (L119) combines clone + `AT` / `BEFORE`
to fork from a historical point in time. **Swapping tables + Hands-on**
(L120) introduces `ALTER TABLE ... SWAP WITH`, the cheap atomic rename
trick used by every production ELT pipeline. Section 17 closes with a
recap (L121).

By the end of this section you should be able to clone any object,
swap two tables atomically, and reason about when the storage bill
finally catches up to the clone.

| L# | Title | Min |
|---|---|---|
| L116 | Understanding Zero-Copy Cloning | 5:00 |
| L117 | Cloning tables | 5:00 |
| L118 | Cloning schemas & databases | 4:00 |
| L119 | Cloning with time travel | 5:00 |
| L120 | Swapping tables + Hands-on | 5:00 |
| L121 | Zero-Copy Cloning recap | 4:00 |

## Key concepts you'll need later

- **Zero-copy clone** — a metadata-only copy of a table/schema/db at
  the micro-partition level. Instant, zero added storage at clone
  time; storage accrues only on divergence.
- **`CREATE TABLE x CLONE y`** — clone a table, optionally with
  `AT (TIMESTAMP => ...)` for a historical fork.
- **`ALTER TABLE x SWAP WITH y`** — atomic rename of two tables.
  Used by ELT "swap and drop" patterns.
- **Cloning clones** — fully supported; you can clone a clone, or
  clone a clone of a clone.

## What comes next

Section 18 is **Data Sharing** — the third Snowflake superpower after
separation of storage/compute and zero-copy cloning. You'll learn how
to give another Snowflake account (or a non-Snowflake consumer)
*read-only* access to your data without copying a single byte.