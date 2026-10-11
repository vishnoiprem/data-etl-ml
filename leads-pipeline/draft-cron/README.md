# Lead Sender — Gmail SMTP

> **TESTING ONLY.** For production, use Mailgun/SendGrid (see `SETUP_MAILGUN.md`).

## Quick start (5 min)

1. **Set up Gmail App Password** — see `SETUP_GMAIL_SMTP.md`
2. **Install Python deps:**
   ```bash
   cd leads-pipeline/draft-cron
   pip3 install python-dotenv
   ```
3. **Configure `.env`:**
   ```bash
   cp .env.example .env
   nano .env  # paste your 16-char app password
   ```
4. **Test:**
   ```bash
   python3 send_emails.py --test
   ```
5. **Run daily:**
   ```bash
   python3 send_emails.py --daily
   ```

## Files

| File | Purpose |
|---|---|
| `send_emails.py` | The main script |
| `leads.json` | Today's 10 leads (subject + body + resume per lead) |
| `.env.example` | Template config |
| `.env` | Your actual config (don't commit) |
| `send_log.csv` | Log of all sends |
| `.sent_today.json` | Tracks what was sent today |
| `SETUP_GMAIL_SMTP.md` | Gmail setup guide |
| `SETUP_MAILGUN.md` | Production setup (Mailgun/SendGrid) |

## Usage

```bash
# Send 1 test email to yourself
python3 send_emails.py --test

# Send today's daily batch (up to DAILY_LIMIT)
python3 send_emails.py --daily

# Preview what would be sent (no actual send)
python3 send_emails.py --preview

# Send just one specific lead (by 0-based index)
python3 send_emails.py --lead 0  # sends A.Team
python3 send_emails.py --lead 1  # sends Lemon.io

# Cap the daily send at 5
python3 send_emails.py --daily --limit 5
```

## Daily cron (optional)

```bash
crontab -e

# Add this line — runs every day at 9am Vietnam time
0 9 * * * cd /Users/vishnoiprem/PycharmProjects/data-etl-ml/leads-pipeline/draft-cron && /usr/bin/python3 send_emails.py --daily >> /tmp/lead-sender.log 2>&1
```

## ⚠️ Gmail limits

| Limit | Value |
|---|---|
| Per day (SMTP) | 500 |
| Per hour (recommended) | 20 |
| Cold email risk threshold | 50-100/day |
| **Safe for testing** | **5-10/day** |

After ~100 cold emails from one Gmail, Google rate-limits. Move to Mailgun/SendGrid for production.

## How to add a new lead

Edit `leads.json` and add an object:

```json
{
  "company": "New Company",
  "role": "Senior AI Engineer",
  "rate": "$80-120/hr",
  "stack": "LLM, RAG",
  "remote": "Anywhere",
  "url": "https://example.com/jobs/123",
  "contact_email": "careers@example.com",
  "cover_letter_subject": "Vietnam-based AI pod for New Company",
  "cover_letter_body": "Hi New Company team —\n\nWe...\n\n{PERSONAL_SIG}",
  "resume_file": "resume-senior-ai-engineer.pdf",
  "status": "pending"
}
```

## Tracking replies

The script marks each lead as `"status": "sent"` after sending. To track replies:

1. Open `leads.json` and change `"status": "sent"` → `"status": "replied"` when you get a reply
2. Or use the status tracker in `leads-pipeline/status/README.md`

## Logging

All sends logged to `send_log.csv`:
```
timestamp,company,email_to,subject,status,error
2026-10-10T15:30:00,A.Team,talent@a.team,Vietnam-based AI/data pod,success,
2026-10-10T15:32:00,Lemon.io,hello@lemon.io,Vietnam bench async-first,success,
```

## When to upgrade to Mailgun/SendGrid

- You've tested 5-10/day for a week
- You want to send 50+/day
- You want proper SPF/DKIM/DMARC (better deliverability)
- You want tracking (open rates, click rates)
- You want to send from hello@vishnoisoft.com (your own domain)

See `SETUP_MAILGUN.md` for migration path.
