---
name: Local Postgres setup for the leads pipeline
description: How to start Postgres on port 5433 without Docker, including the locale requirement and the existing role/database
type: reference
---

The pipeline needs Postgres on `localhost:5433`. Docker Desktop does **not** start headlessly
on this machine (the app launches but its VM never comes up — no `~/.docker/run/docker.sock`),
so `docker compose up -d` is not a reliable option here.

Working alternative — Homebrew `postgresql@16` (installed 2026-11-23):

```bash
LC_ALL="en_US.UTF-8" /usr/local/opt/postgresql@16/bin/pg_ctl \
  -D /usr/local/var/postgresql@16 -o "-p 5433" \
  -l /tmp/pg16_avilx.log start
```

**The `LC_ALL` is mandatory.** Without it Postgres aborts at startup with
`FATAL: postmaster became multithreaded during startup` / `HINT: Set the LC_ALL environment
variable to a valid locale`.

Role `avilx` (password `avilx`, SUPERUSER) and database `avilx_leads` already exist.
Apply the schema with `make schema` from the pipeline dir, then `db/migrations/*.sql`
(`001_role_aware_unique_index.sql`, `002_apply_mode.sql`).

Note the canonical `db/schema.sql` includes `apply_method` and `updated_at` columns on
`leads` — do not hand-write a schema, use the repo's.

**How to apply:** Start Postgres before running any pipeline command that touches the DB.
`projects/data-ai-outreach/run.sh doctor` checks this. The full test suite (52 tests) passes
once Postgres is up; without it, 17 fail on connection refused.
