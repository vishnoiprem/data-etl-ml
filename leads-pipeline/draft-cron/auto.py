#!/usr/bin/env python3
"""
Auto Daily Runner — handles both email + URL apply, no questions asked.

Usage:
  python3 auto.py            # full daily run (emails + open URLs)
  python3 auto.py --email    # emails only
  python3 auto.py --url      # URL-apply only
  python3 auto.py --dry      # preview only, no actions

This is the "automode" entrypoint. Runs without prompts.
"""

import os
import json
import time
import smtplib
import ssl
import argparse
import sys
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv

# Load .env
ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(ENV_PATH)

# Config
SMTP_PROVIDER = os.getenv("SMTP_PROVIDER", "gmail").lower()
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", os.getenv("GMAIL_ADDRESS", ""))
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", os.getenv("GMAIL_APP_PASSWORD", "")).replace(" ", "")
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "true" if SMTP_PROVIDER == "gmail" else "false").lower() == "true"
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "false" if SMTP_PROVIDER == "gmail" else "true").lower() == "true"

# Backwards-compat: GMAIL_ADDRESS used as the From address
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", SMTP_USERNAME)
YOUR_NAME = os.getenv("YOUR_NAME", "Prem Vishnoi")
YOUR_COMPANY = os.getenv("YOUR_COMPANY", "Avilx")
YOUR_EMAIL = os.getenv("YOUR_EMAIL", "hello@avilx.com")
YOUR_PHONE = os.getenv("YOUR_PHONE", "")
YOUR_WHATSAPP = os.getenv("YOUR_WHATSAPP", os.getenv("YOUR_PHONE", ""))
YOUR_WEBSITE = os.getenv("YOUR_WEBSITE", "https://avilx.com")
RESUME_DIR = Path(os.getenv("RESUME_DIR", str(Path.home() / "Documents" / "Resumes")))
DAILY_LIMIT = int(os.getenv("DAILY_LIMIT", "10"))
DELAY_BETWEEN_EMAILS_SEC = int(os.getenv("DELAY_BETWEEN_EMAILS_SEC", "120"))

LEADS_FILE = Path(__file__).parent / "leads.json"
LOG_FILE = Path(__file__).parent / "auto_log.csv"
STATE_FILE = Path(__file__).parent / ".sent_today.json"

PERSONAL_SIG = f"""{YOUR_NAME}
{YOUR_COMPANY} — Global Build · Deploy · Engineers (AI · Data · ML · Cloud · Databricks · 7+ clouds)
Delivery: China · APAC · US · EU | HQ: Ha Noi, Vietnam
📧 {YOUR_EMAIL} | 📱 {YOUR_PHONE} | 💬 WhatsApp: wa.me/{YOUR_WHATSAPP.lstrip('+')} | 🌐 {YOUR_WEBSITE} | 🐦 @vishnoiprem"""


def log(action, company, target, status, error=""):
    """Log an action to auto_log.csv."""
    file_exists = LOG_FILE.exists()
    with open(LOG_FILE, "a") as f:
        if not file_exists:
            f.write("timestamp,action,company,target,status,error\n")
        ts = datetime.now().isoformat()
        action_safe = action.replace(",", ";")
        target_safe = target.replace(",", ";")
        error_safe = error.replace(",", ";")
        f.write(f"{ts},{action_safe},{company},{target_safe},{status},{error_safe}\n")


def load_leads():
    with open(LEADS_FILE) as f:
        return json.load(f)


def save_leads(leads):
    with open(LEADS_FILE, "w") as f:
        json.dump(leads, f, indent=2)


def load_state():
    if not STATE_FILE.exists():
        return {"date": "", "processed": []}
    with open(STATE_FILE) as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def personalize(body):
    return body.replace("{PERSONAL_SIG}", PERSONAL_SIG)


