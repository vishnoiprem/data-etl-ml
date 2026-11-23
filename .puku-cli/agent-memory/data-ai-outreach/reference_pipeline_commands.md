---
name: Pipeline commands and guard behaviour
description: The exact CLI entry points for discovery, sending, bounce sync and reporting, plus what the pre-send guards actually enforce
type: reference
---

Canonical pipeline: `projects/leads-pipeline/draft-cron/`. Use its `.venv/bin/python`.

| Intent | Command |
|---|---|
| Discover client prospects | `find_clients.py` (no flags) |
| Discover more job-based leads | `find_more_leads.py` (no flags) |
| Preview, no writes, no sends | `autopilot.py --dry` |
| Scrape + queue only | `autopilot.py --scrape` |
| Enrich only | `autopilot.py --enrich` |
| Send approved emails | `autopilot.py --email --mode pitch_pod --max-emails N` |
| Sync bounces from Gmail | `check_bounces.py --since 14` |
| State as JSON | `dashboard.py --json` |
| Inspect lead | `db_cli.py company <name>` / `db_cli.py search <email>` / `db_cli.py status` |
| Mark a reply | `bin/mark_reply.py "<company>" --replied --via email` |
| Reports | `daily_report.py`, `full_report.py` |

`db_cli.py` subcommands: status, recent, pending, sent, search, company, companies, log-dm,
followup, dm-status, followups, mark-replied, dm-recent.

`bin/mark_reply.py --via` accepts: email, x_dm, linkedin, platform, inbound, other.

Lead status vocabulary: `pending` → `sent_email` → `replied` → `interviewed` → `offered` → `closed`,
with side exits `bounced`, `failed`, `unsubscribed`.

What `lib/email_guard.py::can_send_to()` enforces, in order:
1. format check (regex) → reason `fmt`
2. bounce deny list, keyed by registered domain (last 2 labels) → reason `deny:<domain>`
3. tail log — emailed within N hours → reason `tail:<N>h`
4. daily cap → reason `cap:daily=<n>/<max>`
5. hourly cap → reason `cap:hourly=<n>/<max>`
6. live MX DNS probe → reason `mx:NXDOMAIN` / `mx:TIMEOUT` / `mx:NOMX`

Returns `(ok, reason)`; reason empty means allowed. It writes nothing to the DB.
Because it fails open on DB errors, a Postgres outage will NOT block a send — the cron lock is
what actually prevents sending in that case.

Dedup key is `(LOWER(company), LOWER(contact_email), LOWER(role))` — never email alone, so a
recruiter who changes jobs is not deduped away. `find_duplicate` tries company+role+email →
company+role → company+email.

Gmail accepts any RCPT TO with 250, so bounces arrive later as "Delivery Status Notification
(Failure)" mails that `check_bounces.py` parses over IMAP.

**How to apply:** Use `--dry` to show the user what would happen. Only run `--email` after
explicit approval of the exact drafts. Report skip reasons from the guard rather than working
around them.
