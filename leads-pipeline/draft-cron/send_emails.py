#!/usr/bin/env python3
"""
Lead Sender — Gmail SMTP version (TESTING ONLY)

Sends personalized emails to leads from leads.json
Sends up to DAILY_LIMIT emails per day with DELAY_BETWEEN_EMAILS_SEC delay.

Usage:
  python3 send_emails.py --test          # send 1 test email to yourself
  python3 send_emails.py --daily         # send up to DAILY_LIMIT emails
  python3 send_emails.py --preview       # preview what would be sent (no send)
  python3 send_emails.py --lead 1        # send a specific lead by index
"""

import os
import json
import time
import smtplib
import ssl
import argparse
import sys
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
from datetime import datetime

# Load .env
ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(ENV_PATH)

# Config
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")
YOUR_NAME = os.getenv("YOUR_NAME", "Prem Vishnoi")
YOUR_COMPANY = os.getenv("YOUR_COMPANY", "Vishnoi Soft")
YOUR_EMAIL = os.getenv("YOUR_EMAIL", "hello@vishnoisoft.com")
YOUR_PHONE = os.getenv("YOUR_PHONE", "")
YOUR_WEBSITE = os.getenv("YOUR_WEBSITE", "https://vishnoisoft.com")
RESUME_DIR = Path(os.getenv("RESUME_DIR", str(Path.home() / "Documents" / "Resumes")))
DAILY_LIMIT = int(os.getenv("DAILY_LIMIT", "10"))
DELAY_BETWEEN_EMAILS_SEC = int(os.getenv("DELAY_BETWEEN_EMAILS_SEC", "120"))
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

LEADS_FILE = Path(__file__).parent / "leads.json"
LOG_FILE = Path(__file__).parent / "send_log.csv"
STATE_FILE = Path(__file__).parent / ".sent_today.json"

PERSONAL_SIG = f"""{YOUR_NAME}
{YOUR_COMPANY} — Vietnam AI & Data Engineering Team
📧 {YOUR_EMAIL} | 🌐 {YOUR_WEBSITE} | 🐦 @vishnoiprem"""

PERSONAL_SIG_HTML = f"""
<br><br>
<div style="font-family: -apple-system, sans-serif; font-size: 14px; color: #1a1a1a;">
  <strong>{YOUR_NAME}</strong><br>
  <span style="color: #4b5563;">{YOUR_COMPANY} — Vietnam AI & Data Engineering Team</span><br>
  <span style="color: #6b7280; font-size: 13px;">📧 {YOUR_EMAIL} | 🌐 {YOUR_WEBSITE} | 🐦 @vishnoiprem</span>
</div>
"""


def log_send(company, email_to, subject, status, error=""):
    """Log a send attempt to CSV."""
    file_exists = LOG_FILE.exists()
    with open(LOG_FILE, "a") as f:
        if not file_exists:
            f.write("timestamp,company,email_to,subject,status,error\n")
        ts = datetime.now().isoformat()
        # Escape commas in fields
        subject_safe = subject.replace(",", ";")
        error_safe = error.replace(",", ";")
        f.write(f"{ts},{company},{email_to},{subject_safe},{status},{error_safe}\n")


def load_leads():
    with open(LEADS_FILE) as f:
        return json.load(f)


def save_leads(leads):
    with open(LEADS_FILE, "w") as f:
        json.dump(leads, f, indent=2)


def load_sent_today():
    """Track which leads were sent today to avoid double-sending."""
    if not STATE_FILE.exists():
        return {"date": "", "sent": []}
    with open(STATE_FILE) as f:
        return json.load(f)


def save_sent_today(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def build_message(to_email, subject, body_text, resume_path=None):
    """Build a MIME email with optional resume attachment."""
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{YOUR_NAME} <{GMAIL_ADDRESS}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["Reply-To"] = YOUR_EMAIL

    # Plain text version
    text_part = MIMEText(body_text, "plain", "utf-8")
    msg.attach(text_part)

    # HTML version (better looking)
    body_html = body_text.replace("\n", "<br>")
    html_content = f"""
    <html>
      <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 15px; line-height: 1.6; color: #1a1a1a;">
        {body_html}
        {PERSONAL_SIG_HTML}
      </body>
    </html>
    """
    html_part = MIMEText(html_content, "html", "utf-8")
    msg.attach(html_part)

    # Attach resume if exists
    if resume_path:
        full_path = RESUME_DIR / resume_path
        if full_path.exists():
            with open(full_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {resume_path}",
                )
                msg.attach(part)
        else:
            print(f"⚠️  Resume not found: {full_path}")

    return msg


def send_email(to_email, subject, body_text, resume_file=None):
    """Send one email via Gmail SMTP."""
    msg = build_message(to_email, subject, body_text, resume_file)
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())


