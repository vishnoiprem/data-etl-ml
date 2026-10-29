# Automode — Daily Lead Pipeline

> **Run everything with one command.** No prompts, no questions.
> `python3 auto.py` = send emails + open URLs in browser.

## What's in automode

| Phase | What it does |
|---|---|
| **Phase 1: Email** | Sends Gmail SMTP email to leads with `apply_method: "email"` (Sticker Mule only, currently) |
| **Phase 2: URL** | Opens apply URLs in your browser for leads with `apply_method: "url"` (9 of 10) |
| **Status update** | Marks each lead as `sent_email` or `opened_url` in `leads.json` |
| **Logging** | Every action logged to `auto_log.csv` |

## Quick start

```bash
cd /Users/vishnoiprem/PycharmProjects/data-etl-ml/leads-pipeline/draft-cron

# 1. First time: dry run to see what would happen
python3 auto.py --dry

# 2. When ready: full run (emails + URLs)
python3 auto.py

# 3. Or just one phase
python3 auto.py --email    # email only
python3 auto.py --url      # URL only
```

## Cron (run daily at 9am Vietnam time)

```bash
crontab -e

# Add this line:
0 9 * * * /Users/vishnoiprem/PycharmProjects/data-etl-ml/leads-pipeline/draft-cron/automode.sh >> /tmp/automode.log 2>&1
```

## How status flows

```
pending → sent_email    (after email sent)
pending → opened_url    (after URL opened in browser)
sent_email → replied    (you mark manually when reply comes)
opened_url → replied    (you mark manually when reply comes)
replied → interviewed   (you mark manually)
interviewed → offered   (you mark manually)
offered → closed        (you mark manually when contract signed)
```

## How to mark replies/interviews/offers

Open `leads.json` and change the `status` field. Examples:

```json
{
  "company": "LiveKit",
  "status": "replied",
  "reply_date": "2026-10-12",
  "notes": "Recruiter Sarah replied, scheduling call for Wed"
}
```

```json
{
  "company": "A.Team",
  "status": "interviewed",
  "interview_date": "2026-10-15",
  "notes": "Tech screen passed, scheduling system design"
}
```

```json
{
  "company": "Tailscale",
  "status": "offered",
  "offer_amount": "$140/hr principal",
  "notes": "Offer received, reviewing contract"
}
```

## Replenish leads (when all 10 are processed)

```bash
# Re-run the lead-finder-scout agent to find 20+ fresh leads
# (tell me: "re-run firehose" or use the agent directly)
```

The new leads will be saved to `leads-pipeline/2026-10-11/full-leads.md`. Copy the JSON entries to `leads.json` with their `apply_method: "url"` (most platforms don't expose emails).

## Files

| File | Purpose |
|---|---|
| `auto.py` | Main runner — email + URL, no prompts |
| `automode.sh` | Shell wrapper for cron |
| `leads.json` | Current 10 leads |
| `auto_log.csv` | Action log (every email sent, URL opened) |
| `.sent_today.json` | Tracks today's processed leads |
| `.env` | Gmail SMTP config |

## Tracking dashboard (terminal)

```bash
# See current state
python3 -c "
import json
leads = json.load(open('leads.json'))
for status in ['pending', 'sent_email', 'opened_url', 'replied', 'interviewed', 'offered', 'closed']:
    count = sum(1 for l in leads if l['status'] == status)
    print(f'  {status:<15} {count}')
print(f'  total: {len(leads)}')
"
```

## ⚠️ Gmail limits (still apply in automode)

- 5-10 emails/day for testing
- 50-100/day before throttling
- Switch to Mailgun when you outgrow Gmail (see `SETUP_MAILGUN.md`)

## What's running automatically in automode

```bash
$ python3 auto.py

📊 STATUS
   Total leads: 10
   Pending:     10
   Email-track: 1
   URL-track:   9

📧 PHASE 1: EMAIL
======================================================================
#1 Sticker Mule
   To: help@stickermule.com
   Subject: AI/Agent Architect for Sticker Mule — LLM + RAG, 18+ yrs
   ✅ Sent

🌐 PHASE 2: URL APPLY
======================================================================
#2 LiveKit
   URL: https://jobs.ashbyhq.com/livekit
   ✅ Opened in browser
#3 A.Team
   URL: https://jobs.ashbyhq.com/a-team
   ✅ Opened in browser
... [7 more URLs opened]

======================================================================
📊 SUMMARY
   Emails sent:  1
   URLs opened:  9
   Log:          /Users/vishnoiprem/.../auto_log.csv
======================================================================
```

Browser opens 9 tabs. You go tab-by-tab, sign in, paste the cover letter (already in your clipboard via the log), attach resume, submit. Takes ~30 min.
