#!/usr/bin/env python3
"""
daily_report.py — Print a daily pipeline status report.

Shows:
  - Lead funnel by status
  - Pending w/ email
  - Sends today, this week
  - Top bounced domains (auto-deriving patterns)
  - Bounce rate
  - Top companies by status
  - Recent sends (last 24h)

Run:  python3 daily_report.py
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))


def main():
    from db.lead_store import get_cursor

    with get_cursor() as cur:
        # Funnel
        cur.execute("SELECT status, COUNT(*) FROM leads GROUP BY status ORDER BY 2 DESC")
        rows = cur.fetchall()
        total = sum(r["count"] for r in rows)
        print(f"\n{'='*60}\n📊 AVILX LEADS — DAILY REPORT ({datetime.now().strftime('%Y-%m-%d %H:%M %Z')})\n{'='*60}")
        print(f"\nTotal leads: {total}")
        for r in rows:
            pct = (r["count"] / total * 100) if total else 0
            print(f"  {r['status']:15s} {r['count']:4d}  ({pct:5.1f}%)")
        sent = next((r["count"] for r in rows if r["status"] == "sent_email"), 0)
        bounced = next((r["count"] for r in rows if r["status"] == "bounced"), 0)
        pending = next((r["count"] for r in rows if r["status"] == "pending"), 0)
        pending_email = 0
        cur.execute("""
            SELECT COUNT(*) FROM leads
            WHERE contact_email IS NOT NULL AND contact_email != ''
              AND status = 'pending'
        """)
        pending_email = cur.fetchone()["count"]
        bounce_rate = (bounced / sent * 100) if sent else 0
        print(f"\nBounce rate: {bounce_rate:.1f}% ({bounced}/{sent})")
        print(f"Pending w/ email: {pending_email}")

        # Sends today
        cur.execute("""
            SELECT COUNT(*) FROM leads
            WHERE sent_at > NOW() - INTERVAL '24 hours'
        """)
        sends_24h = cur.fetchone()["count"]
        cur.execute("""
            SELECT COUNT(*) FROM leads
            WHERE sent_at > NOW() - INTERVAL '7 days'
        """)
        sends_7d = cur.fetchone()["count"]
        print(f"\nSends last 24h: {sends_24h}")
        print(f"Sends last 7d:  {sends_7d}")

        # Top bounced domains
        cur.execute("""
            SELECT SPLIT_PART(contact_email, '@', 2) AS domain, COUNT(*)
            FROM leads
            WHERE status = 'bounced'
            GROUP BY 1
            ORDER BY 2 DESC
            LIMIT 10
        """)
        bounced_domains = cur.fetchall()
        if bounced_domains:
            print(f"\n🚫 Top bounced domains:")
            for r in bounced_domains:
                print(f"  {r['domain']:35s} {r['count']:3d}")

        # Top companies by total leads
        cur.execute("""
            SELECT company, COUNT(*) FROM leads
            GROUP BY 1
            HAVING COUNT(*) > 1
            ORDER BY 2 DESC LIMIT 10
        """)
        top_co = cur.fetchall()
        if top_co:
            print(f"\n🏢 Top companies (multi-role):")
            for r in top_co:
                print(f"  {r['company'][:40]:40s} {r['count']:3d}")

        # Recent sends (24h)
        cur.execute("""
            SELECT id, company, contact_email, sent_at
            FROM leads
            WHERE sent_at > NOW() - INTERVAL '24 hours'
            ORDER BY sent_at DESC LIMIT 15
        """)
        recent = cur.fetchall()
        if recent:
            print(f"\n📧 Recent sends (last 24h):")
            for r in recent:
                d = r["sent_at"].strftime("%m-%d %H:%M") if r["sent_at"] else "-"
                print(f"  #{r['id']:3d} {d}  {r['company'][:25]:25s}  {r['contact_email']}")

        # Pending preview (next 10 to send)
        cur.execute("""
            SELECT id, company, role, contact_email, created_at
            FROM leads
            WHERE contact_email IS NOT NULL AND contact_email != ''
              AND status = 'pending'
            ORDER BY id
            LIMIT 10
        """)
        next_batch = cur.fetchall()
        if next_batch:
            print(f"\n📬 Next batch (pending w/ email):")
            for r in next_batch:
                d = r["created_at"].strftime("%m-%d %H:%M") if r["created_at"] else "-"
                print(f"  #{r['id']:3d} {d}  {r['company'][:25]:25s}  {(r['role'] or '')[:35]:35s}  {r['contact_email']}")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
