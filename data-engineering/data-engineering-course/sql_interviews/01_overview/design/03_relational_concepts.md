# Lesson 03 — Relationships and Relational Database Concepts

> **Goal:** know the vocabulary interviewers use — relation,
> tuple, key, foreign key, cardinality — and the difference
> between OLTP and OLAP.

---

## The relational model in one paragraph

A **relation** is a set of **tuples** (rows) sharing the same
**attributes** (columns). A relation has no order and no
duplicate tuples. Every value in a tuple is atomic (1NF). A
**key** is a subset of attributes whose values uniquely identify
each tuple. A **foreign key** is an attribute in one relation
that refers to a key in another.

That's the model. The rest of SQL is a notation for asking
questions about it.

---

## The vocabulary

| Term | What it means | SQL keyword |
|---|---|---|
| Relation | A table. | `TABLE`, `VIEW` |
| Tuple | A row. | `ROW` |
| Attribute | A column. | `COLUMN` |
| Cardinality | How many rows a table has. | `COUNT(*)` |
| Degree | How many columns a relation has. | n/a |
| Primary key | The chosen key. | `PRIMARY KEY` |
| Foreign key | A reference to a key elsewhere. | `REFERENCES` |
| Null | "Unknown / not applicable". | `NULL` |
| Domain | The set of allowed values. | `CHECK`, type |

Interviewers will use these words. If you don't know them you
will spend mental cycles translating.

---

## Keys and integrity

**Primary key** — one or more columns that uniquely identify
each row. In SQL: `PRIMARY KEY`. The database engine uses the
PK as the clustered index in most engines (PostgreSQL, MySQL
InnoDB, SQL Server). Picking a small, immutable, integer PK
makes life easier for everyone.

**Foreign key** — a column whose values must match the PK
of another table (or be NULL). In SQL: `REFERENCES
other_table(pk)`. Foreign keys are how the database enforces
referential integrity: you cannot insert a row referencing a
parent that doesn't exist.

**Natural key vs surrogate key** — sometimes the data has a
natural unique column (email, SSN, ISBN). More often we
manufacture an integer surrogate (`id`) because the natural
key is long, mutable, or nullable. Both are fine; mixing the
two in one table is the source of many bugs.

**Composite key** — a key made of multiple columns. Common
in junction tables (M:N relations): `order_id, product_id`
together identify a row in `order_items`.

---

## Cardinality

When you describe a relationship between two tables, you
name the cardinality. Read the symbol left to right.

| Symbol | Meaning | Example |
|---|---|---|
| `1:1` | One row in A matches exactly one row in B. | Person ↔ Passport |
| `1:N` | One row in A matches many rows in B. | Department ↔ Employee |
| `N:M` | Many rows in A match many rows in B. | Student ↔ Class |
| `0..1` | Optional (0 or 1). | Employee ↔ Manager (the CEO has no manager). |
| `0..*` | Zero or more. | Person ↔ Orders (a new customer has none). |

N:M is implemented as a third *junction* (or *bridge*) table
with two foreign keys, one to each side.

---

## OLTP vs OLAP

A fact interviewers expect you to know:

- **OLTP** (Online Transaction Processing) — the system of
  record. Many small writes, single-row reads, strong
  consistency. PostgreSQL, MySQL, Oracle. Normalized to 3NF.
- **OLAP** (Online Analytical Processing) — the reporting
  warehouse. Few large reads, full-table scans, denormalized
  star or snowflake schemas. Snowflake, BigQuery, Redshift.

SQL is the same language on both. The differences are
*workload*, *schema shape*, and *indexing strategy*. A query
that runs in 50 ms in an OLTP database can take 50 minutes in
an OLAP one (and vice versa) for completely structural
reasons.

Data engineers spend most of their time moving data from
OLTP into OLAP. The pattern is: extract from source, transform
in Spark/dbt, load into warehouse, serve to BI tools.

---

## Referential actions

Foreign keys come with *referential actions* — what to do
when the parent row is deleted or updated.

| Action | On delete of parent |
|---|---|
| `RESTRICT` (default) | Reject the delete. |
| `CASCADE` | Delete the children too. |
| `SET NULL` | Null out the children's FK. |
| `SET DEFAULT` | Set the children's FK to its default value. |
| `NO ACTION` | Like RESTRICT, but checked at the end of the transaction. |

In practice: `CASCADE` is rare in production (too easy to
delete a million rows by accident). `SET NULL` is common for
optional relationships. `RESTRICT` is the default and the
safest.

---

## Try it

Look at any OLTP schema you've seen (the e-commerce star in
the data modeling track, the URL shortener in the system
design track). For each foreign key, identify:

1. The parent table and column.
2. The cardinality (1:1, 1:N, N:M).
3. The referential action on delete.

This is the muscle you'll use to read any schema in an
interview. It also prepares you for the "design a schema
for X" prompts, which are part of every data modeling round.
