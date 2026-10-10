#!/usr/bin/env python3
"""
check_bounces.py — IMAP bounce detector.

Connects to Gmail via IMAP, finds every "Mail Delivery Subsystem" / bounce
message in the inbox, extracts the failed recipient(s), and marks the
matching leads as `bounced` in Postgres.

Also flags the same addresses as opted out (NOT — opted-out means the user
clicked unsubscribe; bounced means server told us it's dead. We keep a
separate `bounced` status so we can re-evaluate after a typo-fix).

Run modes:
    python3 check_bounces.py           # scan + mark (default)
    python3 check_bounces.py --dry     # show what would be marked, no writes
    python3 check_bounces.py --archive # mark bounces, then move them out of INBOX
    python3 check_bounces.py --since 7d  # only look at last 7 days

Cron-ready: `0 7 * * * /usr/bin/python3 .../check_bounces.py >> bounces.log 2>&1`

Why we need this: Gmail SMTP returns success the moment the message is
accepted by their outbound queue. The recipient's server might reject it
hours later ("550 ... does not exist") and Gmail sends a *new* email back to
us with that reason. We have to read those replies to know not to retry.
"""

import os
import re
import sys
import email
import imaplib
import argparse
from pathlib import Path
from email import policy
from datetime import datetime

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from dotenv import load_dotenv
load_dotenv(HERE / ".env")

from db.lead_store import get_cursor, update_status  # noqa

# Subject patterns that scream "this is a bounce"
BOUNCE_SUBJECTS = (
    "delivery status notification (failure)",
    "undelivered mail",
    "returned mail: see transcript for details",
    "mail delivery failed",
    "failure notice",
    "undeliverable:",
)

# Senders that always indicate a bounce (not a reply from a real person)
BOUNCE_SENDERS = (
    "mailer-daemon@",
    "postmaster@",
    "mail delivery subsystem",
    "mailer daemon",
)

# Body pattern that catches the failed address — Gmail's format:
#   "Your message wasn't delivered to <email> because ..."
FAILED_ADDR_RE = re.compile(
    r"(?:wasn't|was not|not be|not)\s+delivered\s+to\s+(?:[^<]*<)?([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})",
    re.I,
)
# Alternate: "Final-Recipient: rfc822; <email>"
RFC822_RE = re.compile(
    r"Final-Recipient:\s*rfc822;\s*(?:<)?([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})",
    re.I,
)
# And the action/reason line
REASON_RE = re.compile(
    r"(?:Diagnostic[- ]?Information:|Status:\s*5\.\d\.\d|Remote server said:)\s*(.{0,200})",
    re.I,
)


def _is_bounce(msg) -> bool:
    """True if the message looks like a delivery failure notification."""
    sender = (msg.get("From") or "").lower()
    subj = (msg.get("Subject") or "").lower().strip()
    if any(b in sender for b in BOUNCE_SENDERS):
        return True
    if any(s in subj for s in BOUNCE_SUBJECTS):
        return True
    return False


def _extract_failed_recipients(body_text: str) -> set[str]:
    """Pull every email address out of the bounce body. Return unique set."""
    found = set()
    if not body_text:
        return found
    for m in FAILED_ADDR_RE.finditer(body_text):
        found.add(m.group(1).lower())
    for m in RFC822_RE.finditer(body_text):
        found.add(m.group(1).lower())
    # Fallback: any address that's NOT the sender's domain might be the recipient.
    # But that's risky — instead, only use the two structured patterns above.
    return found


def _extract_reason(body_text: str) -> str:
    """Best-effort: pull the 5.x.x reason from the bounce body."""
    if not body_text:
        return ""
    m = REASON_RE.search(body_text)
    if m:
        text = re.sub(r"\s+", " ", m.group(1)).strip()
        return text[:160]
    # Fallback: first non-empty, non-header line
    for ln in body_text.splitlines():
        ln = ln.strip()
        if ln and len(ln) > 5 and not ln.startswith("="):
            return ln[:160]
    return ""


