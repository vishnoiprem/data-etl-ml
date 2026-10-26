"""
db_cli.py — Tiny CLI to view the leads DB + log LinkedIn DMs.

Lead commands:
  python3 db_cli.py status          # summary stats
  python3 db_cli.py recent [N]      # show N most recent leads
  python3 db_cli.py pending        # show pending leads
  python3 db_cli.py sent           # show sent leads (last 30)
  python3 db_cli.py search <email>  # find a lead by email
  python3 db_cli.py company <name>  # find leads by company name
  python3 db_cli.py companies       # all unique companies + counts

LinkedIn DM commands:
  python3 db_cli.py log-dm @handle "Name" "Company" "Title" "Region" "Template" "DM text"
  python3 db_cli.py dm-status                       # campaign stats
  python3 db_cli.py followups                       # DMs needing a bump
  python3 db_cli.py mark-replied @handle [notes]    # mark as replied
  python3 db_cli.py dm-recent [N]                   # last N DMs
"""

import sys
import os
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from db.lead_store import (
    get_cursor, stats, get_by_email,
    log_dm, log_dm_followup, update_dm_status, dm_stats, list_pending_followups,
)  # noqa


def cmd_status():
    s = stats()
    print("📊 Avilx leads DB")
    for k, v in s["by_status"].items():
        print(f"   {k:15s} {v}")
    print(f"   {'sent (24h)':15s} {s['sent_last_24h']}")
    print(f"   {'opt-outs':15s} {s['opt_outs']}")
    print(f"   {'companies':15s} {s['unique_companies']}")


def cmd_recent(n=20):
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, tracking_id, company, role, contact_email, status, sent_at, created_at "
            "FROM leads ORDER BY id DESC LIMIT %s",
            (n,),
        )
        rows = cur.fetchall()
    if not rows:
        print("(no leads)")
        return
    print(f"{'ID':4s} {'TRACK':12s} {'COMPANY':30s} {'ROLE':35s} {'STATUS':12s} EMAIL")
    print("-" * 130)
    for r in rows:
        print(f"{r['id']:<4d} {r['tracking_id']:12s} {r['company'][:30]:30s} {(r['role'] or '?')[:35]:35s} {r['status']:12s} {r['contact_email'] or ''}")


def cmd_pending():
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, tracking_id, company, role, contact_email, apply_method, source_url "
            "FROM leads WHERE status='pending' ORDER BY id"
        )
        rows = cur.fetchall()
    if not rows:
        print("(no pending leads)")
        return
    print(f"📋 {len(rows)} pending lead(s):")
    for r in rows:
        method = r["apply_method"]
        if method == "email":
            target = r["contact_email"] or "?"
        else:
            target = r.get("source_url") or "?"
        print(f"   #{r['id']:3d} {r['tracking_id']:12s} {r['company']:25s} {(r['role'] or '?')[:30]:30s} [{method}] → {target}")


def cmd_sent():
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, tracking_id, company, role, contact_email, sent_at "
            "FROM leads WHERE status='sent_email' ORDER BY sent_at DESC LIMIT 30"
        )
        rows = cur.fetchall()
    if not rows:
        print("(no sent leads)")
        return
    print(f"📧 {len(rows)} most recent sent:")
    for r in rows:
        ts = r["sent_at"].strftime("%Y-%m-%d %H:%M") if r["sent_at"] else "?"
        print(f"   {ts}  {r['tracking_id']:12s} {r['company']:25s} → {r['contact_email']}")


def cmd_search(email):
    lead = get_by_email(email)
    if not lead:
        print(f"No lead with email: {email}")
        return
    for k in ("id", "tracking_id", "company", "role", "contact_email", "contact_phone",
             "apply_method", "status", "sent_at", "send_count", "source", "cover_letter_subject"):
        v = lead.get(k)
        if v is not None:
            print(f"  {k:22s} {v}")


def cmd_company(name):
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM leads WHERE LOWER(company) LIKE LOWER(%s) ORDER BY id",
            (f"%{name}%",),
        )
        rows = cur.fetchall()
    if not rows:
        print(f"No leads matching '{name}'")
        return
    for r in rows:
        print(f"  #{r['id']:3d} {r['tracking_id']:12s} {r['company']:30s} {(r['role'] or '?')[:30]:30s} {r['status']:12s} → {r['contact_email'] or r.get('source_url', '?')}")


def cmd_companies():
    with get_cursor() as cur:
        cur.execute(
            "SELECT company, COUNT(*) AS n, MAX(status) AS latest_status "
            "FROM leads GROUP BY LOWER(company), company ORDER BY company"
        )
        rows = cur.fetchall()
    if not rows:
        print("(no companies)")
        return
    for r in rows:
        print(f"  {r['company']:35s} {r['n']} lead(s)  (latest: {r['latest_status']})")


