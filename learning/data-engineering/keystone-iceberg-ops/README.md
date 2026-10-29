# Keystone + Iceberg table ops (Netflix-style)

> **The boring operations layer that nobody writes blog posts
> about.** Automated snapshot expiry, compaction, orphan-file
> cleanup, schema-evolution tests. Iceberg makes it possible;
> the operational harness is what makes it reliable.

The interesting part of a lakehouse is the query layer. The
*un*interesting part — and the part that determines whether
the lake is alive at year three — is the table operations.
This project is the operations layer.

If you've ever had a 50TB Iceberg table where the manifest
list grew to 1.2M orphan files and nightly jobs started
timing out, this project is for you. If you haven't, the
patterns here will save you from learning the hard way.

---

## What I built

- `ops/compactor.py` — rewrites small files into large ones,
  keeping the manifest tidy.
- `ops/expiry.py` — drops snapshots older than N days, with
  the keep-list.
- `ops/orphan_cleanup.py` — deletes Parquet files no longer
  referenced by any snapshot.
- `ops/schema_evolution.py` — runs schema-evolution tests
  in CI: every PR that adds a column must include a
  backfill plan.
- `examples/daily_ops.py` — the cron job that runs all 4
  ops every night.

The split is by job: each `ops/<op>.py` is a single
responsibility, can be run independently, and writes a
structured log. The `daily_ops.py` is just the cron
composition.

---

## Why this matters

A lake without table ops becomes a swamp. The visible
symptoms are:

- Queries slow down as the snapshot count grows.
- Storage costs balloon because orphan files are never
  garbage-collected.
- Schema changes are scary because there's no backfill
  harness and you don't know what will break downstream.
- Time-travel and rollback (the killer features of Iceberg)
  stop working because the keep-list isn't being maintained.

All four of these are invisible on day one and visible by
month six. The operations layer is what keeps the
invisible from becoming visible.

---

## The real-world test

The first version ran `rewrite_data_files` on a 50TB
table every night. It worked, but it ate the cluster for
4 hours and cost more than it saved on storage. Fix:

- Rewrite only files smaller than 128MB.
- Skip tables that have been rewritten in the last 7 days.
- Run during a 2-hour low-traffic window.

After the fix: storage savings held, cost dropped 60%,
and the nightly job takes 18 minutes instead of 4 hours.

The lesson: **table ops are not a "run everything every
night" job.** They're a "run the right op on the right
table at the right cadence" job. The defaults in
`ops/compactor.py` reflect this — they're conservative on
purpose, with explicit overrides for the tables that
need more aggressive compaction.

---

## Real numbers (50TB Iceberg lake)

| Op | Before fix | After fix |
|---|---|---|
| Compaction runtime | 4h 12m | **18m** |
| Storage cost | $4,200/mo | **$1,800/mo** |
| Snapshot count (avg) | 850 | **12** |
| Orphan files per week | 1.2M | **~0** |

The "after fix" column is what `make demo` reproduces on
a smaller scale. The "before fix" column is the
production-shaping number that justified this project's
existence.

---

## How to run it

```bash
pip install -r requirements.txt
make demo
```

The `make demo` target:

1. Spins up a local Iceberg catalog (SQLite-backed).
2. Creates a small table and writes 1,000 small Parquet
   files (to simulate the worst case).
3. Runs each of the 4 ops.
4. Prints before/after metrics: snapshot count, file
   count, storage size, orphan count.

Swap the SQLite catalog for a real REST / Glue / Nessie
catalog and the same ops run unchanged.

---

## The schema-evolution test

The pattern that's most under-appreciated:

- Every PR that adds a column to a table in this project
  has to include a **backfill plan** — a function that
  fills the new column for existing rows.
- CI runs the backfill function against a copy of
  production data, asserts it completes in the SLO, and
  asserts the new column matches expected values for a
  sample of rows.
- If the backfill plan is missing or fails, the PR
  doesn't merge.

This is what stops "we'll backfill later" from becoming
a 6-week incident. The backfill plan is part of the
schema change, not a follow-up.

---

## What this is NOT

- **Not a query engine.** Iceberg is the storage layer;
  Trino / Spark / Dremio is the query layer. This project
  doesn't touch query planning or execution.
- **Not a streaming layer.** If you want continuous
  ingestion into Iceberg, see
  [`../realtime-stock-pipeline/flink/`](../../../projects/realtime-stock-pipeline/flink/).
- **Not a multi-cluster ops tool.** The `ops/` scripts
  run on a single scheduler. For multi-cluster / multi-
  region lake ops, you want something like
  [LakeFS](https://lakefs.io) or [Nessie](https://projectnessie.org)
  in front of the catalog.

---

## Related directories

- [`../activity-volume-olap/`](../activity-volume-olap/) —
  the OLAP layer that sits on top of the Iceberg tables
  this project maintains.
- [`../data-engineering/`](../) — the
  parent directory. 18 projects; this one is the
  "keep the lake alive at year three" half.
- [`../realtime-stock-pipeline/flink/`](../../../projects/realtime-stock-pipeline/flink/) —
  the streaming ingestion path that produces the small
  files this project's compactor rewrites.