def build_html_email(body_text, subject):
    """Build a nicely designed HTML email from the plain-text cover letter body."""
    # Convert plain-text body to HTML paragraphs
    paragraphs_html = ""
    for para in body_text.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        # If a paragraph is a single line, keep it tight; if multi-line, use <br>
        if "\n" in para:
            para_html = "<br>".join(para.split("\n"))
        else:
            para_html = para
        paragraphs_html += f'<p style="margin:0 0 16px 0;font-size:15px;line-height:1.6;color:#1a1a1a;">{para_html}</p>\n      '

    wa_link = f"https://wa.me/{YOUR_WHATSAPP.lstrip('+')}"
    site = YOUR_WEBSITE.replace("https://", "")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{subject}</title>
</head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background:#f3f4f6;padding:32px 16px;">
<tr><td align="center">
<table role="presentation" cellspacing="0" cellpadding="0" border="0" width="600" style="max-width:600px;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.05);">
  <!-- Header / brand -->
  <tr><td style="background:linear-gradient(135deg,#0a1929 0%,#1e3a5f 100%);padding:32px 40px;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
      <tr>
        <td style="color:#ffffff;font-size:24px;font-weight:800;letter-spacing:-0.02em;">Avilx</td>
        <td align="right" style="color:#4ade80;font-size:11px;font-weight:600;letter-spacing:0.1em;">GLOBAL BUILD · DEPLOY · ENGINEERS</td>
      </tr>
    </table>
  </td></tr>

  <!-- Body -->
  <tr><td style="padding:40px 40px 24px 40px;">
    {paragraphs_html}
  </td></tr>

  <!-- Value-prop callout strip -->
  <tr><td style="padding:0 40px 32px 40px;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background:#f8f9fb;border:1px solid #e5e7eb;border-radius:8px;padding:20px;">
      <tr>
        <td width="33%" valign="top" style="padding:8px 12px;">
          <div style="font-size:11px;font-weight:700;color:#4ade80;letter-spacing:0.1em;margin-bottom:4px;">BUILD</div>
          <div style="font-size:13px;color:#1a1a1a;font-weight:600;margin-bottom:2px;">AI · Data · ML · Apps</div>
          <div style="font-size:12px;color:#6b7280;">Ship end-to-end</div>
        </td>
        <td width="33%" valign="top" style="padding:8px 12px;border-left:1px solid #e5e7eb;">
          <div style="font-size:11px;font-weight:700;color:#4ade80;letter-spacing:0.1em;margin-bottom:4px;">DEPLOY</div>
          <div style="font-size:13px;color:#1a1a1a;font-weight:600;margin-bottom:2px;">AWS · Azure · Tencent · Alibaba</div>
          <div style="font-size:12px;color:#6b7280;">7+ clouds · global</div>
        </td>
        <td width="33%" valign="top" style="padding:8px 12px;border-left:1px solid #e5e7eb;">
          <div style="font-size:11px;font-weight:700;color:#4ade80;letter-spacing:0.1em;margin-bottom:4px;">ENGINEERS</div>
          <div style="font-size:13px;color:#1a1a1a;font-weight:600;margin-bottom:2px;">Senior · Databricks Champion</div>
          <div style="font-size:12px;color:#6b7280;">8+ yrs · async-first</div>
        </td>
      </tr>
    </table>
  </td></tr>

  <!-- Stats strip -->
  <tr><td style="padding:0 40px 32px 40px;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
      <tr>
        <td width="25%" align="center" style="padding:8px;">
          <div style="font-size:22px;font-weight:800;color:#0a1929;">15+</div>
          <div style="font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">yrs senior</div>
        </td>
        <td width="25%" align="center" style="padding:8px;border-left:1px solid #e5e7eb;">
          <div style="font-size:22px;font-weight:800;color:#0a1929;">7+</div>
          <div style="font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">clouds</div>
        </td>
        <td width="25%" align="center" style="padding:8px;border-left:1px solid #e5e7eb;">
          <div style="font-size:22px;font-weight:800;color:#0a1929;">$40-70</div>
          <div style="font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">/hr pod</div>
        </td>
        <td width="25%" align="center" style="padding:8px;border-left:1px solid #e5e7eb;">
          <div style="font-size:22px;font-weight:800;color:#0a1929;">$120-180</div>
          <div style="font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">/hr principal</div>
        </td>
      </tr>
    </table>
  </td></tr>

  <!-- Global delivery strip -->
  <tr><td style="padding:0 40px 32px 40px;">
    <div style="text-align:center;font-size:12px;color:#4b5563;padding:12px;background:#0a1929;border-radius:8px;">
      <span style="color:#4ade80;font-weight:600;">Global delivery:</span>
      <span style="color:#ffffff;font-weight:600;">China</span> ·
      <span style="color:#ffffff;font-weight:600;">APAC</span> ·
      <span style="color:#ffffff;font-weight:600;">US</span> ·
      <span style="color:#ffffff;font-weight:600;">EU</span>
      &nbsp;·&nbsp;
      <span style="color:#9ca3af;">USD / EUR / CNY invoicing</span>
    </div>
  </td></tr>

  <!-- CTA button -->
  <tr><td align="center" style="padding:0 40px 32px 40px;">
    <a href="{YOUR_WEBSITE}" style="display:inline-block;background:#4ade80;color:#0a1929;padding:14px 32px;border-radius:8px;font-weight:700;text-decoration:none;font-size:15px;">Visit avilx.com →</a>
  </td></tr>

  <!-- Signature block -->
  <tr><td style="padding:0 40px 24px 40px;border-top:1px solid #e5e7eb;padding-top:24px;">
    <div style="font-size:15px;font-weight:700;color:#0a1929;margin-bottom:2px;">{YOUR_NAME}</div>
    <div style="font-size:13px;color:#4b5563;margin-bottom:2px;">Principal · {YOUR_COMPANY} — Global Build · Deploy · Engineers</div>
    <div style="font-size:12px;color:#6b7280;margin-bottom:12px;">AI · Data · ML · Cloud · Databricks · 7+ clouds (AWS · Azure · Tencent · Alibaba) · Ha Noi, Vietnam</div>
    <table role="presentation" cellspacing="0" cellpadding="0" border="0">
      <tr>
        <td style="padding:2px 0;font-size:12px;color:#6b7280;">📧 <a href="mailto:{YOUR_EMAIL}" style="color:#6b7280;text-decoration:none;">{YOUR_EMAIL}</a></td>
      </tr>
      <tr>
        <td style="padding:2px 0;font-size:12px;color:#6b7280;">📱 <a href="tel:{YOUR_PHONE}" style="color:#6b7280;text-decoration:none;">{YOUR_PHONE}</a></td>
      </tr>
      <tr>
        <td style="padding:2px 0;font-size:12px;color:#6b7280;">💬 <a href="{wa_link}" style="color:#6b7280;text-decoration:none;">WhatsApp me</a> &nbsp;·&nbsp; 🌐 <a href="{YOUR_WEBSITE}" style="color:#6b7280;text-decoration:none;">{site}</a> &nbsp;·&nbsp; 🐦 <a href="https://x.com/vishnoiprem" style="color:#6b7280;text-decoration:none;">@vishnoiprem</a></td>
      </tr>
    </table>
  </td></tr>

  <!-- Footer -->
  <tr><td style="background:#f8f9fb;padding:16px 40px;text-align:center;font-size:11px;color:#9ca3af;">
    © 2026 {YOUR_COMPANY} · Vietnam LLC · Build with us. Globally.
  </td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""


