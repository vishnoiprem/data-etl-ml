---
name: Canonical pipeline location and the stale duplicate
description: Which leads-pipeline directory is canonical, why a second untracked copy exists, and the env/DB details needed to run it
type: project
---

Canonical pipeline: `projects/leads-pipeline/draft-cron/` (git-tracked, 91 files under `projects/leads-pipeline/`).
A second, untracked copy exists at repo-root `leads-pipeline/draft-cron/`. It is a stale Oct 2026
working copy, gitignored via `*.json` / `*.csv`.

**Why this matters:** On 2026-11-23 the root copy's `.py` sources had been deleted, leaving only
`__pycache__/*.cpython-310.pyc`. A bytecode-level comparison (`.pyc` header `source_size` field +
code-object diff) proved the root copy's bytecode corresponds to an OLDER working state (Oct 11–13)
than the git-tracked canonical source (Oct 14–16+). The canonical tree is a strict superset:
0 functions unique to canonical, 1 unique to the stale copy (dead code, `_pull_verbatim_phrase`,
which canonical removed). Replacing canonical with the stale copy would lose the pre-send guard
rails, hourly send cap, MX recipient verification, and the `db/migrations/` unique-index fixes.
The stale copy's `db/schema.sql` was reconstructed (not original) and lacks those migrations.

**How to apply:** Always run and edit `projects/leads-pipeline/draft-cron/`. Never run from or
modify the repo-root `leads-pipeline/`. Treat the root copy as a scratch area only.

Environment facts:
- Postgres: `localhost:5433`, db `avilx_leads`, user/pass `avilx`/`avilx`. Override with
  `AVILX_DB_HOST`/`AVILX_DB_PORT`/`AVILX_DB_NAME`/`AVILX_DB_USER`/`AVILX_DB_PASSWORD`.
  `db/cron_lock.cron_lock` fails closed when Postgres is unreachable, so sends refuse to run.
- `.env` lives in the canonical dir and is loaded via `load_dotenv(HERE / ".env")` by
  `autopilot.py`, `check_bounces.py`, and `process_jd_inbox.py`. It uses the `AVILX_*` key
  namespace with `${VAR}` interpolation — the stale copy used a different, older key set.
- Gmail SMTP forces `From` to match the login user; the branded display name is used but the
  envelope sender is the Gmail account. `Reply-To` goes to the business address.
- `DRY_RUN=true` is set in the canonical `.env` deliberately. Sending requires flipping it
  AND explicit user approval of the exact drafts.
