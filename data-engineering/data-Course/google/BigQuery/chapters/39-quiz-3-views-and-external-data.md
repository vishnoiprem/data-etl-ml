# 39 · Quiz 3 — External Data, Views & Materialized Views

> **Section 5 · External Data, Views & Materialized Views · Lectures 5.1–5.4**
>
> Twelve questions covering the lake layer, the logical view, and the materialized view —
> and when each one is the right tool. Answers and reasoning are at the bottom — try to
> answer first.

---

## 📝 Questions

**1. External vs managed.** A 400 TB Parquet lake sits in Cloud Storage and a dashboard
queries 2 TB of it daily. Name the table type for the dashboard and state the cost
difference against a managed table.

**2. Where does the schema live?** An external table over files with no schema file.
What does BigQuery use, and what are the two risks of relying on it?

**3. The external table limitation list.** Name **four** things you cannot do to an
external table that you can do to a managed table, and give one operational consequence
for each.

**4. Hive partitioning.** Explain what `hive_partition_uri_prefix` does, and how
Hive-style partitioning in the URI path gives you the pruning benefit you would
otherwise get from a native partition column.

**5. The view's hidden cost.** A logical view is "just a stored query." Why can a view
be *more* expensive than the equivalent query you write by hand?

**6. Row-level security.** Two mechanisms are taught for restricting rows to a user.
Name both, explain how each works, and state which one is the correct choice for
row-level security and why.

**7. `SESSION_USER()`.** What does it return, and what caveat does the course give about
BI connectors?

**8. View vs materialized view — the table.** Complete the comparison for four
dimensions: **cost**, **freshness**, **what the source can be**, and **what you can do
with the result**.

**9. The single-base-table rule.** State the rule, explain why it bites, and describe the
workaround pattern the course recommends.

**10. MV freshness control.** Name the two options that control how fresh an MV is, and
explain what each one does — including which one you use to force a refresh by hand.

**11. The 30-second design rule.** A team wants an MV that joins three tables and
aggregates. Why won't BigQuery build it, and what do you build instead?

**12. Putting it together.** For each, choose external table, logical view, or
materialized view, and justify:
   - (a) A compliance export of a table, filtered to one customer, shared with their
     own BI tool
   - (b) A dashboard that shows daily order counts for the last 90 days, hit 200×/day
   - (c) A raw Parquet drop in Cloud Storage that analysts explore ad hoc
   - (d) A reusable definition of "active customers" that joins orders and sessions,
     used by ten different teams

---

## ✅ Answers

**1. External vs managed.** **External table** over the Parquet files. You pay to scan
   the 2 TB you actually read, every day, and nothing for the other 398 TB. A managed
   table would copy all 400 TB into BigQuery and then bill you for storing it — at
   $0.02/GiB/month that is roughly **$7,800/month** for the whole lake, versus the
   scanning cost of 2 TB/day (≈ 60 TiB/month ≈ **$375/month** at $6.25/TiB). The
   external table wins decisively when you read a small fraction of the data.

**2. Where does the schema live?** **Schema auto-detection**: BigQuery samples the files
   and infers column names and types. Two risks:
   - **Type misdetection.** A column sampled as `INTEGER` may later contain a string or
     a larger number, and the inferred schema then rejects the data.
   - **Silent schema drift.** Different file prefixes can infer *different* schemas, and
     an ad hoc load can quietly change a column's type. Always pin an explicit schema
     for anything you depend on.

**3. The external table limitation list.** Four of these:
   - **No clustering** — you cannot reorder or co-locate columns, so every query pays
     the full scan cost that clustering would have avoided.
   - **No materialized views** — you cannot pre-aggregate over the lake, so every
     dashboard query re-scans the underlying files.
   - **No time travel** — no `FOR SYSTEM_TIME AS OF`, so a bad pipeline run overwrites
     the source and there is no point-in-time recovery.
   - **No DML** (`UPDATE`/`DELETE`/`MERGE`) and **no streaming writes** — the external
     table is read-only; corrections require rewriting files in Cloud Storage, which is
     a whole extra pipeline to build and operate.

**4. Hive partitioning.** `hive_partition_uri_prefix` tells BigQuery how to parse the
   `key=value/` segments that lead each object's path. Files at
   `dt=2026-01-15/region=eu/part-*.parquet` are read as if those were real columns.
   The benefit is **partition pruning**: when you filter on `dt`, BigQuery can skip
   entire directories without opening a single file, so you scan only the matching
   prefix. That is the same pruning a native partitioned table gives you, without
   copying the data.

**5. The view's hidden cost.** A logical view is expanded at query time and **inlined
   into the query plan**. If a view joins three tables and you join the view to two
   more, the planner may not push the filters down through the view boundary
   effectively — you can end up scanning far more than the equivalent hand-written
   query. Worse, each query against the view pays the *full* cost of the view's
   definition, every time, with no caching of the intermediate result.

