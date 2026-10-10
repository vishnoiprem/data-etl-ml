# Section 18 — Data Sharing

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Lectures:** L122–L132
> **Duration:** ~52 min

Section 17 ended with the third superpower — *distribution*. With
**zero-copy cloning** behind you, Snowflake can give another account
read-only access to your data without duplicating a single byte,
without an ETL pipeline, and without you maintaining a separate
database. That mechanism is **Data Sharing**, and section 18 is its
end-to-end walkthrough.

We start with **Understanding data sharing** (L122) — what a share
is, how the producer/consumer model works, and why "no copy" matters.
**Using data sharing** (L123) reviews the SQL surface — `CREATE
SHARE`, `GRANT REFERENCE`, `ALTER SHARE`. We then walk the UI path
in **Create share through the interface** (L124). **Sharing with
non-snowflake users** (L125) introduces reader accounts — a way to
share with companies that aren't Snowflake customers yet. **Creating
a reader account** (L126) walks through that setup.

**Creating a database from share** (L127) flips to the consumer side:
the one-line `CREATE DATABASE ... FROM SHARE`. **Set up users for
share** (L128) covers the access-control work on the consumer
account. **Sharing database & schema** (L129) goes back to the
producer side to walk through end-to-end examples with multiple
objects. **Secure vs. normal view** (L130) introduces secure views —
the only kind of view you can share. **Sharing a secure view** (L131)
puts that into a full worked example. We close with **Share data from
multiple databases** (L132) — the most common production pattern,
combining data from several sources into one logical dataset.

| L# | Title | Min |
|---|---|---|
| L122 | Understanding data sharing | 4:30 |
| L123 | Using data sharing | 4:30 |
| L124 | Create share through the interface | 4:30 |
| L125 | Sharing with non-snowflake users | 5:00 |
| L126 | Creating a reader account | 5:00 |
| L127 | Creating a database from share | 4:30 |
| L128 | Set up users for share | 5:00 |
| L129 | Sharing database & schema | 5:00 |
| L130 | Secure vs. normal view | 4:30 |
| L131 | Sharing a secure view | 5:00 |
| L132 | Share data from multiple databases | 4:30 |

## Key concepts you'll need later

- **Share** — a named, read-only bundle of database objects you give
  to one or more consumer accounts.
- **Producer / consumer** — the two roles in a share. The producer
  owns the data; the consumer can query it.
- **Reader account** — a Snowflake-managed account owned by you,
  used to share with non-Snowflake consumers.
- **Secure view** — the only view type eligible to be shared.
- **Database from share** — the consumer-side one-liner that mounts
  a shared database locally.

## What comes next

Section 19 is **Data Sampling** — a small section that shows you how
to pull statistically valid subsets out of huge tables for testing,
dev, and ML training.