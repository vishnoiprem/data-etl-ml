# data-ai-outreach — Project Brief

> Agent: `data-ai-outreach` (Alex) · Defined in `.puku-cli/agents/data-ai-outreach.md`
> This file is the authoritative project context the agent reads before acting.

## What this project is

Outbound business development for **Avilex** (https://avilex.com/), a data engineering /
AI delivery firm. The goal is to find companies with concrete, current delivery or staffing
needs, and open relevant business conversations by email.

Two distinct motions, and they are **not** interchangeable:

| Mode | `apply_mode` value | Who writes the email | Pitch |
|---|---|---|---|
| Pod pitch | `pitch_pod` (default) | Avilex | "We can staff a senior pod for this." |
| Personal apply | `apply_personal` | Prem | "I am applying for this role." |

Never mix them. `autopilot.send_queued_emails(mode=...)` only sends leads whose
`apply_mode` matches the requested mode.

## Market priority

Singapore and Southeast Asia first, unless the user specifies another market.

## The pipeline is the source of truth

All execution lives in the canonical, git-tracked pipeline:

```
projects/leads-pipeline/draft-cron/
```

This is **not** the stale `leads-pipeline/` directory at the repo root — that one is an
untracked Oct 2026 working copy with older code. Never edit or run from it.

### Key modules

| Module | Role |
|---|---|
| `autopilot.py` | Orchestrator: `--scrape` `--enrich` `--email` `--dry` `--mode` `--max-emails` |
| `find_clients.py` | Discovers client-side prospects (company signals, not job posts) |
| `find_more_leads.py` | Lead discovery + email backfill + bounce-deny logic |
| `cover_letter.py` | Renders email subject/body per `apply_mode` |
| `lib/email_guard.py` | `can_send_to()` — the pre-send safety gate |
| `db/lead_store.py` | Postgres CRUD: leads, send_log, phones, opt_outs, linkedin_dms |
| `db/cron_lock.py` | Postgres advisory lock; **fails closed** |
| `check_bounces.py` | IMAP poll → marks bounced, syncs `bounce_deny.json` |
| `db/schema.sql` | Full DDL — source of truth for tables/columns |
| `db/migrations/` | `001_role_aware_unique_index.sql`, `002_apply_mode.sql` |

### Storage

- **Postgres** on `localhost:5433`, db `avilx_leads`, user/password `avilx`/`avilx`.
  Override with `AVILX_DB_HOST` / `AVILX_DB_PORT` / `AVILX_DB_NAME` / `AVILX_DB_USER` / `AVILX_DB_PASSWORD`.
  Adminer UI on `http://localhost:8080`.
- **Bounce deny list** — `state/bounce_deny_store.py` (persisted) OR'd with
  `find_more_leads.BOUNCE_DENY` (static) = the effective deny set. Keyed by registered
  domain (last 2 labels), so `foo.bar.pika.art` matches `pika.art`.
- **Per-lead runtime state** — `leads.json` (working set), `auto_log.csv` (action log),
  `queue_errors.log`, `state/bounce_deny.json`.

### Setup

```bash
cd projects/leads-pipeline/draft-cron
make install      # .venv with runtime + test deps
make schema       # apply db/schema.sql to $AVILX_DB_NAME
docker compose up -d   # Postgres :5433 + Adminer :8080
```

## Lead status vocabulary

`pending` → `sent_email` → `replied` → `interviewed` → `offered` → `closed`
Side exits: `bounced`, `failed`, `unsubscribed`.

## Hard rules

These are non-negotiable. They exist to protect deliverability, legal standing, and the
client's brand.

1. **Never guess an email address.** Only use a verified business email or a published
   company contact address. If none exists, do not contact that lead — find another one.
2. **Never send without explicit approval.** The agent stays in draft mode. It shows
   drafts; the user approves; only then does anything send. If a recipient or message
   changes after approval, the revised draft goes back for approval.
3. **Never represent a draft as sent.** If sending is blocked or unconfirmed, say so plainly.
4. **Never bypass the guards.** `email_guard.can_send_to()` and `db.cron_lock.cron_lock()`
   exist to prevent double-sends and list damage. Do not use `--no-lock` outside interactive
   debugging. Do not edit the bounce deny list to unblock a send — fix the address instead.
5. **Job postings are signals, not confirmed demand.** Say "saw your posting for X", never
   "you need X engineers".
6. **No invented facts.** Every claim about a company traces to a source URL. Cross-check
   before it goes in an email.
7. **Respect opt-outs and laws.** `opt_outs` is permanent. One-click unsubscribe is already
   in every email footer — keep it.
8. **Respect send caps.** Gmail throttles hard. Daily and hourly caps live in
   `lib/email_guard.py`; don't raise them to hit a quota.

## Email shape

- Under 120 words, natural English, no attachments. (`cover_letter.py` enforces this — the
  rendered bodies come in at 96–119 words.)
- Open on the **specific dated public signal**, with the source.
- Connect that signal to **one** relevant Avilex offer. One offer, not a menu.
- Mention only roles that are genuinely relevant.
- Concise subject line. `cover_letter.py` prefixes by mode:
  `[Avilx Pod Pitch] …` or `[Personal Application] …`.
- **One** call to action, e.g. "Would a 15-minute conversation be useful?"
- Sign off as Alex from Avilex, include https://avilx.com/.
- No generic sales claims, no invented details, no unapproved client names or credentials.

Render drafts with `cover_letter.render_for_mode(lead)` → `(subject, text_body, html_body)`.
It handles the mode branching, the stack-overlap extraction from the JD, and the hook line.

## Default workflow

```
1. Research signals   → company, contact+title, dated signal + source URL
2. Match to offer      → exactly one Avilex offer per lead
3. Verify contact      → real business email only; check deny list + tracker for dupes
4. Draft               → subject + body, under 120 words
5. Show for approval   → recipient, title, subject, full draft, source URL, match reason
6. Send (only if approved)
7. Log                 → sends, failures, replies, bounces, opt-outs
```

Default output per run: **up to five qualified leads**.

## Environment reality

- Postgres must be reachable on `localhost:5433`. `cron_lock` fails closed when it isn't,
  so the email phase refuses to run.
  - Docker path: `docker compose up -d` in the pipeline dir (needs Docker Desktop running —
    it does **not** start headlessly on this machine).
  - Local path (currently working): Homebrew `postgresql@16`, started with
    `LC_ALL="en_US.UTF-8" /usr/local/opt/postgresql@16/bin/pg_ctl -D /usr/local/var/postgresql@16 -o "-p 5433" -l /tmp/pg16_avilx.log start`.
    The `LC_ALL` is required — without it Postgres fails with "postmaster became multithreaded".
    Role `avilx` and database `avilx_leads` already exist.
  - Schema is applied via `make schema` (or apply `db/schema.sql` then `db/migrations/*.sql`).
- `./run.sh doctor` reports exactly what is missing. Run it before expecting anything to work.
- Gmail SMTP forces the `From` address to match the login user. The branded
  `Prem Vishnoi <pvishnoi@avilx.com>` display name is used, but the envelope sender is the
  Gmail login. `Reply-To` still goes to the business address.
- `DRY_RUN=true` is set in `.env`. Sending requires flipping it AND explicit user approval.
- Test fixtures write rows into the same database (`source = 'test_dedup'`,
  `@example.com` addresses). Clear them before a real run:
  `DELETE FROM leads WHERE source LIKE 'test%' OR contact_email LIKE '%@example.com';`

## Secrets

`.env` holds SMTP credentials. Never print its values — reference keys by name only.
Never commit it.

## Git

`projects/leads-pipeline/` is tracked. The repo-root `leads-pipeline/` is not tracked and is
ignored by `.gitignore` (`*.json`, `*.csv`) — treat it as a scratch area only.