def personalize(body):
    """Replace {PERSONAL_SIG} placeholder."""
    return body.replace("{PERSONAL_SIG}", PERSONAL_SIG)


def run_daily(limit=None, specific_index=None, dry_run=False, send_to_self=False):
    leads = load_leads()
    state = load_sent_today()
    today = datetime.now().strftime("%Y-%m-%d")

    # Reset state if new day
    if state["date"] != today:
        state = {"date": today, "sent": []}

    sent_count = 0
    for i, lead in enumerate(leads):
        if specific_index is not None and i != specific_index:
            continue
        if lead["status"] != "pending":
            continue
        if i in state["sent"]:
            continue
        if limit and sent_count >= limit:
            break

        subject = lead["cover_letter_subject"]
        body = personalize(lead["cover_letter_body"])
        to_email = GMAIL_ADDRESS if send_to_self else lead["contact_email"]
        resume = lead.get("resume_file")

        print(f"\n{'='*70}")
        print(f"#{i+1} {lead['company']} — {lead['role']}")
        print(f"   To: {to_email}")
        print(f"   Subject: {subject}")
        print(f"   Resume: {resume}")
        print(f"{'='*70}")
        print(body)
        print()

        if dry_run or DRY_RUN:
            print("🔵 DRY RUN — not sent")
            continue

        try:
            send_email(to_email, subject, body, resume)
            lead["status"] = "sent"
            state["sent"].append(i)
            log_send(lead["company"], to_email, subject, "success")
            print(f"✅ Sent to {to_email}")
            sent_count += 1

            if sent_count < (limit or DAILY_LIMIT):
                print(f"⏱  Waiting {DELAY_BETWEEN_EMAILS_SEC}s before next email...")
                time.sleep(DELAY_BETWEEN_EMAILS_SEC)
        except smtplib.SMTPAuthenticationError:
            print("❌ AUTHENTICATION FAILED")
            print("   Check: GMAIL_ADDRESS, GMAIL_APP_PASSWORD, 2FA enabled")
            log_send(lead["company"], to_email, subject, "auth_failed", "check 2FA + app password")
            sys.exit(1)
        except Exception as e:
            print(f"❌ ERROR: {e}")
            log_send(lead["company"], to_email, subject, "error", str(e))
            continue

    save_leads(leads)
    save_sent_today(state)
    print(f"\n📊 Sent {sent_count} email(s) today.")


def main():
    parser = argparse.ArgumentParser(description="Lead Sender — Gmail SMTP (testing only)")
    parser.add_argument("--test", action="store_true", help="Send 1 test email to yourself")
    parser.add_argument("--daily", action="store_true", help="Send up to DAILY_LIMIT emails")
    parser.add_argument("--preview", action="store_true", help="Preview without sending")
    parser.add_argument("--lead", type=int, help="Send a specific lead by index (0-based)")
    parser.add_argument("--limit", type=int, help="Override DAILY_LIMIT")
    args = parser.parse_args()

    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("❌ Missing GMAIL_ADDRESS or GMAIL_APP_PASSWORD in .env")
        print(f"   Create .env from .env.example: cp .env.example .env")
        print(f"   See SETUP_GMAIL_SMTP.md for instructions")
        sys.exit(1)

    if args.test:
        run_daily(limit=1, send_to_self=True, dry_run=False)
    elif args.daily:
        run_daily(limit=args.limit or DAILY_LIMIT, dry_run=False)
    elif args.preview:
        run_daily(limit=args.limit or DAILY_LIMIT, dry_run=True)
    elif args.lead is not None:
        run_daily(specific_index=args.lead, dry_run=False)
    else:
        print("Usage:")
        print("  python3 send_emails.py --test          # 1 test email to yourself")
        print("  python3 send_emails.py --daily         # send up to DAILY_LIMIT")
        print("  python3 send_emails.py --preview       # preview, no send")
        print("  python3 send_emails.py --lead 0        # send lead at index 0")
        print("  python3 send_emails.py --daily --limit 5  # cap at 5 emails")


if __name__ == "__main__":
    main()
