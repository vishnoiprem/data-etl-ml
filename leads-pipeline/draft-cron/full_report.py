#!/usr/bin/env python3
"""
full_report.py — Detailed multi-section report for the Avilx leads pipeline.
Shows:
  - Funnel by status
  - Top companies by lead count
  - Top sources by lead count
  - Pending leads (next 25 with full details: company, role, email, source URL, JD)
  - Recently sent leads (last 20)
  - Bounced leads (last 20 with bounce domain)
  - Pending leads WITHOUT a tailored cover letter (need to enrich)
  - Pending leads WITHOUT a tailored resume (need to enrich)

Run:  python3 full_report.py
"""

import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))


def main():
    from db.lead_store import get_cursor

    with get_cursor() as cur:
        # Header
        print(f"\n{'='*78}")
        print(f"📊 AVILX LEADS — FULL REPORT")
        print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"{'='*78}")

        # 1. Funnel
        cur.execute("SELECT status, COUNT(*) FROM leads GROUP BY status ORDER BY 2 DESC")
        rows = cur.fetchall()
        total = sum(r["count"] for r in rows)
        print(f"\n1. FUNNEL  (total: {total})")
        for r in rows:
            pct = (r["count"] / total * 100) if total else 0
            bar = "█" * int(pct / 2)
            print(f"   {r['status']:15s} {r['count']:4d}  ({pct:5.1f}%)  {bar}")

        sent = next((r["count"] for r in rows if r["status"] == "sent_email"), 0)
        bounced = next((r["count"] for r in rows if r["status"] == "bounced"), 0)
        bounce_rate = (bounced / sent * 100) if sent else 0
        print(f"\n   Bounce rate: {bounce_rate:.1f}%  ({bounced}/{sent})")

        # 2. Top sources
        cur.execute("""
            SELECT COALESCE(source, '(none)') AS src, COUNT(*) FROM leads
            GROUP BY 1 ORDER BY 2 DESC LIMIT 15
        """)
        print(f"\n2. TOP SOURCES")
        for r in cur.fetchall():
            print(f"   {r['src']:30s} {r['count']:4d}")

        # 3. Top companies
        cur.execute("""
            SELECT company, COUNT(*) FROM leads
            GROUP BY 1 HAVING COUNT(*) > 1
            ORDER BY 2 DESC LIMIT 15
        """)
        print(f"\n3. TOP COMPANIES (multi-role)")
        for r in cur.fetchall():
            print(f"   {r['company'][:40]:40s} {r['count']:3d}")

        # 4. Pending with full details
        cur.execute("""
            SELECT id, company, role, contact_email, source, source_url, jd_text,
                   (cover_letter_body IS NOT NULL) AS has_cover,
                   (resume_file IS NOT NULL) AS has_resume
            FROM leads
            WHERE contact_email IS NOT NULL AND contact_email != ''
              AND status = 'pending'
            ORDER BY id
        """)
        pending = cur.fetchall()
        print(f"\n4. PENDING (w/ email) — {len(pending)} total")
        for r in pending[:25]:
            flags = []
            if not r["has_cover"]:
                flags.append("❌cover")
            if not r["has_resume"]:
                flags.append("❌resume")
            else:
                flags.append("✅resume")
            if r["has_cover"]:
                flags.append("✅cover")
            flag_str = " ".join(flags)
            role_short = (r["role"] or "")[:50]
            jd_short = (r["jd_text"] or "")[:80]
            print(f"   #{r['id']:3d} {(r['company'] or '')[:20]:20s} {role_short:50s}")
            print(f"        ✉ {r['contact_email']}  src={r['source']:15s} {flag_str}")
            if r["source_url"]:
                print(f"        🔗 {r['source_url'][:100]}")
            if jd_short:
                print(f"        📝 {jd_short}")
            print()
        if len(pending) > 25:
            print(f"   ... and {len(pending) - 25} more pending leads\n")

        # 5. Recently sent
        cur.execute("""
            SELECT id, company, contact_email, sent_at FROM leads
            WHERE sent_at IS NOT NULL AND sent_at > NOW() - INTERVAL '7 days'
            ORDER BY sent_at DESC LIMIT 20
        """)
        recent = cur.fetchall()
        print(f"\n5. RECENTLY SENT (last 7d) — {len(recent)}")
        for r in recent:
            d = r["sent_at"].strftime("%m-%d %H:%M")
            print(f"   #{r['id']:3d} {d}  {(r['company'] or '')[:30]:30s}  {r['contact_email']}")

        # 6. Bounced
        cur.execute("""
            SELECT id, company, contact_email FROM leads
            WHERE status = 'bounced' ORDER BY id DESC LIMIT 20
        """)
        bounced_recent = cur.fetchall()
        print(f"\n6. BOUNCED (most recent) — {len(bounced_recent)} shown")
        for r in bounced_recent:
            print(f"   #{r['id']:3d} {(r['company'] or '')[:30]:30s}  {r['contact_email']}")

        # 7. Pending w/o cover letter
        cur.execute("""
            SELECT COUNT(*) FROM leads
            WHERE status = 'pending' AND cover_letter_body IS NULL
        """)
        no_cover = cur.fetchone()["count"]
        # 8. Pending w/o resume
        cur.execute("""
            SELECT COUNT(*) FROM leads
            WHERE status = 'pending' AND resume_file IS NULL
        """)
        no_resume = cur.fetchone()["count"]
        print(f"\n7. ENRICHMENT GAPS")
        print(f"   Pending w/o cover letter: {no_cover}")
        print(f"   Pending w/o tailored resume: {no_resume}")

        # 9. By domain
        cur.execute("""
            SELECT SPLIT_PART(contact_email, '@', 2) AS domain, COUNT(*) FROM leads
            WHERE contact_email IS NOT NULL
            GROUP BY 1 ORDER BY 2 DESC LIMIT 15
        """)
        print(f"\n8. TOP EMAIL DOMAINS")
        for r in cur.fetchall():
            print(f"   {r['domain']:30s} {r['count']:4d}")

    print(f"\n{'='*78}\n")


if __name__ == "__main__":
    main()
