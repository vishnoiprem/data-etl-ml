#!/usr/bin/env python3
"""
bin/send_followups.py — Day-4 follow-up for non-repliers.

For every lead with status='sent_email', sent_at > 4 days ago, and
no reply, generate a 2-3 sentence follow-up and send.

Why this exists: 1st email reply rate is ~1-3% industry standard.
A 2nd email on day 4 typically 2-3x's the cumulative reply rate
because most non-replies are "saw it, forgot to reply", not
"actively rejected".

Sends are throttled to FOLLOWUP_DAILY_CAP (default 5) per run so
we never blow past Gmail's daily sending limit.

Run modes:
    python3 bin/send_followups.py                    # send up to 5 follow-ups
    python3 bin/send_followups.py --max 10           # cap at 10
    python3 bin/send_followups.py --dry              # preview, no sends
    python3 bin/send_followups.py --days 7           # follow up after 7 days
    python3 bin/send_followups.py --mode pitch_pod   # only pod-pitch leads
"""

import argparse
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from dotenv import load_dotenv
load_dotenv(HERE / ".env")

import db.lead_store as ls
from cover_letter import _pick_hook


# ──────────────────────────────────────────────────────────────────
# Follow-up copy
# ──────────────────────────────────────────────────────────────────
def _build_followup(lead: dict) -> tuple[str, str]:
    """Subject + body for a 2-3 sentence day-N follow-up.

    Subject uses Re: prefix to thread under the original, but the body
    is short and adds a new angle (case study or a specific question)
    so the recipient has a fresh reason to engage.
    """
    co = (lead.get("company") or "").strip() or "your team"
    role = (lead.get("role") or "the role").strip()
    jd = lead.get("jd_text") or ""
    hook = _pick_hook(jd)
    mode = (lead.get("apply_mode") or "pitch_pod").strip().lower()

    # Subject: keep it short, change wording so it's not flagged as duplicate
    if mode == "apply_personal":
        subj = f"Re: {co} — {role} application (next steps?)"
    else:
        subj = f"Re: Avilx pod for {co} — quick check-in"

    # Body: pivot on either the hook (if matched) or a generic time-constraint nudge
    if hook:
        angle = (f"Wanted to flag a recent {hook} case study — it's a 6-week "
                 f"build we just shipped for a similar team. Happy to share "
                 f"the architecture if useful.")
    else:
        angle = ("Wanted to bump this — are you still hiring for this role, "
                 "or has the priority shifted?")

    if mode == "apply_personal":
        body = (
            f"Hi {co} team,\n\n"
            f"{angle}\n\n"
            f"15-min call this week if there's still a fit?\n\n"
            f"Prem\n"
        )
    else:
        body = (
            f"Hi {co} team,\n\n"
            f"{angle}\n\n"
            f"No pressure — just wanted to make sure this didn't get "
            f"buried. 2-week pilot pod is still on the table if useful.\n\n"
            f"Prem\n"
        )
    return subj, body


# ──────────────────────────────────────────────────────────────────
# Send path
# ──────────────────────────────────────────────────────────────────
def _send_followup_email(lead: dict, subject: str, body: str) -> None:
    """Send a single follow-up via the same SMTP path as autopilot._send_one.

    Reuses the SMTP env vars (AVILX_SMTP_*).
    """
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders

    SMTP_HOST = os.getenv("AVILX_SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("AVILX_SMTP_PORT", "465"))
    SMTP_USER = os.getenv("AVILX_SMTP_USER") or os.getenv("AVILX_GMAIL_USER", "")
    SMTP_PASS = (os.getenv("AVILX_SMTP_PASS")
                 or os.getenv("AVILX_GMAIL_APP_PASSWORD", ""))
    YOUR_NAME = os.getenv("AVILX_FOUNDER", "Prem Vishnoi")
    YOUR_EMAIL = os.getenv("AVILX_EMAIL", "hello@avilx.com")

    msg = MIMEMultipart()
    msg["From"] = f"{YOUR_NAME} <{YOUR_EMAIL}>"
    msg["To"] = lead["contact_email"]
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # Attach the same JD-tailored resume as the original send so the
    # recipient doesn't have to dig for it
    try:
        from resume_tailor import tailor_resume
        rp = tailor_resume(lead)
        if rp and rp.exists() and rp.stat().st_size <= 5 * 1024 * 1024:
            with open(rp, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{rp.name}"',
            )
            msg.attach(part)
    except Exception as e:
        print(f"    ⚠️  resume attach failed: {e}")

    # Send
    import ssl
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx, timeout=30) as s:
        s.login(SMTP_USER, SMTP_PASS)
        s.sendmail(msg["From"], lead["contact_email"], msg.as_string())