def send_email(to_email, subject, body_text, resume_file):
    """Send one email via Gmail/Outlook SMTP with both plain-text and HTML parts."""
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{YOUR_NAME} <{GMAIL_ADDRESS}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["Reply-To"] = YOUR_EMAIL

    # Plain-text version (for clients that don't render HTML)
    text_part = MIMEText(body_text, "plain", "utf-8")
    msg.attach(text_part)

    # Nicely designed HTML version
    html_content = build_html_email(body_text, subject)
    html_part = MIMEText(html_content, "html", "utf-8")
    msg.attach(html_part)

    if resume_file:
        full_path = RESUME_DIR / resume_file
        if full_path.exists():
            with open(full_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename= {resume_file}")
                msg.attach(part)

    context = ssl.create_default_context()
    if SMTP_USE_SSL:
        # Implicit SSL (Gmail on 465)
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())
    else:
        # STARTTLS (Outlook/Microsoft 365 on 587)
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            if SMTP_USE_TLS:
                server.starttls(context=context)
                server.ehlo()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())


def run_email_phase(leads, dry=False):
    """Send emails for leads with apply_method=email."""
    print("\n📧 PHASE 1: EMAIL")
    print("=" * 70)
    sent = 0
    for i, lead in enumerate(leads):
        if lead["apply_method"] != "email":
            continue
        if lead["status"] != "pending":
            continue
        if not lead.get("contact_email"):
            continue

        subject = lead["cover_letter_subject"]
        body = personalize(lead["cover_letter_body"])

        print(f"\n#{i+1} {lead['company']}")
        print(f"   To: {lead['contact_email']}")
        print(f"   Subject: {subject}")

        if dry:
            print("   🔵 DRY RUN — would send")
            continue

        try:
            send_email(lead["contact_email"], subject, body, lead["resume_file"])
            lead["status"] = "sent_email"
            log("email", lead["company"], lead["contact_email"], "success")
            print(f"   ✅ Sent")
            sent += 1
            if sent < 3:
                time.sleep(DELAY_BETWEEN_EMAILS_SEC)
        except Exception as e:
            log("email", lead["company"], lead.get("contact_email", ""), "error", str(e))
            print(f"   ❌ Error: {e}")

    return sent