**6. Row-level security.**
   - **Plain view** — defines a result set but does *not* restrict who can query the
     underlying table. Anyone with base-table access can bypass the view entirely and
     read every row. It gives you a reusable definition, not security.
   - **Authorized view** — an IAM binding grants a user access to the *view object
     itself*, and the view's query runs with the view's own permissions, so the user
     cannot see the base table directly. Combined with a `WHERE email = SESSION_USER()`
     filter, this restricts rows to the caller's own data.
   - **Authorized view is the correct choice for row-level security**, because a plain
     view enforces nothing.

**7. `SESSION_USER()`.** It returns the **email address of the authenticated user**
   making the query, which is what you compare against a `email` column to scope rows.
   The caveat: it does not work with **personal credentials** in some BI connectors —
   those connectors authenticate as a service account, so `SESSION_USER()` returns the
   *service account's* identity rather than the end user's, and every user would see
   the same rows (or the wrong ones). Use a service account with a dedicated identity
   per user group, or a different mechanism, for those tools.

**8. View vs materialized view — the table.**

| Dimension | Logical view | Materialized view |
|-----------|--------------|-------------------|
| **Cost** | Same as the base query — the view is expanded and re-executed every time | Much lower — the result is stored and read directly |
| **Freshness** | Always current — it reads the base table live | Up to `max_staleness` — it can be stale |
| **Source** | Any tables, any joins, any logic | **A single base table** only |
| **Result** | You can join it, filter it, and aggregate on top of it | It **cannot be joined**; and `WHERE` on an MV column is not pushed down to the base table |

**9. The single-base-table rule.** A materialized view can only be created over **one**
   base table — a query with two base tables fails with *"Materialized view creation is
   not supported for a query with multiple base tables."* It bites because the MV has
   to be refreshed by re-running that one query against that one table; a multi-table
   join has no well-defined single refresh source.
   **Workaround:** build the MV over the single base table that carries the
   aggregation, then **join the MV to the dimension tables in the query** — the MV
   pre-aggregates the expensive part, and the join back to dimensions happens at
   query time.

**10. MV freshness control.**
   - **`max_staleness`** — the maximum age the MV may be before a query against it
     *triggers* a refresh. Set to `INTERVAL 1 HOUR`, a query on a stale MV first
     refreshes it. This is the freshness guarantee you declare.
   - **`enable_refresh`** — `TRUE` turns on automatic background refresh on a schedule;
     `FALSE` means manual only.
   - **Manual refresh** — `CALL bq.refresh_materialized_view('dataset.mv')` forces a
     refresh on demand. This is the one to use in a pipeline when the upstream load
     just completed and you need the MV current immediately.

**11. The 30-second design rule.** BigQuery will not build it, because the MV
   definition touches three tables and an MV may reference only one. Build instead:
   1. An **MV over the single fact table** that holds the aggregate — e.g. daily order
      counts per customer.
   2. **Join the MV to the dimension tables** (and to the other base tables) in the
      consuming query.
   The expensive aggregation happens once at refresh time; the joins happen per query
   but against small dimensions. If the second base table is itself large and
   aggregate-able, give it its own MV.

**12. Putting it together.**
   - (a) **Logical view over a managed table**, with the filter baked in
     (`WHERE customer_id = '...'`) and granted to the customer as an authorized view.
     It is a compliance export — read-only, and it must not be able to see anything
     else — so an authorized view over the source table is right. (If it needs to span
     the raw lake, use an external table as its source.)
   - (b) **Materialized view** over the orders table, aggregated by day. 200 hits/day
     on the same aggregate is precisely the case an MV exists for: without it you pay
     200 full aggregations; with it you pay one refresh plus 200 cheap reads. Set
     `max_staleness` to match your freshness SLA (e.g. `INTERVAL 1 HOUR`).
   - (c) **External table** over the Parquet drop. Ad hoc exploration of files that
     arrive and are then transformed elsewhere — copying them into a managed table
     would cost storage on data you may only read once.
   - (d) **Logical view.** Ten teams need one shared definition, and the definition
     joins orders and sessions. A view is the only option that takes a multi-table
     join, and it always reflects current data. (If the join became a performance
     problem, you would reconsider: give each base table an MV and join the MVs.)

---

## 🔑 Key Takeaways

- **External** = don't copy what you barely read. **Managed** = copy what you read often.
- External tables are read-only: no DML, no time travel, no MVs, no clustering.
- `hive_partition_uri_prefix` buys partition pruning without copying data.
- A **view** is a reusable definition (and a query cost). An **authorized view** is
  also a *security* boundary. A plain view is not.
- **Row-level security = authorized view + `SESSION_USER()`** — and check your BI
  connector's credential type first.
- An **MV is cheaper and faster but stale, joins to nothing, and sits on exactly one
  base table.**

---

## 📚 Next

[40 · Materialized Views](./40-materialized-views.md) — the full treatment of everything
Question 10 and Question 11 above touch on.