# =========================================
# LinkedIn DM tracking
# =========================================

def cmd_log_dm(args):
    """log-dm @handle "Name" "Company" "Title" "Region" "Template" "DM text" [LinkedIn URL]"""
    if len(args) < 7:
        print(__doc__)
        print("Usage: log-dm @handle \"Name\" \"Company\" \"Title\" \"Region\" \"Template\" \"DM text\" [LinkedIn URL]")
        return
    handle = args[0]
    name, company, title, region, template, dm_text = args[1:7]
    linkedin_url = args[7] if len(args) > 7 else None
    dm_id = log_dm(
        handle=handle,
        name=name,
        company=company,
        title=title,
        region=region,
        template_used=template,
        dm_text=dm_text,
        linkedin_url=linkedin_url,
    )
    print(f"✅ Logged DM #{dm_id} to {handle} ({name} @ {company})")


def cmd_log_followup(args):
    """followup @handle "message"  — log a bump"""
    if len(args) < 2:
        print("Usage: followup @handle \"message\"")
        return
    handle, message = args[0], args[1]
    fu_id = log_dm_followup(handle, message)
    print(f"✅ Logged followup #{fu_id} to {handle}")


def cmd_dm_status():
    s = dm_stats()
    print("📣 LinkedIn DM campaign")
    print("   By status:")
    for k, v in s["by_status"].items():
        print(f"     {k:12s} {v}")
    print(f"   Sent (7d):     {s['sent_7d']}")
    print(f"   Replied (7d):  {s['replied_7d']}")
    f = s["funnel_14d"]
    print(f"   Funnel (14d):")
    print(f"     total={f['total']}  pending_reply={f['pending_reply']}  replied={f['replied']}  advanced={f['advanced']}")


def cmd_followups():
    rows = list_pending_followups()
    if not rows:
        print("(no DMs need a follow-up bump)")
        return
    print(f"🔔 {len(rows)} DM(s) need a bump:")
    for r in rows:
        last = r["last_touch_at"] or r["sent_at"]
        ts = last.strftime("%Y-%m-%d") if last else "?"
        name = r.get("name") or "?"
        company = r.get("company") or "?"
        print(f"   @{r['handle']:20s} {name[:20]:20s} {company[:25]:25s} touches={r['touch_count']} last={ts}")


def cmd_mark_replied(args):
    """mark-replied @handle [notes]"""
    if len(args) < 1:
        print("Usage: mark-replied @handle [notes]")
        return
    handle = args[0]
    notes = args[1] if len(args) > 1 else None
    update_dm_status(handle, "replied", notes)
    print(f"✅ Marked @{handle} as replied")


def cmd_dm_recent(n=20):
    with get_cursor() as cur:
        cur.execute(
            "SELECT handle, name, company, title, status, sent_at, touch_count "
            "FROM linkedin_dms ORDER BY sent_at DESC LIMIT %s",
            (n,),
        )
        rows = cur.fetchall()
    if not rows:
        print("(no DMs logged)")
        return
    print(f"{'HANDLE':20s} {'NAME':20s} {'COMPANY':25s} {'TITLE':18s} {'STATUS':10s} {'TOUCH':5s} SENT")
    print("-" * 120)
    for r in rows:
        ts = r["sent_at"].strftime("%Y-%m-%d") if r["sent_at"] else "?"
        print(f"@{r['handle']:19s} {(r['name'] or '?')[:20]:20s} {(r['company'] or '?')[:25]:25s} {(r['title'] or '?')[:18]:18s} {r['status']:10s} {r['touch_count']:5d} {ts}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    if cmd == "status":
        cmd_status()
    elif cmd == "recent":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        cmd_recent(n)
    elif cmd == "pending":
        cmd_pending()
    elif cmd == "sent":
        cmd_sent()
    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: search <email>")
            return
        cmd_search(sys.argv[2])
    elif cmd == "company":
        if len(sys.argv) < 3:
            print("Usage: company <name>")
            return
        cmd_company(sys.argv[2])
    elif cmd == "companies":
        cmd_companies()
    elif cmd == "log-dm":
        cmd_log_dm(sys.argv[2:])
    elif cmd == "followup":
        cmd_log_followup(sys.argv[2:])
    elif cmd == "dm-status":
        cmd_dm_status()
    elif cmd == "followups":
        cmd_followups()
    elif cmd == "mark-replied":
        cmd_mark_replied(sys.argv[2:])
    elif cmd == "dm-recent":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        cmd_dm_recent(n)
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