def run_url_phase(leads, dry=False):
    """Open URLs for leads with apply_method=url."""
    print("\n🌐 PHASE 2: URL APPLY")
    print("=" * 70)
    opened = 0
    for i, lead in enumerate(leads):
        if lead["apply_method"] != "url":
            continue
        if lead["status"] != "pending":
            continue

        print(f"\n#{i+1} {lead['company']}")
        print(f"   URL: {lead['url']}")
        print(f"   Cover letter ready (length: {len(lead['cover_letter_body'])} chars)")

        if dry:
            print("   🔵 DRY RUN — would open")
            continue

        try:
            webbrowser.open_new_tab(lead["url"])
            log("url", lead["company"], lead["url"], "opened")
            lead["status"] = "opened_url"
            print(f"   ✅ Opened in browser")
            opened += 1
            time.sleep(1)  # Don't slam the browser
        except Exception as e:
            log("url", lead["company"], lead.get("url", ""), "error", str(e))
            print(f"   ❌ Error: {e}")

    return opened


def run(dry=False, email_only=False, url_only=False):
    leads = load_leads()
    pending = [l for l in leads if l["status"] == "pending"]
    print(f"\n📊 STATUS")
    print(f"   Total leads: {len(leads)}")
    print(f"   Pending:     {len(pending)}")
    print(f"   Email-track: {sum(1 for l in leads if l['apply_method']=='email' and l['status']=='pending')}")
    print(f"   URL-track:   {sum(1 for l in leads if l['apply_method']=='url' and l['status']=='pending')}")

    if not pending:
        print("\n🎉 All leads processed. Replenish by running the firehose agent.")
        return

    if dry:
        print("\n🔵 DRY RUN MODE — no emails sent, no URLs opened")

    email_sent = 0
    url_opened = 0

    if not url_only:
        email_sent = run_email_phase(leads, dry)
    if not email_only:
        url_opened = run_url_phase(leads, dry)

    save_leads(leads)

    print("\n" + "=" * 70)
    print(f"📊 SUMMARY")
    print(f"   Emails sent:  {email_sent}")
    print(f"   URLs opened:  {url_opened}")
    print(f"   Log:          {LOG_FILE}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Auto daily lead runner — no prompts")
    parser.add_argument("--email", action="store_true", help="Email phase only")
    parser.add_argument("--url", action="store_true", help="URL phase only")
    parser.add_argument("--dry", action="store_true", help="Dry run, no actual sends/opens")
    args = parser.parse_args()

    run(dry=args.dry, email_only=args.email, url_only=args.url)


if __name__ == "__main__":
    main()
