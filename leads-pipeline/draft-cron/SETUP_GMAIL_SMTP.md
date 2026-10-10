# Gmail SMTP Setup — 5 minutes

> **For testing only.** Sends from `premvishnoisoft@gmail.com`. Limit: 5-20 emails/day.
> **Risk:** Google will rate-limit or suspend your account after 50-100 cold emails.
> **For production:** Use Mailgun/SendGrid (see `SETUP_MAILGUN.md`).

## Step 1: Enable 2-Factor Authentication on your Gmail

1. Go to https://myaccount.google.com/security
2. Click "2-Step Verification" → follow prompts to enable
3. You'll need a phone for SMS codes

## Step 2: Create a Gmail App Password

1. Go to https://myaccount.google.com/apppasswords
2. You may need to sign in again
3. App name: "Lead Sender" (or any name)
4. Click "Create"
5. Google shows you a 16-character password like: `abcd efgh ijkl mnop`
6. **Copy this password** — you'll paste it into `.env`

## Step 3: Configure `.env` file

```bash
cd /Users/vishnoiprem/PycharmProjects/data-etl-ml/leads-pipeline/draft-cron
cp .env.example .env
nano .env  # or use any text editor
```

Fill in:
```
GMAIL_ADDRESS=premvishnoisoft@gmail.com
GMAIL_APP_PASSWORD=abcdefghijklmnop    # the 16-char password from Step 2
YOUR_NAME=Prem Vishnoi
YOUR_COMPANY=Vishnoi Soft
YOUR_EMAIL=hello@vishnoisoft.com
YOUR_PHONE=+84-XXX-XXX-XXX
YOUR_WEBSITE=https://vishnoisoft.com
RESUME_DIR=/Users/vishnoiprem/PycharmProjects/data-etl-ml/Resume
```

Save and close.

## Step 4: Test it

```bash
cd /Users/vishnoiprem/PycharmProjects/data-etl-ml/leads-pipeline/draft-cron
python3 send_emails.py --test
```

This sends 1 test email to yourself. If it works, you're ready.

## Step 5: Run the daily sender

```bash
python3 send_emails.py --daily
```

Sends up to 10 emails (configurable) from `leads-pipeline/2026-10-10-RERUN/full-leads.md`.

## Step 6: Set up daily cron (optional)

```bash
# Run every day at 9am Vietnam time
crontab -e
# Add this line:
0 9 * * * cd /Users/vishnoiprem/PycharmProjects/data-etl-ml/leads-pipeline/draft-cron && /usr/bin/python3 send_emails.py --daily >> /tmp/lead-sender.log 2>&1
```

## ⚠️ Gmail sending limits

| Limit | Value |
|---|---|
| Per day | 500 emails |
| Per hour (SMTP) | ~20 emails |
| Recipients per message | 500 (we send 1) |
| Cold email risk threshold | 50-100/day |
| Recommended for testing | 5-10/day |

After ~100 cold emails from one Gmail, Google will:
- Show CAPTCHAs
- Throttle to 5/day
- Eventually suspend the account

**That's why this is for testing only.** Move to Mailgun/SendGrid when ready.

## What to do when you get a reply

1. Open Gmail → reply from your normal inbox
2. Move the lead to "Replied" status in `leads-pipeline/status/README.md`
3. Set up a 15-min call
4. Send a 1-page proposal (services + rates + 2 case studies)
5. If they want a contract: send your Vietnam LLC MSA + SOW
