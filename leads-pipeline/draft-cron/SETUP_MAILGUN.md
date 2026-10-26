# Mailgun Setup — Production (Recommended)

> **For when you outgrow Gmail.** Sends from `hello@vishnoisoft.com` (your own domain).
> Free tier: 5,000 emails/month. After that: $0.80 per 1,000.

## Why Mailgun over Gmail

| Feature | Gmail SMTP | Mailgun |
|---|---|---|
| Daily limit | ~100 cold, then throttled | 5,000/mo free, then $0.80/1K |
| Sender domain | gmail.com (looks personal) | yourdomain.com (looks pro) |
| SPF/DKIM/DMARC | Not configurable | Yes |
| Open/click tracking | No | Yes |
| Bounce handling | Manual | Auto |
| Risk of suspension | High after 50-100 cold | Very low |

## Step 1: Get a domain (if you don't have one)

- Namecheap: https://namecheap.com — `vishnoisoft.com` ~$10/yr
- Cloudflare: https://cloudflare.com — same price
- Porkbun: https://porkbun.com — sometimes cheaper

## Step 2: Sign up for Mailgun

1. Go to https://mailgun.com
2. Sign up (free)
3. Verify your email

## Step 3: Add your domain to Mailgun

1. Mailgun Dashboard → Sending → Domains → Add New Domain
2. Enter `vishnoisoft.com`
3. Mailgun gives you DNS records to add:
   - SPF record (TXT)
   - DKIM record (TXT)
   - MX records (for receiving)
4. Go to your domain registrar (Namecheap/Cloudflare) → DNS settings
5. Add all the records Mailgun gave you
6. Wait 24-48h for DNS propagation (usually <1h)

## Step 4: Get your SMTP credentials

1. Mailgun Dashboard → Sending → Domain Settings → SMTP credentials
2. Default SMTP user: `postmaster@vishnoisoft.com`
3. Default password: (the one Mailgun auto-generated, or create new)

## Step 5: Update `.env`

```bash
# Replace Gmail config with Mailgun
MAILGUN_SMTP_HOST=smtp.mailgun.org
MAILGUN_SMTP_PORT=587
MAILGUN_SMTP_USER=postmaster@vishnoisoft.com
MAILGUN_SMTP_PASSWORD=your-mailgun-password

GMAIL_ADDRESS=hello@vishnoisoft.com
YOUR_EMAIL=hello@vishnoisoft.com
```

## Step 6: Update `send_emails.py` to use Mailgun

Change the SMTP server from Gmail to Mailgun. Open `send_emails.py` and replace the `send_email` function:

```python
def send_email(to_email, subject, body_text, resume_file=None):
    msg = build_message(to_email, subject, body_text, resume_file)
    with smtplib.SMTP(os.getenv("MAILGUN_SMTP_HOST"), int(os.getenv("MAILGUN_SMTP_PORT"))) as server:
        server.starttls()
        server.login(os.getenv("MAILGUN_SMTP_USER"), os.getenv("MAILGUN_SMTP_PASSWORD"))
        server.sendmail(os.getenv("GMAIL_ADDRESS"), to_email, msg.as_string())
```

## Step 7: Test

```bash
python3 send_emails.py --test
```

If it works, you're sending from `hello@vishnoisoft.com` with proper authentication.

## Daily volume

- **Free tier:** 5,000 emails/month ≈ 165/day
- **First paid tier:** $0.80 per 1,000 = $40/mo for 50,000 emails

For your use case (10-20 emails/day), free tier is enough.

## Deliverability tips

1. **Warm up** — start with 5/day, increase by 5/day each week up to 50/day
2. **SPF/DKIM/DMARC** — all set by Mailgun automatically once DNS propagates
3. **Personalize every email** — the script does this with {PERSONAL_SIG} substitution
4. **Avoid spam words** — "free", "guaranteed", "$$$", "limited time" — already avoided in templates
5. **Send from real person, not "noreply"** — Gmail/Outlook trust real-looking senders
6. **Monitor bounce rate** — Mailgun dashboard shows this; keep under 5%

## When to switch from Mailgun to Instantly/Lemlist

When you want to send 100+/day and need:
- Multiple sending inboxes (rotation)
- Automated warmup
- A/B testing
- Built-in CRM/sequences
- Reply detection

Those are $30-100/mo tools. Mailgun is for $0-40/mo. Start with Mailgun.
