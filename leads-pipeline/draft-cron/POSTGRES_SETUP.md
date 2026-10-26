# Avilx — Postgres Lead Tracking (Docker)

## What it does
Stores every Avilx lead + send attempt in Postgres so you can:
- **Dedup** by email, phone, or (company, role) — works across machines
- **Track** send history, opens, replies, bounces
- **Manage opt-outs** (anti-spam compliance)
- **Browse** leads via Adminer UI

## Quick start

```bash
# 1. Start Postgres + Adminer (UI on http://localhost:8080)
docker compose up -d

# 2. Migrate existing leads.json → Postgres
python3 backfill_to_pg.py

# 3. View stats
python3 db_cli.py status
python3 db_cli.py pending
python3 db_cli.py sent
python3 db_cli.py company <name>
python3 db_cli.py search <email>
python3 db_cli.py companies
```

## Connection

| Setting | Value |
|---|---|
| Host | localhost |
| Port | 5433 (5432 in container) |
| Database | avilx_leads |
| User | avilx |
| Password | avilx |
| Adminer UI | http://localhost:8080 |

## Tables

### `leads`
- `id` — primary key
- `tracking_id` — public ID for emails (e.g. `byte-7q3k`)
- `company`, `role`, `contact_email`, `contact_phone`
- `apply_method` — `email` or `url`
- `cover_letter_subject`, `cover_letter_body`, `jd_text`
- `status` — `pending` | `sent_email` | `failed` | `replied` | `bounced` | `unsubscribed`
- `sent_at`, `replied_at`, `last_error`, `send_count`

### `send_log`
Every email send attempt (lead_id, to_email, subject, status, error, smtp_message_id).

### `phones`
Phone-number dedup table.

### `opt_outs`
Email addresses that unsubscribed — never send to these.

## Env vars (override defaults)

```bash
AVILX_DB_HOST=localhost
AVILX_DB_PORT=5433
AVILX_DB_NAME=avilx_leads
AVILX_DB_USER=avilx
AVILX_DB_PASSWORD=avilx
```

## Reset

```bash
docker compose down -v   # nuke volume (deletes data)
docker compose up -d     # restart
python3 backfill_to_pg.py  # re-migrate from leads.json
```

## Tracking in emails

Every email footer includes:
- Tracking ID (e.g. `byte-7q3k`)
- One-click unsubscribe mailto link

When a recipient replies `unsubscribe`, the lead is added to `opt_outs` and never sent again.

## Future: open/click tracking

To add open tracking:
1. Stand up a tiny webhook server (e.g. `/track/open/{tracking_id}.gif`)
2. Inject a 1x1 pixel into the HTML email
3. On request, log to `send_log` and update lead status

To add click tracking:
1. Wrap links in `/r/{tracking_id}?url=<encoded>` redirects
2. Log click → mark lead as `clicked`

Can use FastAPI/Flask for the server, or Cloudflare Workers if you want serverless.
