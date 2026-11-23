---
name: leads-pipeline
description: Drive the Avilx leads pipeline in projects/leads-pipeline/draft-cron/ — discover leads, render drafts, send approved email, check bounces and replies, and report funnel metrics. Use when the user asks to find leads, send emails, check for replies or bounces, or show pipeline status for the Avilx outbound motion.
allowed-tools: Bash, Read, Grep, Glob, Edit, Write
user-invocable: true
---

# Leads pipeline

You drive the Avilx outbound pipeline in `projects/leads-pipeline/draft-cron/`.
Use its own CLI rather than reimplementing discovery, dedup, rendering, or sending.

**Read `projects/data-ai-outreach/PUKU.md` first** — it is the authoritative project
brief: canonical pipeline location, lead status vocabulary, hard rules, email shape,
and the workflow. Do not run anything in the repo-root `leads-pipeline/` directory;
that is a stale untracked copy. The canonical pipeline is
`projects/leads-pipeline/draft-cron/`.

## Setup

```bash
cd projects/leads-pipeline/draft-cron
make install      # .venv with runtime + test deps
make test-db      # create avilx_test and apply schema (once)
make schema       # apply schema to avilx_leads
```

Postgres must be reachable on `localhost:5433`. `db.cron_lock.cron_lock` fails closed
when it is not, so the email phase refuses to run. `projects/data-ai-outreach/run.sh
doctor` reports exactly what is missing.

## Commands

Run from `projects/leads-pipeline/draft-cron/`, using `.venv/bin/python`.

| Intent | Command |
|---|---|
| Discover client prospects (company signals) | `find_clients.py` |
| Discover leads from job posts | `find_more_leads.py` |
| Queue + render drafts | `autopilot.py --scrape --enrich` |
| Preview what would send | `autopilot.py --email --dry` |
| Send approved drafts | `autopilot.py --email --mode <mode> --max-emails N` |
| Send day-N follow-ups | `bin/send_followups.py --max 5 --dry` (drop `--dry` to send) |
| Pipeline state | `dashboard.py --json` |
| Inspect a lead | `db_cli.py company <name>` / `db_cli.py search <email>` |
| Mark a reply | `bin/mark_reply.py "<company>" --replied --via email` |
| Sync bounces | `check_bounces.py --since 14` |
| Daily report | `daily_report.py` / `full_report.py` |

## Modes

`--mode pitch_pod` sends Avilx pod pitches; `--mode apply_personal` sends the
founder's own applications. The queue is filtered by the lead's `apply_mode` column,
so the two never mix. Default to `pitch_pod` for client outreach.

## Sender identity

Emails go out as **Alex Morgan** `<alex.morgan@avilx.com>`. The From header, body
signature, HTML signature, follow-up sign-off, and `Reply-To` all derive from
`AVILX_FROM_NAME` / `AVILX_FROM_EMAIL` in `.env`. The one-click unsubscribe stays on
`hello@avilx.com` (`AVILX_UNSUB_EMAIL` overrides it) — never a person's inbox.

**Gmail strips the avilx.com address from the visible From header.** Verified by
sending three test messages to the account itself on 2026-11-23: SMTP accepts
`MAIL FROM:<alex.morgan@avilx.com>` with 250 OK, but the delivered `From:` reads
`Alex Morgan <premvishnoisoft@gmail.com>`. The name survives; the address does not.
So today the pipeline sends from the Gmail address wearing the Alex Morgan name.
Sending from `alex.morgan@avilx.com` for real needs a provider with the avilx.com
domain verified — see `SETUP_MAILGUN.md`.

Never claim a send succeeded without a `send_log` row.

## Hard rules

1. **Never guess an email address.** Only a verified business email or a published
   company contact address.
2. **Never send without explicit approval.** Stay in draft mode. Show drafts; the
   user approves; only then does anything send. A changed recipient or message goes
   back for approval.
3. **Never represent a draft as sent.**
4. **Never bypass the guards.** `email_guard.can_send_to()` and `db.cron_lock.cron_lock`
   exist to prevent double-sends and list damage. No `--no-lock` outside interactive
   debugging. Never edit the bounce deny list to unblock a send — fix the address.
5. **Job postings are signals, not confirmed demand.** Say "saw your posting for X",
   never "you need X engineers".
6. **No invented facts.** Every company claim traces to a source URL.
7. **Respect opt-outs.** `opt_outs` is permanent. Keep the one-click unsubscribe.
8. **Respect send caps.** Daily and hourly caps live in `lib/email_guard.py`.

## Before sending

- Postgres reachable on `localhost:5433`.
- `can_send_to()` green for the recipient. If a lead is skipped, report the reason.
- `state/bounce_deny_store.py` and `opt_outs` checked.
- If a send is uncertain, check the sent folder or `send_log` before retrying.
  Retrying a possibly-sent email contacts a prospect twice.

## Tests

`make test` runs the 8 test modules against `avilx_test`, never the live database.
The dedup and bounce-deny tests insert lead rows and never delete them — without the
split they accumulate in the live database and show up in the funnel as real leads.