def _record_followup(lead_id: int, subject: str) -> None:
    """Mark the lead as followup-sent in the DB.

    Uses status='followup_sent' to distinguish from the initial send.
    Subsequent runs skip leads already in that state.
    """
    with ls.get_cursor() as cur:
        cur.execute("""
            UPDATE leads
            SET status = 'followup_sent',
                sent_at = NOW(),
                send_count = send_count + 1,
                last_error = %s
            WHERE id = %s
        """, (f"followup: {subject[:60]}", lead_id))


def _pick_followups(days: int, mode: str, max_n: int) -> list[dict]:
    """Find leads eligible for follow-up.

    Excludes addresses that have opted out or are in the bounce-deny list.
    Same exclusion autopilot applies on the first send; otherwise we
    would re-mail a recipient who already told us (or their server)
    to stop.
    """
    with ls.get_cursor() as cur:
        cur.execute("""
            SELECT id, company, role, contact_email, jd_text,
                   apply_mode, sent_at, send_count
            FROM leads
            WHERE status = 'sent_email'
              AND sent_at < NOW() - (%s || ' days')::INTERVAL
              AND contact_email IS NOT NULL
              AND apply_method = 'email'
              AND LOWER(contact_email) NOT IN (SELECT email FROM opt_outs)
            ORDER BY sent_at ASC
            LIMIT %s
        """, (str(days), max_n * 4))  # over-fetch for mode filter
        rows = [dict(r) for r in cur.fetchall()]
    if mode != "both":
        rows = [l for l in rows
                if (l.get("apply_mode") or "pitch_pod") == mode]
    # Also drop anyone on the bounce-deny set (loaded by autopilot at
    # import). This catches domains that bounced hard but were never
    # marked `bounced` in the DB.
    try:
        from state.bounce_deny_store import BOUNCE_DENY
        rows = [l for l in rows
                if l.get("contact_email") and l["contact_email"].lower() not in BOUNCE_DENY]
    except Exception:
        pass
    return rows[:max_n]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--max", type=int, default=5,
                   help="Max follow-ups to send this run (default 5)")
    p.add_argument("--days", type=int, default=4,
                   help="Send follow-up if sent_at is older than N days (default 4)")
    p.add_argument("--mode", choices=("pitch_pod", "apply_personal", "both"),
                   default="both", help="Which leads to follow up")
    p.add_argument("--dry", action="store_true",
                   help="Preview follow-ups, no sends")
    args = p.parse_args()

    print(f"🔁 Avilx follow-up — max={args.max}, days>= {args.days}, mode={args.mode}")
    leads = _pick_followups(args.days, args.mode, args.max)
    if not leads:
        print("  No leads eligible for follow-up.")
        return 0

    sent = 0
    for lead in leads:
        subj, body = _build_followup(lead)
        if args.dry:
            print(f"  [dry] {lead['contact_email']:35s} {lead['company'][:25]:25s} → {subj}")
            sent += 1
            continue
        try:
            _send_followup_email(lead, subj, body)
            _record_followup(lead["id"], subj)
            sent += 1
            print(f"  ✅ {lead['contact_email']:35s} {lead['company'][:25]:25s} → {subj}")
            if sent < len(leads):
                time.sleep(15)  # throttle between sends
        except Exception as e:
            print(f"  ❌ {lead['contact_email']:35s} {lead['company'][:25]:25s} {e}")
    print(f"\n→ followups sent: {sent}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