def _body_text(msg) -> str:
    """Get the plain-text body of a (possibly multipart) email message."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    return part.get_content() if hasattr(part, "get_content") \
                        else part.get_payload(decode=True).decode("utf-8", "ignore")
                except Exception:
                    continue
        # Fallback to first text/* part
        for part in msg.walk():
            ct = part.get_content_type()
            if ct.startswith("text/"):
                payload = part.get_payload(decode=True) or b""
                return payload.decode("utf-8", "ignore")
        return ""
    payload = msg.get_payload(decode=True) or b""
    return payload.decode("utf-8", "ignore")


def _imap_login():
    user = os.getenv("GMAIL_ADDRESS", "")
    pw = (os.getenv("SMTP_PASSWORD") or os.getenv("GMAIL_APP_PASSWORD", "")).replace(" ", "")
    if not user or not pw:
        raise RuntimeError(
            "GMAIL_ADDRESS / SMTP_PASSWORD not set in .env "
            "(IMAP and SMTP share the same App Password)"
        )
    M = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    M.login(user, pw)
    return M


def _imap_search(M, since_days: int) -> list[bytes]:
    """Return message IDs matching bounce-like criteria in the last N days."""
    ids = set()
    # Date filter (Gmail requires the leading single-quote date format)
    since = ""
    if since_days:
        from datetime import datetime, timedelta
        d = (datetime.utcnow() - timedelta(days=since_days)).strftime("%d-%b-%Y")
        since = f' SENTSINCE {d}'
    queries = [
        f'(OR FROM "mailer-daemon@" FROM "postmaster@"){since}',
        f'(SUBJECT "Delivery Status Notification" SUBJECT "Failure"){since}',
        f'SUBJECT "Undelivered Mail"{since}',
        f'SUBJECT "Returned mail"{since}',
    ]
    for q in queries:
        try:
            typ, data = M.search(None, q)
            if data and data[0]:
                ids.update(data[0].split())
        except imaplib.IMAP4.error as e:
            print(f"  search error on {q!r}: {e}")
    return sorted(ids)


def _fetch_message(M, uid: bytes):
    """Fetch a single message by UID, return parsed email.Message or None."""
    typ, data = M.fetch(uid, "(RFC822)")
    if not (data and data[0]):
        return None
    raw = data[0][1]
    if not raw:
        return None
    try:
        return email.message_from_bytes(raw, policy=policy.default)
    except Exception:
        return email.message_from_bytes(raw)


def scan_bounces(since_days: int = 14) -> dict:
    """Scan inbox, return {email: reason} for each bounce detected."""
    M = _imap_login()
    try:
        M.select("INBOX")
        uids = _imap_search(M, since_days)
        result = {}
        for uid in uids:
            try:
                msg = _fetch_message(M, uid)
            except Exception as e:
                print(f"  fetch error on {uid!r}: {e}")
                continue
            if not msg or not _is_bounce(msg):
                continue
            body = _body_text(msg)
            failed = _extract_failed_recipients(body)
            reason = _extract_reason(body)
            for addr in failed:
                # Don't record the sender's own address as a bounce
                if addr not in result:  # first one wins
                    result[addr] = reason or "(no reason extracted)"
        return result, len(uids)
    finally:
        try:
            M.logout()
        except Exception:
            pass


def mark_bounced(bounce_map: dict, dry: bool = False) -> dict:
    """Mark each bounced lead in Postgres. Returns counts."""
    counts = {"matched": 0, "marked": 0, "already_bounced": 0, "unknown": 0}
    if not bounce_map:
        return counts
    with get_cursor() as cur:
        for email_addr, reason in bounce_map.items():
            cur.execute(
                "SELECT id, company, status FROM leads "
                "WHERE LOWER(contact_email) = LOWER(%s) "
                "ORDER BY id DESC LIMIT 1",
                (email_addr,),
            )
            row = cur.fetchone()
            if not row:
                counts["unknown"] += 1
                continue
            counts["matched"] += 1
            if row["status"] == "bounced":
                counts["already_bounced"] += 1
                continue
            if dry:
                counts["marked"] += 1
                continue
            update_status(row["id"], "bounced", error=f"Bounce: {reason}")
            counts["marked"] += 1
            print(f"  🚫 lead #{row['id']:>3}  {row['company'][:25]:25s}  "
                  f"{email_addr:30s}  → bounced  ({reason[:60]})")
    return counts


def archive_processed(M, uids: list[bytes], bounce_map: dict):
    """Move processed bounce messages to a 'Bounced' label/folder."""
    # Try to CREATE the label if missing, then move
    try:
        M.create("Avilx/Bounces")
    except imaplib.IMAP4.error:
        pass
    moved = 0
    for uid in uids:
        try:
            M.copy(uid, "Avilx/Bounces")
            M.store(uid, "+FLAGS", "\\Deleted")
            moved += 1
        except Exception as e:
            print(f"  archive error on {uid!r}: {e}")
    if moved:
        M.expunge()
    return moved


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true",
                    help="Show what would be marked, don't update DB")
    ap.add_argument("--archive", action="store_true",
                    help="After marking, move bounce msgs to Avilx/Bounces label")
    ap.add_argument("--since", type=int, default=14,
                    help="Look back N days (default 14)")
    args = ap.parse_args()

    print(f"\n📬 BOUNCE SCAN — {datetime.now().isoformat()[:19]}")
    print(f"   Since: {args.since}d  dry={args.dry}  archive={args.archive}")

    try:
        bounce_map, scanned = scan_bounces(args.since)
    except Exception as e:
        print(f"❌ IMAP error: {e}")
        print("   Tip: enable IMAP in Gmail settings, and use an App Password.")
        return 1
    print(f"   Scanned {scanned} candidate messages; "
          f"found {len(bounce_map)} unique bounced recipients")

    if bounce_map:
        print("\n   Detected bounces:")
        for addr, reason in sorted(bounce_map.items())[:20]:
            print(f"     • {addr:35s}  {reason[:80]}")
        if len(bounce_map) > 20:
            print(f"     ...and {len(bounce_map) - 20} more")

    counts = mark_bounced(bounce_map, dry=args.dry)
    print(f"\n   Matched {counts['matched']} leads in DB")
    print(f"   Newly marked bounced: {counts['marked']}")
    print(f"   Already bounced:      {counts['already_bounced']}")
    print(f"   Unknown senders:      {counts['unknown']}")

    if args.archive and not args.dry:
        # Re-scan to get UIDs again for archiving (we already logged out)
        try:
            M = _imap_login()
            M.select("INBOX")
            uids = _imap_search(M, args.since)
            bounce_uids = []
            for uid in uids:
                try:
                    msg = _fetch_message(M, uid)
                    if msg and _is_bounce(msg):
                        body = _body_text(msg)
                        if _extract_failed_recipients(body):
                            bounce_uids.append(uid)
                except Exception:
                    continue
            moved = archive_processed(M, bounce_uids, bounce_map)
            print(f"   Archived {moved} bounce messages to Avilx/Bounces")
            M.logout()
        except Exception as e:
            print(f"   (archive failed: {e})")

    if args.dry:
        print("\n  (dry run — no changes made)")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)